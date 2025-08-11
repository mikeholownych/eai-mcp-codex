"""Payment dispute and chargeback management service."""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from uuid import uuid4
from sqlalchemy import and_, or_, func
from sqlalchemy.orm import Session

from .models import Dispute, Charge, Customer, PaymentIntent, AuditLog
from .exceptions import DisputeError
from .gateways.base import PaymentGateway
from .utils import create_audit_log

logger = logging.getLogger(__name__)


class DisputeService:
    """Service for managing payment disputes and chargebacks."""
    
    def __init__(self, db: Session, payment_gateway: PaymentGateway):
        self.db = db
        self.payment_gateway = payment_gateway
    
    def create_dispute(
        self,
        charge_id: str,
        reason: str,
        amount_minor: int,
        currency: str,
        evidence_due_by: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dispute:
        """Create a new dispute record."""
        try:
            # Verify charge exists
            charge = self.db.query(Charge).filter(Charge.id == charge_id).first()
            if not charge:
                raise DisputeError(f"Charge {charge_id} not found")
            
            # Check if dispute already exists
            existing_dispute = self.db.query(Dispute).filter(
                Dispute.charge_id == charge_id
            ).first()
            
            if existing_dispute:
                raise DisputeError(f"Dispute already exists for charge {charge_id}")
            
            # Create dispute in payment gateway
            gateway_dispute = await self.payment_gateway.create_dispute(
                charge_id=charge.provider_charge_id,
                reason=reason,
                amount=amount_minor,
                currency=currency
            )
            
            # Create local dispute record
            dispute = Dispute(
                provider_id=gateway_dispute.id,
                charge_id=charge_id,
                status="needs_response",
                reason=reason,
                amount_minor=amount_minor,
                currency=currency,
                evidence_due_by=evidence_due_by or (datetime.utcnow() + timedelta(days=7)),
                metadata=metadata or {}
            )
            
            self.db.add(dispute)
            self.db.commit()
            self.db.refresh(dispute)
            
            # Create audit log
            await create_audit_log(
                self.db,
                actor="system",
                action="dispute_created",
                resource_type="dispute",
                resource_id=str(dispute.id),
                metadata={
                    'charge_id': charge_id,
                    'reason': reason,
                    'amount': amount_minor,
                    'gateway_dispute_id': gateway_dispute.id
                }
            )
            
            logger.info(f"Created dispute {dispute.id} for charge {charge_id}")
            return dispute
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to create dispute: {e}")
            raise DisputeError(f"Failed to create dispute: {e}")
    
    def update_dispute_status(
        self,
        dispute_id: str,
        status: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dispute:
        """Update dispute status."""
        try:
            dispute = self.db.query(Dispute).filter(Dispute.id == dispute_id).first()
            if not dispute:
                raise DisputeError(f"Dispute {dispute_id} not found")
            
            old_status = dispute.status
            dispute.status = status
            
            if metadata:
                dispute.metadata.update(metadata)
            
            dispute.updated_at = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(dispute)
            
            # Create audit log
            await create_audit_log(
                self.db,
                actor="system",
                action="dispute_status_updated",
                resource_type="dispute",
                resource_id=str(dispute.id),
                metadata={
                    'old_status': old_status,
                    'new_status': status,
                    'metadata': metadata
                }
            )
            
            logger.info(f"Updated dispute {dispute_id} status from {old_status} to {status}")
            return dispute
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to update dispute status: {e}")
            raise DisputeError(f"Failed to update dispute status: {e}")
    
    def submit_evidence(
        self,
        dispute_id: str,
        evidence: Dict[str, Any],
        evidence_type: str = "general"
    ) -> Dispute:
        """Submit evidence for a dispute."""
        try:
            dispute = self.db.query(Dispute).filter(Dispute.id == dispute_id).first()
            if not dispute:
                raise DisputeError(f"Dispute {dispute_id} not found")
            
            # Submit evidence to payment gateway
            await self.payment_gateway.submit_dispute_evidence(
                dispute_id=dispute.provider_id,
                evidence=evidence,
                evidence_type=evidence_type
            )
            
            # Update local dispute record
            if not dispute.evidence:
                dispute.evidence = {}
            
            dispute.evidence[evidence_type] = {
                'data': evidence,
                'submitted_at': datetime.utcnow().isoformat()
            }
            
            dispute.evidence_submitted_at = datetime.utcnow()
            dispute.updated_at = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(dispute)
            
            # Create audit log
            await create_audit_log(
                self.db,
                actor="system",
                action="dispute_evidence_submitted",
                resource_type="dispute",
                resource_id=str(dispute.id),
                metadata={
                    'evidence_type': evidence_type,
                    'evidence': evidence
                }
            )
            
            logger.info(f"Submitted evidence for dispute {dispute_id}")
            return dispute
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to submit evidence: {e}")
            raise DisputeError(f"Failed to submit evidence: {e}")
    
    def accept_dispute(
        self,
        dispute_id: str,
        reason: Optional[str] = None
    ) -> Dispute:
        """Accept a dispute and process refund."""
        try:
            dispute = self.db.query(Dispute).filter(Dispute.id == dispute_id).first()
            if not dispute:
                raise DisputeError(f"Dispute {dispute_id} not found")
            
            if dispute.status not in ["needs_response", "under_review"]:
                raise DisputeError(f"Cannot accept dispute in status {dispute.status}")
            
            # Accept dispute in payment gateway
            await self.payment_gateway.accept_dispute(
                dispute_id=dispute.provider_id,
                reason=reason
            )
            
            # Update local dispute record
            dispute.status = "accepted"
            dispute.metadata['accepted_at'] = datetime.utcnow().isoformat()
            dispute.metadata['acceptance_reason'] = reason
            dispute.updated_at = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(dispute)
            
            # Create audit log
            await create_audit_log(
                self.db,
                actor="system",
                action="dispute_accepted",
                resource_type="dispute",
                resource_id=str(dispute.id),
                metadata={
                    'reason': reason,
                    'accepted_at': datetime.utcnow().isoformat()
                }
            )
            
            logger.info(f"Accepted dispute {dispute_id}")
            return dispute
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to accept dispute: {e}")
            raise DisputeError(f"Failed to accept dispute: {e}")
    
    def contest_dispute(
        self,
        dispute_id: str,
        evidence: Dict[str, Any],
        reason: Optional[str] = None
    ) -> Dispute:
        """Contest a dispute with evidence."""
        try:
            dispute = self.db.query(Dispute).filter(Dispute.id == dispute_id).first()
            if not dispute:
                raise DisputeError(f"Dispute {dispute_id} not found")
            
            if dispute.status not in ["needs_response", "under_review"]:
                raise DisputeError(f"Cannot contest dispute in status {dispute.status}")
            
            # Contest dispute in payment gateway
            await self.payment_gateway.contest_dispute(
                dispute_id=dispute.provider_id,
                evidence=evidence,
                reason=reason
            )
            
            # Update local dispute record
            dispute.status = "contested"
            dispute.metadata['contested_at'] = datetime.utcnow().isoformat()
            dispute.metadata['contest_reason'] = reason
            dispute.evidence['contest'] = {
                'data': evidence,
                'submitted_at': datetime.utcnow().isoformat()
            }
            dispute.updated_at = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(dispute)
            
            # Create audit log
            await create_audit_log(
                self.db,
                actor="system",
                action="dispute_contested",
                resource_type="dispute",
                resource_id=str(dispute.id),
                metadata={
                    'reason': reason,
                    'evidence': evidence,
                    'contested_at': datetime.utcnow().isoformat()
                }
            )
            
            logger.info(f"Contested dispute {dispute_id}")
            return dispute
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to contest dispute: {e}")
            raise DisputeError(f"Failed to contest dispute: {e}")
    
    def get_dispute(self, dispute_id: str) -> Dispute:
        """Get dispute by ID."""
        dispute = self.db.query(Dispute).filter(Dispute.id == dispute_id).first()
        if not dispute:
            raise DisputeError(f"Dispute {dispute_id} not found")
        return dispute
    
    def get_disputes_by_charge(self, charge_id: str) -> List[Dispute]:
        """Get all disputes for a specific charge."""
        return self.db.query(Dispute).filter(Dispute.charge_id == charge_id).all()
    
    def get_disputes_by_customer(self, customer_id: str) -> List[Dispute]:
        """Get all disputes for a specific customer."""
        return self.db.query(Dispute).join(Charge).join(PaymentIntent).filter(
            PaymentIntent.customer_id == customer_id
        ).all()
    
    def get_disputes_by_status(
        self,
        status: str,
        limit: Optional[int] = None
    ) -> List[Dispute]:
        """Get disputes by status."""
        query = self.db.query(Dispute).filter(Dispute.status == status)
        if limit:
            query = query.limit(limit)
        return query.all()
    
    def get_disputes_needing_response(self) -> List[Dispute]:
        """Get disputes that need a response."""
        now = datetime.utcnow()
        return self.db.query(Dispute).filter(
            and_(
                Dispute.status.in_(["needs_response", "under_review"]),
                Dispute.evidence_due_by <= now
            )
        ).all()
    
    def get_disputes_due_soon(self, days_ahead: int = 3) -> List[Dispute]:
        """Get disputes due for response soon."""
        now = datetime.utcnow()
        due_date = now + timedelta(days=days_ahead)
        
        return self.db.query(Dispute).filter(
            and_(
                Dispute.status.in_(["needs_response", "under_review"]),
                Dispute.evidence_due_by <= due_date,
                Dispute.evidence_due_by > now
            )
        ).all()
    
    def get_dispute_statistics(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Get dispute statistics for a period."""
        try:
            # Total disputes
            total_disputes = self.db.query(func.count(Dispute.id)).filter(
                and_(
                    Dispute.created_at >= start_date,
                    Dispute.created_at <= end_date
                )
            ).scalar()
            
            # Disputes by status
            disputes_by_status = self.db.query(
                Dispute.status,
                func.count(Dispute.id).label('count'),
                func.sum(Dispute.amount_minor).label('total_amount')
            ).filter(
                and_(
                    Dispute.created_at >= start_date,
                    Dispute.created_at <= end_date
                )
            ).group_by(Dispute.status).all()
            
            # Disputes by reason
            disputes_by_reason = self.db.query(
                Dispute.reason,
                func.count(Dispute.id).label('count'),
                func.sum(Dispute.amount_minor).label('total_amount')
            ).filter(
                and_(
                    Dispute.created_at >= start_date,
                    Dispute.created_at <= end_date
                )
            ).group_by(Dispute.reason).all()
            
            # Average dispute amount
            avg_dispute_amount = self.db.query(
                func.avg(Dispute.amount_minor)
            ).filter(
                and_(
                    Dispute.created_at >= start_date,
                    Dispute.created_at <= end_date
                )
            ).scalar() or 0
            
            return {
                'total_disputes': total_disputes,
                'disputes_by_status': [
                    {
                        'status': result.status,
                        'count': result.count,
                        'total_amount': result.total_amount
                    }
                    for result in disputes_by_status
                ],
                'disputes_by_reason': [
                    {
                        'reason': result.reason,
                        'count': result.count,
                        'total_amount': result.total_amount
                    }
                    for result in disputes_by_reason
                ],
                'average_dispute_amount': round(avg_dispute_amount, 2),
                'period': {
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get dispute statistics: {e}")
            raise DisputeError(f"Failed to get dispute statistics: {e}")
    
    def process_webhook_dispute_update(
        self,
        dispute_data: Dict[str, Any]
    ) -> Dispute:
        """Process webhook update for dispute status change."""
        try:
            # Find dispute by provider ID
            dispute = self.db.query(Dispute).filter(
                Dispute.provider_id == dispute_data['id']
            ).first()
            
            if not dispute:
                logger.warning(f"Dispute not found for provider ID: {dispute_data['id']}")
                return None
            
            # Update dispute status and metadata
            old_status = dispute.status
            dispute.status = dispute_data.get('status', dispute.status)
            
            if 'evidence_due_by' in dispute_data:
                dispute.evidence_due_by = datetime.fromisoformat(dispute_data['evidence_due_by'])
            
            dispute.metadata.update(dispute_data.get('metadata', {}))
            dispute.updated_at = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(dispute)
            
            # Create audit log for status change
            if old_status != dispute.status:
                await create_audit_log(
                    self.db,
                    actor="webhook",
                    action="dispute_status_updated",
                    resource_type="dispute",
                    resource_id=str(dispute.id),
                    metadata={
                        'old_status': old_status,
                        'new_status': dispute.status,
                        'webhook_data': dispute_data
                    }
                )
            
            logger.info(f"Updated dispute {dispute.id} via webhook to status {dispute.status}")
            return dispute
            
        except Exception as e:
            logger.error(f"Failed to process webhook dispute update: {e}")
            raise DisputeError(f"Failed to process webhook dispute update: {e}")

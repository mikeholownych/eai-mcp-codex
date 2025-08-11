"""
Email service for marketing automation and campaign management.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from uuid import uuid4
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import aiohttp
import json
import jinja2

from ..common.redis_client import RedisClient

logger = logging.getLogger(__name__)


class EmailStatus(str, Enum):
    """Email status values"""
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    SENDING = "sending"
    SENT = "sent"
    DELIVERED = "delivered"
    OPENED = "opened"
    CLICKED = "clicked"
    BOUNCED = "bounced"
    FAILED = "failed"


@dataclass
class EmailTemplate:
    """Email template definition"""
    id: str = field(default_factory=lambda: str(uuid4()))
    name: str = ""
    subject: str = ""
    html_content: str = ""
    text_content: str = ""
    variables: List[str] = field(default_factory=list)
    category: str = ""
    active: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class EmailCampaign:
    """Email campaign definition"""
    id: str = field(default_factory=lambda: str(uuid4()))
    name: str = ""
    description: str = ""
    template_id: str = ""
    subject_line: str = ""
    sender_name: str = ""
    sender_email: str = ""
    reply_to: str = ""
    target_audience: Dict[str, Any] = field(default_factory=dict)
    schedule: Optional[datetime] = None
    status: EmailStatus = EmailStatus.DRAFT
    metrics: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class EmailDelivery:
    """Email delivery tracking"""
    id: str = field(default_factory=lambda: str(uuid4()))
    campaign_id: str = ""
    recipient_email: str = ""
    recipient_name: str = ""
    subject: str = ""
    status: EmailStatus = EmailStatus.DRAFT
    sent_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    opened_at: Optional[datetime] = None
    clicked_at: Optional[datetime] = None
    bounce_reason: Optional[str] = None
    tracking_id: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


class EmailService:
    """Email service for marketing automation"""

    def __init__(self, redis_client: RedisClient, config: Dict[str, Any]):
        self.redis_client = redis_client
        self.config = config
        
        # Email templates
        self.templates: Dict[str, EmailTemplate] = {}
        
        # Email campaigns
        self.campaigns: Dict[str, EmailCampaign] = {}
        
        # Delivery tracking
        self.deliveries: Dict[str, EmailDelivery] = {}
        
        # Jinja2 template engine
        self.template_engine = jinja2.Environment(
            loader=jinja2.DictLoader({}),
            autoescape=True
        )
        
        # SMTP configuration
        self.smtp_config = config.get("smtp", {})
        
        # Email service configuration
        self.email_service_config = config.get("email_service", {})
        
        # Delivery queue
        self.delivery_queue: asyncio.Queue = asyncio.Queue()
        
        # Delivery worker
        self.delivery_worker_running = False
        self.delivery_task: Optional[asyncio.Task] = None

    async def start_delivery_worker(self):
        """Start the email delivery worker"""
        if self.delivery_worker_running:
            logger.warning("Delivery worker already running")
            return

        self.delivery_worker_running = True
        self.delivery_task = asyncio.create_task(self._delivery_worker())
        logger.info("Email delivery worker started")

    async def stop_delivery_worker(self):
        """Stop the email delivery worker"""
        self.delivery_worker_running = False
        if self.delivery_task:
            self.delivery_task.cancel()
            try:
                await self.delivery_task
            except asyncio.CancelledError:
                pass
        logger.info("Email delivery worker stopped")

    async def _delivery_worker(self):
        """Email delivery worker loop"""
        while self.delivery_worker_running:
            try:
                # Get next email from queue
                try:
                    delivery_data = await asyncio.wait_for(
                        self.delivery_queue.get(), timeout=1.0
                    )
                except asyncio.TimeoutError:
                    continue

                # Process email delivery
                await self._process_email_delivery(delivery_data)
                
                # Mark task as done
                self.delivery_queue.task_done()
                
            except Exception as e:
                logger.error(f"Error in delivery worker: {e}")
                await asyncio.sleep(1)

    async def create_template(self, template_data: Dict[str, Any]) -> EmailTemplate:
        """Create a new email template"""
        template = EmailTemplate(**template_data)
        self.templates[template.id] = template
        
        # Add to Jinja2 environment
        self.template_engine.loader.mapping[template.id] = template.html_content
        
        logger.info(f"Created email template: {template.name}")
        return template

    async def update_template(self, template_id: str, updates: Dict[str, Any]) -> Optional[EmailTemplate]:
        """Update email template"""
        if template_id not in self.templates:
            return None
            
        template = self.templates[template_id]
        
        # Update fields
        for key, value in updates.items():
            if hasattr(template, key):
                setattr(template, key, value)
        
        template.updated_at = datetime.utcnow()
        
        # Update Jinja2 environment if content changed
        if "html_content" in updates:
            self.template_engine.loader.mapping[template_id] = template.html_content
        
        logger.info(f"Updated email template: {template.name}")
        return template

    async def create_campaign(self, campaign_data: Dict[str, Any]) -> EmailCampaign:
        """Create a new email campaign"""
        campaign = EmailCampaign(**campaign_data)
        self.campaigns[campaign.id] = campaign
        
        logger.info(f"Created email campaign: {campaign.name}")
        return campaign

    async def send_campaign(self, campaign_id: str, recipients: List[Dict[str, str]]) -> bool:
        """Send an email campaign to recipients"""
        if campaign_id not in self.campaigns:
            logger.error(f"Campaign not found: {campaign_id}")
            return False
            
        campaign = self.campaigns[campaign_id]
        
        if campaign.status != EmailStatus.DRAFT:
            logger.error(f"Cannot send campaign in status: {campaign.status}")
            return False
        
        # Update campaign status
        campaign.status = EmailStatus.SENDING
        
        # Create deliveries for each recipient
        for recipient in recipients:
            delivery = EmailDelivery(
                campaign_id=campaign_id,
                recipient_email=recipient["email"],
                recipient_name=recipient.get("name", ""),
                subject=campaign.subject_line,
                status=EmailStatus.SCHEDULED,
                tracking_id=str(uuid4())
            )
            
            self.deliveries[delivery.id] = delivery
            
            # Add to delivery queue
            await self.delivery_queue.put({
                "delivery_id": delivery.id,
                "campaign_id": campaign_id,
                "recipient": recipient,
                "template_id": campaign.template_id
            })
        
        logger.info(f"Queued campaign {campaign.name} for {len(recipients)} recipients")
        return True

    async def send_single_email(self, to_email: str, subject: str, content: str, 
                               from_name: str = "", from_email: str = "", 
                               html_content: str = "") -> bool:
        """Send a single email"""
        try:
            # Create message
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = f"{from_name} <{from_email}>" if from_name else from_email
            msg["To"] = to_email
            
            # Add text content
            if content:
                text_part = MIMEText(content, "plain")
                msg.attach(text_part)
            
            # Add HTML content
            if html_content:
                html_part = MIMEText(html_content, "html")
                msg.attach(html_part)
            
            # Send email
            await self._send_smtp_email(msg)
            
            logger.info(f"Sent single email to {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            return False

    async def _process_email_delivery(self, delivery_data: Dict[str, Any]):
        """Process email delivery from queue"""
        delivery_id = delivery_data["delivery_id"]
        campaign_id = delivery_data["campaign_id"]
        recipient = delivery_data["recipient"]
        template_id = delivery_data["template_id"]
        
        if delivery_id not in self.deliveries:
            logger.error(f"Delivery not found: {delivery_id}")
            return
        
        delivery = self.deliveries[delivery_id]
        
        try:
            # Update status to sending
            delivery.status = EmailStatus.SENDING
            
            # Get template
            if template_id not in self.templates:
                logger.error(f"Template not found: {template_id}")
                delivery.status = EmailStatus.FAILED
                return
            
            template = self.templates[template_id]
            
            # Render template with recipient data
            rendered_html = await self._render_template(template, recipient)
            rendered_text = await self._render_template_text(template, recipient)
            
            # Create email message
            msg = MIMEMultipart("alternative")
            msg["Subject"] = delivery.subject
            msg["From"] = f"Ethical AI Insider <noreply@ethicalaiinsider.com>"
            msg["To"] = delivery.recipient_email
            
            # Add text content
            if rendered_text:
                text_part = MIMEText(rendered_text, "plain")
                msg.attach(text_part)
            
            # Add HTML content
            if rendered_html:
                html_part = MIMEText(rendered_html, "html")
                msg.attach(html_part)
            
            # Add tracking pixel
            tracking_pixel = await self._create_tracking_pixel(delivery.tracking_id)
            if tracking_pixel:
                msg.attach(tracking_pixel)
            
            # Send email
            await self._send_smtp_email(msg)
            
            # Update delivery status
            delivery.status = EmailStatus.SENT
            delivery.sent_at = datetime.utcnow()
            
            # Schedule delivery confirmation check
            asyncio.create_task(self._check_delivery_confirmation(delivery_id))
            
            logger.info(f"Sent campaign email to {delivery.recipient_email}")
            
        except Exception as e:
            logger.error(f"Failed to send campaign email to {delivery.recipient_email}: {e}")
            delivery.status = EmailStatus.FAILED
            delivery.bounce_reason = str(e)

    async def _render_template(self, template: EmailTemplate, recipient: Dict[str, str]) -> str:
        """Render email template with recipient data"""
        try:
            jinja_template = self.template_engine.get_template(template.id)
            return jinja_template.render(**recipient)
        except Exception as e:
            logger.error(f"Failed to render template {template.id}: {e}")
            return template.html_content

    async def _render_template_text(self, template: EmailTemplate, recipient: Dict[str, str]) -> str:
        """Render text version of email template"""
        try:
            if template.text_content:
                jinja_template = self.template_engine.from_string(template.text_content)
                return jinja_template.render(**recipient)
            else:
                # Convert HTML to text (basic implementation)
                return self._html_to_text(template.html_content)
        except Exception as e:
            logger.error(f"Failed to render text template {template.id}: {e}")
            return template.text_content or ""

    def _html_to_text(self, html_content: str) -> str:
        """Convert HTML content to plain text (basic implementation)"""
        # Basic HTML to text conversion
        import re
        text = re.sub(r'<[^>]+>', '', html_content)
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    async def _create_tracking_pixel(self, tracking_id: str) -> Optional[MIMEBase]:
        """Create tracking pixel for email open tracking"""
        try:
            # Create 1x1 transparent GIF
            tracking_pixel = MIMEBase("image", "gif")
            tracking_pixel.set_payload(b"GIF89a\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff\x00\x00\x00!\xf9\x04\x01\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;")
            
            tracking_pixel.add_header(
                "Content-Disposition", 
                "inline", 
                filename=f"tracking_{tracking_id}.gif"
            )
            
            return tracking_pixel
            
        except Exception as e:
            logger.error(f"Failed to create tracking pixel: {e}")
            return None

    async def _send_smtp_email(self, msg: MIMEMultipart):
        """Send email via SMTP"""
        if not self.smtp_config:
            logger.warning("No SMTP configuration, skipping email send")
            return
        
        try:
            with smtplib.SMTP(
                self.smtp_config["host"], 
                self.smtp_config.get("port", 587)
            ) as server:
                if self.smtp_config.get("use_tls", True):
                    server.starttls()
                
                if self.smtp_config.get("username"):
                    server.login(
                        self.smtp_config["username"], 
                        self.smtp_config["password"]
                    )
                
                server.send_message(msg)
                
        except Exception as e:
            logger.error(f"SMTP send failed: {e}")
            raise

    async def _check_delivery_confirmation(self, delivery_id: str):
        """Check delivery confirmation (simulated)"""
        # In a real implementation, this would check with the email service provider
        await asyncio.sleep(5)  # Simulate delay
        
        if delivery_id in self.deliveries:
            delivery = self.deliveries[delivery_id]
            delivery.status = EmailStatus.DELIVERED
            delivery.delivered_at = datetime.utcnow()
            
            logger.info(f"Email delivered to {delivery.recipient_email}")

    async def track_email_open(self, tracking_id: str):
        """Track email open event"""
        # Find delivery by tracking ID
        delivery = None
        for d in self.deliveries.values():
            if d.tracking_id == tracking_id:
                delivery = d
                break
        
        if delivery:
            delivery.status = EmailStatus.OPENED
            delivery.opened_at = datetime.utcnow()
            
            # Update campaign metrics
            if delivery.campaign_id in self.campaigns:
                campaign = self.campaigns[delivery.campaign_id]
                campaign.metrics["opens"] = campaign.metrics.get("opens", 0) + 1
            
            logger.info(f"Email opened: {delivery.recipient_email}")

    async def track_email_click(self, tracking_id: str, link_url: str):
        """Track email click event"""
        # Find delivery by tracking ID
        delivery = None
        for d in self.deliveries.values():
            if d.tracking_id == tracking_id:
                delivery = d
                break
        
        if delivery:
            delivery.status = EmailStatus.CLICKED
            delivery.clicked_at = datetime.utcnow()
            
            # Update campaign metrics
            if delivery.campaign_id in self.campaigns:
                campaign = self.campaigns[delivery.campaign_id]
                campaign.metrics["clicks"] = campaign.metrics.get("clicks", 0) + 1
                campaign.metrics["click_links"] = campaign.metrics.get("click_links", [])
                campaign.metrics["click_links"].append(link_url)
            
            logger.info(f"Email clicked: {delivery.recipient_email} -> {link_url}")

    def get_campaign_metrics(self, campaign_id: str) -> Dict[str, Any]:
        """Get campaign metrics"""
        if campaign_id not in self.campaigns:
            return {}
        
        campaign = self.campaigns[campaign_id]
        deliveries = [d for d in self.deliveries.values() if d.campaign_id == campaign_id]
        
        metrics = {
            "total_sent": len(deliveries),
            "delivered": len([d for d in deliveries if d.status in [EmailStatus.DELIVERED, EmailStatus.OPENED, EmailStatus.CLICKED]]),
            "opened": len([d for d in deliveries if d.status in [EmailStatus.OPENED, EmailStatus.CLICKED]]),
            "clicked": len([d for d in deliveries if d.status == EmailStatus.CLICKED]),
            "bounced": len([d for d in deliveries if d.status == EmailStatus.BOUNCED]),
            "failed": len([d for d in deliveries if d.status == EmailStatus.FAILED]),
        }
        
        # Calculate rates
        if metrics["total_sent"] > 0:
            metrics["delivery_rate"] = metrics["delivered"] / metrics["total_sent"]
            metrics["open_rate"] = metrics["opened"] / metrics["total_sent"]
            metrics["click_rate"] = metrics["clicked"] / metrics["total_sent"]
            metrics["bounce_rate"] = metrics["bounced"] / metrics["total_sent"]
        
        return metrics

    def get_template(self, template_id: str) -> Optional[EmailTemplate]:
        """Get template by ID"""
        return self.templates.get(template_id)

    def get_campaign(self, campaign_id: str) -> Optional[EmailCampaign]:
        """Get campaign by ID"""
        return self.campaigns.get(campaign_id)

    def get_delivery(self, delivery_id: str) -> Optional[EmailDelivery]:
        """Get delivery by ID"""
        return self.deliveries.get(delivery_id)

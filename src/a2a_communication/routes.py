"""A2A Communication Hub API routes."""

from datetime import datetime
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from src.common.logging import get_logger

from .models import (
    A2AMessage,
    AgentRegistration,
    AgentStatus,
    CollaborationRequest,
    ConsensusItem,
    MessageType,
)
from .message_broker import A2AMessageBroker


router = APIRouter()
logger = get_logger("a2a_communication")


def get_broker(request: Request) -> A2AMessageBroker:
    return request.app.state.broker


@router.post("/messages/send")
async def send_message(
    message: A2AMessage, broker: A2AMessageBroker = Depends(get_broker)
) -> dict:
    """Send an A2A message."""
    success = await broker.send_message(message)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to send message")

    return {"status": "sent", "message_id": str(message.id)}


@router.get("/messages/{agent_id}")
async def get_messages(
    agent_id: str,
    limit: int = Query(10, ge=1, le=100),
    broker: A2AMessageBroker = Depends(get_broker),
) -> List[A2AMessage]:
    """Get messages for an agent."""
    return await broker.get_messages(agent_id, limit)


@router.post("/agents/register")
async def register_agent(
    registration: AgentRegistration, broker: A2AMessageBroker = Depends(get_broker)
) -> dict:
    """Register an agent."""
    success = await broker.register_agent(registration)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to register agent")

    return {"status": "registered", "agent_id": registration.agent_id}


@router.delete("/agents/{agent_id}")
async def unregister_agent(
    agent_id: str, broker: A2AMessageBroker = Depends(get_broker)
) -> dict:
    """Unregister an agent."""
    success = await broker.unregister_agent(agent_id)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to unregister agent")

    return {"status": "unregistered", "agent_id": agent_id}


@router.get("/agents/type/{agent_type}")
async def get_agents_by_type(
    agent_type: str, broker: A2AMessageBroker = Depends(get_broker)
) -> List[str]:
    """Get agents by type."""
    return await broker.get_agents_by_type(agent_type)


@router.get("/agents/{agent_id}")
async def get_agent(
    agent_id: str, broker: A2AMessageBroker = Depends(get_broker)
) -> AgentRegistration:
    """Get agent information."""
    agent = await broker.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    return agent


@router.put("/agents/{agent_id}/status")
async def update_agent_status(
    agent_id: str, status: AgentStatus, broker: A2AMessageBroker = Depends(get_broker)
) -> dict:
    """Update agent status."""
    success = await broker.update_agent_status(agent_id, status)
    if not success:
        raise HTTPException(status_code=404, detail="Agent not found")

    return {"status": "updated", "agent_id": agent_id, "new_status": status}


@router.post("/agents/{agent_id}/heartbeat")
async def agent_heartbeat(
    agent_id: str, broker: A2AMessageBroker = Depends(get_broker)
) -> dict:
    """Agent heartbeat to maintain registration."""
    success = await broker.update_agent_status(agent_id, AgentStatus.AVAILABLE)
    if not success:
        raise HTTPException(status_code=404, detail="Agent not found")

    return {"status": "heartbeat_received", "timestamp": datetime.utcnow()}


@router.get("/conversations/{conversation_id}/history")
async def get_conversation_history(
    conversation_id: UUID,
    limit: int = Query(50, ge=1, le=200),
    broker: A2AMessageBroker = Depends(get_broker),
) -> List[A2AMessage]:
    """Get conversation message history."""
    return await broker.get_conversation_history(conversation_id, limit)


@router.post("/collaborations/request")
async def request_collaboration(
    request: CollaborationRequest, broker: A2AMessageBroker = Depends(get_broker)
) -> dict:
    """Request collaboration from available agents."""
    # Find agents with required capabilities
    available_agents = []
    for capability in request.required_capabilities:
        agents = await broker.get_agents_by_type(capability)
        available_agents.extend(agents)

    # Remove duplicates and limit to max_agents
    unique_agents = list(set(available_agents))[: request.max_agents]

    if not unique_agents:
        raise HTTPException(
            status_code=404, detail="No agents available with required capabilities"
        )

    # Send collaboration request to selected agents
    collaboration_message = A2AMessage(
        sender_agent_id="collaboration_orchestrator",
        message_type=MessageType.COLLABORATION,
        payload={
            "task_id": str(request.task_id),
            "task_description": request.task_description,
            "context": request.context,
            "deadline": request.deadline.isoformat() if request.deadline else None,
        },
        requires_response=True,
        response_timeout=300,  # 5 minutes
    )

    sent_count = 0
    for agent_id in unique_agents:
        collaboration_message.recipient_agent_id = agent_id
        if await broker.send_message(collaboration_message):
            sent_count += 1

    return {
        "task_id": str(request.task_id),
        "agents_contacted": sent_count,
        "agent_ids": unique_agents,
    }


@router.post("/consensus/create")
async def create_consensus_item(
    item: ConsensusItem, broker: A2AMessageBroker = Depends(get_broker)
) -> dict:
    """Create a consensus item for agent voting."""
    # Send consensus request to all participating agents
    consensus_message = A2AMessage(
        sender_agent_id="collaboration_orchestrator",
        message_type=MessageType.CONSENSUS,
        payload={
            "item_id": str(item.item_id),
            "item_type": item.item_type,
            "description": item.description,
            "options": item.options,
            "threshold": item.threshold,
            "deadline": item.deadline.isoformat() if item.deadline else None,
            "metadata": item.metadata,
        },
        requires_response=True,
        response_timeout=600,  # 10 minutes
    )

    # Broadcast to all active agents for now
    await broker.send_message(consensus_message)

    return {"item_id": str(item.item_id), "status": "consensus_requested"}


@router.get("/system/stats")
async def get_system_stats(broker: A2AMessageBroker = Depends(get_broker)) -> dict:
    """Get A2A system statistics."""
    try:
        # Count active agents by type
        agent_types = ["planner", "architect", "developer", "security", "qa"]
        agent_counts = {}
        total_agents = 0

        for agent_type in agent_types:
            count = len(await broker.get_agents_by_type(agent_type))
            agent_counts[agent_type] = count
            total_agents += count

        return {
            "total_active_agents": total_agents,
            "agents_by_type": agent_counts,
            "system_status": "operational",
            "timestamp": datetime.utcnow(),
        }
    except Exception as e:
        logger.error(f"Failed to get system stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get system stats")


@router.post("/system/cleanup")
def cleanup_system(broker: A2AMessageBroker = Depends(get_broker)) -> dict:
    """Clean up expired messages and inactive agents."""
    cleaned_count = broker.cleanup_expired_messages()
    return {"cleaned_items": cleaned_count, "timestamp": datetime.utcnow()}

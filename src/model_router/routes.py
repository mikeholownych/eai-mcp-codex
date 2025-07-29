"""API routes for the Model Router service."""

from typing import Dict, Any
from fastapi import APIRouter, HTTPException

from src.common.metrics import record_request
from src.common.logging import get_logger

from .models import ModelRequest, ModelResponse, ModelInfo, RoutingStats
from .router import route, get_routing_stats, test_routing
from .claude_client import get_claude_client

router = APIRouter(prefix="/model", tags=["model-router"])
logger = get_logger("model_router_routes")


@router.post("/route", response_model=ModelResponse)
async def route_model(req: ModelRequest) -> ModelResponse:
    """Route a request to the appropriate Claude model."""
    record_request("model-router")
    logger.info(f"Routing request with text length: {len(req.text)}")
    
    try:
        response = route(req)
        logger.info(f"Successfully routed request to model: {response.model_used}")
        return response
    except Exception as e:
        logger.error(f"Error routing request: {e}")
        raise HTTPException(status_code=500, detail=f"Routing failed: {str(e)}")


@router.get("/models", response_model=Dict[str, ModelInfo])
async def get_available_models() -> Dict[str, ModelInfo]:
    """Get information about available Claude models."""
    try:
        claude_client = get_claude_client()
        models_info = {}
        
        for model_name in claude_client.list_available_models():
            info = claude_client.get_model_info(model_name)
            models_info[model_name] = ModelInfo(
                name=model_name,
                max_tokens=info.get("max_tokens", 4096),
                context_window=info.get("context_window", 200000),
                cost_per_1k_input=info.get("cost_per_1k_input", 0.0),
                cost_per_1k_output=info.get("cost_per_1k_output", 0.0),
                use_cases=info.get("use_cases", [])
            )
        
        return models_info
    except Exception as e:
        logger.error(f"Error getting model information: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get model info: {str(e)}")


@router.get("/stats", response_model=Dict[str, Any])
async def get_stats() -> Dict[str, Any]:
    """Get routing statistics and system information."""
    try:
        stats = get_routing_stats()
        logger.info("Retrieved routing statistics")
        return stats
    except Exception as e:
        logger.error(f"Error getting routing stats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")


@router.post("/test")
async def test_routing_functionality() -> Dict[str, Any]:
    """Test the routing functionality with sample requests."""
    try:
        test_results = await test_routing()
        logger.info(f"Routing test completed with {test_results['accuracy']}% accuracy")
        return test_results
    except Exception as e:
        logger.error(f"Error testing routing: {e}")
        raise HTTPException(status_code=500, detail=f"Routing test failed: {str(e)}")


@router.post("/health/claude")
async def test_claude_connection() -> Dict[str, Any]:
    """Test connection to Claude API."""
    try:
        claude_client = get_claude_client()
        connection_ok = await claude_client.test_connection()
        
        return {
            "claude_api_connected": connection_ok,
            "available_models": claude_client.list_available_models(),
            "status": "healthy" if connection_ok else "unhealthy"
        }
    except Exception as e:
        logger.error(f"Claude health check failed: {e}")
        return {
            "claude_api_connected": False,
            "error": str(e),
            "status": "unhealthy"
        }


@router.post("/route/batch")
async def route_batch_requests(requests: list[ModelRequest]) -> list[ModelResponse]:
    """Route multiple requests in batch."""
    if len(requests) > 50:
        raise HTTPException(status_code=400, detail="Batch size cannot exceed 50 requests")
    
    responses = []
    for req in requests:
        try:
            response = route(req)
            responses.append(response)
        except Exception as e:
            logger.error(f"Error in batch routing: {e}")
            responses.append(ModelResponse(
                result=f"Error: {str(e)}",
                model_used="error",
                success=False,
                error_message=str(e)
            ))
    
    return responses


@router.get("/models/{model_name}")
async def get_model_details(model_name: str) -> Dict[str, Any]:
    """Get detailed information about a specific model."""
    try:
        claude_client = get_claude_client()
        
        if model_name not in claude_client.list_available_models():
            raise HTTPException(status_code=404, detail=f"Model {model_name} not found")
        
        model_info = claude_client.get_model_info(model_name)
        return {
            "name": model_name,
            "details": model_info,
            "available": True
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting model details: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get model details: {str(e)}")


@router.post("/route/explain")
async def explain_routing_decision(req: ModelRequest) -> Dict[str, Any]:
    """Explain why a particular model was selected for a request."""
    from .router import _table
    
    try:
        selected_model = _table.select(req.text, req.context)
        
        # Analyze the decision factors
        analysis = {
            "selected_model": selected_model,
            "text_length": len(req.text),
            "context_provided": req.context is not None,
            "task_type": req.context.get("task_type") if req.context else None,
            "decision_factors": []
        }
        
        # Check what influenced the decision
        text_lower = req.text.lower()
        
        high_complexity = ["architecture", "design", "complex", "analysis", "research", "planning", "security audit"]
        medium_complexity = ["code review", "debugging", "implementation", "refactor", "optimize"]
        
        if any(keyword in text_lower for keyword in high_complexity):
            analysis["decision_factors"].append("High complexity keywords detected")
        elif any(keyword in text_lower for keyword in medium_complexity):
            analysis["decision_factors"].append("Medium complexity keywords detected")
        
        if len(req.text) > 1000:
            analysis["decision_factors"].append("Long text (>1000 characters)")
        
        if req.context and req.context.get("task_type"):
            analysis["decision_factors"].append(f"Task type: {req.context['task_type']}")
        
        if not analysis["decision_factors"]:
            analysis["decision_factors"].append("Default routing applied")
        
        return analysis
        
    except Exception as e:
        logger.error(f"Error explaining routing decision: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to explain routing: {str(e)}")

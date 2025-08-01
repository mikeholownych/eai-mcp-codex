from src.analytics.workload_optimizer import AgentWorkloadOptimizer
from src.agent_pool.models import WorkloadDistribution, AgentType, AgentPoolConfig


def test_workload_scaling_recommendations() -> None:
    dist = [
        WorkloadDistribution(
            agent_type=AgentType.DEVELOPER,
            total_instances=2,
            active_instances=2,
            idle_instances=0,
            working_instances=2,
            pending_tasks=5,
            utilization_rate=0.95,
            average_response_time=1.0,
        ),
        WorkloadDistribution(
            agent_type=AgentType.QA,
            total_instances=3,
            active_instances=3,
            idle_instances=2,
            working_instances=1,
            pending_tasks=0,
            utilization_rate=0.2,
            average_response_time=1.0,
        ),
    ]

    config = AgentPoolConfig()
    optimizer = AgentWorkloadOptimizer(scale_up_threshold=0.8, scale_down_threshold=0.3)
    recs = optimizer.recommend_scaling(dist, config)

    assert recs[AgentType.DEVELOPER].scale_up == 1
    assert recs[AgentType.QA].scale_down == 1

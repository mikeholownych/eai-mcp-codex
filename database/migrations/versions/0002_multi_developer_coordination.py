"""Multi-Developer Coordination schema."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create multi-developer coordination tables."""
    
    # Developer profiles table
    op.create_table(
        "developer_profiles",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("agent_id", sa.String(100), nullable=False, unique=True),
        sa.Column("agent_type", sa.String(50), nullable=False),
        sa.Column("specializations", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("programming_languages", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("frameworks", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("experience_level", sa.String(20), server_default="intermediate"),
        sa.Column("preferred_tasks", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("availability_schedule", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("current_workload", sa.Integer, server_default="0"),
        sa.Column("max_concurrent_tasks", sa.Integer, server_default="3"),
        sa.Column("performance_metrics", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("collaboration_preferences", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("trust_scores", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("metadata", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
    )
    op.create_index("idx_developer_profiles_agent_type", "developer_profiles", ["agent_type"])
    op.create_index("idx_developer_profiles_specializations", "developer_profiles", ["specializations"], postgresql_using="gin")

    # Team coordination plans table
    op.create_table(
        "team_coordination_plans",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("plan_id", sa.String(36), nullable=False, unique=True),
        sa.Column("session_id", sa.String(36), nullable=False),
        sa.Column("project_name", sa.String(200), nullable=False),
        sa.Column("project_description", sa.Text()),
        sa.Column("team_lead", sa.String(100), nullable=False),
        sa.Column("team_members", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("task_assignments", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("dependencies", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("communication_plan", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("conflict_resolution_strategy", sa.String(50), server_default="consensus"),
        sa.Column("status", sa.String(20), server_default="draft"),
        sa.Column("priority", sa.String(10), server_default="medium"),
        sa.Column("estimated_duration", sa.Integer()),  # hours
        sa.Column("actual_duration", sa.Integer()),  # hours
        sa.Column("success_metrics", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("risk_factors", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("milestone_schedule", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("resource_requirements", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("metadata", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("deadline", sa.DateTime(timezone=True)),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
    )
    op.create_index("idx_team_plans_session", "team_coordination_plans", ["session_id"])
    op.create_index("idx_team_plans_status", "team_coordination_plans", ["status"])
    op.create_index("idx_team_plans_lead", "team_coordination_plans", ["team_lead"])

    # Task assignments table
    op.create_table(
        "task_assignments",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("assignment_id", sa.String(36), nullable=False, unique=True),
        sa.Column("plan_id", sa.String(36), nullable=False),
        sa.Column("task_name", sa.String(200), nullable=False),
        sa.Column("task_description", sa.Text()),
        sa.Column("task_type", sa.String(50), nullable=False),
        sa.Column("assigned_agent", sa.String(100), nullable=False),
        sa.Column("reviewer_agents", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("dependencies", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("requirements", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("deliverables", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("status", sa.String(20), server_default="pending"),
        sa.Column("priority", sa.String(10), server_default="medium"),  
        sa.Column("complexity_score", sa.Float(), server_default="0.5"),
        sa.Column("estimated_effort", sa.Integer()),  # hours
        sa.Column("actual_effort", sa.Integer()),  # hours
        sa.Column("progress_percentage", sa.Integer(), server_default="0"),
        sa.Column("quality_score", sa.Float()),
        sa.Column("feedback", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("blockers", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("metadata", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("deadline", sa.DateTime(timezone=True)),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column("started_at", sa.DateTime(timezone=True)),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
    )
    op.create_index("idx_task_assignments_plan", "task_assignments", ["plan_id"])
    op.create_index("idx_task_assignments_agent", "task_assignments", ["assigned_agent"])
    op.create_index("idx_task_assignments_status", "task_assignments", ["status"])
    op.create_index("idx_task_assignments_priority", "task_assignments", ["priority"])

    # Conflict resolution logs table
    op.create_table(
        "conflict_resolution_logs",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("conflict_id", sa.String(36), nullable=False, unique=True),
        sa.Column("session_id", sa.String(36), nullable=False),
        sa.Column("plan_id", sa.String(36)),
        sa.Column("conflict_type", sa.String(50), nullable=False),
        sa.Column("conflict_description", sa.Text(), nullable=False),
        sa.Column("involved_agents", sa.JSON(), nullable=False),
        sa.Column("conflict_severity", sa.String(10), server_default="medium"),
        sa.Column("conflict_context", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("resolution_strategy", sa.String(50)),
        sa.Column("resolution_steps", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("resolution_outcome", sa.Text()),
        sa.Column("resolved_by", sa.String(100)),
        sa.Column("automation_used", sa.Boolean(), server_default="false"),
        sa.Column("human_intervention", sa.Boolean(), server_default="false"),
        sa.Column("learning_points", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("prevention_measures", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("status", sa.String(20), server_default="open"),
        sa.Column("metadata", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column("resolved_at", sa.DateTime(timezone=True)),
    )
    op.create_index("idx_conflict_logs_session", "conflict_resolution_logs", ["session_id"])
    op.create_index("idx_conflict_logs_type", "conflict_resolution_logs", ["conflict_type"])
    op.create_index("idx_conflict_logs_status", "conflict_resolution_logs", ["status"])
    op.create_index("idx_conflict_logs_severity", "conflict_resolution_logs", ["conflict_severity"])

    # Team performance metrics table
    op.create_table(
        "team_performance_metrics",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("metric_id", sa.String(36), nullable=False, unique=True),
        sa.Column("session_id", sa.String(36), nullable=False),
        sa.Column("plan_id", sa.String(36)),
        sa.Column("team_members", sa.JSON(), nullable=False),
        sa.Column("metric_type", sa.String(50), nullable=False),
        sa.Column("metric_value", sa.Float(), nullable=False),
        sa.Column("metric_details", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("measurement_period", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("benchmark_comparison", sa.Float()),
        sa.Column("trend_data", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("contributing_factors", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("improvement_suggestions", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("metadata", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column(
            "recorded_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
    )
    op.create_index("idx_team_metrics_session", "team_performance_metrics", ["session_id"])
    op.create_index("idx_team_metrics_type", "team_performance_metrics", ["metric_type"])
    op.create_index("idx_team_metrics_recorded", "team_performance_metrics", ["recorded_at"])

    # Agent collaboration history table
    op.create_table(
        "agent_collaboration_history",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("collaboration_id", sa.String(36), nullable=False, unique=True),
        sa.Column("session_id", sa.String(36), nullable=False),
        sa.Column("agent_1", sa.String(100), nullable=False),
        sa.Column("agent_2", sa.String(100), nullable=False),
        sa.Column("collaboration_type", sa.String(50), nullable=False),
        sa.Column("interaction_count", sa.Integer(), server_default="0"),
        sa.Column("successful_collaborations", sa.Integer(), server_default="0"),
        sa.Column("conflict_count", sa.Integer(), server_default="0"),
        sa.Column("average_response_time", sa.Float()),  # minutes
        sa.Column("quality_ratings", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("communication_effectiveness", sa.Float()),
        sa.Column("task_completion_rate", sa.Float()),
        sa.Column("mutual_trust_score", sa.Float()),
        sa.Column("collaboration_notes", sa.Text()),
        sa.Column("improvement_areas", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("strengths", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("metadata", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column(
            "first_collaboration",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column(
            "last_collaboration",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
    )
    op.create_index("idx_collab_history_session", "agent_collaboration_history", ["session_id"])
    op.create_index("idx_collab_history_agents", "agent_collaboration_history", ["agent_1", "agent_2"])
    op.create_index("idx_collab_history_type", "agent_collaboration_history", ["collaboration_type"])


def downgrade() -> None:
    """Drop multi-developer coordination tables."""
    op.drop_index("idx_collab_history_type", table_name="agent_collaboration_history")
    op.drop_index("idx_collab_history_agents", table_name="agent_collaboration_history")
    op.drop_index("idx_collab_history_session", table_name="agent_collaboration_history")
    op.drop_table("agent_collaboration_history")

    op.drop_index("idx_team_metrics_recorded", table_name="team_performance_metrics")
    op.drop_index("idx_team_metrics_type", table_name="team_performance_metrics")
    op.drop_index("idx_team_metrics_session", table_name="team_performance_metrics")
    op.drop_table("team_performance_metrics")

    op.drop_index("idx_conflict_logs_severity", table_name="conflict_resolution_logs")
    op.drop_index("idx_conflict_logs_status", table_name="conflict_resolution_logs")
    op.drop_index("idx_conflict_logs_type", table_name="conflict_resolution_logs")
    op.drop_index("idx_conflict_logs_session", table_name="conflict_resolution_logs")
    op.drop_table("conflict_resolution_logs")

    op.drop_index("idx_task_assignments_priority", table_name="task_assignments")
    op.drop_index("idx_task_assignments_status", table_name="task_assignments")
    op.drop_index("idx_task_assignments_agent", table_name="task_assignments")
    op.drop_index("idx_task_assignments_plan", table_name="task_assignments")
    op.drop_table("task_assignments")

    op.drop_index("idx_team_plans_lead", table_name="team_coordination_plans")
    op.drop_index("idx_team_plans_status", table_name="team_coordination_plans")
    op.drop_index("idx_team_plans_session", table_name="team_coordination_plans")
    op.drop_table("team_coordination_plans")

    op.drop_index("idx_developer_profiles_specializations", table_name="developer_profiles")
    op.drop_index("idx_developer_profiles_agent_type", table_name="developer_profiles")
    op.drop_table("developer_profiles")
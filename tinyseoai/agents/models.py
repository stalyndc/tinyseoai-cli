"""
Data models for the multi-agent AI system.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class AgentRole(str, Enum):
    """Agent role types."""

    ORCHESTRATOR = "orchestrator"
    TECHNICAL_SEO = "technical_seo"
    CONTENT_QUALITY = "content_quality"
    PERFORMANCE = "performance"
    LINK_ANALYSIS = "link_analysis"
    COMPETITIVE_INTEL = "competitive_intel"
    FIX_GENERATOR = "fix_generator"


class TaskPriority(str, Enum):
    """Task priority levels."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class TaskStatus(str, Enum):
    """Task execution status."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class MessageType(str, Enum):
    """Agent message types."""

    REQUEST = "request"
    RESPONSE = "response"
    NOTIFICATION = "notification"
    ERROR = "error"


class AgentMessage(BaseModel):
    """Message passed between agents."""

    id: str = Field(default_factory=lambda: f"msg_{datetime.now().timestamp()}")
    type: MessageType
    from_agent: AgentRole
    to_agent: AgentRole
    content: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.now)


class ThoughtStep(BaseModel):
    """A single step in chain-of-thought reasoning."""

    step_number: int
    type: str  # observation, reflection, planning, action, verification
    content: str
    confidence: float = Field(ge=0.0, le=1.0, default=1.0)
    supporting_data: dict[str, Any] | None = None
    timestamp: datetime = Field(default_factory=datetime.now)


class ChainOfThought(BaseModel):
    """Chain-of-thought reasoning trace for an agent's decision."""

    agent_role: AgentRole
    task_id: str
    goal: str
    steps: list[ThoughtStep] = Field(default_factory=list)
    final_decision: str | None = None
    confidence_score: float = Field(ge=0.0, le=1.0, default=0.0)
    reasoning_time_ms: float = 0.0
    created_at: datetime = Field(default_factory=datetime.now)

    def add_step(
        self,
        step_type: str,
        content: str,
        confidence: float = 1.0,
        supporting_data: dict[str, Any] | None = None,
    ) -> None:
        """Add a reasoning step to the chain."""
        step = ThoughtStep(
            step_number=len(self.steps) + 1,
            type=step_type,
            content=content,
            confidence=confidence,
            supporting_data=supporting_data,
        )
        self.steps.append(step)

    def get_summary(self) -> str:
        """Get a human-readable summary of the reasoning chain."""
        lines = [f"🧠 Chain of Thought for {self.agent_role.value}:", f"Goal: {self.goal}", ""]
        for step in self.steps:
            lines.append(f"{step.step_number}. [{step.type.upper()}] {step.content}")
            if step.confidence < 1.0:
                lines.append(f"   Confidence: {step.confidence:.2%}")
        if self.final_decision:
            lines.append(f"\n✓ Final Decision: {self.final_decision}")
        return "\n".join(lines)


class AgentTask(BaseModel):
    """A task assigned to an agent."""

    id: str = Field(default_factory=lambda: f"task_{datetime.now().timestamp()}")
    assigned_to: AgentRole
    priority: TaskPriority
    status: TaskStatus = TaskStatus.PENDING
    title: str
    description: str
    context: dict[str, Any] = Field(default_factory=dict)
    dependencies: list[str] = Field(default_factory=list)  # Task IDs
    parent_task_id: str | None = None
    created_at: datetime = Field(default_factory=datetime.now)
    started_at: datetime | None = None
    completed_at: datetime | None = None
    result: AgentResult | None = None

    def start(self) -> None:
        """Mark task as started."""
        self.status = TaskStatus.IN_PROGRESS
        self.started_at = datetime.now()

    def complete(self, result: AgentResult) -> None:
        """Mark task as completed with result."""
        self.status = TaskStatus.COMPLETED
        self.completed_at = datetime.now()
        self.result = result

    def fail(self, error: str) -> None:
        """Mark task as failed."""
        self.status = TaskStatus.FAILED
        self.completed_at = datetime.now()
        self.result = AgentResult(
            task_id=self.id,
            agent_role=self.assigned_to,
            success=False,
            data={"error": error},
        )


class AgentResult(BaseModel):
    """Result from an agent's task execution."""

    task_id: str
    agent_role: AgentRole
    success: bool
    data: dict[str, Any] = Field(default_factory=dict)
    insights: list[str] = Field(default_factory=list)
    recommendations: list[dict[str, Any]] = Field(default_factory=list)
    chain_of_thought: ChainOfThought | None = None
    execution_time_ms: float = 0.0
    model_used: str | None = None
    tokens_used: int | None = None
    confidence: float = Field(ge=0.0, le=1.0, default=1.0)
    timestamp: datetime = Field(default_factory=datetime.now)

    def add_insight(self, insight: str) -> None:
        """Add an insight discovered during analysis."""
        self.insights.append(insight)

    def add_recommendation(
        self,
        title: str,
        description: str,
        priority: str,
        impact: float,
        effort: float,
        **kwargs: Any,
    ) -> None:
        """Add a recommendation."""
        rec = {
            "title": title,
            "description": description,
            "priority": priority,
            "impact": impact,
            "effort": effort,
            **kwargs,
        }
        self.recommendations.append(rec)


class AgentCapability(BaseModel):
    """Describes what an agent can do."""

    name: str
    description: str
    required_models: list[str] = Field(default_factory=list)
    estimated_cost: float = 0.0  # USD per invocation
    average_duration_ms: float = 0.0


class AgentProfile(BaseModel):
    """Profile information for an agent."""

    role: AgentRole
    name: str
    description: str
    capabilities: list[AgentCapability]
    specialization: list[str]  # e.g., ["technical", "security", "performance"]
    max_concurrent_tasks: int = 3
    default_model: str = "gpt-4o-mini"
    fallback_models: list[str] = Field(default_factory=lambda: ["gpt-4o", "claude-3-5-sonnet"])


class MultiAgentSession(BaseModel):
    """A complete multi-agent analysis session."""

    id: str = Field(default_factory=lambda: f"session_{datetime.now().timestamp()}")
    site_url: str
    initiated_by: AgentRole = AgentRole.ORCHESTRATOR
    tasks: list[AgentTask] = Field(default_factory=list)
    messages: list[AgentMessage] = Field(default_factory=list)
    results: dict[str, AgentResult] = Field(default_factory=dict)  # task_id -> result
    started_at: datetime = Field(default_factory=datetime.now)
    completed_at: datetime | None = None
    total_cost_usd: float = 0.0
    total_tokens: int = 0

    def add_task(self, task: AgentTask) -> None:
        """Add a task to the session."""
        self.tasks.append(task)

    def add_message(self, message: AgentMessage) -> None:
        """Add an agent message to the session."""
        self.messages.append(message)

    def record_result(self, result: AgentResult) -> None:
        """Record an agent result."""
        self.results[result.task_id] = result
        if result.tokens_used:
            self.total_tokens += result.tokens_used

    def get_task(self, task_id: str) -> AgentTask | None:
        """Get a task by ID."""
        for task in self.tasks:
            if task.id == task_id:
                return task
        return None

    def get_pending_tasks(self) -> list[AgentTask]:
        """Get all pending tasks."""
        return [t for t in self.tasks if t.status == TaskStatus.PENDING]

    def is_complete(self) -> bool:
        """Check if all tasks are completed."""
        return all(
            t.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]
            for t in self.tasks
        )

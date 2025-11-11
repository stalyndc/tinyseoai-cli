"""
Unit tests for agent data models.
"""

import pytest
from datetime import datetime

from tinyseoai.agents.models import (
    AgentMessage,
    AgentResult,
    AgentRole,
    AgentTask,
    ChainOfThought,
    MessageType,
    MultiAgentSession,
    TaskPriority,
    TaskStatus,
    ThoughtStep,
)


@pytest.mark.unit
class TestAgentMessage:
    """Test AgentMessage model."""

    def test_create_message(self):
        """Test creating an agent message."""
        # Arrange & Act
        message = AgentMessage(
            type=MessageType.REQUEST,
            from_agent=AgentRole.ORCHESTRATOR,
            to_agent=AgentRole.TECHNICAL_SEO,
            content="Analyze technical issues",
        )

        # Assert
        assert message.type == MessageType.REQUEST
        assert message.from_agent == AgentRole.ORCHESTRATOR
        assert message.to_agent == AgentRole.TECHNICAL_SEO
        assert message.content == "Analyze technical issues"
        assert message.id.startswith("msg_")
        assert isinstance(message.timestamp, datetime)


@pytest.mark.unit
class TestChainOfThought:
    """Test ChainOfThought reasoning model."""

    def test_create_chain_of_thought(self):
        """Test creating a chain of thought."""
        # Arrange & Act
        cot = ChainOfThought(
            agent_role=AgentRole.CONTENT_QUALITY,
            task_id="task_123",
            goal="Analyze content quality issues",
        )

        # Assert
        assert cot.agent_role == AgentRole.CONTENT_QUALITY
        assert cot.task_id == "task_123"
        assert cot.goal == "Analyze content quality issues"
        assert len(cot.steps) == 0
        assert cot.final_decision is None

    def test_add_reasoning_step(self):
        """Test adding reasoning steps to chain."""
        # Arrange
        cot = ChainOfThought(
            agent_role=AgentRole.PERFORMANCE,
            task_id="task_456",
            goal="Optimize performance",
        )

        # Act
        cot.add_step("observation", "Page load time is 5 seconds", confidence=0.95)
        cot.add_step("reflection", "This is too slow for good UX", confidence=0.90)
        cot.add_step("planning", "Need to optimize images and defer JS", confidence=0.85)

        # Assert
        assert len(cot.steps) == 3
        assert cot.steps[0].step_number == 1
        assert cot.steps[0].type == "observation"
        assert cot.steps[0].confidence == 0.95
        assert cot.steps[2].step_number == 3

    def test_chain_of_thought_summary(self):
        """Test getting a human-readable summary."""
        # Arrange
        cot = ChainOfThought(
            agent_role=AgentRole.LINK_ANALYSIS,
            task_id="task_789",
            goal="Fix broken links",
        )
        cot.add_step("observation", "Found 15 broken links")
        cot.add_step("action", "Creating fix recommendations")
        cot.final_decision = "Recommend fixing all 404s"

        # Act
        summary = cot.get_summary()

        # Assert
        assert "link_analysis" in summary
        assert "Fix broken links" in summary
        assert "observation" in summary.lower()
        assert "action" in summary.lower()
        assert "Recommend fixing all 404s" in summary


@pytest.mark.unit
class TestAgentTask:
    """Test AgentTask model."""

    def test_create_task(self):
        """Test creating an agent task."""
        # Arrange & Act
        task = AgentTask(
            assigned_to=AgentRole.TECHNICAL_SEO,
            priority=TaskPriority.HIGH,
            title="Analyze HTTPS issues",
            description="Check SSL certificates and HTTPS configuration",
        )

        # Assert
        assert task.assigned_to == AgentRole.TECHNICAL_SEO
        assert task.priority == TaskPriority.HIGH
        assert task.status == TaskStatus.PENDING
        assert task.title == "Analyze HTTPS issues"
        assert task.id.startswith("task_")

    def test_start_task(self):
        """Test starting a task."""
        # Arrange
        task = AgentTask(
            assigned_to=AgentRole.CONTENT_QUALITY,
            priority=TaskPriority.MEDIUM,
            title="Optimize titles",
            description="Improve title tags",
        )

        # Act
        task.start()

        # Assert
        assert task.status == TaskStatus.IN_PROGRESS
        assert task.started_at is not None
        assert isinstance(task.started_at, datetime)

    def test_complete_task(self):
        """Test completing a task."""
        # Arrange
        task = AgentTask(
            assigned_to=AgentRole.PERFORMANCE,
            priority=TaskPriority.LOW,
            title="Compress images",
            description="Reduce image file sizes",
        )
        result = AgentResult(
            task_id=task.id,
            agent_role=AgentRole.PERFORMANCE,
            success=True,
            data={"compressed": 10},
        )

        # Act
        task.complete(result)

        # Assert
        assert task.status == TaskStatus.COMPLETED
        assert task.completed_at is not None
        assert task.result == result

    def test_fail_task(self):
        """Test failing a task."""
        # Arrange
        task = AgentTask(
            assigned_to=AgentRole.LINK_ANALYSIS,
            priority=TaskPriority.HIGH,
            title="Check links",
            description="Find broken links",
        )

        # Act
        task.fail("API rate limit exceeded")

        # Assert
        assert task.status == TaskStatus.FAILED
        assert task.completed_at is not None
        assert task.result is not None
        assert task.result.success is False
        assert "API rate limit exceeded" in task.result.data["error"]


@pytest.mark.unit
class TestAgentResult:
    """Test AgentResult model."""

    def test_create_result(self):
        """Test creating an agent result."""
        # Arrange & Act
        result = AgentResult(
            task_id="task_123",
            agent_role=AgentRole.FIX_GENERATOR,
            success=True,
            data={"fixes": 5},
            confidence=0.92,
        )

        # Assert
        assert result.task_id == "task_123"
        assert result.agent_role == AgentRole.FIX_GENERATOR
        assert result.success is True
        assert result.data["fixes"] == 5
        assert result.confidence == 0.92

    def test_add_insight(self):
        """Test adding insights to result."""
        # Arrange
        result = AgentResult(
            task_id="task_456",
            agent_role=AgentRole.TECHNICAL_SEO,
            success=True,
            data={},
        )

        # Act
        result.add_insight("Found 3 critical security issues")
        result.add_insight("HTTPS not enabled")

        # Assert
        assert len(result.insights) == 2
        assert "critical security issues" in result.insights[0]

    def test_add_recommendation(self):
        """Test adding recommendations to result."""
        # Arrange
        result = AgentResult(
            task_id="task_789",
            agent_role=AgentRole.CONTENT_QUALITY,
            success=True,
            data={},
        )

        # Act
        result.add_recommendation(
            title="Optimize Title Tags",
            description="Add unique titles to all pages",
            priority="high",
            impact=8.5,
            effort=3.0,
        )

        # Assert
        assert len(result.recommendations) == 1
        rec = result.recommendations[0]
        assert rec["title"] == "Optimize Title Tags"
        assert rec["priority"] == "high"
        assert rec["impact"] == 8.5
        assert rec["effort"] == 3.0


@pytest.mark.unit
class TestMultiAgentSession:
    """Test MultiAgentSession model."""

    def test_create_session(self):
        """Test creating a multi-agent session."""
        # Arrange & Act
        session = MultiAgentSession(
            site_url="https://example.com",
            initiated_by=AgentRole.ORCHESTRATOR,
        )

        # Assert
        assert session.site_url == "https://example.com"
        assert session.initiated_by == AgentRole.ORCHESTRATOR
        assert session.id.startswith("session_")
        assert len(session.tasks) == 0
        assert len(session.messages) == 0
        assert session.total_tokens == 0

    def test_add_task_to_session(self):
        """Test adding tasks to a session."""
        # Arrange
        session = MultiAgentSession(site_url="https://example.com")
        task = AgentTask(
            assigned_to=AgentRole.TECHNICAL_SEO,
            priority=TaskPriority.HIGH,
            title="Analyze security",
            description="Check HTTPS and headers",
        )

        # Act
        session.add_task(task)

        # Assert
        assert len(session.tasks) == 1
        assert session.tasks[0] == task

    def test_add_message_to_session(self):
        """Test adding messages to a session."""
        # Arrange
        session = MultiAgentSession(site_url="https://example.com")
        message = AgentMessage(
            type=MessageType.NOTIFICATION,
            from_agent=AgentRole.ORCHESTRATOR,
            to_agent=AgentRole.CONTENT_QUALITY,
            content="Task assigned",
        )

        # Act
        session.add_message(message)

        # Assert
        assert len(session.messages) == 1
        assert session.messages[0] == message

    def test_record_result(self):
        """Test recording agent results."""
        # Arrange
        session = MultiAgentSession(site_url="https://example.com")
        result = AgentResult(
            task_id="task_123",
            agent_role=AgentRole.PERFORMANCE,
            success=True,
            data={},
            tokens_used=1500,
        )

        # Act
        session.record_result(result)

        # Assert
        assert "task_123" in session.results
        assert session.total_tokens == 1500

    def test_get_pending_tasks(self):
        """Test getting pending tasks."""
        # Arrange
        session = MultiAgentSession(site_url="https://example.com")

        task1 = AgentTask(
            assigned_to=AgentRole.TECHNICAL_SEO,
            priority=TaskPriority.HIGH,
            title="Task 1",
            description="Description 1",
        )
        task2 = AgentTask(
            assigned_to=AgentRole.CONTENT_QUALITY,
            priority=TaskPriority.MEDIUM,
            title="Task 2",
            description="Description 2",
        )

        session.add_task(task1)
        session.add_task(task2)

        task1.start()

        # Act
        pending = session.get_pending_tasks()

        # Assert
        assert len(pending) == 1
        assert pending[0] == task2

    def test_is_complete(self):
        """Test checking if session is complete."""
        # Arrange
        session = MultiAgentSession(site_url="https://example.com")

        task1 = AgentTask(
            assigned_to=AgentRole.TECHNICAL_SEO,
            priority=TaskPriority.HIGH,
            title="Task 1",
            description="Description 1",
        )
        task2 = AgentTask(
            assigned_to=AgentRole.CONTENT_QUALITY,
            priority=TaskPriority.MEDIUM,
            title="Task 2",
            description="Description 2",
        )

        session.add_task(task1)
        session.add_task(task2)

        # Act & Assert - Not complete yet
        assert not session.is_complete()

        # Complete tasks
        result = AgentResult(task_id=task1.id, agent_role=task1.assigned_to, success=True, data={})
        task1.complete(result)
        task2.complete(result)

        # Act & Assert - Now complete
        assert session.is_complete()

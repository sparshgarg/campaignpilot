"""SQLAlchemy models for agent run storage and history."""

from datetime import datetime
from sqlalchemy import Column, String, JSON, Integer, Float, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
import uuid

Base = declarative_base()


class AgentRun(Base):
    """Stores results from agent executions for history and audit trails."""

    __tablename__ = "agent_runs"

    # Primary key
    run_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    # Agent metadata
    agent_name = Column(String(50), nullable=False, index=True)
    model = Column(String(100), nullable=True)
    max_turns = Column(Integer, nullable=True)

    # Execution inputs
    input_params = Column(JSON, nullable=True)

    # Results
    success = Column(Boolean, nullable=False, default=False)
    output = Column(JSON, nullable=True)
    error = Column(String(1024), nullable=True)

    # Observability
    tool_calls_made = Column(JSON, nullable=True)
    total_input_tokens = Column(Integer, nullable=False, default=0)
    total_output_tokens = Column(Integer, nullable=False, default=0)
    latency_ms = Column(Float, nullable=False, default=0.0)
    trace_url = Column(String(512), nullable=True)

    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        """Convert model to dict for API responses."""
        return {
            "run_id": self.run_id,
            "agent_name": self.agent_name,
            "model": self.model,
            "max_turns": self.max_turns,
            "input_params": self.input_params,
            "success": self.success,
            "output": self.output,
            "error": self.error,
            "tool_calls_made": self.tool_calls_made,
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
            "latency_ms": self.latency_ms,
            "trace_url": self.trace_url,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

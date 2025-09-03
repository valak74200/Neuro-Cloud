# Ensure SQLAlchemy models are importable via app.infrastructure.models

# Explicit import to register the model with SQLAlchemy metadata
from .memory import MemoryModel  # noqa: F401

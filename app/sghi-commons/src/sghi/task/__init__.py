"""
Task interface definition together with its common implementations.
"""
from .common import Chainable, Consumer, Pipeline, Task
from .concurrent import ConcurrentExecutor, ConcurrentExecutorDisposedError

__all__ = [
    "Chainable",
    "ConcurrentExecutor",
    "ConcurrentExecutorDisposedError",
    "Consumer",
    "Pipeline",
    "Task",
]

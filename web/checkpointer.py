"""Adaptador del checkpointer para LangGraph.

Reutiliza `core.checkpointer.DisboardCheckpointer` y lo expone como
`BaseCheckpointSaver` compatible con LangGraph.
"""
from __future__ import annotations

from typing import Any, Optional

from langgraph.checkpoint.base import BaseCheckpointSaver, CheckpointTuple

from core.checkpointer import DisboardCheckpointer


class WebCheckpointer(BaseCheckpointSaver):
    """Checkpointer mínimo que delega en DisboardCheckpointer."""

    def __init__(self, inner: Optional[DisboardCheckpointer] = None):
        super().__init__()
        self.inner = inner or DisboardCheckpointer()

    def get_tuple(self, config: dict) -> Optional[CheckpointTuple]:
        thread_id = config.get("configurable", {}).get("thread_id")
        if not thread_id:
            return None
        state = self.inner.load_checkpoint(thread_id)
        if state is None:
            return None
        return CheckpointTuple(config=config, checkpoint=state, metadata={})

    def put(self, config: dict, checkpoint: Any, metadata: dict, new_versions: dict) -> dict:
        thread_id = config.get("configurable", {}).get("thread_id", "edge-default")
        self.inner.save_checkpoint(thread_id, checkpoint if isinstance(checkpoint, dict) else {"state": checkpoint})
        return config

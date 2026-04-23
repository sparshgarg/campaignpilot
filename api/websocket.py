"""WebSocket handler for real-time agent event streaming."""

import json
import logging
from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, Set

logger = logging.getLogger(__name__)


class AgentEventManager:
    """Manages WebSocket connections and broadcasts agent events."""

    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, run_id: str):
        """Register a WebSocket connection for a specific run."""
        await websocket.accept()
        if run_id not in self.active_connections:
            self.active_connections[run_id] = set()
        self.active_connections[run_id].add(websocket)
        logger.info(f"WebSocket connected for run {run_id}, total: {len(self.active_connections[run_id])}")

    def disconnect(self, run_id: str, websocket: WebSocket):
        """Unregister a WebSocket connection."""
        if run_id in self.active_connections:
            self.active_connections[run_id].discard(websocket)
            if not self.active_connections[run_id]:
                del self.active_connections[run_id]
            logger.info(f"WebSocket disconnected for run {run_id}")

    async def broadcast(self, run_id: str, message: dict):
        """Broadcast an event to all connected clients for a run."""
        if run_id not in self.active_connections:
            return

        message_json = json.dumps(message)
        disconnected = set()

        for websocket in self.active_connections[run_id]:
            try:
                await websocket.send_text(message_json)
            except Exception as e:
                logger.error(f"Failed to send message: {e}")
                disconnected.add(websocket)

        # Clean up disconnected clients
        for ws in disconnected:
            self.disconnect(run_id, ws)


agent_event_manager = AgentEventManager()


async def websocket_endpoint(websocket: WebSocket, run_id: str):
    """
    WebSocket endpoint for real-time agent event streaming.

    Clients connect with a run_id and receive agent events as they occur.
    Events include: agent_start, turn_start, llm_call_start/end, tool_call_start/end, agent_complete.

    Example client usage:
        const ws = new WebSocket('ws://localhost:8000/ws/agent-events/run-uuid-here');
        ws.onmessage = (event) => {
          const agentEvent = JSON.parse(event.data);
          console.log(agentEvent.type, agentEvent);
        };
    """
    await agent_event_manager.connect(websocket, run_id)
    try:
        # Keep connection open; events are pushed from agent execution
        while True:
            # Wait for client messages (optional, for heartbeat/control)
            await websocket.receive_text()
    except WebSocketDisconnect:
        agent_event_manager.disconnect(run_id, websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        agent_event_manager.disconnect(run_id, websocket)

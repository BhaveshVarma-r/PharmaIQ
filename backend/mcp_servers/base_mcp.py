import uuid
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class BaseMCPServer:
    def __init__(self, server_name):
        self.server_name = server_name

    def _success(self, action, data, store_id=None):
        result = {
            "status": "success",
            "server": self.server_name,
            "action": action,
            "data": data,
            "timestamp": datetime.now().isoformat(),
            "transaction_id": str(uuid.uuid4()),
        }
        self._log_action(action, data, "success", store_id)
        return result

    def _error(self, action, message, store_id=None):
        result = {
            "status": "error",
            "server": self.server_name,
            "action": action,
            "message": message,
            "timestamp": datetime.now().isoformat(),
        }
        self._log_action(action, {"error": message}, "error", store_id)
        return result

    def _log_action(self, action, data, outcome, store_id=None):
        try:
            from backend.database.sqlite_manager import write_audit_log
            write_audit_log({
                "event_type": "MCP_{}_{}".format(self.server_name, action),
                "agent_name": self.server_name,
                "store_id": store_id,
                "action_description": "{}: {} - {}".format(
                    self.server_name, action, outcome
                ),
                "after_state": data,
            })
        except Exception as e:
            logger.warning("Audit log write failed: {}".format(e))
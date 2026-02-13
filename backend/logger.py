
import logging
import json
from datetime import datetime

class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "channel": getattr(record, "channel", "app"),
            "context": getattr(record, "context", {}),
            "extra": getattr(record, "extra_data", {})
        }
        return json.dumps(log_record)

logger = logging.getLogger("assessment")
logger.setLevel(logging.INFO)

handler = logging.StreamHandler()
handler.setFormatter(JsonFormatter())
logger.addHandler(handler)

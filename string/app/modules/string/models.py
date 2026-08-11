import uuid
from datetime import datetime, timezone

class stringModel:
    def __init__(self, name: str, status: str = "ACTIVE", id: str = None):
        self.id = id or str(uuid.uuid4())
        self.name = name
        self.status = status
        self.created_at = datetime.now(timezone.utc).isoformat()

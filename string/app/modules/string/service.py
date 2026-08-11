from typing import List, Optional
from app.modules.string.models import stringModel
from app.modules.string.schemas import stringCreate

class stringService:
    def __init__(self):
        self._db = {}

    def create(self, data: stringCreate) -> stringModel:
        record = stringModel(name=data.name, status=data.status)
        self._db[record.id] = record
        return record

    def get_by_id(self, record_id: str) -> Optional[stringModel]:
        return self._db.get(record_id)

    def list_all(self) -> List[stringModel]:
        return list(self._db.values())

    def delete(self, record_id: str) -> bool:
        if record_id in self._db:
            del self._db[record_id]
            return True
        return False

string_service = stringService()

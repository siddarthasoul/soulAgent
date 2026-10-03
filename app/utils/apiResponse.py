from typing import Any, Dict

class ApiResponse:
    def __init__(self, status_code: int, message: str, data: Dict[str, Any] = None):
        self.status_code = status_code
        self.message = message
        self.data = data or {}

    def to_dict(self):
        return {
            "status_code": self.status_code,
            "message": self.message,
            "data": self.data,
        }
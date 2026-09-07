"""Structured user-facing failures shared by CLI, MCP, and editor clients."""


class DynamoDiffError(Exception):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code

    def as_dict(self) -> dict:
        return {"error": {"code": self.code, "message": str(self)}}

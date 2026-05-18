from pydantic import BaseModel


class DocumentUploadResponse(BaseModel):
    document_id: str
    status: str


class DocumentResponse(BaseModel):
    document_id: str
    filename: str
    status: str
    chunk_count: int = 0
    error_message: str | None = None


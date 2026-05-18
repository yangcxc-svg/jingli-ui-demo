from fastapi import APIRouter, BackgroundTasks, UploadFile

from app.schemas.document import DocumentResponse, DocumentUploadResponse
from app.services.knowledge_service import KnowledgeService

router = APIRouter()


@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(file: UploadFile, background_tasks: BackgroundTasks) -> DocumentUploadResponse:
    return await KnowledgeService().upload(file, background_tasks)


@router.get("", response_model=list[DocumentResponse])
async def list_documents() -> list[DocumentResponse]:
    return await KnowledgeService().list_documents()


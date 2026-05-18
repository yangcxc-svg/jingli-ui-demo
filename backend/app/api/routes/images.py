from fastapi import APIRouter, HTTPException, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel

from app.services.image_service import ImageService

router = APIRouter()


class ImageUploadResponse(BaseModel):
    image_id: str
    filename: str
    content_type: str
    size: int
    url: str


@router.post("/upload", response_model=ImageUploadResponse)
async def upload_image(file: UploadFile) -> ImageUploadResponse:
    stored = await ImageService().upload(file)
    return ImageUploadResponse(
        image_id=stored.image_id,
        filename=stored.filename,
        content_type=stored.content_type,
        size=stored.size,
        url=f"/api/images/{stored.image_id}",
    )


@router.get("/{image_id}")
async def get_image(image_id: str) -> FileResponse:
    stored = ImageService().get(image_id)
    if not stored:
        raise HTTPException(status_code=404, detail="image not found")
    return FileResponse(stored.path, media_type=stored.content_type, filename=stored.filename)
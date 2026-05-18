"""Image upload service (MVP).

存储原图到 storage/uploads/images/，返回 image_id 以及可访问 URL。
当前 LLM (DeepSeek) 不支持视觉，因此聊天阶段只把"用户附带了图片 + 文件名 + 大致用途"
作为文本提示告知模型；后续可替换为真正的多模态模型。
"""

from __future__ import annotations

import logging
import threading
from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException, UploadFile

from app.core.config import settings

logger = logging.getLogger(__name__)

_ALLOWED_MIME = {"image/png", "image/jpeg", "image/webp", "image/gif"}
_ALLOWED_SUFFIX = {".png", ".jpg", ".jpeg", ".webp", ".gif"}


@dataclass
class StoredImage:
    image_id: str
    filename: str
    content_type: str
    path: str
    size: int


class ImageService:
    """进程内单例：保存已上传图片元信息。"""

    _instance: "ImageService | None" = None
    _lock = threading.Lock()

    def __new__(cls) -> "ImageService":
        with cls._lock:
            if cls._instance is None:
                inst = super().__new__(cls)
                inst._images = {}  # type: ignore[attr-defined]
                cls._instance = inst
        return cls._instance

    _images: dict[str, StoredImage]

    async def upload(self, file: UploadFile) -> StoredImage:
        filename = file.filename or "image"
        suffix = Path(filename).suffix.lower()
        if file.content_type not in _ALLOWED_MIME and suffix not in _ALLOWED_SUFFIX:
            raise HTTPException(status_code=400, detail="仅支持 PNG / JPEG / WEBP / GIF 图片")

        content = await file.read()
        max_bytes = settings.max_upload_mb * 1024 * 1024
        if len(content) > max_bytes:
            raise HTTPException(
                status_code=413, detail=f"图片超过 {settings.max_upload_mb} MB 上限"
            )

        image_id = str(uuid4())
        target_dir = Path(settings.upload_dir) / "images"
        target_dir.mkdir(parents=True, exist_ok=True)
        target = target_dir / f"{image_id}{suffix or '.png'}"
        target.write_bytes(content)

        stored = StoredImage(
            image_id=image_id,
            filename=filename,
            content_type=file.content_type or "image/png",
            path=str(target),
            size=len(content),
        )
        self._images[image_id] = stored
        return stored

    def get(self, image_id: str) -> StoredImage | None:
        return self._images.get(image_id)
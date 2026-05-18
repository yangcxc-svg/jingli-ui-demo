class VisionClient:
    async def parse_image(self, image_path: str) -> dict[str, object]:
        return {"image_path": image_path, "text": ""}


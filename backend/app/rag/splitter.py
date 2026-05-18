class TextSplitter:
    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 80) -> None:
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def split(self, text: str) -> list[str]:
        if not text:
            return []
        chunks: list[str] = []
        step = max(1, self.chunk_size - self.chunk_overlap)
        for start in range(0, len(text), step):
            chunk = text[start : start + self.chunk_size].strip()
            if chunk:
                chunks.append(chunk)
        return chunks


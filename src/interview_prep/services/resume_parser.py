from io import BytesIO


def extract_resume_text(data: bytes, content_type: str) -> str:
    if content_type == "application/pdf":
        from pypdf import PdfReader

        pages = PdfReader(BytesIO(data)).pages
        text = "\n".join(page.extract_text() or "" for page in pages)
    elif content_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        from docx import Document

        document = Document(BytesIO(data))
        text = "\n".join(paragraph.text for paragraph in document.paragraphs)
    else:
        raise ValueError(f"Unsupported resume content type: {content_type}")
    normalized = "\n".join(
        line.strip() for line in text.replace("\x00", "").splitlines() if line.strip()
    )
    if not normalized:
        raise ValueError("No readable text was found in the resume")
    return normalized


def chunk_text(text: str, *, chunk_size: int = 1200, overlap: int = 180) -> list[str]:
    if chunk_size <= overlap:
        raise ValueError("chunk_size must be larger than overlap")
    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        if end < len(text):
            boundary = text.rfind("\n", start, end)
            if boundary > start + chunk_size // 2:
                end = boundary
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= len(text):
            break
        start = max(end - overlap, start + 1)
    return chunks

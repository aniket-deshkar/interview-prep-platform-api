from interview_prep.services.resume_parser import chunk_text


def test_chunk_text_has_bounded_overlap() -> None:
    text = "\n".join(f"Line {index}: " + "x" * 80 for index in range(40))
    chunks = chunk_text(text, chunk_size=400, overlap=50)
    assert len(chunks) > 1
    assert all(1 <= len(chunk) <= 400 for chunk in chunks)
    assert "Line 0" in chunks[0]

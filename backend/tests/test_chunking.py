import tiktoken

from app.rag.chunking import chunk_text


def test_chunking_token_limits():
    text = "hello world " * 2500
    chunks = chunk_text(text)
    assert len(chunks) > 1

    encoder = tiktoken.get_encoding("cl100k_base")
    for chunk in chunks:
        assert len(encoder.encode(chunk)) <= 800

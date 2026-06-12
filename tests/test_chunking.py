from codereview.rag.indexer import Chunk, chunk_file, comment_chunk, is_style_path, window_chunks


def test_window_chunks_with_overlap():
    text = "\n".join(f"line{i}" for i in range(1, 151))  # 150 lines
    out = window_chunks(text, size=60, overlap=10)
    assert [(s, e) for s, e, _ in out] == [(1, 60), (51, 110), (101, 150)]
    assert out[0][2].startswith("line1\n")


def test_window_chunks_short_file():
    out = window_chunks("a\nb", size=60, overlap=10)
    assert out == [(1, 2, "a\nb")]


def test_style_paths():
    assert is_style_path("README.md")
    assert is_style_path("CONTRIBUTING.md")
    assert is_style_path("STYLEGUIDE.md")
    assert is_style_path("docs/conventions.md")
    assert not is_style_path("app/main.py")
    assert not is_style_path("notes.md")


def test_chunk_file_code_vs_style_vs_other():
    code = chunk_file("app/a.py", "\n".join(["x = 1"] * 70))
    assert all(c.source_type == "code" for c in code) and len(code) == 2
    style = chunk_file("README.md", "hello")
    assert style[0].source_type == "style"
    assert chunk_file("logo.png", "binaryish") == []


def test_comment_chunk():
    c = comment_chunk({"path": "app/a.py", "body": "Use the logger here."})
    assert c == Chunk("pr_comment", "app/a.py", 0, 0, "app/a.py: Use the logger here.")
    assert comment_chunk({"path": "x", "body": ""}) is None

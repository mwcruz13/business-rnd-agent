from backend.app.ingest.text import load_text


def test_load_text(tmp_path):
    sample = tmp_path / "sample.txt"
    sample.write_text("hello", encoding="utf-8")
    assert load_text(str(sample)) == "hello"

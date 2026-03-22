from pytest_bdd import given, parsers, scenarios, then, when

from backend.app.ingest.text import load_text


scenarios("features/text-ingestion.feature")


@given(parsers.parse('a UTF-8 text file containing "{content}"'), target_fixture="text_file_path")
def text_file_path(tmp_path, content: str) -> str:
    sample_file = tmp_path / "source.txt"
    sample_file.write_text(content, encoding="utf-8")
    return str(sample_file)


@when("the text ingestion loader reads the file", target_fixture="loaded_text")
def load_text_file(text_file_path: str) -> str:
    return load_text(text_file_path)


@then(parsers.parse('the loaded text is "{expected}"'))
def assert_loaded_text(loaded_text: str, expected: str) -> None:
    assert loaded_text == expected

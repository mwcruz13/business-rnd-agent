import csv

from pytest_bdd import given, parsers, scenarios, then, when

from backend.app.ingest.csv import load_csv_rows


scenarios("features/csv-ingestion.feature")


@given(parsers.parse('a CSV file with headers "{header_line}"'), target_fixture="csv_definition")
def csv_definition(tmp_path, header_line: str) -> dict[str, object]:
    return {"tmp_path": tmp_path, "headers": header_line.split(","), "rows": []}


@given(parsers.parse('a CSV row "{row_line}"'))
def append_csv_row(csv_definition: dict[str, object], row_line: str) -> None:
    rows = csv_definition["rows"]
    assert isinstance(rows, list)
    rows.append(row_line.split(","))


@when("the CSV ingestion loader reads the CSV file", target_fixture="loaded_rows")
def load_csv_file(csv_definition: dict[str, object]) -> list[dict[str, str]]:
    csv_path = csv_definition["tmp_path"] / "survey.csv"
    headers = csv_definition["headers"]
    rows = csv_definition["rows"]

    assert isinstance(headers, list)
    assert isinstance(rows, list)

    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(headers)
        writer.writerows(rows)

    return load_csv_rows(str(csv_path))


@then(parsers.parse("{expected_count:d} CSV rows are loaded"))
def assert_csv_row_count(loaded_rows: list[dict[str, str]], expected_count: int) -> None:
    assert len(loaded_rows) == expected_count


@then(parsers.parse('CSV row {row_number:d} column "{column_name}" is "{expected}"'))
def assert_csv_cell(
    loaded_rows: list[dict[str, str]], row_number: int, column_name: str, expected: str
) -> None:
    assert loaded_rows[row_number - 1][column_name] == expected

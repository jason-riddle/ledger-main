"""Golden tests for JSONL output from parsers."""

import json
import pathlib
import sys
from typing import Callable

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

import beanout.ally_bank
import beanout.chase
import beanout.clover_leaf
import beanout.sheer_value
import beanout.sps
import beanout.schwab


def _test_jsonl_golden_files(
    parser_name: str,
    golden_dir: pathlib.Path,
    render_func: Callable[[str], str],
) -> None:
    """Validate JSONL golden files match expected output.

    Args:
        parser_name: Name of the parser for error messages.
        golden_dir: Directory containing golden test files.
        render_func: Function that takes text and returns JSONL.
    """
    txt_paths = sorted(
        path
        for path in golden_dir.iterdir()
        if path.is_file() and path.name.lower().endswith(".pdf.txt")
    )

    assert txt_paths, f"No {parser_name} golden .pdf.txt files found"

    for txt_path in txt_paths:
        jsonl_path = txt_path.with_suffix(".jsonl")
        assert jsonl_path.exists(), f"Missing golden file: {jsonl_path}"

        output = render_func(txt_path.read_text())
        expected = jsonl_path.read_text()

        # Parse and compare as JSON objects for order-independent comparison
        output_lines = [json.loads(line) for line in output.strip().split("\n") if line]
        expected_lines = [
            json.loads(line) for line in expected.strip().split("\n") if line
        ]

        assert len(output_lines) == len(expected_lines), (
            f"Line count mismatch in {txt_path.name}: "
            f"got {len(output_lines)}, expected {len(expected_lines)}"
        )

        for i, (output_obj, expected_obj) in enumerate(
            zip(output_lines, expected_lines)
        ):
            assert output_obj == expected_obj, (
                f"Line {i + 1} mismatch in {txt_path.name}"
            )


def test_sps_jsonl_golden_files() -> None:
    """Validate SPS JSONL golden files match expected output."""
    _test_jsonl_golden_files(
        "SPS",
        pathlib.Path("fixtures/golden/loans/sps"),
        beanout.sps.render_sps_text_to_jsonl,
    )


def test_clover_leaf_jsonl_golden_files() -> None:
    """Validate CloverLeaf JSONL golden files match expected output."""
    _test_jsonl_golden_files(
        "CloverLeaf",
        pathlib.Path("fixtures/golden/managers/clover-leaf"),
        beanout.clover_leaf.render_clover_leaf_text_to_jsonl,
    )


def test_sheer_value_jsonl_golden_files() -> None:
    """Validate Sheer Value JSONL golden files match expected output."""
    _test_jsonl_golden_files(
        "Sheer Value",
        pathlib.Path("fixtures/golden/managers/sheer-value"),
        beanout.sheer_value.render_sheer_value_text_to_jsonl,
    )


def test_schwab_jsonl_golden_files() -> None:
    """Validate Schwab JSONL golden files match expected output."""
    golden_dir = pathlib.Path("fixtures/golden/institutions/banking/schwab")
    json_paths = sorted(golden_dir.glob("*.json"))
    xml_paths = sorted(golden_dir.glob("*.xml"))

    assert json_paths or xml_paths, "No Schwab golden files found"

    for json_path in json_paths:
        jsonl_path = json_path.with_suffix(f"{json_path.suffix}.jsonl")
        assert jsonl_path.exists(), f"Missing golden file: {jsonl_path}"

        output = beanout.schwab.render_schwab_json_text_to_jsonl(json_path.read_text())
        expected = jsonl_path.read_text()

        _assert_jsonl_equal(output, expected, json_path.name)

    for xml_path in xml_paths:
        jsonl_path = xml_path.with_suffix(f"{xml_path.suffix}.jsonl")
        assert jsonl_path.exists(), f"Missing golden file: {jsonl_path}"

        output = beanout.schwab.render_schwab_xml_text_to_jsonl(xml_path.read_bytes())
        expected = jsonl_path.read_text()

        _assert_jsonl_equal(output, expected, xml_path.name)


def test_ally_bank_jsonl_golden_files() -> None:
    """Validate Ally Bank JSONL golden files match expected output."""
    golden_dir = pathlib.Path("fixtures/golden/institutions/banking/ally-bank")
    csv_paths = sorted(
        path for path in golden_dir.iterdir() if path.suffix.lower() == ".csv"
    )
    qfx_paths = sorted(
        path for path in golden_dir.iterdir() if path.suffix.lower() == ".qfx"
    )

    assert csv_paths or qfx_paths, "No Ally Bank golden files found"

    for csv_path in csv_paths:
        jsonl_path = csv_path.with_suffix(f"{csv_path.suffix}.jsonl")
        assert jsonl_path.exists(), f"Missing golden file: {jsonl_path}"

        output = beanout.ally_bank.render_ally_bank_csv_text_to_jsonl(
            csv_path.read_text()
        )
        expected = jsonl_path.read_text()
        _assert_jsonl_equal(output, expected, csv_path.name)

    for qfx_path in qfx_paths:
        jsonl_path = qfx_path.with_suffix(f"{qfx_path.suffix}.jsonl")
        assert jsonl_path.exists(), f"Missing golden file: {jsonl_path}"

        output = beanout.ally_bank.render_ally_bank_qfx_text_to_jsonl(
            qfx_path.read_text()
        )
        expected = jsonl_path.read_text()
        _assert_jsonl_equal(output, expected, qfx_path.name)


def test_chase_jsonl_golden_files() -> None:
    """Validate Chase JSONL golden files match expected output."""
    golden_dir = pathlib.Path("fixtures/golden/institutions/banking/chase")
    csv_paths = sorted(
        path for path in golden_dir.iterdir() if path.suffix.lower() == ".csv"
    )
    qfx_paths = sorted(
        path for path in golden_dir.iterdir() if path.suffix.lower() == ".qfx"
    )

    assert csv_paths or qfx_paths, "No Chase golden files found"

    for csv_path in csv_paths:
        jsonl_path = csv_path.with_suffix(f"{csv_path.suffix}.jsonl")
        assert jsonl_path.exists(), f"Missing golden file: {jsonl_path}"

        output = beanout.chase.render_chase_csv_text_to_jsonl(csv_path.read_text())
        expected = jsonl_path.read_text()
        _assert_jsonl_equal(output, expected, csv_path.name)

    for qfx_path in qfx_paths:
        jsonl_path = qfx_path.with_suffix(f"{qfx_path.suffix}.jsonl")
        assert jsonl_path.exists(), f"Missing golden file: {jsonl_path}"

        output = beanout.chase.render_chase_qfx_text_to_jsonl(qfx_path.read_text())
        expected = jsonl_path.read_text()
        _assert_jsonl_equal(output, expected, qfx_path.name)


def _assert_jsonl_equal(output: str, expected: str, filename: str) -> None:
    output_lines = [json.loads(line) for line in output.strip().split("\n") if line]
    expected_lines = [json.loads(line) for line in expected.strip().split("\n") if line]

    assert len(output_lines) == len(expected_lines), (
        f"Line count mismatch in {filename}: "
        f"got {len(output_lines)}, expected {len(expected_lines)}"
    )

    for i, (output_obj, expected_obj) in enumerate(zip(output_lines, expected_lines)):
        assert output_obj == expected_obj, f"Line {i + 1} mismatch in {filename}"


if __name__ == "__main__":
    test_sps_jsonl_golden_files()
    print("✓ SPS JSONL golden tests passed")

    test_clover_leaf_jsonl_golden_files()
    print("✓ CloverLeaf JSONL golden tests passed")

    test_sheer_value_jsonl_golden_files()
    print("✓ Sheer Value JSONL golden tests passed")

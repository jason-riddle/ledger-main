"""Golden tests for JSONL output from parsers."""

import json
import pathlib
import sys
from typing import Callable

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

import beanout.clover_leaf
import beanout.sheer_value
import beanout.sps


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
    txt_paths = sorted(golden_dir.glob("*.pdf.txt"))

    assert txt_paths, f"No {parser_name} golden .pdf.txt files found"

    for txt_path in txt_paths:
        jsonl_path = txt_path.with_suffix(".jsonl")
        assert jsonl_path.exists(), f"Missing golden file: {jsonl_path}"

        output = render_func(txt_path.read_text())
        expected = jsonl_path.read_text()
        
        # Parse and compare as JSON objects for order-independent comparison
        output_lines = [json.loads(line) for line in output.strip().split("\n") if line]
        expected_lines = [json.loads(line) for line in expected.strip().split("\n") if line]
        
        assert len(output_lines) == len(expected_lines), (
            f"Line count mismatch in {txt_path.name}: "
            f"got {len(output_lines)}, expected {len(expected_lines)}"
        )
        
        for i, (output_obj, expected_obj) in enumerate(zip(output_lines, expected_lines)):
            assert output_obj == expected_obj, (
                f"Line {i+1} mismatch in {txt_path.name}"
            )


def test_sps_jsonl_golden_files() -> None:
    """Validate SPS JSONL golden files match expected output."""
    _test_jsonl_golden_files(
        "SPS",
        pathlib.Path("fixtures/golden/sps"),
        beanout.sps.render_sps_text_to_jsonl,
    )


def test_clover_leaf_jsonl_golden_files() -> None:
    """Validate CloverLeaf JSONL golden files match expected output."""
    _test_jsonl_golden_files(
        "CloverLeaf",
        pathlib.Path("fixtures/golden/clover-leaf"),
        beanout.clover_leaf.render_clover_leaf_text_to_jsonl,
    )


def test_sheer_value_jsonl_golden_files() -> None:
    """Validate Sheer Value JSONL golden files match expected output."""
    _test_jsonl_golden_files(
        "Sheer Value",
        pathlib.Path("fixtures/golden/sheer-value"),
        beanout.sheer_value.render_sheer_value_text_to_jsonl,
    )


if __name__ == "__main__":
    test_sps_jsonl_golden_files()
    print("✓ SPS JSONL golden tests passed")
    
    test_clover_leaf_jsonl_golden_files()
    print("✓ CloverLeaf JSONL golden tests passed")
    
    test_sheer_value_jsonl_golden_files()
    print("✓ Sheer Value JSONL golden tests passed")

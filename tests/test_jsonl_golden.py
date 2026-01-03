"""Golden tests for JSONL output from parsers."""

import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

import beanout.clover_leaf
import beanout.sheer_value
import beanout.sps


def test_sps_jsonl_golden_files() -> None:
    """Validate SPS JSONL golden files match expected output."""
    golden_dir = pathlib.Path("fixtures/golden/sps")
    txt_paths = sorted(golden_dir.glob("*.pdf.txt"))

    assert txt_paths, "No SPS golden .pdf.txt files found"

    for txt_path in txt_paths:
        jsonl_path = txt_path.with_suffix(".jsonl")
        assert jsonl_path.exists(), f"Missing golden file: {jsonl_path}"

        output = beanout.sps.render_sps_text_to_jsonl(txt_path.read_text())
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


def test_clover_leaf_jsonl_golden_files() -> None:
    """Validate CloverLeaf JSONL golden files match expected output."""
    golden_dir = pathlib.Path("fixtures/golden/clover-leaf")
    txt_paths = sorted(golden_dir.glob("*.pdf.txt"))

    assert txt_paths, "No CloverLeaf golden .pdf.txt files found"

    for txt_path in txt_paths:
        jsonl_path = txt_path.with_suffix(".jsonl")
        assert jsonl_path.exists(), f"Missing golden file: {jsonl_path}"

        output = beanout.clover_leaf.render_clover_leaf_text_to_jsonl(txt_path.read_text())
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


def test_sheer_value_jsonl_golden_files() -> None:
    """Validate Sheer Value JSONL golden files match expected output."""
    golden_dir = pathlib.Path("fixtures/golden/sheer-value")
    txt_paths = sorted(golden_dir.glob("*.pdf.txt"))

    assert txt_paths, "No Sheer Value golden .pdf.txt files found"

    for txt_path in txt_paths:
        jsonl_path = txt_path.with_suffix(".jsonl")
        assert jsonl_path.exists(), f"Missing golden file: {jsonl_path}"

        output = beanout.sheer_value.render_sheer_value_text_to_jsonl(txt_path.read_text())
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


if __name__ == "__main__":
    test_sps_jsonl_golden_files()
    print("✓ SPS JSONL golden tests passed")
    
    test_clover_leaf_jsonl_golden_files()
    print("✓ CloverLeaf JSONL golden tests passed")
    
    test_sheer_value_jsonl_golden_files()
    print("✓ Sheer Value JSONL golden tests passed")

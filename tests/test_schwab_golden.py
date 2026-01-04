"""Golden tests for Schwab statement parsing."""

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

import beanout.schwab


def test_schwab_golden_files() -> None:
    """Render all Schwab golden fixtures and compare to expected output."""
    golden_dir = pathlib.Path("fixtures/golden/institutions/banking/schwab")
    json_paths = sorted(
        path for path in golden_dir.iterdir() if path.suffix.lower() == ".json"
    )
    xml_paths = sorted(
        path for path in golden_dir.iterdir() if path.suffix.lower() == ".xml"
    )

    assert json_paths or xml_paths, "No Schwab golden files found"

    for json_path in json_paths:
        bean_path = json_path.with_suffix(f"{json_path.suffix}.bean")
        assert bean_path.exists(), f"Missing golden file: {bean_path}"

        output = beanout.schwab.render_schwab_json_text(json_path.read_text())
        expected = bean_path.read_text()
        assert output == expected

    for xml_path in xml_paths:
        bean_path = xml_path.with_suffix(f"{xml_path.suffix}.bean")
        assert bean_path.exists(), f"Missing golden file: {bean_path}"

        output = beanout.schwab.render_schwab_xml_text(xml_path.read_bytes())
        expected = bean_path.read_text()
        assert output == expected

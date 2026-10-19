from pathlib import Path

import pytest

from app.menu import load_menu


def test_menu_loads_all_expected_sections():
    menu = load_menu(Path("data/menu.json"))
    assert menu.get("main") is not None
    assert menu.get("schedule") is not None
    assert menu.get("benefits_rail") is not None
    assert menu.get("benefits_air") is not None
    assert menu.get("benefits_kurgan") is not None
    assert menu.get("benefits_shadrinsk") is not None
    assert menu.get("taxi") is not None
    assert menu.get("contact") is not None


def test_invalid_json_is_reported(tmp_path: Path):
    broken = tmp_path / "menu.json"
    broken.write_text("{broken", encoding="utf-8")
    with pytest.raises(RuntimeError, match="Invalid menu JSON"):
        load_menu(broken)


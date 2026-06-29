from common import defects_db


def test_engineering_system_alias_uses_existing_defects_section():
    assert defects_db.normalize_construction_type(
        "Инженерные сети: система отопления"
    ) == "Инженерные сети"

    text = defects_db.get_defects_text("Инженерные сети: система отопления")

    assert "code: ENG-HEAT-CORR;" in text
    assert "visual_signs:" in text
    assert "tags:" in text


def test_new_engineering_defects_are_indexed_by_code():
    defect = defects_db.get_defect_by_code("ENG-FIRE-FAIL")

    assert defect is not None
    assert defect["construction_type"] == "Инженерные сети"
    assert defect["category"] == "Б"
    assert defect["recommendation"]


def test_construction_prompt_contains_engineering_systems():
    assert "- Инженерные сети: система отопления" in defects_db.USER_PROMPT_CONSTRUCTIONS
    assert "- Инженерные сети: система электроснабжения" in defects_db.USER_PROMPT_CONSTRUCTIONS

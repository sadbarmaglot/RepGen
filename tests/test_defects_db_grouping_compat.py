import common.defects_db as defects_db


def test_wall_finish_location_codes_are_direct_prompt_codes():
    wall_codes = {defect["code"] for defect in defects_db.get_defects_for_type("Стена")}

    assert "FIN-CRACK" not in wall_codes
    assert {"STN004", "STN010", "STN012"}.issubset(wall_codes)

    prompt_text = defects_db.get_defects_text("Стена")
    for code in ("STN004", "STN010", "STN012"):
        item = defects_db.get_defect_by_code(code)
        assert item is not None
        assert item.get("alias_of") is None
        assert item["construction_type"] == "Стена"
        assert code not in defects_db.LEGACY_CODE_ALIASES
        assert f"code: {code};" in prompt_text


def test_roof_water_drainage_codes_are_direct_prompt_codes():
    roof_codes = {defect["code"] for defect in defects_db.get_defects_for_type("Кровля")}

    assert {"KRV005", "KRV006", "KRV008"}.issubset(roof_codes)

    prompt_text = defects_db.get_defects_text("Кровля")
    for code in ("KRV006", "KRV008"):
        item = defects_db.get_defect_by_code(code)
        assert item is not None
        assert item.get("alias_of") is None
        assert item["construction_type"] == "Кровля"
        assert code not in defects_db.LEGACY_CODE_ALIASES
        assert f"code: {code};" in prompt_text


def test_true_duplicate_column_corrosion_codes_remain_aliases():
    for code in ("KOL006", "KOL011"):
        item = defects_db.get_defect_by_code(code)
        assert item is not None
        assert item.get("alias_of") == "MTL-CORR_1"
        assert item["category"] == "В"
        assert item["recommendation"]


def test_legacy_aliases_do_not_resolve_to_empty_category_or_recommendation():
    for legacy_code in defects_db.LEGACY_CODE_ALIASES:
        item = defects_db.get_defect_by_code(legacy_code)
        assert item is not None, legacy_code
        assert item.get("category"), legacy_code
        assert item.get("recommendation"), legacy_code


def test_legacy_category_overrides_preserve_saved_project_meaning():
    assert defects_db.get_defect_by_code("LST003")["category"] == "В"
    assert defects_db.get_defect_by_code("STN016")["category"] == "В"


def test_legacy_construction_type_names_are_normalized():
    assert defects_db.normalize_construction_type("Колонна каркаса") == "Колонна"
    assert defects_db.normalize_construction_type("Ригель каркаса") == "Ригель"
    assert defects_db.normalize_construction_type("Стропильная система") == "Стропильная система покрытия"
    assert defects_db.normalize_construction_type("Инженерные сети: система отопления") == "Инженерные сети: отопление"

    assert defects_db.get_defects_for_type("Колонна каркаса")
    assert defects_db.get_defects_for_type("Инженерные сети: система отопления")


def test_construction_prompt_is_generated_from_catalog_types():
    prompt = defects_db.USER_PROMPT_CONSTRUCTIONS
    for construction_type in defects_db.CONSTRUCTION_TYPES:
        assert f"- {construction_type['name']}" in prompt
    assert "- Лифт" not in prompt

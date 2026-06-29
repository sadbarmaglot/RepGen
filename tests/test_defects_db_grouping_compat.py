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
        assert item.get("alias_of") == "MTL-CORR"

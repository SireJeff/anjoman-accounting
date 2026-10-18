# analysis_tools/tests/test_audit_rules.py
import pytest
from analysis_tools.audit import load, rules

def test_every_register_id_covered():
    reg = load.load_register()
    for e in reg:
        rid = e["id"]
        assert rid in rules.RULES or rid in rules.NO_FIELD_CHANGE, rid

def test_every_rule_id_in_register():
    reg_ids = {e["id"] for e in load.load_register()}
    assert set(rules.RULES) == reg_ids
    assert rules.NO_FIELD_CHANGE <= reg_ids

def test_no_double_patches():
    seen = {}
    for rid, patches in rules.RULES.items():
        for tx, field, _ in patches:
            key = (tx, field)
            assert key not in seen, f"{key} patched by {seen.get(key)} and {rid}"
            seen[key] = rid

def test_patch_fields_exist():
    valid = set(load.SOURCE_COLS) | set(load.AUDIT_COLS)
    for rid, patches in rules.RULES.items():
        for tx, field, _ in patches:
            assert field in valid, (rid, field)

def test_register_set_fidelity():
    """Where the register declares explicit set-keys, RULES must carry the same
    values (register text is never parsed; this checks the declared numbers)."""
    reg = {e["id"]: e for e in load.load_register()}
    assert reg["R-06"]["set"] == {"amount_toman": 10003780,
                                  "unit_original": "rial",
                                  "amount_original": 100037800,
                                  "date_jalali": "1404/10/01"}
    assert reg["R-07"]["set"] == {"TX0058.amount_toman": 275000}
    assert reg["P-03"]["set"]["split"][1]["id"] == "TX0034-B"
    assert reg["R-08"]["pending_item"]["id"] == "PI-01"

def test_pending_item_matches_register():
    reg = {e["id"]: e for e in load.load_register()}
    pi = reg["R-08"]["pending_item"]
    assert rules.PENDING_ITEMS[0]["id"] == pi["id"]
    assert rules.PENDING_ITEMS[0]["amount_toman"] == pi["amount_toman"]
    assert rules.PENDING_ITEMS[0]["project"] == pi["project"]

def test_open_items_shape():
    ids = [o["id"] for o in rules.OPEN_ITEMS]
    assert ids == [f"OI-{n:02d}" for n in range(1, 19)]
    carried = {tx for o in rules.OPEN_ITEMS for tx in o["txs"]}
    patched = {tx for patches in rules.RULES.values()
               for tx, f, v in patches if f == "open_item"}
    assert carried == patched

def test_validate_raises_on_unknown_id():
    with pytest.raises(rules.AuditError):
        rules.validate([{"id": "X-99"}, *[{"id": f"D-{n:02d}"} for n in range(1, 6)],
                        *[{"id": f"R-{n:02d}"} for n in range(1, 17)],
                        *[{"id": f"U-{n:02d}"} for n in range(1, 9)],
                        *[{"id": f"P-{n:02d}"} for n in range(1, 6)]])

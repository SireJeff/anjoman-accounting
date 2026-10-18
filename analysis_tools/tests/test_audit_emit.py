import csv, json
from analysis_tools.audit import apply, bridge, balance, emit, load, rules

def test_write_all_outputs(tmp_path):
    rows, log = apply.apply()
    sheets = balance.project_sheets(rows, rules.PENDING_ITEMS)
    emit.write_ledger(rows, out_dir=tmp_path)
    emit.write_log(log, out_dir=tmp_path)
    emit.write_register(out_dir=tmp_path)
    emit.write_sheets(sheets, rules.PENDING_ITEMS, out_dir=tmp_path)
    emit.write_open_items(rows, out_dir=tmp_path)
    ledger = list(csv.DictReader(open(tmp_path / "Transactions_Audited.csv",
                                       encoding="utf-8-sig")))
    assert len(ledger) == 97 and ledger[0]["source_status"] in {
        "Supported", "Review", "Duplicate", "Invoice only", "Summary only"}
    j = json.loads((tmp_path / "Transactions_Audited.json").read_text(encoding="utf-8"))
    assert len(j) == 97
    logrows = list(csv.DictReader(open(tmp_path / "Audit_Log.csv", encoding="utf-8-sig")))
    assert {"tx", "field", "old", "new", "source_id"} <= set(logrows[0])
    oi = list(csv.DictReader(open(tmp_path / "Open_Items.csv", encoding="utf-8-sig")))
    assert len(oi) == 18 and oi[6]["id"] == "OI-07"

def test_register_is_byte_copy(tmp_path):
    emit.write_register(out_dir=tmp_path)
    assert (tmp_path / "Decisions_Register.json").read_bytes() == \
        (load.DATA / "decisions.json").read_bytes()

def test_deterministic(tmp_path):
    rows, log = apply.apply()
    sheets = balance.project_sheets(rows, rules.PENDING_ITEMS)
    import io
    outs = []
    for _ in range(2):
        emit.write_ledger(rows, out_dir=tmp_path)
        buf = io.StringIO()
        emit._csv_string(rows, load.SOURCE_COLS + load.AUDIT_COLS, buf)
        outs.append(buf.getvalue())
    assert outs[0] == outs[1]

import json
import shutil

import pytest

from analysis_tools import i18n


@pytest.fixture
def pseudo_fa(tmp_path):
    """FA catalog = EN templates prefixed with «FA», hashes current. Lets FA
    code paths run before the real fa.json exists (Task 6)."""
    en = json.loads((i18n.PKG_DIR / "en.json").read_text(encoding="utf-8"))
    (tmp_path / "en.json").write_text(json.dumps(en, ensure_ascii=False), encoding="utf-8")
    (tmp_path / "fa.json").write_text(json.dumps(
        {k: "«FA» " + v for k, v in en.items()}, ensure_ascii=False), encoding="utf-8")
    (tmp_path / "hashes.json").write_text(json.dumps(
        {k: i18n.sha(v) for k, v in en.items()}), encoding="utf-8")
    shutil.copy(i18n.PKG_DIR / "glossary.json", tmp_path / "glossary.json")
    i18n.set_catalog_dir(tmp_path)
    yield tmp_path
    i18n.set_catalog_dir(None)

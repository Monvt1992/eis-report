import pandas as pd

from eis_report.data_loader import _ensure_eis14


def test_ensure_eis14_computes_when_missing():
    df = pd.DataFrame({"Eis1": [-1.0, 2.0], "Eis2": [-3.0, 1.0], "Eis4": [5.0, 0.0]})
    columns = {"eis1": "Eis1", "eis2": "Eis2", "eis4": "Eis4", "eis14": "Eis14"}
    out = _ensure_eis14(df, columns, "eis1", "eis2", "eis4", "eis14")
    # Eis14 = Eis4 + abs(Eis1) - abs(Eis2)
    assert out["Eis14"].tolist() == [5.0 + 1.0 - 3.0, 0.0 + 2.0 - 1.0]


def test_ensure_eis14_skips_when_present():
    df = pd.DataFrame({"Eis14": [9.9]})
    columns = {"eis14": "Eis14"}
    out = _ensure_eis14(df, columns, "eis1", "eis2", "eis4", "eis14")
    assert out["Eis14"].tolist() == [9.9]

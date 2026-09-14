import pandas as pd

from eis_report.cw import cw_from_datetime, cw_from_mixno


def test_cw_from_mixno_basic():
    s = pd.Series(["C636-501", "C737-102", "bad"])
    result = cw_from_mixno(s)
    assert result.tolist() == [36, 37, pd.NA]


def test_cw_from_datetime_basic():
    s = pd.Series(pd.to_datetime(["2026-09-07", "2026-09-14"]))
    result = cw_from_datetime(s)
    assert result.tolist() == [37, 38]

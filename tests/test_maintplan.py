import pandas as pd
from maintplan import notifications as nt, scheduling as sc, master_data as md

FL = pd.DataFrame({"site_id": [1, 2], "TPLNR": ["SOL-NSW-2000-001", "SOL-NSW-2300-002"],
                   "ARBPL": ["WC-SYD", "WC-HUNTER"]})


def _alerts(site, kind, days):
    return pd.DataFrame({"site_id": site, "alert_type": kind,
                         "day": pd.to_datetime(days), "severity": "x"})


def test_consecutive_alert_days_become_one_notification():
    a = _alerts(1, "no_generation", pd.date_range("2013-01-01", periods=30))
    assert len(nt.notifications(a, FL)) == 1


def test_small_gaps_are_bridged_but_long_gaps_split():
    a = _alerts(1, "no_generation", ["2013-01-01", "2013-01-03", "2013-01-20"])
    assert len(nt.episodes(a)) == 2


def test_short_underperformance_is_not_notified():
    a = _alerts(1, "underperforming", ["2013-01-01", "2013-01-02"])
    assert nt.notifications(a, FL).empty


def test_outage_is_notified_on_its_first_day_with_top_priority():
    n = nt.notifications(_alerts(1, "no_generation", ["2013-01-07"]), FL)
    assert n["PRIOK"].iloc[0] == 1 and n["QMDAT"].iloc[0] == pd.Timestamp("2013-01-07")


def test_scheduler_respects_capacity_priority_and_weekends():
    notes = pd.DataFrame({"QMNUM": ["a", "b"], "ARBPL": "WC-SYD", "PRIOK": [3, 1],
                          "QMDAT": pd.Timestamp("2013-01-04"), "TPLNR": "x"})   # a Friday
    s = sc.schedule(notes, "priority", capacity=1).set_index("QMNUM")
    assert s.loc["b", "scheduled"] == pd.Timestamp("2013-01-04")   # urgent job first
    assert s.loc["a", "scheduled"] == pd.Timestamp("2013-01-07")   # next working day, Monday


def test_work_centre_mapping():
    assert md.work_centre(2076) == "WC-SYD" and md.work_centre(2300) == "WC-HUNTER"

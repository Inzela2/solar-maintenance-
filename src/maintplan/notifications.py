"""Collapse daily alerts into maintenance notifications (SAP PM type M2, malfunction report).

A site that is down for 30 days raises 30 daily alerts, but a planner needs ONE notification.
Consecutive alert days for the same site and fault type become one episode (gaps of up to
MAX_GAP_DAYS are bridged). Underperformance must persist CONFIRM_DAYS before a notification
is raised, because the fault-detection evaluation showed short dips are the main source of
false alarms; outages are raised immediately.
"""
import pandas as pd

MAX_GAP_DAYS = 2
CONFIRM_DAYS = {"no_generation": 1, "missing_data": 2, "underperforming": 3}
PRIORITY = {"no_generation": 1, "missing_data": 2, "underperforming": 3}   # 1 = very high
TEXT = {"no_generation": "PV system producing no output",
        "missing_data": "No telemetry received from meter",
        "underperforming": "PV output well below normal"}


def episodes(alerts: pd.DataFrame) -> pd.DataFrame:
    a = alerts.sort_values(["site_id", "alert_type", "day"]).copy()
    gap = a.groupby(["site_id", "alert_type"])["day"].diff().dt.days
    a["episode"] = (gap.isna() | (gap > MAX_GAP_DAYS + 1)).cumsum()
    e = a.groupby("episode").agg(site_id=("site_id", "first"), alert_type=("alert_type", "first"),
                                 start=("day", "min"), end=("day", "max"), alert_days=("day", "size"))
    return e.reset_index(drop=True)


def notifications(alerts: pd.DataFrame, fl: pd.DataFrame) -> pd.DataFrame:
    e = episodes(alerts)
    e = e[e["alert_days"] >= e["alert_type"].map(CONFIRM_DAYS)].copy()
    e["QMDAT"] = e["start"] + pd.to_timedelta(e["alert_type"].map(CONFIRM_DAYS) - 1, unit="D")
    e["PRIOK"] = e["alert_type"].map(PRIORITY)
    e["QMTXT"] = e["alert_type"].map(TEXT)
    e = e.merge(fl[["site_id", "TPLNR", "ARBPL"]], on="site_id")
    e = e.sort_values("QMDAT").reset_index(drop=True)
    e["QMNUM"] = [f"{300000000 + i}" for i in range(1, len(e) + 1)]
    e["QMART"] = "M2"
    return e[["QMNUM", "QMART", "TPLNR", "ARBPL", "site_id", "alert_type", "PRIOK", "QMTXT",
              "QMDAT", "start", "end", "alert_days"]]

"""Schedule work orders (SAP PM order type PM01) against limited crew capacity.

Each work centre can do CAPACITY jobs per working day. Every priority has a target response
time. We compare two rules a planner could follow:
* fifo: first notified, first scheduled (what happens without a planning rule)
* priority: highest priority first, then the earliest due date
and measure how many jobs meet their target. Weekends are not worked.
"""
import pandas as pd

CAPACITY = 1                                # jobs per work centre per working day
TARGET_DAYS = {1: 2, 2: 5, 3: 14}           # response targets by priority (calendar days)


def schedule(notes: pd.DataFrame, rule: str = "priority", capacity: int = CAPACITY) -> pd.DataFrame:
    n = notes.copy()
    n["due"] = n["QMDAT"] + pd.to_timedelta(n["PRIOK"].map(TARGET_DAYS), unit="D")
    out = []
    for wc, jobs in n.groupby("ARBPL"):
        pending = []
        jobs = jobs.sort_values("QMDAT")
        day = jobs["QMDAT"].min()
        i = 0
        while i < len(jobs) or pending:
            while i < len(jobs) and jobs.iloc[i]["QMDAT"] <= day:
                pending.append(jobs.iloc[i])
                i += 1
            if day.dayofweek < 5 and pending:
                key = (lambda j: (j["QMDAT"], j["QMNUM"])) if rule == "fifo" else \
                      (lambda j: (j["PRIOK"], j["due"], j["QMNUM"]))
                pending.sort(key=key)
                for j in pending[:capacity]:
                    out.append({**j.to_dict(), "scheduled": day})
                pending = pending[capacity:]
            day += pd.Timedelta(days=1)
    s = pd.DataFrame(out)
    s["AUFNR"] = [f"{4000000 + i}" for i in range(1, len(s) + 1)]
    s["AUART"] = "PM01"
    s["days_to_schedule"] = (s["scheduled"] - s["QMDAT"]).dt.days
    s["met_target"] = s["scheduled"] <= s["due"]
    return s


def compare(notes: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for rule in ("fifo", "priority"):
        s = schedule(notes, rule)
        for p, g in s.groupby("PRIOK"):
            rows.append({"rule": rule, "priority": p, "jobs": len(g),
                         "met_target_pct": round(100 * g["met_target"].mean(), 1),
                         "median_days_to_schedule": g["days_to_schedule"].median()})
    return pd.DataFrame(rows)

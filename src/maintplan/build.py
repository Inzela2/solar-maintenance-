"""python -m maintplan  ->  builds master data, notifications, work orders and the Power BI model.

Inputs (data/): sites.csv, alerts.csv, daily_metrics.csv, site_metadata_flags.csv, exported
from the solar-fleet-health pipeline. Outputs: powerbi/*.csv (a star schema) and results/.
"""
from pathlib import Path
import json
import pandas as pd
from . import master_data as md, notifications as nt, scheduling as sc

D, P, R = Path("data"), Path("powerbi"), Path("results")


def main():
    P.mkdir(exist_ok=True); R.mkdir(exist_ok=True)
    sites = pd.read_csv(D / "sites.csv")
    alerts = pd.read_csv(D / "alerts.csv", parse_dates=["day"])
    daily = pd.read_csv(D / "daily_metrics.csv", parse_dates=["day"])
    flags = pd.read_csv(D / "site_metadata_flags.csv")

    fl = md.functional_locations(sites)
    eq = md.equipment(sites, fl)
    dq = md.quality_issues(fl, eq, flags)
    notes = nt.notifications(alerts, fl)
    orders = sc.schedule(notes, "priority")
    comparison = sc.compare(notes)

    # Power BI star schema: one dimension per "who/where/when", facts for what happened
    dim_site = fl.merge(sites[["site_id", "capacity_kw"]], on="site_id")
    dim_site["has_data_issue"] = dim_site["TPLNR"].isin(dq["TPLNR"])
    dim_date = pd.DataFrame({"date": pd.date_range(daily.day.min(), daily.day.max())})
    dim_date["month"] = dim_date["date"].dt.strftime("%Y-%m")
    dim_date["weekday"] = dim_date["date"].dt.day_name()
    dim_date["is_weekend"] = dim_date["date"].dt.dayofweek >= 5
    fact_daily = daily.rename(columns={"day": "date"})
    dim_site.to_csv(P / "dim_site.csv", index=False)
    dim_date.to_csv(P / "dim_date.csv", index=False)
    eq.to_csv(P / "dim_equipment.csv", index=False)
    fact_daily.to_csv(P / "fact_daily_generation.csv", index=False)
    notes.to_csv(P / "fact_notifications.csv", index=False)
    orders.drop(columns=["start", "end"]).to_csv(P / "fact_work_orders.csv", index=False)
    dq.to_csv(P / "master_data_issues.csv", index=False)

    summary = {"alert_days": len(alerts), "episodes": len(nt.episodes(alerts)),
               "notifications": len(notes),
               "reduction_pct": round(100 * (1 - len(notes) / len(alerts)), 1),
               "notifications_by_type": notes["alert_type"].value_counts().to_dict(),
               "master_data_issues": dq["issue"].value_counts().to_dict(),
               "functional_locations": len(fl), "equipment": len(eq)}
    comparison.to_csv(R / "scheduling_comparison.csv", index=False)
    (R / "summary.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2)); print(comparison.to_string(index=False))


if __name__ == "__main__":
    main()

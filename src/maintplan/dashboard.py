"""Render the three dashboard pages as images from the Power BI model in powerbi/.

Same tables and measures as the Power BI build guide, drawn with matplotlib so the dashboard
can be viewed directly on GitHub.  python -m maintplan.dashboard
"""
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

P, OUT = Path("powerbi"), Path("results/dashboard")
NAVY, BLUE, ORANGE, RED, GREY = "#1f3864", "#2c7fb8", "#e6a100", "#c0392b", "#9e9e9e"
PRIO = {1: "1 · No output", 2: "2 · No telemetry", 3: "3 · Underperforming"}


def _cards(fig, items, top=0.83):
    w = 0.9 / len(items)
    for i, (label, value, colour) in enumerate(items):
        ax = fig.add_axes([0.05 + i * w, top, w - 0.02, 0.09])
        ax.set_facecolor("#f4f6fa"); ax.set_xticks([]); ax.set_yticks([])
        for s in ax.spines.values():
            s.set_visible(False)
        ax.text(0.5, 0.62, value, ha="center", va="center", fontsize=20, weight="bold", color=colour)
        ax.text(0.5, 0.2, label, ha="center", va="center", fontsize=9, color="#444")


def _title(fig, text, sub):
    fig.text(0.05, 0.955, text, fontsize=16, weight="bold", color=NAVY)
    fig.text(0.95, 0.955, sub, fontsize=9, color="#666", ha="right")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    site = pd.read_csv(P / "dim_site.csv")
    daily = pd.read_csv(P / "fact_daily_generation.csv", parse_dates=["date"])
    notes = pd.read_csv(P / "fact_notifications.csv", parse_dates=["QMDAT"])
    orders = pd.read_csv(P / "fact_work_orders.csv", parse_dates=["QMDAT", "scheduled"])
    issues = pd.read_csv(P / "master_data_issues.csv")
    daily = daily.merge(site[["site_id", "ARBPL"]], on="site_id")
    sub = "Ausgrid Solar Home data · Jul 2012 – Jun 2013"

    # Page 1: fleet overview
    fig = plt.figure(figsize=(12, 7))
    _title(fig, "Fleet overview", sub)
    _cards(fig, [("Total generation (MWh)", f"{daily.gen_kwh.sum() / 1000:,.0f}", NAVY),
                 ("Notifications raised", f"{len(notes)}", NAVY),
                 ("Sites", f"{site.site_id.nunique()}", NAVY),
                 ("Priority 1 notifications", f"{(notes.PRIOK == 1).sum()}", RED)])
    ax = fig.add_axes([0.06, 0.1, 0.55, 0.65])
    for wc, c in zip(["WC-SYD", "WC-CCOAST", "WC-HUNTER"], [NAVY, BLUE, ORANGE]):
        s = daily[daily.ARBPL == wc].groupby("date").gen_kwh.sum().rolling(7).mean() / 1000
        ax.plot(s.index, s.values, label=wc, color=c, lw=2)
    ax.set_title("Daily generation by work centre (MWh, 7-day average)", loc="left", fontsize=11)
    ax.legend(frameon=False); ax.spines[["top", "right"]].set_visible(False)
    ax2 = fig.add_axes([0.68, 0.1, 0.28, 0.65])
    m = notes.groupby(notes.QMDAT.dt.to_period("M")).size()
    ax2.bar(m.index.strftime("%b"), m.values, color=BLUE)
    ax2.set_title("Notifications raised per month", loc="left", fontsize=11)
    ax2.tick_params(axis="x", rotation=90); ax2.spines[["top", "right"]].set_visible(False)
    fig.savefig(OUT / "1_fleet_overview.png", dpi=130); plt.close(fig)

    # Page 2: maintenance planning
    fig = plt.figure(figsize=(12, 7))
    _title(fig, "Maintenance planning", sub)
    _cards(fig, [("Work orders", f"{len(orders)}", NAVY),
                 ("On target", f"{orders.met_target.mean():.0%}", NAVY),
                 ("Median days to schedule", f"{orders.days_to_schedule.median():.0f}", NAVY),
                 ("Daily alerts automated away", "94%", BLUE)])
    ax = fig.add_axes([0.06, 0.12, 0.38, 0.6])
    cmp = pd.read_csv("results/scheduling_comparison.csv")
    c1 = cmp[cmp.priority == 1].set_index("rule")["met_target_pct"]
    ax.bar(["First in, first out", "Priority rule"], [c1["fifo"], c1["priority"]], color=[GREY, NAVY])
    for i, v in enumerate([c1["fifo"], c1["priority"]]):
        ax.text(i, v + 0.2, f"{v:.1f}%", ha="center", fontsize=11, weight="bold")
    ax.set_ylim(90, 100.5); ax.set_ylabel("% on target (axis starts at 90%)"); ax.set_title("Priority 1 jobs scheduled within 2 days", loc="left", fontsize=11)
    ax.spines[["top", "right"]].set_visible(False)
    ax2 = fig.add_axes([0.5, 0.12, 0.46, 0.6]); ax2.axis("off")
    t = orders.sort_values(["PRIOK", "scheduled"]).head(12)
    rows = [[r.AUFNR, r.TPLNR, PRIO[r.PRIOK], r.scheduled.strftime("%d %b %Y"), "Yes" if r.met_target else "No"]
            for r in t.itertuples()]
    tb = ax2.table(cellText=rows, colLabels=["Order", "Functional location", "Priority", "Scheduled", "On target"],
                   loc="upper center", cellLoc="left", colLoc="left", colWidths=[0.15, 0.3, 0.24, 0.18, 0.13])
    tb.auto_set_font_size(False); tb.set_fontsize(8); tb.scale(1, 1.35)
    for (r, c), cell in tb.get_celld().items():
        cell.set_edgecolor("#ddd")
        if r == 0:
            cell.set_facecolor(NAVY); cell.set_text_props(color="white", weight="bold")
    ax2.set_title("Work orders (PM01), highest priority first", loc="left", fontsize=11)
    fig.savefig(OUT / "2_maintenance_planning.png", dpi=130); plt.close(fig)

    # Page 3: master data quality
    fig = plt.figure(figsize=(12, 7))
    _title(fig, "Master data quality", sub)
    _cards(fig, [("Functional locations", f"{len(site)}", NAVY),
                 ("Sites with data issues", f"{site.has_data_issue.sum()}", RED),
                 ("Capacity too low", f"{(issues.issue == 'capacity_too_low').sum()}", ORANGE),
                 ("Meter channels suspect", f"{(issues.issue == 'meter_channels_suspect').sum()}", ORANGE)])
    ax = fig.add_axes([0.05, 0.05, 0.9, 0.7]); ax.axis("off")
    rows = [[r.TPLNR, r.issue.replace("_", " "), r.detail] for r in issues.itertuples()]
    tb = ax.table(cellText=rows, colLabels=["Functional location", "Issue", "Detail"], loc="upper center",
                  cellLoc="left", colLoc="left", colWidths=[0.18, 0.17, 0.65])
    tb.auto_set_font_size(False); tb.set_fontsize(8); tb.scale(1, 1.3)
    for (r, c), cell in tb.get_celld().items():
        cell.set_edgecolor("#ddd")
        if r == 0:
            cell.set_facecolor(NAVY); cell.set_text_props(color="white", weight="bold")
    ax.set_title("Issues for a data steward to confirm and fix", loc="left", fontsize=11)
    fig.savefig(OUT / "3_master_data_quality.png", dpi=130); plt.close(fig)


if __name__ == "__main__":
    main()

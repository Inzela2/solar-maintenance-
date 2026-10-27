"""SAP PM-style master data: functional locations, equipment, and data-quality checks.

Field names follow SAP PM conventions (TPLNR functional location, EQUNR equipment, ARBPL work
centre) so the tables map directly onto how a real plant-maintenance system is organised.
"""
import pandas as pd


def work_centre(postcode: int) -> str:
    if postcode < 2250:
        return "WC-SYD"
    if postcode < 2280:
        return "WC-CCOAST"
    return "WC-HUNTER"


def functional_locations(sites: pd.DataFrame) -> pd.DataFrame:
    fl = sites.copy()
    fl["TPLNR"] = [f"SOL-NSW-{p}-{s:03d}" for s, p in zip(fl.site_id, fl.postcode)]
    fl["ARBPL"] = fl["postcode"].map(work_centre)
    fl["PLTXT"] = "Rooftop PV system, postcode " + fl["postcode"].astype(str)
    return fl[["site_id", "TPLNR", "PLTXT", "postcode", "ARBPL"]]


def equipment(sites: pd.DataFrame, fl: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for s, cap in zip(sites.site_id, sites.capacity_kw):
        tplnr = fl.loc[fl.site_id == s, "TPLNR"].iloc[0]
        rows.append({"EQUNR": f"{10000000 + s * 10 + 1}", "TPLNR": tplnr, "EQKTX": "PV array",
                     "capacity_kw": cap, "site_id": s})
        rows.append({"EQUNR": f"{10000000 + s * 10 + 2}", "TPLNR": tplnr, "EQKTX": "Gross meter",
                     "capacity_kw": None, "site_id": s})
    return pd.DataFrame(rows)


def quality_issues(fl: pd.DataFrame, eq: pd.DataFrame, flags: pd.DataFrame) -> pd.DataFrame:
    """Master data problems a data steward should fix, one row per issue."""
    out = []
    for r in flags.itertuples():
        tplnr = fl.loc[fl.site_id == r.site_id, "TPLNR"].iloc[0]
        if r.over_capacity:
            out.append((tplnr, "capacity_too_low", f"peak output is {r.peak_to_rated:.0%} of rated capacity; "
                        "capacity on the PV array record is probably wrong"))
        if r.night_generation:
            out.append((tplnr, "meter_channels_suspect", f"generation recorded at night on "
                        f"{int(r.night_generation_days)} days; meter channels may be swapped"))
    for t in fl.loc[fl["TPLNR"].duplicated(), "TPLNR"]:
        out.append((t, "duplicate_functional_location", "TPLNR appears more than once"))
    for t in fl.loc[fl["ARBPL"].isna(), "TPLNR"]:
        out.append((t, "missing_work_centre", "no work centre assigned"))
    return pd.DataFrame(out, columns=["TPLNR", "issue", "detail"])

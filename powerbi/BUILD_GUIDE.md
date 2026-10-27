# Build the dashboard and automation (about 30–45 minutes)

Everything here uses free tools: Power BI Desktop (Windows, free from the Microsoft Store) and, optionally, a free Microsoft 365 developer account for Power Automate and Power Apps.

## 1. Power BI dashboard (about 25 minutes)

1. **Get data → Text/CSV:** load every CSV in this folder.
2. **Model view → create relationships** (all single direction, many-to-one):
   - `fact_daily_generation[site_id]` → `dim_site[site_id]`
   - `fact_daily_generation[date]` → `dim_date[date]`
   - `fact_notifications[TPLNR]` → `dim_site[TPLNR]`
   - `fact_work_orders[TPLNR]` → `dim_site[TPLNR]`
   - `dim_equipment[TPLNR]` → `dim_site[TPLNR]`
   - `master_data_issues[TPLNR]` → `dim_site[TPLNR]`
3. **Add the measures** from `measures.dax` (Modeling → New measure, one at a time).
4. **Build three pages:**
   - **Fleet overview:** cards for Total Generation, Fleet Performance Ratio, Priority 1 Notifications; a line chart of `gen_kwh` by `dim_date[date]`; a slicer on `dim_site[ARBPL]` (work centre).
   - **Maintenance planning:** a table of `fact_work_orders` (AUFNR, TPLNR, QMTXT, PRIOK, scheduled, met_target); a bar chart of Work Orders On Target % by `PRIOK`; cards for Median Days To Schedule.
   - **Master data quality:** a table of `master_data_issues`; a card for Sites With Data Issues.
5. **Save as** `solar_maintenance.pbix` and add it, plus a screenshot of each page, to the repo.

## 2. Power Automate flow (optional, about 10 minutes)

Goal: a new priority 1 notification alerts the work centre straight away.

1. Upload `fact_notifications.csv` to a SharePoint list called **Notifications** (or import it with "Create list from Excel").
2. In Power Automate, create an **Automated cloud flow**: trigger **When an item is created** (SharePoint, list Notifications).
3. Add a **Condition**: `PRIOK` is equal to `1`.
4. If yes: **Post message in a chat or channel** (Teams) with the TPLNR, QMTXT and QMDAT fields. If no: do nothing.
5. Test by adding one row with PRIOK = 1, then screenshot the flow and the Teams message for the repo.

## 3. Power Apps form (optional, about 10 minutes)

Goal: a technician closes a work order from their phone.

1. Create a **Canvas app from SharePoint** using a list built from `fact_work_orders.csv`.
2. Keep the generated browse, detail and edit screens. On the edit screen, add a **Status** choice (Open, In progress, Done) and a **Technician notes** text field.
3. Screenshot the phone layout for the repo.

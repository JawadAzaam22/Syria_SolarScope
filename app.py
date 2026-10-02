import altair as alt
import pandas as pd
import streamlit as st
import core

st.set_page_config(page_title="Syria SolarScope", page_icon="☀️", layout="centered")
MONTHS = ["January", "February", "March", "April", "May", "June", "July",
          "August", "September", "October", "November", "December"]
SHORT = [m[:3] for m in MONTHS]

# grid tariffs, SYP per kWh (ministry of energy, 1 Nov 2025)
TARIFFS = pd.DataFrame([
    ["Tier 1 - households (subsidised)", "up to 300 kWh per 2-month bill", 600],
    ["Tier 2 - households / small business", "above 300 kWh (whole bill at this rate)", core.GRID_TIER2_SYP],
    ["Tier 3 - institutions / companies", "public institutions, factories", 1700],
    ["Tier 4 - energy-intensive factories", "heavy industrial consumers", 1800],
], columns=["Tier", "Consumption bracket", "SYP per kWh"])

TARIFFS["USD per kWh (approx.)"] = (TARIFFS["SYP per kWh"] / core.SYP_PER_USD).round(3)
GRID = core.GRID_TIER2_USD

@st.cache_data
def load():
    return pd.read_csv("monthly_stats.csv"), pd.read_csv("annual_stats.csv")

@st.cache_data
def load_daily():
    d = core.add_physics(pd.read_csv("power_syria_daily_2015_2025.csv", parse_dates=["date"]))
    d["year"], d["month"] = d.date.dt.year, d.date.dt.month
    d["heat_loss_day"] = 1 - d.f_temp
    return d

monthly, annual = load()
st.title("☀️ Syria SolarScope")

tab_calc, tab_analysis, tab_tariff = st.tabs(["🧮 System calculator", "📊 Analysis", "⚡ Grid tariffs (Syria)"])

with tab_calc:
    st.write("Pick a governorate, enter your system size and cost, and see what it will produce and what each kWh will cost.")

    c1, c2, c3 = st.columns([1.2, 1.4, 1])
    # user inputs: governorate, size (kW or panels), total cost, batteries yes/no
    gov = c1.selectbox("Governorate", sorted(annual.governorate))
    unit = c2.radio("System capacity in", ["kW", "Panels"], horizontal=True)
    size = c2.number_input("Capacity", 0.5, 1000.0, 5.0 if unit == "kW" else 10.0, 0.5, label_visibility="collapsed")
    cost = c3.number_input("Total capital cost (USD)", 100.0, 1_000_000.0, 5000.0, 100.0)

    with_batt = c3.toggle("System includes batteries", value=False,
                          help="Batteries raise yearly costs (maintenance + replacement): O&M = 10 % of cost/yr instead of 2 %.")
    om = core.OM_SHARE if with_batt else core.OM_NO_BATTERY

    a = annual[annual.governorate == gov].iloc[0]
    m = monthly[monthly.governorate == gov].sort_values("month")
    kw = size if unit == "kW" else core.kw_from_panels(size)
    e1 = a["mean"] * kw
    lcoe_val = core.lcoe(cost, e1, om_share=om)
    st.subheader(f"A {kw:g} kW system in {gov} should produce about {e1:,.0f} kWh a year.")
    k1, k2, k3 = st.columns(3)
    k1.metric("Annual output", f"{e1:,.0f} kWh", f"Low {a.low * kw:,.0f} – High {a.high * kw:,.0f}", delta_color="off")
    k2.metric("Heat loss", f"{a.heat_loss * 100:.1f}%")
    k3.metric("Cost per kWh (LCOE)", f"${lcoe_val:.3f}",
              delta=None if lcoe_val < GRID else "above grid tier-2 price")

    if lcoe_val < GRID:
        st.success(f"Your solar kWh (~${lcoe_val:.3f}) is cheaper than the grid's tier-2 price (~${GRID:.3f}/kWh).")
    else:
        st.warning(f"Your solar kWh (~${lcoe_val:.3f}) is above the grid's tier-2 price (~${GRID:.3f}/kWh) - check the cost or size of the system.")

    st.subheader("Monthly output (kWh)")
    t = pd.DataFrame({"Low": m.low.values * kw, "Expected": m["mean"].values * kw,
                      "High": m.high.values * kw, "Heat loss %": m.heat_loss.values * 100}, index=MONTHS)

    chart_df = pd.DataFrame({"Month": MONTHS, "Expected kWh": t["Expected"].values})
    st.altair_chart(alt.Chart(chart_df).mark_bar().encode(
        x=alt.X("Month:N", sort=MONTHS, title=None), y=alt.Y("Expected kWh:Q"),
        tooltip=["Month", alt.Tooltip("Expected kWh:Q", format=",.0f")]), width="stretch")
    st.dataframe(t.round(1))
    daily = load_daily()
    twins = [g for grp in core.shared_cells(daily) if gov in grp for g in grp if g != gov]
    if twins:
        st.caption(f"Note: {gov} falls in the same NASA grid cell as {', '.join(twins)}, so they share the same solar data.")
    st.caption("Based on NASA POWER solar and temperature data, 2015-2025. Low/High = 10th/90th percentile of yearly results. "
               "O&M assumption: 10 % of cost/yr with batteries, 2 %/yr without (industry rule of thumb 1-2 %).")

with tab_analysis:
    daily = load_daily()
    st.write("The four analyses behind the calculator (NASA POWER, 2015-2025). Yields are per kWp of installed panels.")

    st.subheader("1. Which governorates produce the most?")
    rank = annual.sort_values("mean", ascending=False)
    base = alt.Chart(rank).encode(y=alt.Y("governorate:N", sort=None, title=None))
    st.altair_chart(base.mark_bar().encode(
        x=alt.X("mean:Q", title="Annual yield (kWh per kWp)"),
        tooltip=["governorate", alt.Tooltip("mean:Q", format=",.0f")])
        + base.mark_rule().encode(x="low:Q", x2="high:Q"), width="stretch")
    spread = (rank["mean"].max() / rank["mean"].min() - 1) * 100
    st.write(f"Best: **{rank.governorate.iloc[0]}** ({rank['mean'].iloc[0]:,.0f} kWh/kWp). "
             f"Lowest: **{rank.governorate.iloc[-1]}** ({rank['mean'].iloc[-1]:,.0f}). Spread: {spread:.1f}%.")
    cells = "; ".join(" = ".join(grp) for grp in core.shared_cells(daily))
    st.caption("Lines show the 10th-90th percentile of yearly results. "
               f"Governorates in the same NASA grid cell share solar data ({cells}).")

    st.subheader("2. Seasonality and heat loss")
    picks = st.multiselect("Governorates to compare", sorted(annual.governorate),
                           default=["Damascus", "Aleppo", "Latakia", "Deir ez-Zor"])
    if picks:
        sel = monthly[monthly.governorate.isin(picks)].copy()
        sel["Month"] = sel.month.map(lambda k: SHORT[k - 1])
        sel["Heat loss %"] = sel.heat_loss * 100
        for col, title in [("mean", "Monthly yield (kWh per kWp)"), ("Heat loss %", "Heat loss (%)")]:
            st.altair_chart(alt.Chart(sel).mark_line(point=True).encode(
                x=alt.X("Month:N", sort=SHORT, title=None), y=alt.Y(f"{col}:Q", title=title),
                color=alt.Color("governorate:N", title=None),
                tooltip=["governorate", "Month", alt.Tooltip(f"{col}:Q", format=",.1f")]), width="stretch")
    peak = monthly.groupby("month")["heat_loss"].mean() * 100
    st.write(f"Across Syria heat loss peaks in **{MONTHS[peak.idxmax() - 1]}** ({peak.max():.1f}%) "
             f"and is lowest in **{MONTHS[peak.idxmin() - 1]}** ({peak.min():.1f}%).")

    st.subheader("3. Reliability: year-to-year variability and trend")
    cv = annual.assign(cv_pct=annual.cv * 100).sort_values("cv_pct", ascending=False)
    st.altair_chart(alt.Chart(cv).mark_bar().encode(
        y=alt.Y("governorate:N", sort=None, title=None), x=alt.X("cv_pct:Q", title="Variability between years (CV, %)"),
        tooltip=["governorate", alt.Tooltip("cv_pct:Q", format=".2f")]), width="stretch")
    chg = core.period_change(daily).sort_values().rename("change").reset_index()
    st.altair_chart(alt.Chart(chg).mark_bar().encode(
        y=alt.Y("governorate:N", sort=None, title=None), x=alt.X("change:Q", title="Change in yearly yield, 2021-25 vs 2015-19 (%)"),
        color=alt.condition(alt.datum.change > 0, alt.value("#0f6b6b"), alt.value("#c0392b")),
        tooltip=["governorate", alt.Tooltip("change:Q", format="+.2f")]), width="stretch")
    st.write(f"Yearly output varies by only {cv.cv_pct.min():.1f}-{cv.cv_pct.max():.1f}% between years; "
             f"the average change between the two periods is {chg.change.mean():+.2f}%.")

    st.subheader("4. How often does heat cut the output noticeably?")
    limit = st.slider("Heat-loss threshold (% of output)", 5, 20, 10)
    hot = core.hot_days(daily, limit / 100).sort_values(ascending=False).rename("days").reset_index()
    st.altair_chart(alt.Chart(hot).mark_bar().encode(
        y=alt.Y("governorate:N", sort=None, title=None), x=alt.X("days:Q", title=f"Days per year with more than {limit}% heat loss"),
        tooltip=["governorate", alt.Tooltip("days:Q", format=".0f")]), width="stretch")
    corr = daily[["ghi", "t_day", "t_cell", "heat_loss_day"]].corr().round(2)
    corr.index = corr.columns = ["Irradiance", "Air temp.", "Cell temp.", "Heat loss"]
    st.write("Correlation between daily variables:")
    st.dataframe(corr)
    st.caption(f"Heat loss follows cell temperature (r = {corr.loc['Cell temp.', 'Heat loss']:.2f}), "
               "which depends on both air temperature and sunshine.")

with tab_tariff:
    st.subheader("⚡ Official Syrian electricity tariffs (since 1 Nov 2025)")
    st.write("Four consumption tiers, billed every two months. The government still subsidises "
             "about 60 % of tier-1 (the actual production cost is ~$0.14/kWh).")
    st.dataframe(TARIFFS, hide_index=True)
    st.info("Reference: Ministry of Energy tiered pricing effective 1 Nov 2025 "
            "(reported by The National, 5 Nov 2025; Enab Baladi, 31 Oct 2025). "
            f"USD at ~{core.SYP_PER_USD:,} SYP/USD. Tariffs change - verify the latest decree before quoting.")
    st.subheader("How does solar compare?")
    ex_kwh = 5 * annual["mean"].mean()
    no_b, with_b = core.lcoe(5000, ex_kwh), core.lcoe(5000, ex_kwh, om_share=core.OM_SHARE)
    st.write(f"A 5 kW system with Syria's average sunshine (5,000 USD, no batteries) delivers solar power at roughly "
             f"**${no_b:.3f}/kWh** - below the tier-2 grid price of ~${GRID:.3f}/kWh and well below the real "
             f"production cost of the grid (~$0.14/kWh). With batteries the cost rises to about "
             f"**${with_b:.3f}/kWh** because of battery replacement.")
    st.caption("Note: grid supply is still rationed (about 8 hours/day in many areas), "
               "so the comparison is per-kWh only, not availability.")
# Syria SolarScope – Project Summary
**Team 8 · FTL Syria AI4Climate Python for Climate Hackathon · Challenge: Renewable energy and energy efficiency**

**Problem.** Severe electricity shortages push Syrian households and businesses toward solar power, but buyers have no location-specific estimate of how much a system will produce or what each kWh will really cost, so installations are often poorly sized and expensive.

**Question.** How do solar irradiance and temperature-adjusted PV output vary across Syria's 14 governorates and months (2015-2025), and what are the expected yield ranges and levelized cost of energy (LCOE) for standard system sizes at different upfront costs?

**Data.** NASA POWER daily data, 2015-2025 (`ALLSKY_SFC_SW_DWN`, `T2M`, `T2M_MAX`): 56,252 records for 14 governorates, no missing values. Syrian grid tariffs (Ministry of Energy, effective 1 Nov 2025) are used for comparison.

**Method (Python: pandas, numpy, requests, matplotlib, Streamlit).** Daily irradiance and temperature give the panel temperature, then the heat loss, then the daily yield per kWp (14 % other losses). Monthly and yearly yield with a P10–P90 range across years. Economics: LCOE over 20 years (8 % discount rate, 0.7 %/year degradation, O&M 2 % without / 10 % with batteries). Four analyses: ranking, seasonality and heat loss, year-to-year variability and trend, threshold days and correlation.

**Main findings.**
- Yearly yield ranges from 1,510 kWh/kWp (Aleppo) to 1,671 (As-Suwayda), a 10.7 % spread; Damascus: 1,652.
- Heat reduces annual output by 5.0-6.7 %; July is the worst month (10.0 % average loss), and Hasakah has the most days with more than 10 % loss (83 per year).
- Year-to-year variability is small (CV 1.4-2.5 %).
- 10 panels (5.5 kW, $5,000) in Damascus: about 9,080 kWh/year; LCOE $0.070/kWh without batteries (32 % below grid tier 2 at $0.104) and $0.117/kWh with batteries (about 12 % above the grid).
- Financial assumptions move LCOE far more than weather: O&M 2% to 10% raises it about 66 %, discount rate 4% to 12% about 62 %, year-to-year weather about 3 %.

**Solution.** A web-based decision-support tool (Streamlit app): the user picks a governorate, system size (kW or panels) and cost, and gets expected yearly output with a low–high range, heat loss, LCOE and a comparison with the grid tariffs.

**Limitations.** About 0.5° data resolution: Damascus/Rif Dimashq, Daraa/As-Suwayda and Hama/Idlib share one NASA grid cell (14 governorates, 11 distinct cells); horizontal-surface radiation; estimated panel temperature; dust and maintenance assumptions; changing USD prices and tariffs. Results are planning estimates, not a price quote.
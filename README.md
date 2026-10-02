# Syria SolarScope

Decision-support tool that estimates rooftop solar output and cost per kWh (LCOE) for Syria's 14 governorates and compares it with the official grid tariffs.
Built for the **FTL Syria AI4Climate Python for Climate Hackathon** (Team 8, challenge: Renewable energy and energy efficiency).

* **Notebook (analysis and figures):** `Syria_SolarScope.ipynb`. Colab: `https://colab.research.google.com/drive/1liyVEgR9G1190ANbxwsdQzFdRMhn2sRP?usp=sharing`
* **Web app:** (code: `app.py`)
* **Presentation:** `Frontier_Tech_Leaders_Syria_SolarScope.pptx`. **Summary:** `Project_Summary.md`

## Data
NASA POWER daily data, 2015-2025 (`ALLSKY_SFC_SW_DWN`, `T2M`, `T2M_MAX`) for 14 governorates: https://power.larc.nasa.gov/data-access-viewer/
`T2M_MAX` is added to the two core variables to estimate panel temperature.
The downloaded file is included: `power_syria_daily_2015_2025.csv` (56,252 rows).

## Files
| File | Purpose |
|---|---|
| `core.py` | Model: panel temperature, heat loss, yield, monthly/annual statistics, LCOE |
| `build_stats.py` | Downloads the NASA data, cleans it, writes `monthly_stats.csv` and `annual_stats.csv` |
| `app.py` | Streamlit app (reads the stats files and the daily data) |
| `test_core.py` | Small checks of the LCOE function and constants |
| `Syria_SolarScope.ipynb` | Full analysis: data inspection, cleaning, 4 analyses, LCOE vs grid, figures |
| `figures/` | Charts produced by the notebook |
| `requirements.txt` | Python packages |

## Run
```bash
pip install -r requirements.txt
python build_stats.py        # optional: re-download the data and rebuild the stats files
python test_core.py          # optional: sanity checks
streamlit run app.py
```

## Method in one paragraph
Daily irradiance and air temperature give the cell temperature (NOCT model), then the temperature loss, then the daily yield per kWp with 14 % other losses. Yearly yield is shown with a P10-P90 range across 2015-2025. LCOE = (capital cost + discounted O&M) / discounted lifetime energy, over 20 years at an 8 % discount rate with 0.7 %/year degradation. O&M is 2 % of cost per year, or 10 % with batteries. The grid reference is tier 2 of the Ministry of Energy tariff effective 1 Nov 2025: 1,400 SYP/kWh, about $0.104 at 13,500 SYP/USD.

## Main results
* Yearly yield: 1,510 kWh/kWp (Aleppo) to 1,671 (As-Suwayda); Damascus 1,652.
* Heat reduces annual output by 5.0-6.7 %; July is the worst month (10.0 %).
* 10 panels (5.5 kW, $5,000) in Damascus: about 9,080 kWh/year. LCOE is $0.070/kWh without batteries (about 32 % below grid tier 2 at $0.104) and $0.117 with batteries (about 12 % above the grid).

## Limitations
About 0.5 degree data resolution: Damascus/Rif Dimashq, Daraa/As-Suwayda and Hama/Idlib share one NASA grid cell (11 distinct cells for 14 governorates). Radiation is on a horizontal surface, panel temperature is estimated, and dust and maintenance are assumptions. USD prices and tariffs change. Planning estimates only, not a price quote.
import time
import numpy as np
import pandas as pd
import requests
import core

# name: (lat, lon) of each governorate centre
GOVS = {
    "Damascus": (33.51, 36.29), "Rif Dimashq": (33.57, 36.40), "Aleppo": (36.20, 37.16),
    "Homs": (34.73, 36.72), "Hama": (35.13, 36.75), "Latakia": (35.52, 35.79),
    "Tartus": (34.89, 35.89), "Idlib": (35.93, 36.63), "Deir ez-Zor": (35.34, 40.14),
    "Raqqa": (35.95, 39.01), "Hasakah": (36.50, 40.75), "Daraa": (32.62, 36.10),
    "As-Suwayda": (32.71, 36.57), "Quneitra": (33.13, 35.82),
}
START, END = 2015, 2025   # years to download
URL = "https://power.larc.nasa.gov/api/temporal/daily/point"

# one point, three variables: ghi, mean temp, max temp
def fetch(lat, lon, tries=3):
    p = dict(parameters="ALLSKY_SFC_SW_DWN,T2M,T2M_MAX", community="RE", latitude=lat,
             longitude=lon, start=f"{START}0101", end=f"{END}1231", format="JSON")
    for i in range(tries):
        try:
            r = requests.get(URL, params=p, timeout=120)
            r.raise_for_status()
            df = pd.DataFrame(r.json()["properties"]["parameter"])
            df.index = pd.to_datetime(df.index, format="%Y%m%d")
            return df.replace(-999, np.nan)
        except requests.RequestException:
            time.sleep(3 * (i + 1))
    raise RuntimeError(f"NASA POWER download failed for {lat},{lon}")

def main():
    frames = []
    for gov, (lat, lon) in GOVS.items():
        d = fetch(lat, lon)
        d["governorate"] = gov
        frames.append(d)
    raw = (pd.concat(frames).rename_axis("date").reset_index()
             .rename(columns={"ALLSKY_SFC_SW_DWN": "ghi", "T2M": "t_mean", "T2M_MAX": "t_max"}))
    raw.to_csv("power_syria_daily_2015_2025.csv", index=False)
    cols = ["ghi", "t_mean", "t_max"]
    print("missing values:\n", raw[cols].isna().sum())
    raw[cols] = raw.groupby("governorate")[cols].transform(lambda s: s.interpolate(limit=3))
    raw = raw.dropna(subset=cols)
    assert raw.ghi.between(0, 12).all(), "GHI out of physical range"
    d = core.add_physics(raw)
    d["year"], d["month"] = d.date.dt.year, d.date.dt.month
    ms, m = core.monthly_stats(d)
    a = core.annual_stats(m)
    ms.to_csv("monthly_stats.csv", index=False)
    a.to_csv("annual_stats.csv", index=False)
    core.daily_output(d).to_csv("daily_production_2015_2025.csv", index=False)
    print(a.sort_values("mean", ascending=False).round(3))

if __name__ == "__main__":
    main()
import numpy as np

# fixed inputs of the model
LIFETIME_YEARS = 20       # system life
DEGRADATION = 0.007       # panels lose 0.7% output each year
GAMMA = -0.0035           # power loss per degC above 25
OM_SHARE = 0.10           # yearly O&M as share of cost, with batteries
OM_NO_BATTERY = 0.02      # same but without batteries
DISCOUNT_RATE = 0.08
NOCT = 45.0               # panel operating temp, degC
DAYLIGHT_H = 12.0         # hours used to turn daily ghi into watts/m2
OTHER_LOSSES = 0.14       # inverter, wires, dust
PANEL_W = 550             # watt per panel

# grid price used for comparison (tier 2, SYP per kWh)
SYP_PER_USD = 13_500
GRID_TIER2_SYP = 1_400
GRID_TIER2_USD = GRID_TIER2_SYP / SYP_PER_USD

# df needs columns ghi (kWh/m2/day), t_mean, t_max (degC)
def add_physics(df):
    d = df.copy()
    d["t_day"] = (d.t_mean + d.t_max) / 2
    g = d.ghi * 1000 / DAYLIGHT_H
    d["t_cell"] = d.t_day + (NOCT - 20) / 800 * g
    d["f_temp"] = (1 + GAMMA * (d.t_cell - 25)).clip(upper=1.0)
    d["y_ideal"] = d.ghi * (1 - OTHER_LOSSES)
    d["y_real"] = d.y_ideal * d.f_temp
    return d

def _q(p):
    return lambda s: s.quantile(p)

def monthly_stats(d):
    m = d.groupby(["governorate", "year", "month"])[["y_ideal", "y_real"]].sum().reset_index()
    s = (m.groupby(["governorate", "month"])["y_real"]
           .agg(mean="mean", low=_q(.10), high=_q(.90)).reset_index())
    t = m.groupby(["governorate", "month"])[["y_ideal", "y_real"]].sum()
    s["heat_loss"] = (1 - t.y_real / t.y_ideal).values
    return s, m

def annual_stats(m):
    a = m.groupby(["governorate", "year"])[["y_ideal", "y_real"]].sum().reset_index()
    s = (a.groupby("governorate")["y_real"]
           .agg(mean="mean", low=_q(.10), high=_q(.90)))
    t = a.groupby("governorate")[["y_ideal", "y_real"]].sum()
    s["heat_loss"] = 1 - t.y_real / t.y_ideal
    s["cv"] = a.groupby("governorate")["y_real"].std() / s["mean"]
    return s.reset_index()

# capex in USD, e1_kwh = energy of the first year in kWh
def lcoe(capex, e1_kwh, rate=DISCOUNT_RATE, years=LIFETIME_YEARS,
         degr=DEGRADATION, om_share=OM_NO_BATTERY):
    if capex <= 0 or e1_kwh <= 0:
        return float("nan")
    t = np.arange(1, years + 1)
    disc = (1 + rate) ** t
    energy = e1_kwh * (1 - degr) ** (t - 1)
    return (capex + (om_share * capex / disc).sum()) / (energy / disc).sum()

def kw_from_panels(n, watt=PANEL_W):
    return n * watt / 1000

# daily table saved for the project: yield in kWh per kWp per day (y_real) and its steps
def daily_output(d):
    cols = ["date", "governorate", "ghi", "t_mean", "t_max", "t_cell", "f_temp", "y_ideal", "y_real"]
    out = d[cols].copy()
    out[cols[2:]] = out[cols[2:]].round(4)
    return out

# avg days per year on which temperature costs more than `limit` of the output
def hot_days(d, limit=0.10):
    flag = (1 - d.f_temp) > limit
    return flag.groupby([d.governorate, d.year]).sum().groupby("governorate").mean()

# % change of yearly yield between two periods (needs columns governorate, year, y_real)
def period_change(d, early=(2015, 2019), late=(2021, 2025)):
    y = d.groupby(["governorate", "year"])["y_real"].sum().reset_index()
    a = y[y.year.between(*early)].groupby("governorate")["y_real"].mean()
    b = y[y.year.between(*late)].groupby("governorate")["y_real"].mean()
    return (b / a - 1) * 100

# governorates whose irradiance series are identical = same NASA grid cell
def shared_cells(d):
    p = d.pivot(index="date", columns="governorate", values="ghi")
    groups = {}
    for g in p.columns:
        groups.setdefault(p[g].round(4).to_numpy().tobytes(), []).append(g)
    return [v for v in groups.values() if len(v) > 1]
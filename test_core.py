"""Quick checks of the model. Run: python test_core.py"""
import math
import core

# 1) With no discounting, no degradation and no O&M, LCOE = capex / (yearly energy x years)
v = core.lcoe(5000, 9000, rate=0.0, degr=0.0, om_share=0.0)
assert math.isclose(v, 5000 / (9000 * core.LIFETIME_YEARS)), v

# 2) More O&M or a higher discount rate must raise the cost per kWh
base = core.lcoe(5000, 9000)
assert core.lcoe(5000, 9000, om_share=0.10) > base
assert core.lcoe(5000, 9000, rate=0.12) > base

# 3) Invalid inputs return NaN
assert math.isnan(core.lcoe(0, 9000)) and math.isnan(core.lcoe(5000, 0))

# 4) 10 panels of 550 W = 5.5 kW
assert math.isclose(core.kw_from_panels(10), 5.5)

# 5) Exchange rate and grid price are consistent (1,400 SYP at 13,500 SYP/USD = about $0.104)
assert abs(core.GRID_TIER2_USD - 0.104) < 0.001

print("All checks passed")
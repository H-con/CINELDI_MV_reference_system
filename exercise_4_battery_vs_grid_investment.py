# -*- coding: utf-8 -*-
# ---
# jupyter:
#   jupytext:
#     cell_metadata_filter: title,-all
#     formats: ipynb,py:percent
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.19.5
#   kernelspec:
#     display_name: cineldi-mv-reference-system (3.14.x)
#     language: python
#     name: python3
# ---

# %% [markdown]
#
# ## Script for Exercise 4 ("Battery energy storage system in the grid vs. grid investments") 
#
# Intro script for Exercise 4 in specialization course module 
# "Flexibility in power grid operation and planning" at NTNU (TET4565/TET4575) 


# %%
# Dependencies

import pandas as pd
import os
import load_profiles as lp
import pandapower_read_csv as ppcsv
import matplotlib.pyplot as plt
import numpy as np


# %%
# Define input data

# Location of (processed) data set for CINELDI MV reference system
# (to be replaced by your own local data folder)
path_data_set         = 'D:\\EMIL\\CINELDI_MV_reference_system\\data_sets'

filename_load_data_fullpath = os.path.join(path_data_set,'load_data_CINELDI_MV_reference_system.csv')
filename_load_mapping_fullpath = os.path.join(path_data_set,'mapping_loads_to_CINELDI_MV_reference_grid.csv')
filename_standard_overhead_lines = os.path.join(path_data_set,'standard_overhead_line_types.csv')
filename_reldata = os.path.join(path_data_set,'reldata_for_component_types.csv')
filename_load_point = os.path.join(path_data_set,'CINELDI_MV_reference_system_load_point.csv')

# Subset of load buses to consider in the grid area, considering the area at the end of the main radial in the grid
bus_i_subset = [90, 91, 92, 96]

# Assumed power flow limit in MW that limit the load demand in the grid area (through line 85-86)
P_lim = 4

# Factor to scale the loads for this exercise compared with the base version of the CINELDI reference system data set
scaling_factor = 10

# Read standard data for overhead lines
data_standard_overhead_lines = pd.read_csv(filename_standard_overhead_lines, delimiter=';')
data_standard_overhead_lines.set_index(keys = 'type', drop = True, inplace = True)

# Read standard component reliability data
data_comp_rel = pd.read_csv(filename_reldata, delimiter=';')
data_comp_rel.set_index(keys = 'main_type', drop = True, inplace = True)

# Read load point data (incl. specific rates of costs of energy not supplied) for data
data_load_point = pd.read_csv(filename_load_point, delimiter=';')
data_load_point.set_index(keys = 'bus_i', drop = True, inplace = True)


# %%
# Read pandapower network

net = ppcsv.read_net_from_csv(path_data_set, baseMVA=10)


# %% Set up hourly normalized load time series for a representative day (task 2; this code is provided to the students)

load_profiles = lp.load_profiles(filename_load_data_fullpath)

# Consider only the day with the peak load in the area (28 February)
repr_days = [31+28]

all_days = list(range(1, 366))

# Get relative load profiles for representative days mapped to buses of the CINELDI test network;
# the column index is the bus number (1-indexed) and the row index is the hour of the year (0-indexed)
profiles_mapped = load_profiles.map_rel_load_profiles(filename_load_mapping_fullpath,repr_days)

# Calculate load time series in units MW (or, equivalently, MWh/h) by scaling the normalized load time series by the
# maximum load value for each of the load points in the grid data set (in units MW); the column index is the bus number
# (1-indexed) and the row index is the hour of the year (0-indexed)
load_time_series_mapped = profiles_mapped.mul(net.load['p_mw'])


# %%
# Aggregate the load demand in the area

# Aggregated load time series for the subset of load buses
load_time_series_subset = load_time_series_mapped[bus_i_subset] * scaling_factor
load_time_series_subset_aggr = load_time_series_subset.sum(axis=1)

P_max = load_time_series_subset_aggr.max()
print(P_max)

# %%

#Input deifinitions for the analysis
annual_growth_rate = 0.03  # 3% increase in load demand each year
planning_horizon = list(range(0, 11)) # 10 years of analysis
P_limit = 4.0 #Power flow limit of line 85-86 in MW
analysis_horizon = list(range(0,21)) # 20 years of analysis
lifetime_new_line = 40 #40 years of economic lifetime for new distibution
discount_rate = 0.04 
P_battery = 1.0 #Battery power capacity in MW
E_battery = 2.0 #Battery energy capacity in MWh
battery_cost_shifting = 2000  #NOK/MWh of shifted energy
P_avg = load_time_series_subset_aggr.mean() #Average load demand in MW
length_main_feeder = 20 #km


# %%

#Task 2: Calculating and plotting the peak load demand for each year in the planning horizon, considering the annual growth rate
load_demand_years = [] # List to store the peak load demand for each year
yearly_scaling_factors = [] # List to store the scaling factors for each year

for year in planning_horizon:
    #Add the peak load demand for each year to a list
    extra_scaling_factor = (1 + annual_growth_rate) ** year
    yearly_scaling_factors.append(extra_scaling_factor)
    peak_load_year = P_max * extra_scaling_factor
    load_demand_years.append(peak_load_year)
    print(f"Year {year+1}: Peak Load Demand = {peak_load_year:.2f} MW\nScaling factor: {yearly_scaling_factors[year]}")



plt.figure(figsize=(10, 5))
plt.step(planning_horizon, load_demand_years, where='post', label='Annual peak load demand (MW)', linewidth=2)

plt.axhline(y=P_limit, color='red', linestyle='--',
            linewidth=2, label='Power flow limit of line 85-86 (4 MW)')

plt.axhline(y = P_limit + 1, color = 'green', linestyle='--', linewidth = 2, label = 'Power flow limit including battery (5 MW)')

plt.title('Peak Load Demand Over Time')
plt.xlabel('t (years)')
plt.ylabel('Peak Load Demand (MW)')
plt.legend()
plt.grid(True)
plt.xticks(planning_horizon)
plt.xlim(0, 10)
plt.ylim(0, max(load_demand_years) * 1.1)
plt.show()


#%% 

#Debugging the data set for standard overhead lines
print(data_standard_overhead_lines.columns.tolist())
print(data_standard_overhead_lines.head())

for idx in data_standard_overhead_lines.index:
    print(repr(idx))
# %%


line_type_old = "40-AL1/7-ST1A (FeAl nr. 25 6/1)"
line_type_new = "111-AL1/19-ST1A (FeAl nr. 70 6/1)"



price_new_line = data_standard_overhead_lines.loc[line_type_new, 'cost_NOK_per_km'] * length_main_feeder
print(f"Price of new line (type {line_type_new}) for {length_main_feeder} km: {price_new_line:.2f} NOK")

#%%

#Present value
#Calculating the present value of the cost of the new line, considering the discount rate and installation at the beginning of year 2
year_of_investment = 9

present_value_new_line = price_new_line / ((1 + discount_rate) ** year_of_investment)
print(f"Present value of the cost of the new line in year (t) {year_of_investment}: {present_value_new_line:.2f} NOK")

#%%

#Residual Value
years_in_use = analysis_horizon[-1] - year_of_investment 
residual_value_new_line = price_new_line * (years_in_use / lifetime_new_line)
print(f"Residual value of the new line after 20 years: {residual_value_new_line:.2f} NOK")

corrected_present_value_new_line = present_value_new_line - residual_value_new_line
print(f"Corrected present value of the new line after considering residual value: {corrected_present_value_new_line:.2f} NOK")


#%% 

#Investigating for how long the battery can postpone grid investments
#Reusing code from ex. 3

#Scaling load to the relevant year.
#The peak load is on feb. 28th between 11 and 12.
#The battery can supply 1 MW over 2 hours (2 MWh)
investigated_year = 6
load_time_series_subset_aggr_scaled = load_time_series_subset_aggr * yearly_scaling_factors[investigated_year]



dt = 1.0  # Hour

load = load_time_series_subset_aggr_scaled.to_numpy()
hours = np.arange(len(load) + 1)

# Battery starts fully charged
E = E_battery

energy = [E]

dispatch = []

for P_load in load:

    P_required = P_load - P_limit

    if P_required > 0:
        # Discharge battery (positive dispatch)
        P = min(P_required, P_battery, E / dt)

    else:
        # Charge battery (negative dispatch)
        P = -min(
            -P_required,
            P_battery,
            (E_battery - E) / dt
        )

    E -= P * dt

    dispatch.append(P)
    energy.append(E)

dispatch = np.array(dispatch)
energy = np.array(energy)

# Actual power drawn from grid
P_grid = load - dispatch

# Extend arrays for staircase plotting
load_step = np.append(load, load[-1])
grid_step = np.append(P_grid, P_grid[-1])

plt.figure(figsize=(11, 5))

# Original aggregated load (dashed blue)
plt.step(
    hours, load_step, where='post',
    color='blue', linestyle='--', linewidth=1.5,
    label='Original aggregated load demand'
)

# Actual grid power after battery dispatch (solid blue)
plt.step(
    hours, grid_step, where='post',
    color='blue', linewidth=2, zorder = 3,
    label='Actual grid power'
)

# Backup feeder capacity
plt.axhline(
    P_limit, color='red', linestyle='--',
    linewidth=2, zorder = 1,
    label='Power Flow Capacity of line 85-86'
)

# Battery discharging (red)
plt.fill_between(
    hours,
    grid_step,
    np.maximum(load_step, grid_step),
    step='post',
    color='red', alpha=0.3,
    label='Battery discharging'
)

# Battery charging (green)
plt.fill_between(
    hours,
    load_step,
    np.maximum(grid_step, load_step),
    step='post',
    color='limegreen', alpha=0.3,
    label='Battery charging'
)


plt.xlabel('Hour of day')
plt.ylabel('Power [MW]')
plt.title(f'Battery Dispatch – February 28 (Year: {investigated_year})')

plt.xticks(np.arange(0, len(load) + 1, 2))
plt.xlim(0, len(load))
plt.grid(True, alpha=0.3)
plt.legend()


# Battery State of Charge (SoC)

SoC = energy / E_battery * 100

# Create secondary y-axis
ax2 = plt.gca().twinx()

# Plot battery SoC
ax2.plot(
    hours, SoC,
    color='green',
    linewidth=2,
    label='Battery SoC',
    zorder=5
)

# Configure secondary y-axis
ax2.set_ylabel('Battery State of Charge [%]', color='green')
ax2.set_ylim(0, 100)
ax2.set_yticks(np.arange(0, 101, 20))
ax2.tick_params(axis='y', labelcolor='green')

# Combine legends from both axes
ax1 = plt.gca()
lines1, labels1 = ax1.get_legend_handles_labels()


ax1.legend(lines1, labels1, loc='upper right')

plt.tight_layout()
plt.show()

# %%

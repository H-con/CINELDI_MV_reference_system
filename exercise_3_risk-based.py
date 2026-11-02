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
# ## Script for Exercise 3 ("Risk-based grid operation") 
#
# Intro script for Exercise 3 in specialization course module 
# "Flexibility in power grid operation and planning" at NTNU (TET4565/TET4575) 


# %%
# Dependencies

import os
import pandas as pd
import load_profiles as lp
import pandapower_read_csv as ppcsv
import matplotlib.pyplot as plt
import matplotlib as mpl
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

# Factor to scale the loads for this exercise compared with the base version of the CINELDI reference system data set
scaling_factor = 10

# Read standard component reliability data
data_comp_rel = pd.read_csv(filename_reldata, delimiter=';')
data_comp_rel.set_index(keys = 'main_type', drop = True, inplace = True)

# Read load point data (incl. specific rates of costs of energy not supplied) for data
data_load_point = pd.read_csv(filename_load_point, delimiter=';')
data_load_point.set_index(keys = 'bus_i', drop = True, inplace = True)

# %%
# Read pandapower network

net = ppcsv.read_net_from_csv(path_data_set, baseMVA=10)

# %%
# Set up hourly normalized load time series for a representative day

load_profiles = lp.load_profiles(filename_load_data_fullpath)

# Consider only the day with the peak load in the area (28 February)
repr_days = [31+28]

all_days = list(range(1,366))

# Get relative load profiles for representative days mapped to buses of the CINELDI test network;
# the column index is the bus number (1-indexed) and the row index is the hour of the year (0-indexed)
profiles_mapped = load_profiles.map_rel_load_profiles(filename_load_mapping_fullpath,repr_days)

# Calculate load time series in units MW (or, equivalently, MWh/h) by scaling the normalized load time series by the
# maximum load value for each of the load points in the grid data set (in units MW); the column index is the bus number
# (1-indexed) and the row index is the hour of the year (0-indexed)
load_time_series_mapped = profiles_mapped.mul(net.load['p_mw'])

# Aggregated load time series for the subset of load buses
load_time_series_subset = load_time_series_mapped[bus_i_subset] * scaling_factor
load_time_series_subset_aggr = load_time_series_subset.sum(axis=1)



# %%

#Average reliablility data for the MF (Overhead line)

lambda_perm_OH = data_comp_rel.loc['Overhead line (1–22 kV)','lambda_perm'] #permanent failure rate [failures/year]. Defined per 100km of line lenght
lambda_temp_OH = data_comp_rel.loc['Overhead line (1–22 kV)','lambda_temp'] #temporary failure rate [failures/year]. Defined per 100km of line lenght
r_perm_OH = data_comp_rel.loc['Overhead line (1–22 kV)','r_perm'] #permanent repair time [h/failure] 
r_temp_OH = data_comp_rel.loc['Overhead line (1–22 kV)','r_temp'] #temporary repair time [h/failure]

lambda_perm_MF = 0.2 * lambda_perm_OH #permanent failure rate for 20km main feeder [failures/year].
lambda_temp_MF = 0.2 * lambda_temp_OH #temporary failure rate for 20km main feeder [failures/year].

#Average area load demand

avg_load_demand = 1.841 #MW

#Expected annual energy not supplied

EENS_perm = lambda_perm_MF * avg_load_demand * r_perm_OH # [MWh/year]
EENS_temp = lambda_temp_MF * avg_load_demand * r_temp_OH # [MWh/year]

print('Expected annual energy not supplied due to permanent failures in the main feeder: ', EENS_perm, 'MWh/year')
print('Expected annual energy not supplied due to temporary failures in the main feeder: ', EENS_temp, 'MWh/year')
# %%

#Cost of energy not supplied (CENS) for the load point in the area
#First splitting the EENS into the different load points in the area, based on their average load demand
#Then multiplying the EENS for each load point with the specific rate of CENS for that load point
#Doing this as there are different rates of CENS for the different load points in the area

# Annual average load demand for each bus
avg_load_per_bus = load_time_series_subset.mean(axis=0)

# Total annual average load demand
avg_load_total = avg_load_per_bus.sum()


#Individual EENS for each bus, assuming that the EENS is distributed proportionally to the average load demand of each bus
#and that there are no failures in the distribution grid behind the main feeder

EENS_perm_per_bus = EENS_perm * (avg_load_per_bus / avg_load_total)
EENS_temp_per_bus = EENS_temp * (avg_load_per_bus / avg_load_total)

CENS_perm_per_bus = EENS_perm_per_bus * data_load_point.loc[bus_i_subset,'c_NOK_per_kWh_4h'] *1000 # [NOK/year]

print('Expected annual cost of energy not supplied due to permanent failures in the main feeder: ', CENS_perm_per_bus.sum(), 'NOK/year')    
# %%

#Measure A: Adding a 2 MWh battery at bus 88.
#As the temporary faults are over in a short time, these fall away completely with the addition of a battery. Therefore, we only need to consider the permanent faults in the main feeder.
#Each permanent faults last for 3 hours at 1.841 MW, which is 5.523 MWh. Therefore, a 2 MWh battery will cover 36% of the energy not supplied due to permanent faults in the main feeder.

EENS_per_fault_with_battery = 3. * avg_load_demand - 2. # [MWh/fault]
EENS_per_fault_without_battery = 3. * avg_load_demand # [MWh/fault]

EENS_perm_with_battery = lambda_perm_MF * EENS_per_fault_with_battery # [MWh/year]


print(EENS_perm)
print('Expected annual energy not supplied due to permanent failures in the main feeder with a 2 MWh battery: ', EENS_perm_with_battery, 'MWh/year')

EENS_per_bus_with_battery = EENS_perm_with_battery * (avg_load_per_bus / avg_load_total)
CENS_per_bus_with_battery = EENS_per_bus_with_battery * data_load_point.loc[bus_i_subset,'c_NOK_per_kWh_4h'] *1000 # [NOK/year]

print('Expected annual cost of energy not supplied due to permanent failures in the main feeder with a 2 MWh battery: ', CENS_per_bus_with_battery.sum(), 'NOK/year')



# %%
# Plot aggregated load demand for February 28

load = load_time_series_subset_aggr.to_numpy()

# Create time axis based on actual number of values
hours = np.arange(len(load) + 1)

# Extend load to cover the final interval
load_step = np.append(load, load[-1])

P_limit = 3.5  # MW

plt.figure(figsize=(10, 5))

plt.step(hours, load_step, where='post',
         label='Aggregated load demand', linewidth=2)

plt.axhline(y=P_limit, color='red', linestyle='--',
            linewidth=2, label='Backup feeder capacity (3.5 MW)')

plt.fill_between(
    hours,
    P_limit,
    np.maximum(load_step, P_limit),
    step='post',
    color='red',
    alpha=0.3,
    label='Load exceeding backup capacity'
)

plt.xlabel('Hour of day')
plt.ylabel('Load demand [MW]')
plt.title('Aggregated Load Demand – February 28')
plt.xticks(np.arange(0, len(hours), 2))
plt.xlim(0, len(load))
plt.grid(True, alpha=0.3)
plt.legend()
plt.tight_layout()
plt.show()
# %%

# Calculate ENS per bus using proportional load shedding

P_limit = 3.5  # MW

# Total load exceeding backup feeder capacity
P_excess = (load_time_series_subset_aggr - P_limit).clip(lower=0)

# Fraction of load that cannot be supplied each hour
load_shedding_fraction = (
    P_excess / load_time_series_subset_aggr.replace(0, np.nan)
).fillna(0)

# Unsupplied power at each bus [MW]
P_unsupplied = load_time_series_subset.mul(
    load_shedding_fraction, axis=0
)

# Energy not supplied per bus [MWh]
# Assuming hourly time steps
EENS_backup_per_bus = P_unsupplied.sum(axis=0)

print("Energy not supplied per bus:")
print(EENS_backup_per_bus)

print(f"\nTotal ENS: {EENS_backup_per_bus.sum():.4f} MWh")

#Calculating the expected annual cost of energy not supplied due to overlaoding the backup feeder.
#Preferably the perdiods should be split in two, one for the 5 hour period and one for the one hour period.
#For simplicity, these are combined into one period of of 6 hours, using the coresponding rate for 4 hours.

CENS_backup_WC = EENS_backup_per_bus * data_load_point.loc[bus_i_subset,'c_NOK_per_kWh_4h'] *1000 # [NOK/year]
print('Worst case scenario CENS due to overloading the backup feeder \nwhithout the main feeder on the highest load day, February 28th:',CENS_backup_WC.sum(), 'NOK')

#Chance of failure in the main feeder on February 28th, assuming that the failure rate is constant throughout the year and that the failures are independent of the load level.

lambda_perm_MF_per_day = lambda_perm_MF / 365 #permanent failure rate for 20km main feeder [failures/day].
print('Chance of permanent failure in the main feeder on February 28th: ', lambda_perm_MF_per_day * 100, '%')
CENS_backup_daily = CENS_backup_WC * lambda_perm_MF_per_day
print('Expected daily cost of energy not supplied due to overloading the backup feeder \nwhithout the main feeder on the highest load day, February 28th:',CENS_backup_daily.sum(), 'NOK')

# %%

#Calculating the new failure frequency that would result in an expected daily cost of energy not supplied of 3000 NOK.
daily_chance = lambda_perm_MF_per_day
CENS_daily = CENS_backup_daily.sum()

while CENS_daily < 3000:
    daily_chance += 0.0002
    CENS_daily = CENS_backup_WC.sum() * (daily_chance)

print('Percentage change of failure that would result in an expected daily cost of energy not supplied of 3000 NOK:', daily_chance * 100, '%')

# %%
# Task 5: Battery dispatch visualization

P_limit = 3.5  # MW
P_battery = 1.0  # MW
E_battery = [2.0, 1.4, 1.0]  # MWh

battery_capacity = E_battery[2]  # Select battery case
dt = 1.0  # Hour

load = load_time_series_subset_aggr.to_numpy()
hours = np.arange(len(load) + 1)

# Battery starts fully charged
E = battery_capacity

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
            (battery_capacity - E) / dt
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



# %%
# Plot load demand and battery dispatch

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
    label='Backup feeder capacity (3.5 MW)'
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
plt.title(f'Battery Dispatch – February 28 ({battery_capacity} MWh)')

plt.xticks(np.arange(0, len(load) + 1, 2))
plt.xlim(0, len(load))
plt.grid(True, alpha=0.3)
plt.legend()


# Battery State of Charge (SoC)

SoC = energy / battery_capacity * 100

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
# Check N-1 criterion and battery state of charge

print(f"Battery capacity: {battery_capacity} MWh")
print(f"Minimum stored energy: {energy.min():.3f} MWh")
print(f"Final stored energy: {energy[-1]:.3f} MWh")

if np.all(P_grid <= P_limit + 1e-9):
    print("N-1 criterion satisfied")
else:
    print("N-1 criterion NOT satisfied")
    print("Hours with violations:",
          np.where(P_grid > P_limit + 1e-9)[0])

# %%

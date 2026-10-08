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
#     display_name: cineldi-mv-reference-system (3.14.6.final.0)
#     language: python
#     name: python3
# ---

# %% [markdown]
# # Script for Exercise 2 ("Load analysis to evaluate the need for flexibility")
#
# Intro script for Exercise 2 in specialization course module 
# "Flexibility in power grid operation and planning" at NTNU (TET4565/TET4575) 


# %%
# Dependencies

import pandapower as pp
import pandapower.plotting as pp_plotting
import pandas as pd
import os
import load_scenarios as ls
import load_profiles as lp
import pandapower_read_csv as ppcsv
import matplotlib.pyplot as plt
import matplotlib as mpl
import numpy as np


# %%
# Define input data

# Location of (processed) data set for CINELDI MV reference system
# (to be replaced by your own local data folder)
path_data_set         = 'C:\\Koding\\PSOA\\CINELDI_MV_reference_system\\data_sets'
filename_load_data_fullpath = os.path.join(path_data_set,'load_data_CINELDI_MV_reference_system.csv')
filename_load_mapping_fullpath = os.path.join(path_data_set,'mapping_loads_to_CINELDI_MV_reference_grid.csv')

# Subset of load buses to consider in the grid area, considering the area at the end of the main radial in the grid
bus_i_subset = [90, 91, 92, 96]

# Assumed power flow limit in MW that limit the load demand in the grid area (through line 85-86)
P_lim = 0.637 

# Maximum load demand of new load being added to the system
P_max_new = 0.4

# Which time series from the load data set that should represent the new load
i_time_series_new_load = 90


# %%
# Read pandapower network

net = ppcsv.read_net_from_csv(path_data_set, baseMVA=10)

# %%
# Extract hourly load time series for a full year for all the load points in the CINELDI reference system
# (this code is made available for solving task 3)

load_profiles = lp.load_profiles(filename_load_data_fullpath)

# Get all the days of the year
repr_days = list(range(1,366))

# Get normalized load profiles for representative days mapped to buses of the CINELDI reference grid;
# the column index is the bus number (1-indexed) and the row index is the hour of the year (0-indexed)
profiles_mapped = load_profiles.map_rel_load_profiles(filename_load_mapping_fullpath,repr_days)

# Retrieve normalized load time series for new load to be added to the area
new_load_profiles = load_profiles.get_profile_days(repr_days)
new_load_time_series = new_load_profiles[i_time_series_new_load]*P_max_new

# Calculate load time series in units MW (or, equivalently, MWh/h) by scaling the normalized load time series by the
# maximum load value for each of the load points in the grid data set (in units MW); the column index is the bus number
# (1-indexed) and the row index is the hour of the year (0-indexed)
load_time_series_mapped = profiles_mapped.mul(net.load['p_mw'])
# %%

pp.runpp(net,init='results',algorithm='bfsw')
print('Total load demand in the system assuming a peak load model: ' + str(net.res_load['p_mw'].sum()) + ' MW')
# %%

# Plotting voltage profile for the system
pp_plotting.pf_res_plotly(net)
# %%
#Creating the new load as a static load in the system (not as a time series)
new_load_static = pd.Series(P_max_new, index=load_time_series_mapped.index)

load_demand_area = load_time_series_mapped[bus_i_subset].sum(axis=1) + new_load_time_series #+ new_load_static
load_demand_area.plot(figsize=(12, 5), color='tab:blue', label='Aggregated load demand in area')

# A load duration curve is obtained by sorting the hourly load values from highest to lowest,
# so the x-axis becomes the duration (how many hours the load is above a given level).
load_duration_curve = load_demand_area.sort_values(ascending=False).reset_index(drop=True)

ax = load_duration_curve.plot(
    figsize=(12, 5),
    color='tab:green',
    linewidth=2,
    label='Load duration curve',
    title='Load duration curve for buses 90, 91, 92 and 96 with new dynamic load',
    xlabel='Duration [hours]',
    ylabel='Load demand [MW]'
)
ax.axhline(P_lim, color='tab:red', linestyle='--', linewidth=1.5, label=f'Power-flow limit = {P_lim} MW')
ax.legend()
ax.grid(True, alpha=0.3)

# The sorted series can also be used directly for threshold checks, e.g. how many hours the area load exceeds the line limit
hours_above_limit = (load_demand_area > P_lim).sum()
print(f'Number of hours with load above the limit: {hours_above_limit}')

# %%

#Finding the peak load demand in the area
peak_load_demand = load_time_series_mapped[bus_i_subset].sum(axis=1).max() + new_load_time_series.max()
print(f'Peak load demand in the area: {peak_load_demand} MW')

bus_loads = load_time_series_mapped[bus_i_subset] 
print(bus_loads.head())  # Display the first few rows of the bus loads DataFrame
bus_peak_loads = bus_loads.max()          # per-bus peak demand

P_max_possible_area = bus_peak_loads.sum()
print(f'Maximum possible load demand in the area: {P_max_possible_area} MW')



# %%

#Calculating the coincidence factor for the area load 

alpha = peak_load_demand / P_max_possible_area
print(f'Coincidence factor for the area load: {alpha:.3f}')
# %%

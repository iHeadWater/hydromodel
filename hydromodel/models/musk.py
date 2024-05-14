import xarray as xr
import os
import numpy as np
from muskingumcunge.reach import TrapezoidalReach
from hydromodel.models.model_config import read_model_param_dict
from hydromodel.datasets import *

def Musk(inflows, mannings_n, length):
    bottom_width, side_slope, slope = 100, 100, 0.01
    reach = TrapezoidalReach(bottom_width, side_slope, mannings_n, slope, length)
    outflows = np.array(reach.route_hydrograph(inflows, 0.1))
    return outflows

def MuskEvaluate(qsim, qin, params, param_range_file, data_dir):
    # mannings
    param_ranges = read_model_param_dict(param_range_file)["xaj"]["param_range"]
    xaj_params = [(value[1] - value[0]) * params[:, i] + value[0] for i, (key, value) in enumerate(param_ranges.items())]
    mannings = xaj_params[15]
    # length
    len_name = remove_unit_from_name(LEN_NAME)
    flow_name = remove_unit_from_name(FLOW_NAME)  
    nodeflow_name = remove_unit_from_name(NODE_FLOW_NAME)
    attr_data = xr.open_dataset(os.path.join(data_dir, "attributes.nc"))
    musklen = np.array(attr_data[len_name].values) * 1000
    # musk
    for i in range(len(musklen)):
        inflows = qin[nodeflow_name][i].values
        muskflow = Musk(inflows, mannings[i], musklen[i])
        qsim[flow_name][:, i] = qsim[flow_name][:, i] + muskflow
    return qsim

def MuskCali(sim, qin, params, param_range_file, data_dir, basin_index):
    # mannings
    param_range_file = param_range_file["param_range_file"]
    param_ranges = read_model_param_dict(param_range_file)["xaj"]["param_range"]
    xaj_params = [(value[1] - value[0]) * params[:, i] + value[0] for i, (key, value) in enumerate(param_ranges.items())]
    mannings = xaj_params[15]
    # length
    len_name = remove_unit_from_name(LEN_NAME)
    area_name = remove_unit_from_name(AREA_NAME)
    flow_name = remove_unit_from_name(FLOW_NAME)  
    nodeflow_name = remove_unit_from_name(NODE_FLOW_NAME)
    attr_data = xr.open_dataset(os.path.join(data_dir, "attributes.nc"))
    musklen = np.array(attr_data[len_name].values) * 1000
    area = np.array(attr_data[area_name].values) * 1000000
    inflow = np.array(qin/1000/3600*area[basin_index]).flatten()
    muskflow = Musk(inflow, mannings, musklen[basin_index])
    muskflow = muskflow.reshape(len(muskflow), 1, 1)
    sim = muskflow/area[basin_index]*3600*1000 + sim
    return sim
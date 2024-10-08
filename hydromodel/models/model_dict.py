"""
Author: Wenyu Ouyang
Date: 2024-03-23 08:25:49
LastEditTime: 2024-03-26 20:41:22
LastEditors: Wenyu Ouyang
Description: LOSS_DICT and MODEL_DICT
FilePath: \hydro-model-xaj\hydromodel\models\model_dict.py
Copyright (c) 2023-2024 Wenyu Ouyang. All rights reserved.
"""

import numpy as np
from spotpy.objectivefunctions import rmse

from hydromodel.models.semi_xaj import semi_xaj
from hydromodel.models.xaj import xaj
from hydromodel.models.gr4j import gr4j
from hydromodel.models.hymod import hymod


def rmse43darr(obs, sim):
    """RMSE for 3D array

    Parameters
    ----------
    obs : np.ndarray
        observation data
    sim : np.ndarray
        simulation data

    Returns
    -------
    _type_
        _description_

    Raises
    ------
    ValueError
        _description_
    """
    # print('--------------------shape--------------------------')
    # print(sim.shape)
    sim_N = np.squeeze(sim)
    obs_N = np.squeeze(obs)
    # print(obs.shape)
    # print(obs[0])
    # rmses = np.sqrt(np.nanmean((sim - obs) ** 2, axis=0))
    # rmse = rmses.mean(axis=0)
    rmse = np.sqrt(np.nanmean((sim_N - obs_N) ** 2, axis=0))
    np.savetxt("sim.txt", sim_N)
    np.savetxt("obs.txt", obs_N)
    print('--------------------rmse--------------------------')
    print('rmse', rmse)
    if np.isnan(rmse) or any(np.isnan(sim)):
        raise ValueError(
            "RMSE is nan or there are nan values in the simulation data, please check the input data."
        )
    # tolist is necessary for spotpy to get the value
    # otherwise the print will incur to an issue https://github.com/thouska/spotpy/issues/319
    return rmse.tolist()


LOSS_DICT = {
    "RMSE": rmse43darr,
    "spotpy_rmse": rmse,
}

MODEL_DICT = {
    "xaj_mz": xaj,
    "xaj": xaj,
    "gr4j": gr4j,
    "hymod": hymod,
    "semi_xaj": semi_xaj,
}

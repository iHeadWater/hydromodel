import os
from typing import Union
import numpy as np
import spotpy
import pandas as pd
from spotpy.parameter import Uniform, ParameterSet
from hydromodel.models.model_config import read_model_param_dict
from hydromodel.models.model_dict import LOSS_DICT, MODEL_DICT
from hydromodel.models.musk import Musk 
import netCDF4



class SpotSetup(object):
    def __init__(
        self, p_and_e, qobs, warmup_length=365, model=None, param_file=None, loss=None, basin_index=None, data_dir=None, qin=None
    ):
        if model is None:
            model = {
                "name": "xaj_mz",
                "source_type": "sources5mm",
                "source_book": "HF",
                "time_interval_hours": 1,
            }
        if loss is None:
            loss = {
                "type": "time_series",
                "obj_func": "rmse",
                "events": None,
            }
        self.param_range_file = {"param_range_file": param_file}
        self.param_range = read_model_param_dict(param_file)
        self.parameter_names = self.param_range[model["name"]]["param_name"]
        self.model = model
        self.params = []
        self.params.extend(
            Uniform(par_name, low=0.0, high=1.0) for par_name in self.parameter_names
        )
        self.loss = loss
        self.p_and_e = p_and_e
        self.true_obs = qobs[warmup_length:, :, :]
        self.warmup_length = warmup_length
        self.basin_index = basin_index
        self.data_dir = data_dir
        self.qin = qin

    def parameters(self):
        return spotpy.parameter.generate(self.params)

    def simulation(self, x: ParameterSet) -> Union[list, np.array]:
        # Here the model is started with one parameter combination
        # parameter, 2-dim variable: [basin=1, parameter]
        params = np.array(x).reshape(1, -1)
        sim1, _ = MODEL_DICT[self.model["name"]](self.p_and_e,params,warmup_length=self.warmup_length,**self.model,**self.param_range_file)

        data = netCDF4.Dataset(os.path.join(self.data_dir, "attributes.nc"))
        datatime = netCDF4.Dataset(os.path.join(self.data_dir, "timeseries.nc"))
        time_interval_hours = int(self.model["time_interval_hours"]) if "time_interval_hours" in self.model else 1
        area, area2 = data.variables['area'][self.basin_index], data.variables['area2'][self.basin_index]
        area1 = area-area2
        simu = sim1.copy()
        simu = np.array(simu*area1/(3600*time_interval_hours*1000/1000000)).flatten()  # 上游新安江流量
        qin = np.array(self.qin*area/(3600*time_interval_hours*1000/1000000)).flatten()[self.warmup_length:]   # 节点流量
        simu = np.where(np.isnan(qin), simu, qin)  # 如果有节点用节点，否则新安江
        param_ranges = self.param_range[self.model['name']]["param_range"]  # 获取马斯京根参数
        MK = [(value[1] - value[0]) * params[:, i] + value[0]for i, (key, value) in enumerate(param_ranges.items())][15][0]
        MX = [(value[1] - value[0]) * params[:, i] + value[0]for i, (key, value) in enumerate(param_ranges.items())][16][0]
        simm = Musk(simu, MK, MX, time_interval_hours)  # 马斯京根，节点流量传播到出口
        simu = simm.reshape(sim1.shape)
        simd = sim1.copy()
        simd = np.array(simd*area2/(3600*time_interval_hours*1000/1000000))  # 下游新安江流量
        sim = (simu + simd)/area*(3600*time_interval_hours*1000/1000000)  # 合并流量转径流深
        return sim

    def evaluation(self) -> Union[list, np.array]:
        return self.true_obs

    def objectivefunction(
        self,
        simulation: Union[list, np.array],
        evaluation: Union[list, np.array],
        params=None,  # this cannot be removed
    ) -> float:
        if self.loss["type"] == "time_series":
            return LOSS_DICT[self.loss["obj_func"]](evaluation, simulation)
        # for events
        time = self.loss["events"]
        if time is None:
            raise ValueError(
                "time should not be None since you choose events, otherwise choose time_series"
            )
        calibrate_starttime = pd.to_datetime("2012-06-10 0:00:00")
        calibrate_endtime = pd.to_datetime("2019-12-31 23:00:00")
        total = 0
        count = 0
        for i in range(len(time)):
            if time.iloc[i, 0] < calibrate_endtime:
                start_num = (
                    time.iloc[i, 0] - calibrate_starttime - pd.Timedelta(hours=365)
                ) / pd.Timedelta(hours=1)
                end_num = (
                    time.iloc[i, 1] - calibrate_starttime - pd.Timedelta(hours=365)
                ) / pd.Timedelta(hours=1)
                start_num = int(start_num)
                end_num = int(end_num)
                like_ = LOSS_DICT[self.loss["obj_func"]](
                    evaluation[start_num:end_num,], simulation[start_num:end_num,]
                )
                count += 1

                total += like_
        return total / count


def calibrate_by_sceuamusk(
    basins,
    p_and_e,
    qobs,
    dbname,
    warmup_length=365,
    model=None,
    algorithm=None,
    loss=None,
    param_file=None,
    data_dir=None,
    qin=None,
):
    if model is None:
        model = {
            "name": "xaj_mz",
            "source_type": "sources5mm",
            "source_book": "HF",
            "time_interval_hours": 1,
        }
    if algorithm is None:
        algorithm = {
            "name": "SCE_UA",
            "random_seed": 1234,
            "rep": 1000,
            "ngs": 1000,
            "kstop": 500,
            "peps": 0.1,
            "pcento": 0.1,
        }
    if loss is None:
        loss = {
            "type": "time_series",
            "obj_func": "RMSE",
            "events": None,
        }
    random_seed = algorithm["random_seed"]
    rep = algorithm["rep"]
    ngs = algorithm["ngs"]
    kstop = algorithm["kstop"]
    peps = algorithm["peps"]
    pcento = algorithm["pcento"]
    np.random.seed(random_seed)
    for i in range(len(basins)):
        spot_setup = SpotSetup(
            p_and_e[:, i : i + 1, :],
            qobs[:, i : i + 1, :],
            warmup_length=warmup_length,
            model=model,
            loss=loss,
            param_file=param_file,
            basin_index=i,
            data_dir=data_dir,
            qin=qin
        )
        if not os.path.exists(dbname):
            os.makedirs(dbname)
        db_basin = os.path.join(dbname, basins[i])
        sampler = spotpy.algorithms.sceua(
            spot_setup,
            dbname=db_basin,
            dbformat="csv",
            random_state=random_seed,
        )
        # Start the sampler, one can specify ngs, kstop, peps and pcento id desired
        sampler.sample(rep, ngs=ngs, kstop=kstop, peps=peps, pcento=pcento)
        print("Calibrate Finished!")
    return sampler
    

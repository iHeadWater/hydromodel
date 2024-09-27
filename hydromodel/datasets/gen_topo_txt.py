import hydrotopo.ig_path as htip
import numpy as np

from hydromodel.models.model_config import MODEL_PARAM_DICT


# 特化，只针对上游
def find_edge_nodes(gpd_nodes_df, gpd_network_df, station_indexes, cutoff: int = 2):
    geom_array, new_geom_array, index_geom_array = htip.line_min_dist(gpd_nodes_df, gpd_network_df)
    graph = htip.build_graph(geom_array)
    station_dict = {}
    # 当前站点所对应线索引
    for station_index in station_indexes:
        cur_index = np.argwhere(new_geom_array == index_geom_array[station_index])[0][0]
        true_index = len(geom_array) - len(new_geom_array) + cur_index
        paths = graph.get_all_shortest_paths(v=true_index, mode='in')
        sta_lists = []
        for path in paths:
            sta_list = []
            for line in path:
                if line >= len(geom_array) - len(new_geom_array):
                    new_line_index = line - len(geom_array) + len(new_geom_array)
                    sta_index = np.argwhere(index_geom_array == new_geom_array[new_line_index])
                    if len(sta_index) > 0:
                        sta_list.append(sta_index[0][0])
            sta_list.reverse()
            sta_lists.append(sta_list[-cutoff:])
        paths = np.unique(np.array(sta_lists, dtype=object))
        station_dict[station_index] = paths
    return station_dict

def gen_topo_text_and_default_json(gpd_nodes_df, gpd_network_df, station_indexes, model_name='xaj'):
    # gpd_node_df: gpd.GeoDataFrame，站点图层数据
    # gpd_network_df: gpd.GeoDataFrame，用来确定拓扑关系的河网图层数据
    # station_indexes: 要生成上下游关系的站点索引列表，【0，1，2……】
    # 本测试中采取所有站点的索引
    # model_name: 率定时所用的模型名，默认为xaj（新安江模型）
    import ujson
    station_dict = find_edge_nodes(gpd_nodes_df, gpd_network_df, station_indexes)
    riv_1lvl_list = []
    higher_list = []
    for val in station_dict.values():
        if len(val) == 1:
            riv_1lvl_list.extend(val)
        else:
            topo_path = np.unique(np.concatenate(val))
            higher_list.append(topo_path)
    default_params_list = []
    for sta_id in station_indexes:
        sta_id = int(sta_id)
        params_dict = {'MODELID': sta_id, 'START': sta_id, 'END': sta_id, 'MODELNAME': model_name.upper(),
                       'PARAMETER': [float(x) for x in np.repeat(1.0, len(MODEL_PARAM_DICT[model_name]['param_name']))],
                       'UP': [float(x) for x in np.repeat(1.0, len(MODEL_PARAM_DICT[model_name]['param_name']))],
                       'DOWN': [float(x) for x in np.repeat(0.0, len(MODEL_PARAM_DICT[model_name]['param_name']))]}
        default_params_list.append(params_dict)
    musk_index = 0
    for hlist in higher_list:
        for elem in hlist[1:]:
            elem = int(elem)
            params_dict = {"MODELID": len(station_indexes) + musk_index, "START": elem, "END": int(hlist[0]),
                           "MODELNAME": "MUSK",
                           "PARAMETER": [float(x) for x in np.repeat(1.0, len(MODEL_PARAM_DICT[model_name]["param_name"]))],
                           "UP": [float(x) for x in np.repeat(1.0, len(MODEL_PARAM_DICT[model_name]['param_name']))],
                           "DOWN": [float(x) for x in np.repeat(0.0, len(MODEL_PARAM_DICT[model_name]['param_name']))]}
            default_params_list.append(params_dict)
            musk_index+=1
    with open('params.json', 'w') as fp:
        ujson.dump(default_params_list, fp, indent=4)
    model_with_same_paras_list = []
    for sta_id in station_indexes:
        sta_id = int(sta_id)
        params_dict = {"ParaID": sta_id, "MODELNAME": model_name.upper(),"ParaNo": len(MODEL_PARAM_DICT[model_name]['param_name']),
                       "MODELIDSET": [sta_id],
                       "PARAMETER": [float(x) for x in np.repeat(0.5, len(MODEL_PARAM_DICT[model_name]['param_name']))],
                       "UP": [value[1] for value in list(MODEL_PARAM_DICT[model_name]['param_range'].values())],
                       "DOWN": [value[0] for value in list(MODEL_PARAM_DICT[model_name]['param_range'].values())]}
        # params_dict['ParaNo'] = len(MODEL_PARAM_DICT[model_name]['param_name'])
        # params_dict['MODELIDSET'] = [sta_id]
        model_with_same_paras_list.append(params_dict)
    musk_index = 0
    for hlist in higher_list:
        for elem in hlist[1:]:
            params_dict = {"ParaID": len(station_indexes) + musk_index, "MODELNAME": "MUSK", "ParaNo": 2,
                           "MODELIDSET": [len(station_indexes) + musk_index],
                           "PARAMETER": [1.0, 1.0], "UP": [1.0, 1.0], "DOWN": [0.0, 0.0]}
            model_with_same_paras_list.append(params_dict)
            musk_index+=1
    with open('ModelwithsameParas.json', 'w') as fp:
        ujson.dump(model_with_same_paras_list, fp, indent=4)
    with open('topo.txt', 'w') as f:
        [f.write(str(i)+' ') for i in riv_1lvl_list]
        f.write('\n')
        for hlist in higher_list:
            [f.write(str(i)+' ') for i in hlist]
            f.write('\n')


# 将站点数据分配到泰森多边形上整理
import geopandas as gpd
import numpy as np
from scipy.spatial import Voronoi
from shapely.geometry import Polygon
import pandas as pd
import xarray as xr
from hydromodel.datasets import STTYPE_NAME, CODE_NAME
from hydromodel.datasets.read_data_from_topo import read_data_from_topo


def organize_stations_df(era5l_ds_path, stations, basin):
    nearest_gdf, centroids = separate_stations(stations, basin)
    center_dict = {}
    centers = np.unique(nearest_gdf['index_right'].to_numpy())
    for poly_id in centers:
        sta_ids = nearest_gdf.index[nearest_gdf['index_right'] == poly_id].to_numpy()
        # sta_types = stations[stations[CODE_NAME].isin(sta_ids)][STTYPE_NAME].to_numpy()
        if len(sta_ids) >= 2:
            data_dict = read_data_from_topo(stations, sta_ids)
            dfs = list(data_dict.values())
            tm_min = np.min(dfs[0]['tm'])
            tm_max = np.max(dfs[0]['tm'])
            for df in dfs:
                if len(df)>0:
                    if np.min(df['tm']) > pd.to_datetime('2000-01-01'):
                        tm_min = np.min([tm_min, np.min(df['tm'])])
                        tm_max = np.max([tm_max, np.max(df['tm'])])
            pp_comp_df, rr_comp_df = organize_rain_and_flow(dfs)
            # pp_comp_df = pp_comp_df.set_index('tm')
            pp_comp_df = pp_comp_df[~pp_comp_df.index.duplicated()]
            rr_comp_df = rr_comp_df[~rr_comp_df.index.duplicated()]
            pp_comp_df = pp_comp_df.resample('1h', origin='epoch').interpolate()[tm_min: tm_max]
            try:
                rr_comp_df = rr_comp_df.resample('1h', origin='epoch').interpolate()[tm_min: tm_max]
            except TypeError:
                # 存在实际没有流量的废站
                rr_comp_df = pd.DataFrame()
            pr_comp_df = pd.concat([pp_comp_df, rr_comp_df], axis=1)
            # 由于含有蒸散发的文件已经是根据流域编号拆分的结果，所以不需要再指定basin_id
            pev_df = read_pev_from_era5(era5l_ds_path, tm_min, tm_max)
            comp_df = pd.concat([pr_comp_df, pev_df], axis=1)
            center_dict[poly_id] = comp_df
        else:
            center_dict[poly_id] = None
    return center_dict, centroids


def read_pev_from_era5(era5l_ds_path, time_min, time_max):
    # 使用ftproot里的数据集, 时间最晚到2024.6.9 19:00
    era5l_ds = xr.open_dataset(era5l_ds_path)
    evapo = era5l_ds['total_evaporation_hourly'].sel(time_start=slice(time_min, time_max))
    evapo_df = evapo.to_dataframe().drop(columns=['basin_id']).rename(columns={'total_evaporation_hourly': 'pet'})
    return evapo_df


def organize_rain_and_flow(dfs):
    # dfs is list of GeoDataFrame
    # tm_min = np.min(dfs[0]['tm'])
    # tm_max = np.max(dfs[0]['tm'])
    pp_comp_df = pd.concat([df.set_index('tm') for df in dfs if 'drp' in df.columns])
    pp_comp_df['drp'] = pp_comp_df['drp'].groupby(level=0).mean()
    try:
        river_comp_df = pd.concat([df.set_index('tm') for df in dfs if ('q' in df.columns)])
    except ValueError:
        river_comp_df = pd.DataFrame()
    try:
        rsvr_comp_df = pd.concat([df.set_index('tm') for df in dfs if ('inq' in df.columns)])
        rsvr_comp_df = rsvr_comp_df.rename(columns={'inq': 'q'})
    except ValueError:
        rsvr_comp_df = pd.DataFrame()
    rr_comp_df = pd.concat([river_comp_df, rsvr_comp_df]).groupby(level=0).agg({'q': 'mean'})
    return pp_comp_df, rr_comp_df


def separate_stations(stations, basin):
    # 考虑到碧流河流域雨量站远多于洪量站的现状，以洪量站划分泰森多边形，再在多边形上做雨量平均，以此拼合雨洪量
    stations_npp = stations[stations[STTYPE_NAME].str.contains('|'.join(['RR', 'ZQ']))]
    stations_pp = stations[stations[STTYPE_NAME] == 'PP']
    # 以数量少的站点类型划分泰森多边形
    if len(stations_npp) >= len(stations_pp):
        polygons = calculate_voronoi_polygons(stations_pp, basin)
    else:
        polygons = calculate_voronoi_polygons(stations_npp, basin)
    nearest_gdf = gpd.sjoin_nearest(stations, polygons, how="left")
    centroids = polygons.geometry.centroid.to_list()
    return nearest_gdf, centroids


# Copied from hydrodatasource/cleaner/rainfall_cleaner.py
def calculate_voronoi_polygons(stations, basin):
    """
    计算泰森多边形并裁剪至流域边界。

    参数：
    stations - 位于流域内部的站点GeoDataFrame。
    basin - 流域shapefile的GeoDataFrame。

    返回：
    clipped_polygons - 裁剪后的泰森多边形GeoDataFrame。
    """
    if len(stations) < 2:
        stations["original_area"] = np.nan
        stations["clipped_area"] = np.nan
        stations["area_ratio"] = 1.0
        return stations

    # 获取流域边界的最小和最大坐标，构建边界框
    x_min, y_min, x_max, y_max = basin.total_bounds

    # 扩展边界框
    x_min -= 1.0 * (x_max - x_min)
    x_max += 1.0 * (x_max - x_min)
    y_min -= 1.0 * (y_max - y_min)
    y_max += 1.0 * (y_max - y_min)

    bounding_box = np.array(
        [[x_min, y_min], [x_max, y_min], [x_max, y_max], [x_min, y_max]]
    )

    # 提取站点坐标
    points = np.array([point.coords[0] for point in stations.geometry])

    # 将站点坐标与边界框点结合，确保Voronoi多边形覆盖整个流域
    points_extended = np.concatenate((points, bounding_box), axis=0)

    # 计算Voronoi图
    vor = Voronoi(points_extended)

    # 提取每个点对应的Voronoi区域
    regions = [vor.regions[vor.point_region[i]] for i in range(len(points))]

    # 生成多边形
    polygons = [
        Polygon([vor.vertices[i] for i in region if i != -1])
        for region in regions
        if -1 not in region
    ]

    # 创建GeoDataFrame
    gdf_polygons = gpd.GeoDataFrame(geometry=polygons, crs=stations.crs)
    gdf_polygons["编码"] = stations["编码"].values
    gdf_polygons["original_area"] = gdf_polygons.geometry.area

    # 将多边形裁剪到流域边界
    clipped_polygons = gpd.clip(gdf_polygons, basin)
    clipped_polygons["clipped_area"] = clipped_polygons.geometry.area
    clipped_polygons["area_ratio"] = (
        clipped_polygons["clipped_area"] / clipped_polygons["clipped_area"].sum()
    )
    return clipped_polygons
import hydromodel.datasets.gen_topo_txt as gtt
import geopandas as gpd

gpd_node_df = gpd.read_file(r'C:\Users\Administrator\IdeaProjects\hydrotopo\hydrotopo\test_data\near_changchun_dots.shp')
gpd_network_df = gpd.read_file(r'C:\Users\Administrator\IdeaProjects\hydrotopo\hydrotopo\test_data\near_changchun_cut.shp')

def test_gen_topo_txt():
    # gpd_node_df: gpd.GeoDataFrame，站点图层数据
    # gpd_network_df: gpd.GeoDataFrame，用来确定拓扑关系的河网图层数据
    # station_indexes: 要生成上下游关系的站点索引列表，【0，1，2……】
    # 本测试中采取所有站点的索引
    # model_name: 率定时所用的模型名，默认为xaj（新安江模型）
    gtt.gen_topo_text_and_default_json(gpd_node_df, gpd_network_df, gpd_node_df.index.tolist(), model_name='xaj')


def test_merge_grid_dataset():
    import pandas as pd
    import xarray as xr
    import glob
    gsmap_datas0 = r'D:\Downloads\gsmap'
    # sanxia_gpm_datas = r'E:\Users\Administrator\Documents\WeChat Files\wxid_t95o8zdo0wu622\FileStorage\File\2024-09\gpm'
    gsmap_datas1 = r'E:\Users\Administrator\Documents\WeChat Files\wxid_t95o8zdo0wu622\FileStorage\File\2024-09\gsmap'
    gsmap_csv_files0 = glob.glob(gsmap_datas0 + '/*.csv', recursive=True)
    gsmap_csv_files1 = [file for file in glob.glob(gsmap_datas1 + '/*.csv', recursive=True) if 'camels' in file]
    gsmap_csv_files = gsmap_csv_files0 + gsmap_csv_files1
    total_df = pd.DataFrame()
    for file in gsmap_csv_files:
        df = pd.read_csv(file).set_index(['time_start', 'basin_id'])
        total_df = pd.concat([total_df, df])
    total_df = total_df[~total_df.index.duplicated()]
    total_ds = xr.Dataset.from_dataframe(total_df)
    total_ds.to_netcdf('616_basins_gsmap_1998_2024.nc')

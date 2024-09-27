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

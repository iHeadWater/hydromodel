import geopandas as gpd
import hydromodel.datasets.separate_stations as hdss
from hydromodel.datasets.gen_topo_txt import gen_topo_text


def test_point_stations_polygons():
    stations = gpd.read_file(r'C:\Users\Administrator\IdeaProjects\hydromodel-master\input\station_shps\biliu_21401550.shp')
    basin = gpd.read_file(r'C:\Users\Administrator\IdeaProjects\hydromodel-master\input\station_shps\basin_CHN_songliao_21401550.shp')
    riv_net = gpd.read_file(r'C:\Users\Administrator\IdeaProjects\hydromodel-master\input\station_shps\biliu_rivnet.shp')
    organized_dict, centroids = hdss.organize_stations_df(
        r'C:\Users\Administrator\IdeaProjects\hydromodel-master\input\station_shps\biliu_era5l_aver.nc', stations, basin)
    topo_gdf = gpd.GeoDataFrame().set_geometry(centroids)
    for i in range(len(centroids)):
        df = list(organized_dict.values())[i]
        df.to_csv(rf'C:\Users\Administrator\IdeaProjects\hydromodel-master\input\21401550_{i}.csv')
    gen_topo_text(topo_gdf, riv_net, topo_gdf.index.tolist())
    return organized_dict


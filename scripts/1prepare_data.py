"""
Author: Wenyu Ouyang
Date: 2024-03-25 09:21:56
LastEditTime: 2024-05-20 18:54:58
LastEditors: Wenyu Ouyang
Description: Script for preparing data
FilePath: \hydromodel\scripts\prepare_data.py
Copyright (c) 2023-2024 Wenyu Ouyang. All rights reserved.
"""

from pathlib import Path
import sys
import os
import argparse
import geopandas as gpd
from loguru import logger

current_script_path = Path(os.path.realpath(__file__))
repo_root_dir = current_script_path.parent.parent
sys.path.append(str(repo_root_dir))
from hydromodel.datasets.data_preprocess_topo import process_and_save_data_as_nc


def main(args):
    data_path = args.origin_data_dir
    checks = args.check_topo_and_basins
    replace_pet = args.replace_pet_with_subbasin
    # 校验拓扑点数量和子流域数量的代码
    logger.warning('雨量数据需要先行准备好！')
    if checks:
        node_path = os.path.join(data_path, "station_shps", "nodes.shp")
        sub_basin_path = os.path.join(data_path, "station_shps", "sub_basins.shp")
        node_gdf = gpd.read_file(node_path)
        sub_basin_gdf = gpd.read_file(sub_basin_path)
        assert len(node_gdf) == len(sub_basin_gdf)
    if process_and_save_data_as_nc(data_path, save_folder=data_path, replace_pet=replace_pet):
        print("Data is ready!")
    else:
        print("Data format is incorrect! Please check the data.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Prepare data.")
    parser.add_argument(
        "--origin_data_dir",
        type=str,
        help="Path to your hydrological data",
        default=r"C:\Users\Administrator\IdeaProjects\hydromodel-master\input",
    )
    parser.add_argument("--check_topo_and_basins", type=bool,
                        help="Check amount of topological points and subbasins are equal or not", default=False)
    parser.add_argument("--replace_pet_with_subbasin", type=bool,
                        help="replace pet in data with other subbasin's pet", default=False)
    args = parser.parse_args()
    main(args)

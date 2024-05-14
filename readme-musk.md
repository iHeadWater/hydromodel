# 数据准备
## result/xaj
新安江模型的数据。

## result/musk
新安江+马斯京根模型的数据。与新安江模型数据相比，有以下变化：

1. basin_attributes.csv  
    将area改成区间面积  
    增加len(km)列，数据一定要以km为单位  
2. basin_21401550.csv  
    增加node1_flow(m^3/s)列
3. param_range.yaml  
    xaj参数最下面增加MM，曼宁系数，范围是[0.03, 1.0]

# 率定模型
模型根据 ```calibrate_xaj.py``` 的 ```--data_type```参数，判断是否启用马斯京根
- ```--data_type = owndata```，纯新安江
- ```--data_type = owndata-musk```，启用马斯京根

# 修改的代码文件
1. ```datasets/__init__.py```
2. ```datasets/data_preprocess.py```
3. ```trainers/calibrate_sceua.py```
4. ```trainers/evaluate.py```
5. ```scripts/calibrate_xaj.py```
6. ```models/musk.py```
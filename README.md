# 数据准备

- basin_attributies.csv包含以下几项：
  id, name, area(km^2), area2(km^2)
  area2代表节点以下流域面积
  注：能力有限，一次只能跑一个流域！

- basin_xxx.csv
  新增node1_flow(m^3/s)，表示节点流量
  如果node1_flow为空，则计算上游xaj模型，作为节点流量

# 参数

- 在xaj 的 param_name 增加 MK, MX
  MK: [0.00, 10]
  MX: [0.00, 1.0]

# 运行calibrate_xaj.py

在所有参数后边，增加：
```bash
python calibrate_xaj.py --subbasin true
```

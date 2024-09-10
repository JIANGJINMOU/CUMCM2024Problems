import pandas as pd
import ace_tools as tools
import pandas as pd
from pulp import LpMaximize, LpProblem, LpVariable, lpSum

# 地块数据

land_data = {

    "地块名称": ["A1", "A2", "A3", "A4", "A5", "A6", "B1", "B2", "B3", "B4", "B5", "B6", "B7", "B8", "B9", "B10", "B11", "B12", "B13", "B14", "C1", "C2", "C3", "C4", "C5", "C6", "D1", "D2", "D3", "D4", "D5", "D6", "D7", "D8", "E1", "E2", "E3", "E4", "E5", "E6", "E7", "E8", "E9", "E10", "E11", "E12", "E13", "E14", "E15", "E16", "F1", "F2", "F3", "F4"],

    "地块类型": ["平旱地"]*6 + ["梯田"]*14 + ["山坡地"]*6 + ["水浇地"]*8 + ["普通大棚"]*16 + ["智慧大棚"]*4,

    "地块面积/亩": [80, 55, 35, 72, 68, 55, 60, 46, 40, 28, 25, 86, 55, 44, 50, 25, 60, 45, 35, 20, 15, 13, 15, 18, 27, 20, 15, 10, 14, 6, 10, 12, 22, 20, 0.6]*20

}

land_df = pd.DataFrame(land_data)

# 作物数据

crop_data = {

    "作物编号": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41],

    "作物名称": ["黄豆", "黑豆", "红豆", "绿豆", "爬豆", "小麦", "玉米", "谷子", "高粱", "黍子", "荞麦", "南瓜", "红薯", "莜麦", "大麦", "水稻", "豇豆", "刀豆", "芸豆", "土豆", "西红柿", "茄子", "菠菜", "青椒", "菜花", "包菜", "油麦菜", "小青菜", "黄瓜", "生菜", "辣椒", "空心菜", "黄心菜", "芹菜", "大白菜", "白萝卜", "红萝卜", "榆黄菇", "香菇", "白灵菇", "羊肚菌"],

    "作物类型": ["粮食（豆类）"]*5 + ["粮食"]*11 + ["蔬菜（豆类）"]*3 + ["蔬菜"]*20 + ["食用菌"]*4,

    "适宜种植耕地": ["平旱地,梯田,山坡地"]*15 + ["水浇地"]*1 + ["水浇地,普通大棚,智慧大棚"]*1 + ["普通大棚,智慧大棚"]*25

}

crop_df = pd.DataFrame(crop_data)


# 增加必要的模拟数据
crop_df["亩产量/斤"] = [100, 120, 140, 150, 110] + [200] * 11 + [180] * 3 + [160] * 20 + [300] * 4
crop_df["销售单价/(元/斤)"] = [5, 6, 7, 5, 6] + [4] * 11 + [8] * 3 + [10] * 20 + [12] * 4
crop_df["种植成本/(元/亩)"] = [300, 320, 340, 350, 310] + [200] * 11 + [250] * 3 + [400] * 20 + [500] * 4

crop_df = pd.DataFrame(crop_data)

# 展示地块和作物的DataFrame

tools.display_dataframe_to_user(name="地块数据", dataframe=land_df)
tools.display_dataframe_to_user(name="作物数据", dataframe=crop_df)


# 数据加载和预处理

land_df = pd.read_csv("land_data.csv")  # 读取地块数据
crop_df = pd.read_csv("crop_data.csv")  # 读取作物数据
planting_data = pd.read_csv("planting_data_2023.csv")  # 读取2023年的种植数据

# 创建线性规划问题

model = LpProblem(name="crop-planting-optimization", sense=LpMaximize)

# 创建变量，决定每个地块每季种植多少作物

crop_vars = {
    (land, crop): LpVariable(name=f"{land}_{crop}", lowBound=0, cat="Continuous")
    for land in land_df["地块名称"]
    for crop in crop_df["作物编号"]
}

# 目标函数：最大化总净收益

model += lpSum(
    [
        crop_vars[(land, crop)]
        * crop_df.loc[crop, "亩产量/斤"]
        * crop_df.loc[crop, "销售单价/(元/斤)"]
        - crop_vars[(land, crop)] * crop_df.loc[crop, "种植成本/(元/亩)"]
        for land in land_df["地块名称"]
        for crop in crop_df["作物编号"]
    ]
)

# 添加约束条件

# 约束1：每块地每季的作物面积不能超过其总面积

for land in land_df["地块名称"]:
    model += (
        lpSum([crop_vars[(land, crop)] for crop in crop_df["作物编号"]])<= land_df.loc[land_df["地块名称"] == land, "地块面积/亩"].values[0]
    )

    # 约束2：豆类作物至少每三年种植一次

    # 约束3：同一作物不能连续种植

    # 求解问题

    model.solve()

# 打印结果

for var in model.variables():
    print(f"{var.name}: {var.value()}")

# 输出结果到文件

result1 = pd.DataFrame(
    [
        {
            "地块名称": land,
            "作物编号": crop,
            "种植面积": crop_vars[(land, crop)].varValue,
        }
        for land, crop in crop_vars
    ]
)

result1.to_excel("result1_1.xlsx", index=False)
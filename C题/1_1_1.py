import pandas as pd
from pulp import LpMaximize, LpProblem, LpVariable, lpSum

# 数据加载和预处理
data1 = pd.read_excel("./附件1.xlsx", sheet_name="乡村的现有耕地")
data2 = pd.read_excel("./附件1.xlsx", sheet_name="乡村种植的农作物")
data3 = pd.read_excel("./附件2_1.xlsx", sheet_name="2023年的农作物种植情况")
data4 = pd.read_excel("./附件2_1.xlsx", sheet_name="2023年统计的相关数据")

# 处理缺失值，例如填充或删除
data1.fillna(0, inplace=True)
data2.dropna(inplace=True)
data3.fillna(0, inplace=True)
data4.dropna(inplace=True)
# 地块数据

data1.columns = ["地块名称", "地块类型", "地块面积/亩", "说明"]
data1.drop(columns=["说明"], inplace=True)
print(data1)

land_df = data1

# # 作物数据
# data2.columns = ["作物编号", "作物名称", "作物类型", "适宜种植耕地", "说明"]
# data2.drop(columns=["说明"], inplace=True)
# print(data2)
data2 = {
    "作物编号": range(1, 42),

    "作物名称": ["黄豆", "黑豆", "红豆", "绿豆", "爬豆", "小麦", "玉米", "谷子", "高粱", "黍子", "荞麦", "南瓜", "红薯", "莜麦", "大麦", "水稻", "豇豆", "刀豆", "芸豆", "土豆", "西红柿", "茄子", "菠菜", "青椒", "菜花", "包菜", "油麦菜", "小青菜", "黄瓜", "生菜", "辣椒", "空心菜", "黄心菜", "芹菜", "大白菜", "白萝卜", "红萝卜", "榆黄菇", "香菇", "白灵菇", "羊肚菌"],

    "作物类型": ["粮食（豆类）"]*5 + ["粮食"]*11 + ["蔬菜（豆类）"]*3 + ["蔬菜"]*18 + ["食用菌"]*4,

    "适宜种植耕地": ["平旱地,梯田,山坡地"]*15 + ["水浇地"]*1 + ["水浇地第一季,普通大棚第一季,智慧大棚第一季、第二季"]*18 + ["水浇地第二季"]*3 +["普通大棚第二季"]*4
}

data2 = pd.DataFrame(data2)
data2.drop(columns=["作物编号"], inplace=True)
print(data2)

crop_df = data2

def calculate_mean_of_range(x):
    lower, upper = map(float, x.split('-'))
    return (lower + upper) / 2
data4['销售单价均值/(元/斤)'] = data4['销售单价/(元/斤)'].apply(calculate_mean_of_range)

data4.drop(['序号', '地块类型', '种植季次', '销售单价/(元/斤)'], axis=1, inplace=True)

data4.drop_duplicates(subset='作物编号', keep='first', inplace=True)
data4['种植成本/(元/斤)'] = data4['种植成本/(元/亩)'] / data4['亩产量/斤']
data4['利润/(元/斤)'] = data4['销售单价均值/(元/斤)'] - data4['种植成本/(元/斤)']

print(data4)

crop_df["亩产量/斤"] = data4["亩产量/斤"]
crop_df["销售单价/(元/斤)"] = data4["销售单价均值/(元/斤)"]
crop_df["种植成本/(元/亩)"] = data4["种植成本/(元/亩)"]
crop_df.fillna(0, inplace=True)

print(crop_df)


# 创建线性规划问题
model = LpProblem(name="crop-planting-optimization", sense=LpMaximize)
result_data = []
years = [2024, 2025, 2026, 2027, 2028, 2029, 2030]

# 创建变量，决定每个地块每季种植多少作物
crop_vars = {
    (land, crop): LpVariable(name=f"{land}_{crop}", lowBound=0, cat="Continuous")
    for land in data1["地块名称"]
    for crop in range(len(crop_df))
}

# 超过部分的面积变量
excess_vars = {
    (land, crop): LpVariable(name=f"excess_{land}_{crop}", lowBound=0, cat="Continuous")
    for land in data1["地块名称"]
    for crop in range(len(crop_df))
}
# 目标函数：最大化总净收益
model += lpSum(
    crop_vars[(land, crop)] * crop_df.loc[crop, "亩产量/斤"] * crop_df.loc[crop, "销售单价/(元/斤)"]
    - crop_vars[(land, crop)] * crop_df.loc[crop, "种植成本/(元/亩)"]
    for land in data1["地块名称"]
    for crop in range(len(crop_df))
)

# # 约束1：每块地每季的作物面积不能超过其总面积
# for land in data1["地块名称"]:
#     model += lpSum([crop_vars[(land, crop)] for crop in range(len(crop_df))]) <= data1.loc[data1["地块名称"] == land, "地块面积/亩"].values[0]
for land in data1["地块名称"]:
    for y in years:
        for s in crop_vars:
            model += lpSum([crop_vars[(land, crop)] for crop in range(len(crop_df))]) <= data1.loc[data1["地块名称"] == land, "地块面积/亩"].values[0]

# 约束2：豆类作物至少每三年种植一次
# for land in data1["地块名称"]:
#     for crop in range(5):  # 假设豆类作物是0到4号
#         model += lpSum([crop_vars[(land, crop)]]) >= (1 / 3) * data1.loc[data1["地块名称"] == land, "地块面积/亩"].values[0]

for land in data1["地块名称"]:
    for crop in range(len(crop_df)):
        model += excess_vars[(land, crop)] <= crop_vars[(land, crop)]

# 求解问题
model.solve()

# 输出结果到文件

for land, crop in crop_vars:
    result_data.append({
        "年份": years,
        "地块名称": land,
        "作物名称": crop_df.loc[crop, "作物名称"],
        "种植面积": crop_vars[(land, crop)].varValue
    })

# 转换为 DataFrame
result1 = pd.DataFrame(result_data)


result_pivot = result1.pivot(index="地块名称", columns="作物名称", values="种植面积")
result_pivot.fillna(0, inplace=True)

# result_pivot.to_excel("temp.xlsx")
# print(result_pivot)

# 处理季节数据
two_season_lands = ["D1", "D2", "D3", "D4", "D5", "D6", "D7", "D8", 
                    "E1", "E2", "E3", "E4", "E5", "E6", "E7", "E8", 
                    "E9", "E10", "E11", "E12", "E13", "E14", "E15", "E16", 
                    "F1", "F2", "F3", "F4"]

# Create a new DataFrame with "第一季" and "第二季" labels
season1_df = result_pivot.drop(two_season_lands).copy()
season1_df['季节'] = "第一季"

season2_df = result_pivot.loc[two_season_lands].copy()
season2_df = pd.concat([season2_df, season2_df], axis=0)
season2_df['季节'] = ["第一季"] * len(two_season_lands) + ["第二季"] * len(two_season_lands)

# Combine the two DataFrames
final_df = pd.concat([season1_df, season2_df])

# Reset index to make '地块名称' a column
final_df.reset_index(inplace=True)

# Reorder the columns to have '季节' as the first column
final_df = final_df[['季节', '地块名称'] + [col for col in final_df.columns if col not in ['季节', '地块名称']]]


yearly_data = pd.DataFrame(final_df)
with pd.ExcelWriter("temp.xlsx") as writer:
    for year in years:
        yearly_data.to_excel(writer, sheet_name=f"{year}", index=False)


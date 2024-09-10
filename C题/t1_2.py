import pandas as pd
from pulp import LpMaximize, LpProblem, LpVariable, lpSum, lpDot, value, LpStatus

data = pd.read_excel("预处理后的数据.xlsx")
required_columns = ["作物名称", "平均价", "亩产量/斤", "种植成本/(元/亩)", "作物类型"]
if not all(col in data.columns for col in required_columns):
    raise ValueError("数据缺少必要的列")

data["预计销售量"] = data.groupby("作物名称")["种植面积/亩"].transform("sum")

years = range(2024, 2031)
crops = data["作物名称"].unique()
plots = data["地块名称"].unique()

# 线性约束
prob1_1 = LpProblem("Problem_1_1", LpMaximize)
prob1_2 = LpProblem("Problem_1_2", LpMaximize)
x1_1 = LpVariable.dicts("x1_1", [(i, j, t) for i in plots for j in crops for t in years], lowBound=0, cat='Continuous')
x1_2 = LpVariable.dicts("x1_2", [(i, j, t) for i in plots for j in crops for t in years], lowBound=0, cat='Continuous')

# 目标函数
for j in crops:
    for t in years:
        crop_data = data.loc[data["作物名称"] == j].iloc[0]
        profit_per_unit = crop_data["平均价"] * crop_data["亩产量/斤"] - crop_data["种植成本/(元/亩)"]
        total_production = lpDot([x1_2[i, j, t] for i in plots], crop_data["亩产量/斤"])
        excess = total_production - crop_data["预计销售量"]

        # 设置 prob1_1 的目标函数
        if prob1_1.objective is None:
            prob1_1 += lpDot([x1_1[i, j, t] for i in plots], profit_per_unit)

        # 设置 prob1_2 的目标函数
        if prob1_2.objective is None:
            prob1_2 += profit_per_unit * total_production - 0.5 * crop_data["平均价"] * excess

# 耕地资源
for t in years:
    prob1_1 += lpSum([x1_1[i, j, t] for i in plots for j in crops]) <= 1201
    prob1_2 += lpSum([x1_2[i, j, t] for i in plots for j in crops]) <= 1201

# 种植间作
for i in plots:
    for t in years:
        grain_crops = [j for j in crops if data.loc[data["作物名称"] == j, "作物类型"].values[0].startswith("粮食")]
        prob1_1 += lpSum([x1_1[i, j, t] for j in grain_crops]) <= 1
        prob1_2 += lpSum([x1_2[i, j, t] for j in grain_crops]) <= 1

# 豆类作物轮作
for i in plots:
    for t in years:
        if t <= 2026:
            prob1_1 += lpSum([x1_1[i, j, t] for j in crops if data.loc[data["作物名称"] == j, "作物类型"].values[0].startswith("粮食（豆类）")]) >= 1
            prob1_2 += lpSum([x1_2[i, j, t] for j in crops if data.loc[data["作物名称"] == j, "作物类型"].values[0].startswith("粮食（豆类）")]) >= 1

for i in plots:
    if data.loc[data["地块名称"] == i, "地块类型"].values[0] == "水浇地":
        for t in years:
            prob1_1 += lpSum([x1_1[i, j, t] for j in crops if j == "水稻" or data.loc[data["作物名称"] == j, "作物类型"].values[0].startswith("蔬菜")]) <= 1
            prob1_2 += lpSum([x1_2[i, j, t] for j in crops if j == "水稻" or data.loc[data["作物名称"] == j, "作物类型"].values[0].startswith("蔬菜")]) <= 1
    else:
        for t in years:
            prob1_1 += lpSum([x1_1[i, j, t] for j in crops if data.loc[data["作物名称"] == j, "作物类型"].values[0].startswith("粮食") and j!= "水稻"]) <= 1
            prob1_2 += lpSum([x1_2[i, j, t] for j in crops if data.loc[data["作物名称"] == j, "作物类型"].values[0].startswith("粮食") and j!= "水稻"]) <= 1

for j in crops:
    for t in years:
        if not data.loc[data["作物名称"] == j, "作物类型"].values[0].startswith("粮食（豆类）"):
            prob1_1 += lpSum([x1_1[i, j, t] for i in plots]) >= 30
            prob1_2 += lpSum([x1_2[i, j, t] for i in plots]) >= 30

for j in crops:
    for t in years:
        if not data.loc[data["作物名称"] == j, "作物类型"].values[0].startswith("粮食"):
            prob1_1 += lpSum([x1_1[i, j, t] for i in plots]) >= 20
            prob1_2 += lpSum([x1_2[i, j, t] for i in plots]) >= 20

for i in plots:
    for t in years:
        prob1_1 += lpSum([x1_1[i, j, t] for j in crops]) >= 0.6
        prob1_2 += lpSum([x1_2[i, j, t] for j in crops]) >= 0.6

# 求解问题
prob1_1.solve()
prob1_2.solve()

# 检查求解器的状态
print("Status for Problem 1_1:", LpStatus[prob1_1.status])
print("Status for Problem 1_2:", LpStatus[prob1_2.status])

# 提取结果
result1_1 = pd.DataFrame([(i, j, t, value(x1_1[i, j, t])) for i in plots for j in crops for t in years if value(x1_1[i, j, t]) > 0], columns=["地块名称", "作物名称", "年份", "种植面积/亩"])
result1_2 = pd.DataFrame([(i, j, t, value(x1_2[i, j, t])) for i in plots for j in crops for t in years if value(x1_2[i, j, t]) > 0], columns=["地块名称", "作物名称", "年份", "种植面积/亩"])

two_season = ["D1", "D2", "D3", "D4", "D5", "D6", "D7", "D8",
                    "E1", "E2", "E3", "E4", "E5", "E6", "E7", "E8",
                    "E9", "E10", "E11", "E12", "E13", "E14", "E15", "E16",
                    "F1", "F2", "F3", "F4"]

# print(two_season)
result1_1 = result1_1.rename(columns={"地块名称": "地块名称"})
result1_1_two_season = result1_1[result1_1["地块名称"].isin(two_season)]

season1_df = result1_1_two_season[result1_1_two_season["地块名称"].isin(two_season) & (result1_1_two_season["年份"] % 2 == 0)].copy()
season1_df['季节'] = "第一季"

season2_df = result1_1_two_season[result1_1_two_season["地块名称"].isin(two_season) & (result1_1_two_season["年份"] % 2 == 1)].copy()
season2_df['季节'] = "第二季"

result1_1_two_season = pd.concat([season1_df, season2_df])

season1_df_other = result1_1[~result1_1["地块名称"].isin(two_season)].copy()
season1_df_other['季节'] = "第一季"

# 合并所有数据
result1_1 = pd.concat([season1_df_other, result1_1_two_season])
result1_1.reset_index(drop=True, inplace=True)

# print(result1_1)

# 整理结果
result1_1_formatted = {}
result1_2_formatted = {}
for t in years:
    result1_1_formatted[t] = pd.DataFrame(0, index=plots, columns=crops)
    result1_2_formatted[t] = pd.DataFrame(0, index=plots, columns=crops)

for _, row in result1_1.iterrows():
    plot_name = row["地块名称"]
    crop_name = row["作物名称"]
    year = row["年份"]
    planting_area = row["种植面积/亩"]
    result1_1_formatted[year].loc[plot_name, crop_name] += planting_area

for _, row in result1_2.iterrows():
    plot_name = row["地块名称"]
    crop_name = row["作物名称"]
    year = row["年份"]
    planting_area = row["种植面积/亩"]
    result1_2_formatted[year].loc[plot_name, crop_name] += planting_area

# with pd.ExcelWriter("result1_1_1.xlsx") as writer:
#     for t, df in result1_1_formatted.items():
#         df.to_excel(writer, sheet_name=str(t))

# with pd.ExcelWriter("result1_2_2.xlsx") as writer:
#     for t, df in result1_2_formatted.items():
#         df.to_excel(writer, sheet_name=str(t))



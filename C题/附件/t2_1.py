import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pulp import LpMaximize, LpProblem, LpVariable, lpSum, lpDot, value, LpStatus

plt.rcParams['font.sans-serif'] = ['SimHei']  # 用来正常显示中文标签
plt.rcParams['axes.unicode_minus'] = False  # 用来正常显示负号

# 读取预处理后的数据
data = pd.read_excel("预处理后的数据.xlsx")
data0 = pd.read_csv("data.csv", encoding='GBK')

# 提取相关数据
years = range(2024, 2031)
crops = data["作物名称"].unique()
plots = data["地块名称"].unique()

# 模拟次数
num_simulations = 10
results = {}
for t in years:
    results[t] = pd.DataFrame(0, index=plots, columns=crops)

# 模拟构建
for _ in range(num_simulations):
    data["预计销售量"] = data0["23年产量"]
    # 处理小麦和玉米的预期销售量增长
    wheat_corn_data = data[(data["作物名称"] == "小麦") | (data["作物名称"] == "玉米")]
    growth_rate = np.random.uniform(0.05, 0.1)
    wheat_corn_data["预计销售量"] *= (1 + growth_rate)**(years[0] - 2023)

    # 处理其他农作物的预期销售量变化
    other_crops_data = data[~data["作物名称"].isin(["小麦", "玉米"])]
    change_rate = np.random.uniform(-0.05, 0.05)
    data["预计销售量"] *= (1 + change_rate)

    # 处理农作物亩产量的变化
    yield_change_rate = np.random.uniform(-0.1, 0.1)
    data["亩产量/斤"] *= (1 + yield_change_rate)

    # 处理种植成本的增长
    cost_growth_rate = 0.05
    data["种植成本/(元/亩)"] *= (1 + cost_growth_rate)**(years[0] - 2023)

    # 处理蔬菜类作物销售价格增长
    vegetable_crops_data = data[data["作物类型"].str.startswith("蔬菜")]
    price_growth_rate = 0.05
    vegetable_crops_data["平均价"] *= (1 + price_growth_rate)**(years[0] - 2023)

    # 处理食用菌销售价格下降
    mushroom_crops_data = data[data["作物类型"].str.startswith("食用菌")]
    if "羊肚菌" in mushroom_crops_data["作物名称"].values:
        price_decline_rate = 0.05
    else:
        price_decline_rate = np.random.uniform(0.01, 0.05)
    mushroom_crops_data["平均价"] *= (1 - price_decline_rate)**(years[0] - 2023)

    # 计算每年每个作物的销售量
    for t in years:
        for crop in crops:
            if crop in wheat_corn_data["作物名称"].values:
                results[t].loc[wheat_corn_data["地块名称"], crop] += wheat_corn_data.loc[wheat_corn_data["作物名称"] == crop, "预计销售量"].values[0]

            elif crop in other_crops_data["作物名称"].values:
                results[t].loc[other_crops_data["地块名称"], crop] += other_crops_data.loc[other_crops_data["作物名称"] == crop, "预计销售量"].values[0]
            else:
                raise ValueError("数据中不存在该作物")

# 计算平均销售量

# for t in years:
#     results[t] = results[t].apply(lambda x: x / num_simulations)

# # 计算总销售量
# total_sales = pd.DataFrame(0, index=plots, columns=years)
# for t in years:
#     total_sales[t] = results[t].sum(axis=1)

# 计算总亩产量
total_yield = pd.DataFrame(0, index=plots, columns=years)
for t in years:
    total_yield[t] = data.groupby("地块名称")["亩产量/斤"].transform("sum")

# 计算总成本
total_cost = pd.DataFrame(0, index=plots, columns=years)
for t in years:
    total_cost[t] = data.groupby("地块名称")["种植成本/(元/亩)"].transform("sum")

# 打印预期销售量
# for t in years:
print(f"Year {t} - Expected Sales:")
print(data["预计销售量"])
print()
data["预计销售量"].to_csv("data0.csv")

# 打印亩产量
print("Yield per acre:")
print(data["亩产量/斤"])
print()
data["亩产量/斤"].to_csv("data1.csv")

# 打印种植成本
print("Planting Cost:")
print(data["种植成本/(元/亩)"])
print()
data["种植成本/(元/亩)"].to_csv("data2.csv")

# 打印销售价格
print("Sales Price:")
print(data["平均价"])
print()
data["平均价"].to_csv("data3.csv")
import pandas as pd
import random
from deap import base, creator, tools, algorithms

# 数据加载和处理
data1 = pd.read_excel("./附件1.xlsx", sheet_name="乡村的现有耕地")
data2 = pd.read_excel("./附件1.xlsx", sheet_name="乡村种植的农作物")

# 数据预处理
data1.columns = ["地块名称", "地块类型", "地块面积/亩", "说明"]
data1.drop(columns=["说明"], inplace=True)

data2 = {
    "作物编号": range(1, 42),
    "作物名称": ["黄豆", "黑豆", "红豆", "绿豆", "爬豆", "小麦", "玉米", "谷子", "高粱", "黍子", "荞麦", "南瓜", "红薯", "莜麦", "大麦", "水稻", "豇豆", "刀豆", "芸豆", "土豆", "西红柿", "茄子", "菠菜", "青椒", "菜花", "包菜", "油麦菜", "小青菜", "黄瓜", "生菜", "辣椒", "空心菜", "黄心菜", "芹菜", "大白菜", "白萝卜", "红萝卜", "榆黄菇", "香菇", "白灵菇", "羊肚菌"],
    "作物类型": ["粮食（豆类）"]*5 + ["粮食"]*11 + ["蔬菜（豆类）"]*3 + ["蔬菜"]*18 + ["食用菌"]*4,
    "适宜种植耕地": ["平旱地,梯田,山坡地"]*15 + ["水浇地"]*1 + ["水浇地第一季,普通大棚第一季,智慧大棚第一季、第二季"]*18 + ["水浇地第二季"]*3 + ["普通大棚第二季"]*4
}
data2 = pd.DataFrame(data2)
data2.drop(columns=["作物编号"], inplace=True)

crop_df = data2

stats_2023 = pd.read_excel('./附件2.xlsx', sheet_name=1)
stats_2023 = stats_2023.rename(
    columns={
        "序号": "index",
        "作物编号": "crop_id",
        "作物名称": "crop_name",
        "地块类型": "field_type",
        "种植季次": "season",
        "亩产量/斤": "yield_per_mu",
        "种植成本/(元/亩)": "cost_per_mu",
        "销售单价/(元/斤)": "price_range",
    }
)
# 处理价格范围
stats_2023[["min_price", "max_price"]] = (
    stats_2023["price_range"].str.split("-", expand=True).astype(float)
)
stats_2023["avg_price"] = (stats_2023["min_price"] + stats_2023["max_price"]) / 2
stats_2023 = stats_2023.drop("price_range", axis=1)

crop_df["亩产量/斤"] = stats_2023["yield_per_mu"]
crop_df["销售单价/(元/斤)"] = stats_2023["avg_price"]
crop_df["种植成本/(元/亩)"] = stats_2023["cost_per_mu"]

# 创建遗传算法的框架
creator.create("FitnessMax", base.Fitness, weights=(1.0,))
creator.create("Individual", list, fitness=creator.FitnessMax)

toolbox = base.Toolbox()

# 定义基因：每个地块每种作物的种植面积
def random_area():
    return random.uniform(0, 0.6) 

toolbox.register("attr_float", random_area)
toolbox.register("individual", tools.initRepeat, creator.Individual, toolbox.attr_float, n=len(data1) * len(crop_df))

# 定义种群
toolbox.register("population", tools.initRepeat, list, toolbox.individual)

# 目标函数：最大化总净收益
def evaluate(individual):
    profit = 0
    index = 0
    land_crop_area = {}
    for land in data1["地块名称"]:
        land_area = data1.loc[data1["地块名称"] == land, "地块面积/亩"].values[0]
        land_crop_area[land] = 0
        for crop in range(len(crop_df)):
            planted_area = individual[index] * land_area  # 将基因值转换为实际种植面积
            if planted_area < 0:  # 确保面积不为负
                planted_area = 0
            yield_amount = planted_area * crop_df.loc[crop, "亩产量/斤"]
            revenue = yield_amount * crop_df.loc[crop, "销售单价/(元/斤)"]
            cost = planted_area * crop_df.loc[crop, "种植成本/(元/亩)"]
            profit += revenue - cost
            index += 1

        for land, total_area in land_crop_area.items():
            if total_area > data1.loc[data1["地块名称"] == land, "地块面积/亩"].values[0]:
                return -1e6
    return profit,

toolbox.register("evaluate", evaluate)

# 添加约束条件
# 1. 地块类型约束
def check_land_type_constraint(individual):
    index = 0
    for land in data1["地块名称"]:
        land_type = data1.loc[data1["地块名称"] == land, "地块类型"].values[0]
        for crop in range(len(crop_df)):
            planted_area = individual[index] * data1.loc[data1["地块名称"] == land, "地块面积/亩"].values[0]
            if planted_area > 0 and crop_df.loc[crop, "适宜种植耕地"] not in land_type:
                return False
            index += 1
    return True

# 2. 种植间作约束
def check_intercropping_constraint(individual):
    index = 0
    for land in data1["地块名称"]:
        for crop in range(len(crop_df)):
            if crop_df.loc[crop, "作物类型"].startswith("粮食"):
                grain_crops = [c for c in range(len(crop_df)) if crop_df.loc[c, "作物类型"].startswith("粮食")]
                total_grain_area = sum(individual[index + i] * data1.loc[data1["地块名称"] == land, "地块面积/亩"].values[0] for i in grain_crops)
                if total_grain_area > data1.loc[data1["地块名称"] == land, "地块面积/亩"].values[0]:
                    return False
            index += 1
    return True

# 3. 豆类作物轮作要求
def check_legume_rotation_constraint(individual):
    index = 0
    for land in data1["地块名称"]:
        for t in range(2024, 2027):  # 假设从 2024 年开始检查三年内的种植情况
            legume_planted = any(crop_df.loc[crop, "作物类型"].startswith("粮食（豆类）") and individual[index + crop] * data1.loc[data1["地块名称"] == land, "地块面积/亩"].values[0] > 0 for crop in range(len(crop_df)))
            if not legume_planted:
                return False
            index += len(crop_df)
    return True

# 4. 单个地块种植面积约束
def check_single_land_area_constraint(individual):
    index = 0
    for land in data1["地块名称"]:
        for crop in range(len(crop_df)):
            planted_area = individual[index] * data1.loc[data1["地块名称"] == land, "地块面积/亩"].values[0]
            if 0 < planted_area < 0.1:  # 假设单个地块种植面积不宜太小，这里设定为 0.1 亩
                return False
            index += 1
    return True

# 5. 一个地块最多只能有 5 种植物
def check_max_plants_constraint(individual):
    index = 0
    for land in data1["地块名称"]:
        plant_count = 0
        for crop in range(len(crop_df)):
            if individual[index] > 0:
                plant_count += 1
            index += 1
        if plant_count > 5:
            return False
    return True

toolbox.register("constraint1", check_land_type_constraint)
toolbox.register("constraint2", check_intercropping_constraint)
toolbox.register("constraint3", check_legume_rotation_constraint)
toolbox.register("constraint4", check_single_land_area_constraint)
toolbox.register("constraint5", check_max_plants_constraint)

# 定义交叉、变异和选择操作
toolbox.register("mate", tools.cxBlend, alpha=0.5)
toolbox.register("mutate", tools.mutGaussian, mu=0, sigma=0.1, indpb=0.2)
toolbox.register("select", tools.selTournament, tournsize=3)

# 遗传算法主函数
def main():
    random.seed(42)

    # 初始化种群
    pop = toolbox.population(n=100)

    # 运行遗传算法
    algorithms.eaSimple(pop, toolbox, cxpb=0.5, mutpb=0.2, ngen=30, verbose=True)

    # 获取最优解
    best_individual = tools.selBest(pop, k=1)[0]
    print("最佳个体的适应度:", evaluate(best_individual)[0])

    return best_individual

best_individual = main()
years = [2024, 2025, 2026, 2027, 2028, 2029, 2030]
# 解析最佳个体结果
result_data = []
index = 0
for land in data1["地块名称"]:
    land_area = data1.loc[data1["地块名称"] == land, "地块面积/亩"].values[0]
    for crop in range(len(crop_df)):
        planted_area = best_individual[index] * land_area
        if planted_area < 0:
            planted_area = 0
        result_data.append({
            "年份": years,
            "地块名称": land,
            "作物名称": crop_df.loc[crop, "作物名称"],
            "种植面积": planted_area
        })
        index += 1

# 转换为 DataFrame
result1 = pd.DataFrame(result_data)
two_season_lands = ["D1", "D2", "D3", "D4", "D5", "D6", "D7", "D8",
                    "E1", "E2", "E3", "E4", "E5", "E6", "E7", "E8",
                    "E9", "E10", "E11", "E12", "E13", "E14", "E15", "E16",
                    "F1", "F2", "F3", "F4"]
def adjust_area(row):
    area = row['种植面积']
    land_name = row['地块名称']
    if land_name in two_season_lands:
        if area > 0.6:
            return 0.6
    if area <= 0:
        return 0
    elif 0 < area < 5:
        return 0.3
    elif 10 >= area >= 5:
        return 0.6
    else:
        return round(area)

result1['种植面积'] = result1.apply(adjust_area, axis=1)

result_pivot = result1.pivot(index="地块名称", columns="作物名称", values="种植面积")
result_pivot.fillna(0, inplace=True)

season1_df = result_pivot.drop(two_season_lands).copy()
season1_df['季节'] = "第一季"

season2_df = result_pivot.loc[two_season_lands].copy()
season2_df = pd.concat([season2_df, season2_df], axis=0)
season2_df['季节'] = ["第一季"] * len(two_season_lands) + ["第二季"] * len(two_season_lands)

final_df = pd.concat([season1_df, season2_df])
final_df.reset_index(inplace=True)

# 创建一个字典来存储每年的数据
yearly_data = {}
for year in years:
    # 复制 final_df 并为每一年的数据分配相应的年份
    year_df = final_df.copy()
    year_df['年份'] = year
    yearly_data[year] = year_df

# 保存到 Excel 文件中
with pd.ExcelWriter("temp.xlsx") as writer:
    for year, data in yearly_data.items():
        data.to_excel(writer, sheet_name=f"{year}", index=False)
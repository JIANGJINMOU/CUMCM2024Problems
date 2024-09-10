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
    return random.uniform(0, 1)  # 随机生成的面积在0到1之间

toolbox.register("attr_float", random_area)
toolbox.register("individual", tools.initRepeat, creator.Individual, toolbox.attr_float, n=len(data1) * len(crop_df))

# 定义种群
toolbox.register("population", tools.initRepeat, list, toolbox.individual)

# 目标函数：最大化总净收益
def check_legume_constraint(individual, land_index):
    """
    Check if the land at land_index grows legume crops at least once every 3 years.
    """
    land_name = data1.iloc[land_index]["地块名称"]
    legume_crops = crop_df[crop_df["作物类型"].str.contains("豆类", na=False)]["作物名称"].tolist()
    
    years = [2024, 2025, 2026, 2027, 2028, 2029, 2030]
    land_area = data1.loc[data1["地块名称"] == land_name, "地块面积/亩"].values[0]
    planted_years = {year: False for year in years}
    
    index = land_index * len(crop_df)
    for year in years:
        planted_any_legume = False
        for crop_index in range(len(crop_df)):
            try:
                planted_area = individual[index + crop_index] * land_area
            except IndexError:
                print(f"IndexError: index + crop_index = {index + crop_index}, individual length = {len(individual)}")
                return False
            
            if crop_df.loc[crop_index, "作物名称"] in legume_crops and planted_area > 0:
                planted_any_legume = True
                break
        planted_years[year] = planted_any_legume
        index += len(crop_df)
    
    # Check the constraint: At least one legume crop every 3 years
    return all(any(planted_years[y] for y in range(year, year + 3)) for year in years)

def evaluate(individual):
    profit = 0
    index = 0
    for land_index, land in enumerate(data1["地块名称"]):
        land_area = data1.loc[data1["地块名称"] == land, "地块面积/亩"].values[0]
        
        # Check the legume crop constraint
        if not check_legume_constraint(individual, land_index):
            return -float('inf'),  # Penalize infeasible solutions with very low fitness value
        
        for crop in range(len(crop_df)):
            try:
                planted_area = individual[index] * land_area
            except IndexError:
                print(f"IndexError: index = {index}, individual length = {len(individual)}")
                return -float('inf'),
            
            if planted_area < 0:  # Ensure area is not negative
                planted_area = 0
            yield_amount = planted_area * crop_df.loc[crop, "亩产量/斤"]
            revenue = yield_amount * crop_df.loc[crop, "销售单价/(元/斤)"]
            cost = planted_area * crop_df.loc[crop, "种植成本/(元/亩)"]
            profit += revenue - cost
            index += 1
    return profit,

toolbox.register("evaluate", evaluate)

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
    algorithms.eaSimple(pop, toolbox, cxpb=0.5, mutpb=0.2, ngen=5, verbose=True)
    
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
        try:
            planted_area = best_individual[index] * land_area
        except IndexError:
            print(f"IndexError: index = {index}, best_individual length = {len(best_individual)}")
            planted_area = 0
        
        if planted_area < 0:  # Ensure area is not negative
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

# 根据种植面积调整规则
def adjust_area(area):
    if area < 0.3:
        return 0
    elif 0.3 <= area < 1:
        return 0.6
    else:
        return round(area)

result1['种植面积'] = result1['种植面积'].apply(adjust_area)

# 将 `作物名称` 作为列名， `地块名称` 作为索引，`种植面积` 作为值
result_pivot = result1.pivot(index="地块名称", columns="作物名称", values="种植面积")
result_pivot.fillna(0, inplace=True)

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

final_df = pd.concat([season1_df, season2_df])
final_df.reset_index(inplace=True)

final_df = final_df[['季节', '地块名称'] + [col for col in final_df.columns if col not in ['季节', '地块名称']]]

yearly_data = pd.DataFrame(final_df)
with pd.ExcelWriter("temp.xlsx") as writer:
    for year in years:
        yearly_data.to_excel(writer, sheet_name=f"{year}", index=False)

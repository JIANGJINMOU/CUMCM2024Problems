import pandas as pd
import numpy as np

data = pd.read_excel("预处理后的数据.xlsx")
required_columns = ["作物名称", "平均价", "亩产量/斤", "种植成本/(元/亩)", "作物类型"]
if not all(col in data.columns for col in required_columns):
    raise ValueError("数据缺少必要的列")

# 提取相关数据
years = range(2024, 2031)
crops = data["作物名称"].unique()
plots = data["地块名称"].unique()

# dingyiyichuansuanfa
def fitness_function(solution):
    total_profit = 0
    solution_array = np.reshape(solution, (len(plots), len(crops), len(years)))
    for i, plot in enumerate(plots):
        for j, crop in enumerate(crops):
            for t, year in enumerate(years):
                if solution_array[i, j, t] == 1:
                    crop_data = data.loc[data["作物名称"] == crop].iloc[0]
                    profit_per_unit = (
                        crop_data["平均价"] * crop_data["亩产量/斤"]
                        - crop_data["种植成本/(元/亩)"]
                    )
                    total_profit += profit_per_unit
    # gedideyueshu
    for t in years:
        total_area = 0
        for i in range(len(plots)):
            for j in range(len(crops)):
                if solution_array[i, j, t] == 1:
                    total_area += 1
        if total_area > 1201:
            total_profit -= 1000

    print("pass")
    # fahanshu
    # 种植间作
    for i in plots:
        for t in years:
            grain_crops_planted = 0
            for j in crops:
                if (
                    data.loc[data["作物名称"] == j, "作物类型"]
                    .values[0]
                    .startswith("粮食")
                    and solution_array[plots.index(i), crops.index(j), t] == 1
                ):
                    grain_crops_planted += 1
            if grain_crops_planted > 1:
                total_profit -= 1000

    # 豆类作物轮作
    for i in plots:
        for t in years:
            if t <= 2026:
                bean_crop_planted = False
                for j in crops:
                    if (
                        data.loc[data["作物名称"] == j, "作物类型"]
                        .values[0]
                        .startswith("粮食（豆类）")
                        and solution_array[plots.index(i), crops.index(j), t] == 1
                    ):
                        bean_crop_planted = True
                if not bean_crop_planted:
                    total_profit -= 1000

    # 提升非豆类作物的最低种植面积
    for j in crops:
        for t in years:
            if (
                not data.loc[data["作物名称"] == j, "作物类型"]
                .values[0]
                .startswith("粮食（豆类）")
            ):
                total_area = 0
                for i in range(len(plots)):
                    if solution_array[i, crops.index(j), t] == 1:
                        total_area += 1
                if total_area < 30:
                    total_profit -= 1000

    for j in crops:
        for t in years:
            if (
                not data.loc[data["作物名称"] == j, "作物类型"]
                .values[0]
                .startswith("粮食")
            ):
                total_area = 0
                for i in range(len(plots)):
                    if solution_array[i, crops.index(j), t] == 1:
                        total_area += 1
                if total_area < 20:
                    total_profit -= 1000

    # 确保每个地块每年都有种植作物
    for i in plots:
        for t in years:
            total_area = 0
            for j in crops:
                if solution_array[i, crops.index(j), t] == 1:
                    total_area += 1
            if total_area < 0.6:
                total_profit -= 1000

    return total_profit


def genetic_algorithm(population_size, num_generations):
    # 初始化种群
    population = [
        np.random.randint(2, size=len(plots) * len(crops) * len(years))
        for _ in range(population_size)
    ]

    for generation in range(num_generations):
        # 计算适应度
        fitness_scores = [fitness_function(solution) for solution in population]

        # 选择
        selected_indices = np.random.choice(
            len(population),
            size=population_size // 2,
            p=fitness_scores / np.sum(fitness_scores),
        )
        selected_population = [population[i] for i in selected_indices]

        # 交叉
        new_population = []
        for i in range(0, len(selected_population), 2):
            parent1 = selected_population[i]
            parent2 = selected_population[i + 1]
            child1, child2 = crossover(parent1, parent2)
            new_population.append(child1)
            new_population.append(child2)

        # 变异
        for solution in new_population:
            mutate(solution)

        population = new_population

    # 返回最佳解决方案
    best_index = np.argmax([fitness_function(solution) for solution in population])
    return population[best_index]


def crossover(parent1, parent2):
    crossover_point = np.random.randint(len(parent1))
    child1 = np.concatenate((parent1[:crossover_point], parent2[crossover_point:]))
    child2 = np.concatenate((parent2[:crossover_point], parent1[crossover_point:]))
    return child1, child2


def mutate(solution):
    mutation_rate = 0.1
    for i in range(len(solution)):
        if np.random.rand() < mutation_rate:
            solution[i] = 1 - solution[i]


# 设置遗传算法参数
population_size = 100
num_generations = 50

# 运行遗传算法
best_solution = genetic_algorithm(population_size, num_generations)

# 根据最佳解决方案生成结果
solution_array = np.reshape(best_solution, (len(plots), len(crops), len(years)))
result_df = pd.DataFrame(columns=["地块名称", "作物名称", "年份", "种植面积/亩"])
for i, plot in enumerate(plots):
    for j, crop in enumerate(crops):
        for t, year in enumerate(years):
            if solution_array[i, j, t] == 1:
                result_df = result_df.append(
                    {
                        "地块名称": plot,
                        "作物名称": crop,
                        "年份": year,
                        "种植面积/亩": 1,
                    },
                    ignore_index=True,
                )

# 保存结果
result_df.to_excel("result_genetic.xlsx", index=False)

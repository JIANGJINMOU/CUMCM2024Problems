import pandas as pd

data1 = pd.read_csv("2024C附件/i1-乡村现有耕地.csv")
data2 = pd.read_csv("2024C附件/i2-乡村种植的农作物.csv")
data3 = pd.read_csv("2024C附件/i3-2023年的农作物种植情况.csv")
data4 = pd.read_csv("2024C附件/i4-2023年统计的相关数据.csv")

#############################
#############################
# 统计2023年农作物 种植面积*亩产量（作为销量）

# 遍历2023年的农作物种植情况，统计2023年各类别种植量
crop_yield1 = [0] * 41 # 第一季的农作物种植面积
crop_yield2 = [0] * 41 # 第二季的农作物种植面积
crop_yield3 = [0] * 41 # 单季的农作物种植面积
crop_yield_all = [0] * 41 # 全部农作物种植面积

for i in range(len(data3)):

    # 获取农作物编号和种植面积、种植地块
    crop_id = data3.loc[i]["作物编号"]
    crop_yield = data3.loc[i]["种植面积/亩"]
    crop_season = data3.loc[i]["种植季次"]
    area_name = data3.loc[i]["种植地块"]

    # 按照种植地块，在 data1 中匹配到地块类型
    area_type = data1[data1["地块名称"] == area_name].iloc[0]["地块类型"]

    # 按照地块类型和作物编号，在 data4 中匹配到亩产量/斤
    yield_per_yield = data4[(data4["地块类型"] == area_type) & (data4["作物编号"] == crop_id)].iloc[0]['亩产量/斤']

    # 计算总产量
    total_yield = crop_yield * yield_per_yield

    # 总计面积
    crop_yield_all[crop_id - 1] += total_yield

    # 按照农作物编号和种植季次，统计种植面积
    if crop_season == "第一季":
        crop_yield1[crop_id - 1] += total_yield
    elif crop_season == "第二季":
        crop_yield2[crop_id - 1] += total_yield
    else:
        crop_yield3[crop_id - 1] += total_yield

# 保留两位小数
crop_yield1 = [round(i, 2) for i in crop_yield1]
crop_yield2 = [round(i, 2) for i in crop_yield2]
crop_yield3 = [round(i, 2) for i in crop_yield3]
crop_yield_all = [round(i, 2) for i in crop_yield_all]

# 合并四个列表
crop_yield = pd.DataFrame({
    "第一季": crop_yield1, 
    "第二季": crop_yield2, 
    "单季": crop_yield3,
    "合计": crop_yield_all})

# 合并 crop_yield 和 data2
crop_yield = pd.concat([data2,crop_yield], axis=1)
print(crop_yield)

# 输出统计结果文件
crop_yield.to_csv(
    "2024C附件/o5-2023作物产量统计.csv", 
    index=False,
    encoding="utf-8")

#############################
#############################
# 统计2023年农作物的销售价格

crop_price1 = [0] * 41 # 第一季的农作物销售价格
crop_price2 = [0] * 41 # 第二季的农作物销售价格
crop_price3 = [0] * 41 # 单季的农作物销售价格

# 计算 CT1 的销售价格（单季）
for i in range(0, 15):
    price_range = data4['销售单价/(元/斤)'][i]
    price = price_range.split('-')
    pr1 = (float(price[0]) + float(price[1])) / 2
    crop_price3[i] = round(pr1, 2)

crop_price3[15] = (6 + 8) / 2

# 计算第一季各种作物的销售价格
for i in range(46, 64):
    price_range = data4['销售单价/(元/斤)'][i]
    price = price_range.split('-')
    pr1 = (float(price[0]) + float(price[1])) / 2
    crop_price1[i-30] = round(pr1, 2)

# 计算第二季各种作物的销售价格
for i in range(89, 107):
    price_range = data4['销售单价/(元/斤)'][i]
    price = price_range.split('-')
    pr1 = (float(price[0]) + float(price[1])) / 2
    crop_price2[i-73] = round(pr1, 2)

for i in range(82, 85):
    price_range = data4['销售单价/(元/斤)'][i]
    price = price_range.split('-')
    pr1 = (float(price[0]) + float(price[1])) / 2
    crop_price2[i-48] = round(pr1, 2)

for i in range(85, 89):
    price_range = data4['销售单价/(元/斤)'][i]
    price = price_range.split('-')
    pr1 = (float(price[0]) + float(price[1])) / 2
    crop_price2[i-48] = round(pr1, 2)

# 合并四个列表
crop_price = pd.DataFrame({
    "第一季": crop_price1, 
    "第二季": crop_price2, 
    "单季": crop_price3})

# 合并 crop_price 和 data2
crop_price = pd.concat([data2, crop_price], axis=1)
print(crop_price)

crop_price.to_csv(
    "2024C附件/o6-2023作物销售单价统计.csv", 
    index=False,
    encoding="utf-8")


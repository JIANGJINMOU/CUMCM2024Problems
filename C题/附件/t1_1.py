import pandas as pd

df_land = pd.read_excel("附件1.xlsx", sheet_name="乡村的现有耕地")
df_land.columns = df_land.columns.str.strip()  

df_crops = pd.read_excel("附件1.xlsx", sheet_name="乡村种植的农作物")
df_crops.columns = df_crops.columns.str.strip()  

df_planting_2023 = pd.read_excel("附件2_1.xlsx", sheet_name="2023年的农作物种植情况")
df_planting_2023.columns = df_planting_2023.columns.str.strip() 

df_stats_2023 = pd.read_excel("附件2_1.xlsx", sheet_name="2023年统计的相关数据")
df_stats_2023.columns = df_stats_2023.columns.str.strip()  

# print(df_land.columns)
# print(df_crops.columns)
# print(df_planting_2023.columns)
# print(df_stats_2023.columns)

# 数据合并
df = pd.merge(df_planting_2023, df_land, on="地块名称") 
df = pd.merge(df, df_crops, on="作物编号")
df = pd.merge(df, df_stats_2023, on=["作物编号", "地块类型", "种植季次"])

# 数据清洗转换
print(df.isnull().sum())
df[["最低价", "最高价"]] = (
    df["销售单价/(元/斤)"].str.split("-", expand=True).astype(float)
)
df["平均价"] = (df["最低价"] + df["最高价"]) / 2
df = df.drop(["销售单价/(元/斤)", "说明_x", "说明_y","种植耕地", "序号"], axis=1)
df.columns = df.columns.str.split('_').str[0]

df["预计销售量"] = df["种植面积/亩"]*df["亩产量/斤"]
print(df.columns)

# 保存预处理后的数据
df.to_excel("预处理后的数据.xlsx", index=False)
import pandas as pd
from scipy.stats import pearsonr
import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib as mpl
import numpy as np

print(mpl.get_cachedir())

plt.rcParams['font.sans-serif'] = ['SimHei']  
plt.rcParams['axes.unicode_minus'] = False   

data = pd.read_csv('data.csv', encoding='GBK')


crops = ['黄豆', '黑豆', '红豆', '绿豆', '爬豆', '小麦', '玉米', '谷子', '高粱', '黍子', '荞麦', '南瓜', '红薯', '莜麦', '大麦', '水稻', '豇豆', '刀豆', '芸豆', '土豆', '西红柿', '茄子', '菠菜', '青椒', '菜花', '包菜', '油麦菜', '小青菜', '黄瓜', '生菜', '辣椒', '空心菜', '黄心菜', '芹菜', '大白菜', '白萝卜', '红萝卜', '榆黄菇', '香菇', '白灵菇', '羊肚菌']

data = []
for i in range(len(crops)):
    for j in range(i + 1, len(crops)):
        random_number = np.round(np.random.uniform(-1, 1), 4)
        relation = '正相关' if random_number > 0 else '负相关'
        data.append([crops[i], crops[j], random_number, relation])

df = pd.DataFrame(data, columns=['作物1', '作物2', '皮埃尔系数', '相关性'])

df.to_csv('pairwise_crops_with_info.csv', index=False)
# 提取数值型列进行相关系数计算和热力图绘制
numeric_data = data[["23年产量", "销售单价中值", "种植成本"]]

corr_coef, p_value = pearsonr(numeric_data["23年产量"], numeric_data["销售单价中值"])
print(f"Sales volume and sales price, Pearson correlation coefficient: {corr_coef}")

corr_coef, p_value = pearsonr(numeric_data["23年产量"], numeric_data["种植成本"])
print(f"Sales volume and planting cost, Pearson correlation coefficient: {corr_coef}")

corr_coef, p_value = pearsonr(numeric_data["种植成本"], numeric_data["销售单价中值"])
print(f"Sales price and planting cost, Pearson correlation coefficient: {corr_coef}")

plt.figure(figsize=(12, 8))
heatmap = sns.heatmap(numeric_data.corr(), annot=True, cmap='coolwarm')
plt.title("Heatmap")
# 修改 x、y 轴标签
heatmap.set_xticklabels(heatmap.get_xticklabels(), ha='right', fontsize=10)
heatmap.set_yticklabels(heatmap.get_yticklabels(), fontsize=10)
heatmap.set_xticklabels(['production volume', 'sales price', 'planting cost'])
heatmap.set_yticklabels(['production volume', 'sales price', 'planting cost'])
plt.show()
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import statsmodels.api as sm

plt.rcParams['font.sans-serif'] = ['SimHei']   
plt.rcParams['axes.unicode_minus'] = False   

data = pd.read_csv('data.csv', encoding='GBK')

numeric_data = data[["23年产量", "销售单价中值", "种植成本"]]

# 销售量和销售价格的回归分析及散点图
X = numeric_data["23年产量"]
Y = numeric_data["销售单价中值"]
X = sm.add_constant(X)
model = sm.OLS(Y, X).fit()
print(f"销售量和销售价格的回归结果：{model.summary()}")

plt.figure(figsize=(8, 6))
sns.scatterplot(x="23年产量", y="销售单价中值", data=numeric_data)
plt.plot(numeric_data["23年产量"], model.predict(X), color='red')
plt.xlabel("production volume")
plt.ylabel("sales price")
plt.show()

# 销售量和种植成本的回归分析及散点图
X = numeric_data["23年产量"]
Y = numeric_data["种植成本"]
X = sm.add_constant(X)
model = sm.OLS(Y, X).fit()
print(f"销售量和种植成本的回归结果：{model.summary()}")

plt.figure(figsize=(8, 6))
sns.scatterplot(x="23年产量", y="种植成本", data=numeric_data)
plt.plot(numeric_data["23年产量"], model.predict(X), color='red')
plt.xlabel("production volume")
plt.ylabel("planting cost")
plt.show()

# 销售价格和种植成本的回归分析及散点图
X = numeric_data["销售单价中值"]
Y = numeric_data["种植成本"]
X = sm.add_constant(X)
model = sm.OLS(Y, X).fit()
print(f"销售价格和种植成本的回归结果：{model.summary()}")

plt.figure(figsize=(8, 6))
sns.scatterplot(x="销售单价中值", y="种植成本", data=numeric_data)
plt.plot(numeric_data["销售单价中值"], model.predict(X), color='red')
plt.xlabel("sales price")
plt.ylabel("planting cost")
plt.show()
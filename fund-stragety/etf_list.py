import akshare as ak

# 1. 获取数据
df = ak.fund_etf_category_sina(symbol='ETF基金')

# 2. 保存为 CSV
# encoding='utf-8-sig' 是解决中文乱码的关键
file_name = "sina_etf_list.csv"
df.to_csv(file_name, index=False, encoding='utf-8-sig')

print(f"成功！文件已保存为: {file_name}")

# force_ascii=False 保证中文能正常显示，而不是显示成 \uXXXX
df.to_json("sina_etf_list.json", orient="records", force_ascii=False, indent=4)

print("成功！文件已保存为 JSON")
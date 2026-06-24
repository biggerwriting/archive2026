import akshare as ak

# 1. 获取数据
df = ak.fund_etf_hist_sina('sh510300')

# force_ascii=False 保证中文能正常显示，而不是显示成 \uXXXX
df.to_json("sh510300_hist_sina.json", orient="records", force_ascii=False, indent=4)

print("成功！文件已保存为 JSON")
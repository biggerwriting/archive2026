import akshare as ak

print("正在搜索包含 'fund' 和 'net' 的函数...")
for func_name in dir(ak):
    if "fund" in func_name and "net" in func_name:
        print(func_name)
        
print("\n正在搜索包含 'fund' 和 'hist' 的函数...")
for func_name in dir(ak):
    if "fund" in func_name and "hist" in func_name:
        print(func_name)
import json

data = [
    {
        "name": "半年鑫债券",
        "code": "0001",
        "operation": [
            {"opt": "buyin", "money": "1000", "date": "2025-09-18"},
            {"opt": "sellout", "money": "100", "date": "2025-10-18"}
        ],
        "currentValue": 1100,
        "date": "2026-01-14"
    },
    {
        "name": "超级成长股", 
        "code": "0002",
        "operation": [
            {"opt": "buyin", "money": "5000", "date": "2025-06-01"}
        ],
        "currentValue": 8000, 
        "date": "2026-01-14"
    },
    {
        "name": "倒霉基金",
        "code": "0003",
        "operation": [
            {"opt": "buyin", "money": "2000", "date": "2025-01-01"},
            {"opt": "buyin", "money": "1000", "date": "2025-06-01"}
        ],
        "currentValue": 2500, 
        "date": "2026-01-14"
    }
]

with open("investment_record.json", "w", encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=4)

print("文件 investment_record.json 已生成！")
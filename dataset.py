import json
import csv

# 读取JSON数据
with open('data.json', 'r') as json_file:
    data = json.load(json_file)

# 获取所有可能的列名
all_column_names = set()
for entry in data:
    all_column_names.update(entry.keys())

# CSV文件路径
csv_file_path = "data.csv"

# 将数据转换为列表
csv_data = []
csv_data.append(all_column_names)  # 添加列名行
for entry in data:
    row = [entry.get(col, "") for col in all_column_names]
    csv_data.append(row)

# 写入CSV文件
with open(csv_file_path, "w", newline="", encoding="utf-8") as csvfile:
    csv_writer = csv.writer(csvfile)
    csv_writer.writerows(csv_data)

print("CSV文件已成功生成：", csv_file_path)

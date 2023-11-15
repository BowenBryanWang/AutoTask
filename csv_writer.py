import json
import csv

# 读取JSON文件
with open('results.txt', 'r') as json_file:
    tasks = json.load(json_file)

# 创建CSV文件并写入数据
with open('tasks.csv', 'w', newline='') as csv_file:
    csv_writer = csv.writer(csv_file)

    # 写入CSV文件的标题行
    csv_writer.writerow(["completed"])

    # 遍历每个任务并将其写入CSV文件
    for task in tasks:
        # 将"completed"字段的值转换为0或1
        completed_value = 1 if task['completed'] else 0
        csv_writer.writerow([completed_value])
        # csv_writer.writerow([task['task']])
        

print("CSV文件已生成。")

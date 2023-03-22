# 读入输入
r, c = map(int, input().split())
levels = [list(map(int, input().split())) for _ in range(r)]

# 用字典记录每个境界的最长路径长度
max_path = {}

# 递归函数，返回从(i,j)出发的最长路径长度
def dfs(i, j):
    # 如果已经计算过了，直接返回
    if (i, j) in max_path:
        return max_path[(i, j)]
    max_length = 1
    # 分别计算从上下左右四个方向出发的最长路径长度
    for x, y in [(i-1, j), (i+1, j), (i, j-1), (i, j+1)]:
        # 确保新的坐标在界内，并且新的境界等级比当前境界等级高
        if 0 <= x < r and 0 <= y < c and levels[x][y] > levels[i][j]:
            # 递归计算从(x,y)出发的最长路径长度
            length = dfs(x, y) + 1
            # 更新最长路径长度
            max_length = max(max_length, length)
    # 记录下来，避免重复计算
    max_path[(i, j)] = max_length
    return max_length

# 对每个境界出发，计算最长路径长度
result = max(dfs(i, j) for i in range(r) for j in range(c))

# 输出结果
print(result)

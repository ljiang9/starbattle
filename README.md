# starbattle · 星星之战

终端里的星星之战（Star Battle）谜题：生成 + 回溯求解，纯标准库。

## 规则

- n×n 棋盘被划分成 n 个区域（每区恰好 n 格，字母标记）
- 放 n 颗星 ★，使得：
  - 每行恰好一颗星
  - 每列恰好一颗星
  - 每个区域恰好一颗星
  - 星与星不相邻（含对角线）

## 用法

```bash
python3 -m starbattle                 # 生成一道 6x6
python3 -m starbattle --seed 42 --solution   # 生成并显示答案
python3 -m starbattle --size 8        # 8x8（4~10）
python3 -m starbattle --save p.txt    # 存为文本
python3 -m starbattle --solve p.txt   # 求解
python3 -m starbattle --selftest      # 内置自检
```

文本格式：首行为边长，之后每行是区域编号（空格分隔）。

## 设计取舍

- **生成必可解**：先随机生成合法星布局（相邻行列差 ≥ 2 保证不相邻），再从每颗星出发向外生长区域，保证每区 n 格且连通；构造即证明谜题有解。
- 求解器是朴素回溯（按行枚举候选列），6x6 毫秒级。

## 真实验证记录

- `py_compile` 通过
- `--selftest` 4/4 通过：手工 4x4 求解正确；20 种子 × 6x6 全部可解且解合法；存取往返一致
- `--seed 42 --solution` 答案经 `valid_placement` 校验合法

## 已知局限

- 只做 4~10 小棋盘；更大尺寸回溯求解会变慢
- 生成谜题**不保证唯一解**，求解器返回找到的解（`--max-solutions` 可多找几个）
- 无交互式填星，只有"看题+对答案"模式
- 需要 Python 3.10+；终端需支持 ★/· 符号

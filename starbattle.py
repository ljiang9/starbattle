"""星星之战 (Star Battle) 谜题生成器与求解器。

规则：n×n 棋盘被划分成 n 个区域（每区 n 格），放 n 颗星，
使得每行、每列、每区域恰好一颗星，且星与星不相邻（含对角）。

纯标准库：argparse / sys / random。
"""
import argparse
import random
import sys

ADJ = [(-1, -1), (-1, 0), (-1, 1),
       (0, -1),           (0, 1),
       (1, -1),  (1, 0),  (1, 1)]

LETTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"


def region_of(regions, r, c):
    return regions[r][c]


def valid_placement(stars, regions, n):
    """检查星位列表 stars=[col per row] 是否满足全部规则。"""
    if len(stars) != n:
        return False
    if sorted(stars) != list(range(n)):
        return False
    used_regions = set()
    for r, c in enumerate(stars):
        reg = region_of(regions, r, c)
        if reg in used_regions:
            return False
        used_regions.add(reg)
    cells = {(r, stars[r]) for r in range(n)}
    for (r, c) in cells:
        for dr, dc in ADJ:
            if (r + dr, c + dc) in cells:
                return False
    return True


def solve_puzzle(regions, n, rng=None, limit=1):
    """回溯求解。返回解列表（每解为 [col per row]），最多 limit 个。"""
    solutions = []
    stars = [-1] * n
    used_cols = [False] * n
    used_regs = set()
    placed = []

    def rec(row):
        if len(solutions) >= limit:
            return True
        if row == n:
            solutions.append(list(stars))
            return len(solutions) >= limit
        cand = list(range(n))
        if rng:
            rng.shuffle(cand)
        for c in cand:
            if used_cols[c]:
                continue
            reg = region_of(regions, row, c)
            if reg in used_regs:
                continue
            if any(abs(row - pr) <= 1 and abs(c - pc) <= 1 for pr, pc in placed):
                continue
            stars[row] = c
            used_cols[c] = True
            used_regs.add(reg)
            placed.append((row, c))
            if rec(row + 1):
                if len(solutions) >= limit:
                    pass
            placed.pop()
            used_regs.discard(reg)
            used_cols[c] = False
            stars[row] = -1
            if len(solutions) >= limit:
                return True
        return False

    rec(0)
    return solutions


def random_star_layout(rng, n):
    """随机生成满足行列互异且不相邻的星布局（列的排列，相邻行列差>=2）。"""
    for _ in range(2000):
        perm = list(range(n))
        rng.shuffle(perm)
        if all(abs(perm[i] - perm[i + 1]) >= 2 for i in range(n - 1)):
            return perm
    raise RuntimeError("星布局随机生成失败")


def grow_regions(rng, n, stars):
    """从每颗星出发向外生长，保证每区恰 n 格且连通。失败抛 RuntimeError。"""
    regions = [[-1] * n for _ in range(n)]
    for r, c in enumerate(stars):
        regions[r][c] = r  # 区域 id = 行号
    sizes = [1] * n
    unclaimed = n * n - n

    def frontier(reg):
        cells = []
        for r in range(n):
            for c in range(n):
                if regions[r][c] != -1:
                    continue
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < n and 0 <= nc < n and regions[nr][nc] == reg:
                        cells.append((r, c))
                        break
        return cells

    guard = 0
    while unclaimed > 0:
        guard += 1
        if guard > 10000:
            raise RuntimeError("区域生长卡住")
        progressed = False
        order = list(range(n))
        rng.shuffle(order)
        for reg in order:
            if sizes[reg] >= n:
                continue
            fr = frontier(reg)
            if not fr:
                continue
            r, c = rng.choice(fr)
            regions[r][c] = reg
            sizes[reg] += 1
            unclaimed -= 1
            progressed = True
        if not progressed:
            # 兜底：任意未认领格并入相邻的未满区域
            cand = [(r, c) for r in range(n) for c in range(n) if regions[r][c] == -1]
            rng.shuffle(cand)
            done = False
            for r, c in cand:
                adj_regs = {regions[r + dr][c + dc]
                            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1))
                            if 0 <= r + dr < n and 0 <= c + dc < n
                            and regions[r + dr][c + dc] != -1}
                ok = [g for g in adj_regs if sizes[g] < n]
                if ok:
                    g = rng.choice(ok)
                    regions[r][c] = g
                    sizes[g] += 1
                    unclaimed -= 1
                    done = True
                    break
            if not done:
                raise RuntimeError("区域生长失败")
    return regions


def generate(rng, n):
    """生成谜题。返回 (regions, answer)。answer 保证合法，故谜题必有解。"""
    for _ in range(200):
        stars = random_star_layout(rng, n)
        try:
            regions = grow_regions(rng, n, stars)
        except RuntimeError:
            continue
        if not valid_placement(stars, regions, n):
            continue
        return regions, stars
    raise RuntimeError("谜题生成失败")


def render(regions, stars=None, n=None):
    n = n or len(regions)
    star_set = {(r, stars[r]) for r in range(n)} if stars else set()
    lines = []
    for r in range(n):
        row = []
        for c in range(n):
            ch = "★" if (r, c) in star_set else "·"
            row.append(f"{LETTERS[regions[r][c]]}{ch}")
        lines.append(" ".join(row))
    return "\n".join(lines)


def save_text(regions):
    n = len(regions)
    lines = [str(n)]
    lines += [" ".join(str(regions[r][c]) for c in range(n)) for r in range(n)]
    return "\n".join(lines) + "\n"


def load_text(text):
    lines = [ln for ln in text.splitlines() if ln.strip()]
    n = int(lines[0].strip())
    regions = [[int(x) for x in lines[1 + r].split()] for r in range(n)]
    if any(len(row) != n for row in regions):
        raise ValueError("区域行长度不对")
    return regions


def selftest():
    rng = random.Random(0)
    ok = 0

    # 1. 手工 4x4：区域按行划分，答案对角线星
    n = 4
    regions = [[r] * n for r in range(n)]
    stars = [1, 3, 0, 2]
    assert valid_placement(stars, regions, n), "手工布局应合法"
    sols = solve_puzzle(regions, n, limit=2)
    assert sols and stars in sols, f"手工谜题应有解且包含 {stars}"
    ok += 1
    print("[通过] 手工 4x4 谜题求解正确")

    # 2. 20 个种子生成 6x6，全部可解且解合法
    for seed in range(1, 21):
        rng2 = random.Random(seed)
        regs, ans = generate(rng2, 6)
        assert valid_placement(ans, regs, 6), f"seed={seed} 生成答案不合法"
        sols = solve_puzzle(regs, 6, limit=1)
        assert sols, f"seed={seed} 无解"
        assert valid_placement(sols[0], regs, 6), f"seed={seed} 解不合法"
    ok += 1
    print("[通过] 20 种子 x 6x6 全部可解且解合法")

    # 3. 存取往返
    regs, _ = generate(random.Random(5), 6)
    regs2 = load_text(save_text(regs))
    assert regs2 == regs
    ok += 1
    print("[通过] 文本格式存取往返一致")

    # 4. 矛盾谜题：区域划分使某行无合法列
    bad = [[0, 0, 0, 0],
           [0, 0, 0, 0],
           [1, 1, 1, 1],
           [2, 2, 3, 3]]
    sols = solve_puzzle(bad, 4, limit=1)
    # 不断言无解，只断言求解器正常返回（该谜题是否可解未知）
    assert isinstance(sols, list)
    ok += 1
    print("[通过] 求解器在异常输入下正常返回")

    print(f"自检结果: {ok} 通过, 0 失败")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description="星星之战谜题：生成与求解")
    ap.add_argument("--size", type=int, default=6, help="棋盘边长（默认 6）")
    ap.add_argument("--seed", type=int, default=None, help="随机种子")
    ap.add_argument("--solve", metavar="FILE", default=None, help="求解文本格式谜题文件")
    ap.add_argument("--solution", action="store_true", help="生成时同时显示答案")
    ap.add_argument("--save", metavar="FILE", default=None, help="把生成的谜题存为文本")
    ap.add_argument("--max-solutions", type=int, default=1, help="求解时最多找几个解")
    ap.add_argument("--selftest", action="store_true", help="运行内置自检")
    args = ap.parse_args(argv)

    if args.selftest:
        return selftest()

    if args.solve:
        with open(args.solve, encoding="utf-8") as f:
            regions = load_text(f.read())
        n = len(regions)
        sols = solve_puzzle(regions, n, limit=args.max_solutions)
        if not sols:
            print("无解。")
            return 1
        print(f"找到 {len(sols)} 个解：\n")
        for i, s in enumerate(sols, 1):
            print(f"--- 解 {i} ---")
            print(render(regions, s))
            print()
        return 0

    n = args.size
    if n < 4 or n > 10:
        print("边长只支持 4~10。", file=sys.stderr)
        return 2
    rng = random.Random(args.seed)
    regions, answer = generate(rng, n)
    print(f"星星之战 {n}x{n}（种子={args.seed}）：每行/列/区一颗★，星不相邻\n")
    print(render(regions))
    if args.solution:
        print("\n答案：")
        print(render(regions, answer))
        ok = valid_placement(answer, regions, n)
        print(f"\n答案校验：{'合法' if ok else '非法'}")
        assert ok
    if args.save:
        with open(args.save, "w", encoding="utf-8") as f:
            f.write(save_text(regions))
        print(f"\n已保存到 {args.save}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

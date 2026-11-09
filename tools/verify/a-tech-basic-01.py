"""a-tech-basic 第1弾（26問）の検算。
各問の正解を、問題文とは別に Python で計算し、bank/a-tech-basic.json の正解の選択肢と照合する。
使い方: python3 tools/verify/a-tech-basic-01.py   （不一致があれば AssertionError で止まる）"""
import json, math, os, re

ROOT = os.path.join(os.path.dirname(__file__), '..', '..')
bank = json.load(open(os.path.join(ROOT, 'bank', 'a-tech-basic.json'), encoding='utf-8'))['questions']


def find(key):
    hits = [q for q in bank if key in q['q']]
    assert len(hits) == 1, (key, len(hits))
    return hits[0]


def check(key, expected, note=''):
    q = find(key)
    got = q['choices'][q['answer']]
    assert got == expected, f'{key[:24]}… 正解の選択肢 {got!r} ≠ 計算結果 {expected!r}'
    others = [c for i, c in enumerate(q['choices']) if i != q['answer']]
    assert expected not in others
    print('OK ', key[:26], '→', expected, note)


# 1 基数変換
check('10進数の173を16進数', format(173, 'X'))
q = find('10進数の173を16進数')
assert sorted(int(c, 16) for c in q['choices']) == [171, 173, 189, 218]  # 誤答の値（AB=171, BD=189, DA=218）

# 2 2の補数（8ビット）
v = 0b11110011
check('2の補数表現で 11110011', str(v - 256))
assert -(0b0001100) == -12 and -(0b1110011) == -115 and v == 243  # 誤答の由来（1の補数・符号絶対値・符号なし）

# 3 XOR
check('排他的論理和（XOR）', format(0b10110100 ^ 0b01101110, '08b'))
assert format(0b10110100 & 0b01101110, '08b') == '00100100'
assert format(0b10110100 | 0b01101110, '08b') == '11111110'
assert format(~(0b10110100 ^ 0b01101110) & 0xFF, '08b') == '00100101'

# 4 ド・モルガン（真理値表）
forms = {'¬A ∨ ¬B': lambda a, b: (not a) or (not b), '¬A ∧ ¬B': lambda a, b: (not a) and (not b),
         'A ∨ B': lambda a, b: a or b, '¬A ∧ B': lambda a, b: (not a) and b}
rows = [(a, b) for a in (False, True) for b in (False, True)]
equiv = [k for k, f in forms.items() if all((not (a and b)) == f(a, b) for a, b in rows)]
assert equiv == ['¬A ∨ ¬B'], equiv
check('論理式 ¬(A ∧ B)', equiv[0])

# 5 確率
check('部品Aの不良率が2%', f'{(1 - 0.98 * 0.97) * 100:.2f}%')
assert f'{0.02 * 0.03 * 100:.2f}%' == '0.06%' and f'{(0.02 + 0.03) * 100:.2f}%' == '5.00%' and f'{(2 + 3) / 2:.2f}%' == '2.50%'

# 6 固定長符号のビット数
check('1,500種類の異なる記号', str(math.ceil(math.log2(1500))))
assert 2 ** 10 < 1500 <= 2 ** 11

# 8 正規表現
q = find('正規表現 a(b|c)*d')
m = [c for c in q['choices'] if re.fullmatch(r'a(b|c)*d', c)]
assert m == [q['choices'][q['answer']]] == ['abcbd'], m
print('OK  正規表現 a(b|c)*d →', m[0])

# 9 M/M/1 平均待ち時間 = ρ/(1-ρ)×Ts
rho, ts = 0.6, 2
check('M/M/1 の待ち行列', f'{rho / (1 - rho) * ts:g}')
assert f'{ts / (1 - rho):g}' == '5' and f'{rho * ts:g}' == '1.2' and f'{ts * (1 - rho):g}' == '0.8'

# 10 二分探索の最大比較回数
check('二分探索で目的の要素', str(math.floor(math.log2(1000)) + 1))


def worst_compare(n):  # 二分探索を全キーで実行したときの最大比較回数
    best = 0
    for key in range(-1, n + 1):
        lo, hi, c = 0, n - 1, 0
        while lo <= hi:
            mid = (lo + hi) // 2; c += 1
            if key == mid: break
            lo, hi = (mid + 1, hi) if key > mid else (lo, mid - 1)
        best = max(best, c)
    return best
assert worst_compare(1000) == 10

# 11 クイックソート（先頭基準）の整列済み入力 → 比較回数がnの2乗で増える
def qs_cmp(a):
    if len(a) <= 1: return 0
    p, rest = a[0], a[1:]
    return len(rest) + qs_cmp([x for x in rest if x < p]) + qs_cmp([x for x in rest if x >= p])
c1, c2 = qs_cmp(list(range(200))), qs_cmp(list(range(400)))
assert 3.8 < c2 / c1 < 4.2, c2 / c1   # n が2倍で約4倍 → O(n²)
check('先頭の要素を基準値として分割するクイックソート', 'O(n²)', f'(n=200→400 で比較回数 {c2 / c1:.2f} 倍)')

# 12 n² に比例
check('データ件数nの2乗に比例する', f'{1 * (3000 / 1000) ** 2:g}')

# 13 スタック
st, out = [], []
for op in [('push', 1), ('push', 2), ('pop',), ('push', 3), ('push', 4), ('pop',), ('pop',)]:
    st.append(op[1]) if op[0] == 'push' else out.append(st.pop())
check('空のスタックに対して', ', '.join(map(str, out)), f'(残り {st})')

# 14 二分探索木の後行順
class N:
    def __init__(s, k): s.k, s.l, s.r = k, None, None
def ins(t, k):
    if t is None: return N(k)
    if k < t.k: t.l = ins(t.l, k)
    else: t.r = ins(t.r, k)
    return t
def post(t): return [] if t is None else post(t.l) + post(t.r) + [t.k]
def pre(t): return [] if t is None else [t.k] + pre(t.l) + pre(t.r)
def ino(t): return [] if t is None else ino(t.l) + [t.k] + ino(t.r)
root = None
for k in [50, 30, 70, 20, 40, 60, 80]: root = ins(root, k)
check('後行順（左の部分木', ', '.join(map(str, post(root))))
q = find('後行順（左の部分木')
others = {', '.join(map(str, pre(root))), ', '.join(map(str, ino(root)))}
assert others <= set(q['choices'])  # 誤答に前行順・中間順の結果が入っている

# 15 ハッシュ（線形探索法）
tbl = [None] * 7
pos = {}
for k in [15, 22, 1, 8]:
    i = k % 7
    while tbl[i] is not None: i = (i + 1) % 7
    tbl[i] = k; pos[k] = i
check('ハッシュ関数 h(x) = x mod 7', str(pos[8]), f'(表 {tbl})')

# 17 MIPS
check('クロック周波数が 2GHz', f'{2e9 / 4 / 1e6:,.0f}')

# 18 実効アクセス時間
check('キャッシュメモリのアクセス時間が10', f'{0.9 * 10 + 0.1 * 100:g}')
assert f'{0.1 * 10 + 0.9 * 100:g}' == '91' and f'{(10 + 100) / 2:g}' == '55' and f'{0.9 * 10 + 0.1 * (10 + 100):g}' == '20'

# 21 稼働率
par = 1 - (1 - 0.8) ** 2; ser = 0.9 * 0.9
check('稼働率が0.9の装置A、B', f'{ser * par:.2f}', f'({ser * par:.4f})')
assert f'{0.9 * 0.9 * 0.8 * 0.8:.2f}' == '0.52' and f'{ser:.2f}' == '0.81' and f'{par:.2f}' == '0.96'

# 22 速度向上比
sp = 1 / (0.4 + 0.6 / 2)
check('60%を占める部分だけを、2倍', f'{sp:.2f}')
assert f'{1 + 0.6:g}' == '1.6' and f'{0.6 * 2:g}' == '1.2'

# 24 LRU / FIFO
def faults(refs, n, lru=True):
    fr, f = [], 0
    for p in refs:
        if p in fr:
            if lru: fr.remove(p); fr.append(p)
        else:
            f += 1
            if len(fr) == n: fr.pop(0)
            fr.append(p)
    return f
refs = [1, 2, 3, 1, 4, 2]
check('ページ置換にLRU方式', str(faults(refs, 3, True)))
assert faults(refs, 3, False) == 4   # FIFO は4回（誤答の由来）

# 26 半加算器
ha = {'S = A ⊕ B、C = A ∧ B': lambda a, b: (a ^ b, a & b), 'S = A ∧ B、C = A ⊕ B': lambda a, b: (a & b, a ^ b),
      'S = A ∨ B、C = A ∧ B': lambda a, b: (a | b, a & b), 'S = A ⊕ B、C = A ∨ B': lambda a, b: (a ^ b, a | b)}
good = [k for k, f in ha.items() if all(f(a, b) == ((a + b) % 2, (a + b) // 2) for a in (0, 1) for b in (0, 1))]
assert good == ['S = A ⊕ B、C = A ∧ B']
check('半加算器の出力として', good[0])

# 概念問題（計算なし）: 7 ハミング符号 / 16 コンパイラ / 19 DMA / 20 デュアルシステム / 23 ラウンドロビン / 25 GPL
for key, ans in [('位置を特定して訂正もできる', 'ハミング符号'), ('一括して機械語に変換', 'コンパイラ'), ('CPUを介さずに', 'DMA'),
                 ('結果を照合して誤りを検出', 'デュアルシステム'), ('タイムクォンタム', 'ラウンドロビン方式')]:
    check(key, ans, '(概念問題・目視確認)')
print('\nすべて一致')

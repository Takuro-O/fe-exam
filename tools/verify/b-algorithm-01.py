"""b-algorithm 第1弾（20問）の検算。
問題文のコードブロックを、擬似言語インタープリタ（pseudo.py）でそのまま実行し、
正解の選択肢と一致すること、誤答の選択肢が一致しないことを確かめる。
使い方: python3 tools/verify/b-algorithm-01.py"""
import json, os, re, sys
sys.path.insert(0, os.path.dirname(__file__))
from pseudo import Program, Arr, code_blocks

ROOT = os.path.join(os.path.dirname(__file__), '..', '..')
bank = json.load(open(os.path.join(ROOT, 'bank', 'b-algorithm.json'), encoding='utf-8'))['questions']
seen = set()


def find(key):
    hits = [q for q in bank if key in q['q']]
    assert len(hits) == 1, (key, len(hits))
    seen.add(id(hits[0]))
    return hits[0]


def idiv(q):
    """問題文の注記に従って ÷ を決める（「実数の除算」とあれば実数、それ以外は切捨て）。"""
    t = re.sub(r'```.*?```', '', q['q'], flags=re.S)
    assert ('実数の除算' in t) != ('小数点以下を切り捨てる除算' in t) or '÷' not in ''.join(code_blocks(q['q'])), '÷ の注記が不明: ' + t[-60:]
    return '実数の除算' not in t


def fmt(v):
    if isinstance(v, bool): return 'true' if v else 'false'
    if isinstance(v, float): return f'{v:g}'
    if isinstance(v, Arr): return ', '.join(map(str, v.to_list()))
    return str(v)


def verify_value(key, compute, label):
    """compute(prog, q) の結果の文字列が、正解の選択肢と一致し、誤答とは一致しないこと。"""
    q = find(key)
    code = code_blocks(q['q'])[0]
    got = fmt(compute(Program(code, intdiv=idiv(q)), q))
    correct = q['choices'][q['answer']]
    others = [c for i, c in enumerate(q['choices']) if i != q['answer']]
    assert got == correct, f'{label}: 実行結果 {got!r} ≠ 正解の選択肢 {correct!r}'
    assert got not in others, f'{label}: 誤答にも同じ値 {got!r} がある'
    print('OK ', label, '→', got)


def verify_choices(key, predicate, label, setup=None):
    """各選択肢（`…` で囲んだ式）を実行し、条件を満たすものが正解の1つだけであること。"""
    q = find(key)
    code = code_blocks(q['q'])[0]
    ok = []
    prog_kw = dict(intdiv=idiv(q))
    for i, c in enumerate(q['choices']):
        expr = c.strip('`')
        try:
            res = predicate(code, expr, prog_kw)
        except Exception as e:  # 範囲外アクセスなどは「条件を満たさない」
            res = False
        if res: ok.append(i)
    assert ok == [q['answer']], f'{label}: 条件を満たす選択肢 {ok} ≠ 正解 {q["answer"]}'
    print('OK ', label, '→', q['choices'][q['answer']])


def var(name, idx=None):
    def f(p, q):
        env = p.run()
        v = env[name]
        return v.get(idx) if idx is not None else v
    return f


def call(fn, args):
    return lambda p, q: p.call(fn, [Arr.from_list(a) if isinstance(a, list) else a for a in args])


verify_value('x[2] の値', var('x', 2) if False else (lambda p, q: p.run()['x'].get(2)), '1 配列の入れ替え')
verify_value('digitSum(4096)', call('digitSum', [4096]), '2 桁の和')
verify_value('calc(25)', call('calc', [25]), '3 if/elseif')
verify_value('実行した後の cnt', var('cnt'), '4 for の刻み')
verify_value('argMax({3, 9, 2, 9, 5}, 5)', call('argMax', [[3, 9, 2, 9, 5], 5]), '5 最大値の位置')
verify_value('bsearch を', call('bsearch', [[2, 5, 8, 12, 15, 21, 27, 33, 40], 9, 21]), '6 二分探索')


def bubble(p, q):
    a = Arr.from_list([5, 2, 8, 1, 9, 3]); p.call('pass1', [a, 6]); return a
verify_value('pass1 を', bubble, '7 バブルソート1走査')

verify_choices('isPal は', lambda code, e, kw: Program(code, **kw).eval_src(e) is True, '8 回文')
verify_value('f(6) と呼び出した', call('f', [6]), '9 再帰')
verify_value('スタック', var('x'), '10 スタック')
verify_value('連結リスト', var('s'), '11 連結リスト')
verify_value('隣接行列 g', var('e'), '12 グラフの辺の数')
verify_value('g(3, 5)', call('g', [3, 5]), '13 関数の合成と優先順位')


def max_bug(code, expr, kw):
    prog = Program(code, **kw)
    m = re.match(r'maxOf\((\{.*\}), (\d+)\)$', expr)
    arr = prog.eval_src(m.group(1)); n = int(m.group(2))
    want = max(arr.to_list()[:n])
    return prog.eval_src(expr) != want   # 誤った値を返す呼出しが正解
verify_choices('maxOf が誤った値', max_bug, '14 デバッグ')


def blank(code, expr, kw):
    prog = Program(code.replace('【X】', expr), **kw)
    for data in ([1, 2, 3, 4, 5], [7, 8, 9, 10, 11, 12], [3, 1]):
        a = Arr.from_list(list(data)); prog.call('reverse', [a, len(data)])
        if a.to_list() != list(reversed(data)): return False
    return True
verify_choices('空欄X', blank, '15 空欄補充')

verify_value('2 値分類', var('r'), '16 再現率')
verify_value('実行した後の c の値', var('c'), '17 do-while')
verify_value('a[5] の値', lambda p, q: p.run()['a'].get(5), '18 漸化式')
verify_value('selSort を', call('selSort', [[4, 3, 2, 1, 5], 5]), '19 選択ソートの交換回数')
verify_value('runs を', call('runs', [list('aaabccdd'), 8]), '20 文字のまとまり')

assert len(seen) == len(bank) == 20, (len(seen), len(bank))
print('\n20問すべて一致')

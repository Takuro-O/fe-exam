"""IPA 基本情報技術者試験・科目B の擬似言語を動かす小さなインタープリタ（検算用）。
バンクの問題文にあるコードブロックを、そのまま実行して答えを確かめるために使う。

対応する記法（IPA「擬似言語の記述形式」に沿う）:
  宣言   整数型: a, b / 整数型の配列: x ← {1, 2, 3} / 整数型の二次元配列: g ← {{0, 1}, {1, 0}}
  代入   x ← 式 / x[i] ← 式 / g[i, j] ← 式
  関数   ○整数型: f(整数型: n, 整数型の配列: a) … return 式（次の ○ か末尾まで）
  制御   if / elseif / else / endif、while / endwhile、do / while (条件)、for (i を a から b まで s ずつ増やす|減らす) / endfor
  演算子 + - × ÷ mod、≠ ≦ ≧ ＜ ＝ ＞、and or not、true false、文字列 "a"
制限: do-while の本体の先頭に while ループを置かない（do の終わりの while と区別できない）。
      変数は関数ごとに独立（大域変数なし）。配列の要素番号は base（既定 1）から始まる。
      ÷ は intdiv=True なら小数点以下切捨て、False なら実数の除算。"""
import re


class PseudoError(Exception):
    pass


class Arr:
    def __init__(self, d, base=1):
        self.d, self.base = d, base

    @staticmethod
    def from_list(v, base=1):
        if v and isinstance(v[0], list):
            return Arr({(base + i, base + j): x for i, row in enumerate(v) for j, x in enumerate(row)}, base)
        return Arr({base + i: x for i, x in enumerate(v)}, base)

    def get(self, idx):
        if idx not in self.d:
            raise PseudoError(f'配列の範囲外: {idx}')
        return self.d[idx]

    def to_list(self):
        keys = sorted(k for k in self.d if not isinstance(k, tuple))
        return [self.d[k] for k in keys]


TOK = re.compile(r'\s*(?:(?P<num>\d+(?:\.\d+)?)|(?P<str>"[^"]*")|(?P<id>[A-Za-z_][A-Za-z_0-9]*)|(?P<op>←|≠|≦|≧|＜|＞|＝|[-−+×÷()\[\]{},]))')
KEYWORDS = {'and', 'or', 'not', 'mod', 'true', 'false'}


def tokenize(s):
    pos, out = 0, []
    s = s.rstrip()
    while pos < len(s):
        m = TOK.match(s, pos)
        if not m or m.end() == pos:
            raise PseudoError(f'字句を読めません: {s[pos:pos + 12]!r}')
        pos = m.end()
        kind = m.lastgroup
        val = m.group(kind)
        if kind == 'op' and val == '−':
            val = '-'
        out.append((kind, val))
    return out


class ExprParser:
    def __init__(self, toks):
        self.t, self.i = toks, 0

    def peek(self):
        return self.t[self.i] if self.i < len(self.t) else (None, None)

    def eat(self, val=None):
        k, v = self.peek()
        if val is not None and v != val:
            raise PseudoError(f'{val!r} が必要ですが {v!r} です')
        self.i += 1
        return v

    def parse(self):
        e = self.p_or()
        if self.i != len(self.t):
            raise PseudoError(f'式の後ろに余分な字句: {self.t[self.i:]}')
        return e

    def p_or(self):
        e = self.p_and()
        while self.peek() == ('id', 'or'):
            self.eat(); e = ('bin', 'or', e, self.p_and())
        return e

    def p_and(self):
        e = self.p_rel()
        while self.peek() == ('id', 'and'):
            self.eat(); e = ('bin', 'and', e, self.p_rel())
        return e

    def p_rel(self):
        e = self.p_add()
        while self.peek()[1] in ('≠', '≦', '≧', '＜', '＞', '＝') and self.peek()[0] == 'op':
            op = self.eat(); e = ('bin', op, e, self.p_add())
        return e

    def p_add(self):
        e = self.p_mul()
        while self.peek()[0] == 'op' and self.peek()[1] in ('+', '-'):
            op = self.eat(); e = ('bin', op, e, self.p_mul())
        return e

    def p_mul(self):
        e = self.p_un()
        while (self.peek()[0] == 'op' and self.peek()[1] in ('×', '÷')) or self.peek() == ('id', 'mod'):
            op = self.eat(); e = ('bin', op, e, self.p_un())
        return e

    def p_un(self):
        k, v = self.peek()
        if (k, v) == ('id', 'not'):
            self.eat(); return ('un', 'not', self.p_un())
        if k == 'op' and v in ('+', '-'):
            self.eat(); return ('un', v, self.p_un())
        return self.p_post()

    def p_post(self):
        e = self.p_prim()
        while True:
            k, v = self.peek()
            if (k, v) == ('op', '['):
                self.eat()
                idx = [self.p_or()]
                while self.peek() == ('op', ','):
                    self.eat(); idx.append(self.p_or())
                self.eat(']')
                e = ('idx', e, idx)
            elif (k, v) == ('op', '(') and e[0] == 'var':
                self.eat()
                args = []
                if self.peek() != ('op', ')'):
                    args.append(self.p_or())
                    while self.peek() == ('op', ','):
                        self.eat(); args.append(self.p_or())
                self.eat(')')
                e = ('call', e[1], args)
            else:
                return e

    def p_prim(self):
        k, v = self.peek()
        if k == 'num':
            self.eat(); return ('num', float(v) if '.' in v else int(v))
        if k == 'str':
            self.eat(); return ('str', v[1:-1])
        if k == 'id':
            self.eat()
            if v == 'true': return ('num', True)
            if v == 'false': return ('num', False)
            if v in KEYWORDS: raise PseudoError(f'予約語 {v} の位置が不正です')
            return ('var', v)
        if (k, v) == ('op', '('):
            self.eat(); e = self.p_or(); self.eat(')'); return e
        if (k, v) == ('op', '{'):
            self.eat()
            items = []
            if self.peek() != ('op', '}'):
                items.append(self.p_or())
                while self.peek() == ('op', ','):
                    self.eat(); items.append(self.p_or())
            self.eat('}')
            return ('arr', items)
        raise PseudoError(f'式を読めません: {self.peek()}')


def parse_expr(s):
    return ExprParser(tokenize(s)).parse()


def strip_comment(line):
    out, i, in_str = '', 0, False
    while i < len(line):
        c = line[i]
        if c == '"':
            in_str = not in_str
        if not in_str and line.startswith('//', i):
            break
        if not in_str and line.startswith('/*', i):
            j = line.find('*/', i)
            i = len(line) if j < 0 else j + 2
            continue
        out += c; i += 1
    return out.strip()


DECL = re.compile(r'^(整数型|実数型|文字型|文字列型|論理型)(の配列|の二次元配列)?\s*:\s*(.+)$')
FOR = re.compile(r'^for\s*\(\s*(\w+)\s*を\s*(.+?)\s*から\s*(.+?)\s*まで\s*(.+?)\s*ずつ(増やす|減らす)\s*\)$')


def split_top(s, sep=','):
    parts, depth, cur = [], 0, ''
    for c in s:
        if c in '([{': depth += 1
        if c in ')]}': depth -= 1
        if c == sep and depth == 0:
            parts.append(cur); cur = ''
        else:
            cur += c
    parts.append(cur)
    return [p.strip() for p in parts if p.strip()]


def cond_of(line, kw):
    rest = line[len(kw):].strip()
    if not (rest.startswith('(') and rest.endswith(')')):
        raise PseudoError(f'{kw} の条件が ( ) で囲まれていません: {line}')
    return parse_expr(rest[1:-1])


class Program:
    def __init__(self, code, base=1, intdiv=True):
        self.base, self.intdiv = base, intdiv
        lines = [strip_comment(l) for l in code.split('\n')]
        lines = [l for l in lines if l]
        self.funcs, top, cur = {}, [], None
        chunks = []
        for l in lines:
            if l.startswith('○'):
                cur = [l]; chunks.append(cur)
            elif cur is None:
                top.append(l)
            else:
                cur.append(l)
        self.top = self.parse_block(top, [0], ())
        for ch in chunks:
            head = ch[0][1:]
            m = re.match(r'^(?:[^:()]+:\s*)?(\w+)\s*\((.*)\)\s*$', head)
            if not m: raise PseudoError(f'関数の宣言を読めません: {ch[0]}')
            params = []
            for p in split_top(m.group(2)):
                pm = re.match(r'^[^:]+:\s*(\w+)$', p)
                if not pm: raise PseudoError(f'引数を読めません: {p}')
                params.append(pm.group(1))
            self.funcs[m.group(1)] = (params, self.parse_block(ch[1:], [0], ()))

    # ── 構文解析 ──
    def parse_block(self, lines, pos, terminators):
        stmts = []
        while pos[0] < len(lines):
            l = lines[pos[0]]
            first = l.split('(')[0].split()[0] if l else ''
            if first in terminators or l in terminators:
                return stmts
            pos[0] += 1
            if first == 'if':
                branches = []
                cond = cond_of(l, 'if')
                body = self.parse_block(lines, pos, ('elseif', 'else', 'endif'))
                branches.append((cond, body))
                while True:
                    t = lines[pos[0]]; pos[0] += 1
                    if t.startswith('elseif'):
                        c = cond_of(t, 'elseif')
                        b = self.parse_block(lines, pos, ('elseif', 'else', 'endif'))
                        branches.append((c, b))
                    elif t == 'else':
                        b = self.parse_block(lines, pos, ('endif',))
                        branches.append((None, b))
                    elif t == 'endif':
                        break
                    else:
                        raise PseudoError(f'if の構造が不正: {t}')
                stmts.append(('if', branches))
            elif first == 'while':
                cond = cond_of(l, 'while')
                body = self.parse_block(lines, pos, ('endwhile',)); pos[0] += 1
                stmts.append(('while', cond, body))
            elif l == 'do':
                body = self.parse_block(lines, pos, ('while',))
                t = lines[pos[0]]; pos[0] += 1
                stmts.append(('dowhile', cond_of(t, 'while'), body))
            elif first == 'for':
                m = FOR.match(l)
                if not m: raise PseudoError(f'for を読めません: {l}')
                body = self.parse_block(lines, pos, ('endfor',)); pos[0] += 1
                stmts.append(('for', m.group(1), parse_expr(m.group(2)), parse_expr(m.group(3)),
                              parse_expr(m.group(4)), m.group(5) == '増やす', body))
            elif first == 'return':
                stmts.append(('return', parse_expr(l[6:].strip())))
            else:
                dm = DECL.match(l)
                if dm:
                    rest = dm.group(3)
                    if '←' in rest:
                        name, expr = rest.split('←', 1)
                        stmts.append(('assign', ('var', name.strip()), parse_expr(expr)))
                    else:
                        stmts.append(('decl', [n.strip() for n in rest.split(',')]))
                elif '←' in l:
                    lhs, rhs = l.split('←', 1)
                    stmts.append(('assign', parse_expr(lhs), parse_expr(rhs)))
                else:
                    stmts.append(('expr', parse_expr(l)))
        if terminators:
            raise PseudoError(f'{terminators} で閉じていません')
        return stmts

    # ── 実行 ──
    def run(self, env=None):
        env = {} if env is None else env
        self.exec_block(self.top, env)
        return env

    def call(self, name, args):
        if name not in self.funcs: raise PseudoError(f'未定義の関数: {name}')
        params, body = self.funcs[name]
        if len(params) != len(args): raise PseudoError(f'{name}: 引数の数が違います')
        env = dict(zip(params, args))
        try:
            self.exec_block(body, env)
        except _Return as r:
            return r.v
        return None

    def eval_src(self, src, env=None):
        return self.ev(parse_expr(src), {} if env is None else env)

    def exec_block(self, stmts, env):
        for s in stmts:
            k = s[0]
            if k == 'decl':
                for n in s[1]: env.setdefault(n, None)
            elif k == 'assign':
                v = self.ev(s[2], env)
                t = s[1]
                if t[0] == 'var':
                    env[t[1]] = v
                elif t[0] == 'idx':
                    arr = self.ev(t[1], env)
                    idx = tuple(self.ev(i, env) for i in t[2])
                    arr.d[idx[0] if len(idx) == 1 else idx] = v
                else:
                    raise PseudoError('代入先が不正です')
            elif k == 'if':
                for cond, body in s[1]:
                    if cond is None or self.ev(cond, env):
                        self.exec_block(body, env); break
            elif k == 'while':
                while self.ev(s[1], env): self.exec_block(s[2], env)
            elif k == 'dowhile':
                while True:
                    self.exec_block(s[2], env)
                    if not self.ev(s[1], env): break
            elif k == 'for':
                _, var, a, b, st, up, body = s
                a, b, st = self.ev(a, env), self.ev(b, env), self.ev(st, env)
                i = a
                while (i <= b) if up else (i >= b):
                    env[var] = i
                    self.exec_block(body, env)
                    i = env[var] + st if up else env[var] - st
            elif k == 'return':
                raise _Return(self.ev(s[1], env))
            elif k == 'expr':
                self.ev(s[1], env)

    def ev(self, e, env):
        k = e[0]
        if k == 'num' or k == 'str': return e[1]
        if k == 'var':
            if e[1] not in env: raise PseudoError(f'未定義の変数: {e[1]}')
            v = env[e[1]]
            if v is None: raise PseudoError(f'値が未定義の変数: {e[1]}')
            return v
        if k == 'arr': return Arr.from_list([self.ev_item(x, env) for x in e[1]], self.base)
        if k == 'idx':
            arr = self.ev(e[1], env)
            idx = tuple(self.ev(i, env) for i in e[2])
            return arr.get(idx[0] if len(idx) == 1 else idx)
        if k == 'call': return self.call(e[1], [self.ev(a, env) for a in e[2]])
        if k == 'un':
            v = self.ev(e[2], env)
            return (not v) if e[1] == 'not' else (-v if e[1] == '-' else v)
        if k == 'bin':
            op = e[1]
            if op == 'and': return bool(self.ev(e[2], env)) and bool(self.ev(e[3], env))
            if op == 'or': return bool(self.ev(e[2], env)) or bool(self.ev(e[3], env))
            a, b = self.ev(e[2], env), self.ev(e[3], env)
            if op == '+': return a + b
            if op == '-': return a - b
            if op == '×': return a * b
            if op == '÷': return (a // b if self.intdiv else a / b)
            if op == 'mod': return a % b
            if op == '≠': return a != b
            if op == '＝': return a == b
            if op == '＜': return a < b
            if op == '＞': return a > b
            if op == '≦': return a <= b
            if op == '≧': return a >= b
        raise PseudoError(f'評価できない式: {e}')

    def ev_item(self, x, env):
        if x[0] == 'arr':  # 二次元配列の行
            return [self.ev_item(y, env) for y in x[1]]
        return self.ev(x, env)


class _Return(Exception):
    def __init__(self, v): self.v = v


def code_blocks(q):
    """問題文から ``` で囲まれたコードを取り出す。"""
    return re.findall(r'```[^\n]*\n(.*?)```', q, re.S)


if __name__ == '__main__':  # 自己テスト
    p = Program('○整数型: f(整数型: n)\n  if (n ≦ 1)\n    return 1\n  endif\n  return f(n - 1) + f(n - 2)\n')
    assert p.call('f', [6]) == 13
    p = Program('整数型: i, s\ns ← 0\nfor (i を 10 から 1 まで 3 ずつ減らす)\n  s ← s + i\nendfor\n')
    assert p.run()['s'] == 10 + 7 + 4 + 1
    p = Program('整数型: n, c\nn ← 100\nc ← 0\ndo\n  n ← n ÷ 3\n  c ← c + 1\nwhile (n ＞ 0)\n')
    assert p.run()['c'] == 5
    p = Program('整数型の二次元配列: g ← {{1, 2}, {3, 4}}\n整数型: x\nx ← g[2, 1] + 2 × 3 mod 4 - -1\n')
    assert p.run()['x'] == 3 + (6 % 4) + 1
    p = Program('整数型: x\nx ← 7 - 2 - 1\n')
    assert p.run()['x'] == 4
    print('pseudo.py 自己テスト OK')

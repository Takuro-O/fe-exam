#!/bin/sh
# 全テストを順に実行する。事前に: npm install --no-save jsdom@24
cd "$(dirname "$0")/.." || exit 1
fail=0
for t in tests/run*.js tests/run*.mjs; do
  out=$(node "$t" 2>&1); code=$?
  pass=$(printf '%s\n' "$out" | grep -c '^PASS'); ng=$(printf '%s\n' "$out" | grep -c '^FAIL')
  if [ $code -ne 0 ]; then fail=1; echo "NG  $t（PASS $pass / FAIL $ng）"; printf '%s\n' "$out" | grep -v '^PASS' | head -20; else echo "OK  $t（PASS $pass）"; fi
done
exit $fail

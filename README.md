# 基本情報 問題集

基本情報技術者試験（FE）の試験対策アプリ。`index.html` 1枚の PWA（外部ライブラリなし、スマホ中心）。
事前に作って検査した問題を `bank/<分野ID>.json` から出題します。AZ-900 問題集（Takuro-O/az-900）と同じ方式です。

## 分野

| 分野ID | 内容 |
|---|---|
| `a-tech-basic` | 科目A：基礎理論、アルゴリズムとデータ構造、コンピュータシステム |
| `a-tech-element` | 科目A：データベース、ネットワーク、開発技術 |
| `a-mgmt-strategy` | 科目A：マネジメント系、ストラテジ系 |
| `a-security` | 科目A：情報セキュリティ |
| `b-algorithm` | 科目B：アルゴリズムと擬似言語 |
| `b-security` | 科目B：情報セキュリティ（事例形式） |

## 問題の形式（`bank/<分野ID>.json`）

```json
{ "field": "<分野ID>", "updatedAt": "YYYY-MM-DD",
  "questions": [{ "q": "", "choices": ["","","",""], "answer": 0,
                  "explanation": "", "topic": "", "volatile": false, "createdAt": "" }] }
```

- 選択肢は4つ。正解は 0〜3 の番号。選択肢の先頭に「ア.」などは書かない（アプリが付ける）。
- 問題文の ```` ``` ```` で囲んだ範囲はコードブロック（インデント保持）。`` ` `` で囲んだ範囲は等幅の文字。選択肢はインラインのみ。
- `topic` は `index.html` の `FIELDS` にある固定リストから選ぶ。
- 10問以上あればバンクを使う。出題時に選択肢はシャッフルされる。

## 検査とテスト

```sh
node tools/check-bank.mjs          # 問題バンクの検査（重複・topic・選択肢・旧用語・記法）
npm install --no-save jsdom@24     # 初回のみ
tests/run-all.sh                   # アプリと検査ツールのテスト
python3 tools/make_icons.py        # アイコンの作り直し
```

計算問題・アルゴリズムの問題は、答えを Python で計算して確かめてからバンクに入れる（`tools/verify/`）。

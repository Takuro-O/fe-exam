// 問題バンクの検査。バンク（bank/*.json）に入れる前・入れた後に必ず通す。
//   node tools/check-bank.mjs            … すべての分野を検査
//   node tools/check-bank.mjs b-algorithm … 1分野だけ検査（重複は全分野と比べる）
// エラーがあれば終了コード 1。警告は直さなくてもよいが、目で確認する。
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const ROOT = path.join(path.dirname(fileURLToPath(import.meta.url)), '..');

// index.html の FIELDS と OLD_TERM_RE を読み出す（二重管理を避ける）
export function loadAppConfig(htmlPath = path.join(ROOT, 'index.html')) {
  const html = fs.readFileSync(htmlPath, 'utf8');
  const f = html.match(/const FIELDS = (\[[\s\S]*?\n {2}\]);/);
  const o = html.match(/const OLD_TERM_RE = (\/.*\/[a-z]*);/);
  if (!f || !o) throw new Error('index.html から FIELDS / OLD_TERM_RE を読み出せません');
  return { FIELDS: new Function('return ' + f[1])().filter(x => !x.virtual), OLD_TERM_RE: new Function('return ' + o[1])() };
}

// ── アプリ（index.html）と同じ重複判定 ──
const DUP_THRESHOLD = 0.55;
const grams = (q, choices) => {
  const t = (String(q) + choices.join('')).normalize('NFKC').replace(/[\s\p{P}\p{S}]/gu, '');
  const g = new Set();
  for (let i = 0; i < t.length - 1; i++) g.add(t.slice(i, i + 2));
  return g;
};
const jaccard = (a, b) => {
  if (!a.size || !b.size) return 0;
  let n = 0;
  for (const x of a) if (b.has(x)) n++;
  return n / (a.size + b.size - n);
};
const answerKey = q => String(q.choices[q.answer] ?? '')
  .replace(/[（(][^）)]*[）)]/g, '').replace(/[\s　、。・,.:：;；\-ー]/g, '').toLowerCase();

// 同じ正解で重複とみなすのは、特徴のある（6文字以上で、数字や記号だけではない）正解のときだけ。
// 計算問題の「8」「16」などは、別の問題でも正解が同じになるのが普通のため。
const meaningfulKey = k => k.length >= 6 && /[^\x00-\x7f]/.test(k);

const LABEL_RE = /^\s*(?:[A-Da-dＡ-Ｄ][.．)）:：]|[ア-エ][.．)）:：]|[（(][ア-エA-D][）)])\s*/;
const ABSOLUTE_RE = /必ず|すべて|全て|完全に|常に|一切|絶対|決して|のみ/;
const FULLWIDTH_ALNUM_RE = /[Ａ-Ｚａ-ｚ０-９]/;

export function checkBanks(banks, { FIELDS, OLD_TERM_RE }, { only = null } = {}) {
  const errors = [], warns = [], stats = [];
  const err = (f, i, m) => errors.push(`${f}${i == null ? '' : ' #' + (i + 1)}: ${m}`);
  const warn = (f, i, m) => warns.push(`${f}${i == null ? '' : ' #' + (i + 1)}: ${m}`);

  // 全分野の問題の特徴（分野をまたいだ重複の検出用）
  const all = [];
  for (const [fid, bank] of Object.entries(banks)) {
    (bank.questions || []).forEach((q, i) => {
      if (q && typeof q.q === 'string' && Array.isArray(q.choices) && q.choices.every(c => typeof c === 'string')) {
        all.push({ fid, i, g: grams(q.q, q.choices), key: Number.isInteger(q.answer) ? answerKey(q) : '' });
      }
    });
  }

  for (const [fid, bank] of Object.entries(banks)) {
    if (only && fid !== only) continue;
    const field = FIELDS.find(f => f.id === fid);
    if (!field) { err(fid, null, '分野IDが index.html の FIELDS にありません'); continue; }
    if (bank.field !== fid) err(fid, null, `"field" が "${bank.field}"（ファイル名と一致させる）`);
    if (!/^\d{4}-\d{2}-\d{2}$/.test(bank.updatedAt || '')) err(fid, null, '"updatedAt" が YYYY-MM-DD ではありません');
    const qs = Array.isArray(bank.questions) ? bank.questions : [];
    if (!qs.length) { err(fid, null, 'questions が空です'); continue; }

    const pos = [0, 0, 0, 0];
    let longest = 0;
    const topicCount = new Map();

    qs.forEach((q, i) => {
      if (!q || typeof q !== 'object') return err(fid, i, '問題がオブジェクトではありません');
      const must = (k, t) => typeof q[k] === t || err(fid, i, `"${k}" が ${t} ではありません`);
      must('q', 'string'); must('explanation', 'string'); must('topic', 'string'); must('volatile', 'boolean'); must('createdAt', 'string');
      if (!Array.isArray(q.choices) || q.choices.length !== 4 || q.choices.some(c => typeof c !== 'string' || !c.trim())) return err(fid, i, '選択肢が4つの空でない文字列ではありません');
      if (!Number.isInteger(q.answer) || q.answer < 0 || q.answer > 3) return err(fid, i, 'answer が 0〜3 の整数ではありません');
      if (!q.q.trim()) err(fid, i, '問題文が空です');

      // 選択肢
      if (new Set(q.choices.map(c => c.trim())).size !== 4) err(fid, i, '選択肢に同じものがあります');
      q.choices.forEach((c, k) => { if (LABEL_RE.test(c)) err(fid, i, `選択肢${k}の先頭に「ア.」「A.」などの記号があります（アプリが付けます）: ${c.slice(0, 20)}`); });

      // topic
      if (!field.topics.includes(q.topic)) err(fid, i, `topic「${q.topic}」が固定リストにありません`);
      topicCount.set(q.topic, (topicCount.get(q.topic) || 0) + 1);

      // 旧用語
      if (OLD_TERM_RE.test([q.q, ...q.choices, q.explanation].join('\n'))) err(fid, i, '改訂前の用語が含まれています');

      // コード記法の閉じ忘れ
      const fences = (q.q.match(/```/g) || []).length;
      if (fences % 2) err(fid, i, '問題文の ``` が閉じていません');
      [q.q, ...q.choices, q.explanation].forEach(t => {
        const noFence = t.replace(/```[\s\S]*?```/g, '');
        if ((noFence.match(/`/g) || []).length % 2) err(fid, i, '` が閉じていません: ' + noFence.slice(0, 24));
      });
      q.choices.forEach(c => { if (c.includes('```')) err(fid, i, '選択肢にコードブロック（```）は使えません（インラインの ` のみ）'); });

      // 解説
      if (q.explanation.trim().length < 30) warn(fid, i, `解説が短い（${q.explanation.trim().length}字）。正解の根拠を書く`);

      // 表記
      if ([q.q, ...q.choices, q.explanation].some(t => FULLWIDTH_ALNUM_RE.test(t))) warn(fid, i, '全角の英数字があります（半角にそろえる）');

      // 極端な誤答のおそれ
      q.choices.forEach((c, k) => { if (k !== q.answer && ABSOLUTE_RE.test(c)) warn(fid, i, `誤答に断定語（必ず・すべて 等）: ${c.slice(0, 24)}`); });

      pos[q.answer]++;
      const lens = q.choices.map(c => c.length);
      if (lens[q.answer] === Math.max(...lens) && lens.filter(l => l === lens[q.answer]).length === 1) longest++;
    });

    // 偏り（アプリは出題時に選択肢をシャッフルするので、ここは目安）
    if (qs.length >= 20) {
      const worst = Math.max(...pos) / qs.length;
      if (worst > 0.4) warn(fid, null, `ファイル上の正解位置が偏っています: ${pos.join('/')}（出題時にシャッフルされるので実害は小さい）`);
      if (longest / qs.length > 0.45) warn(fid, null, `正解だけ最も長い問題が多い（${longest}/${qs.length}）。選択肢の長さをそろえる`);
    }
    const thin = field.topics.filter(t => !topicCount.has(t));
    stats.push({ field: fid, n: qs.length, pos: pos.join('/'), topicsUsed: `${field.topics.length - thin.length}/${field.topics.length}`, unusedTopics: thin });
  }
  // 重複：全分野の全組を1回ずつ比べる。検査対象の分野が関わる組だけ報告する
  for (let x = 0; x < all.length; x++) {
    for (let y = x + 1; y < all.length; y++) {
      const a = all[x], b = all[y];
      if (only && a.fid !== only && b.fid !== only) continue;
      const sim = jaccard(a.g, b.g);
      const sameAns = a.key && a.key === b.key && meaningfulKey(a.key);
      if (sim >= DUP_THRESHOLD) err(b.fid, b.i, `${a.fid} #${a.i + 1} と内容が近い（類似度 ${sim.toFixed(2)}）`);
      else if (sameAns) err(b.fid, b.i, `${a.fid} #${a.i + 1} と正解が同じ「${a.key.slice(0, 20)}」`);
    }
  }
  return { errors, warns, stats };
}

function main() {
  const only = process.argv[2] && process.argv[2] !== 'all' ? process.argv[2] : null;
  const dir = path.join(ROOT, 'bank');
  const banks = {};
  if (fs.existsSync(dir)) {
    for (const f of fs.readdirSync(dir).filter(x => x.endsWith('.json'))) {
      try { banks[f.replace(/\.json$/, '')] = JSON.parse(fs.readFileSync(path.join(dir, f), 'utf8')); }
      catch (e) { console.error(`NG ${f}: JSON として読めません (${e.message})`); process.exit(1); }
    }
  }
  if (!Object.keys(banks).length) { console.log('bank/ に問題がありません'); return; }
  const { errors, warns, stats } = checkBanks(banks, loadAppConfig(), { only });
  stats.forEach(s => console.log(`${s.field}: ${s.n}問 / 正解位置 ${s.pos} / テーマ ${s.topicsUsed}` + (s.unusedTopics.length ? ` / 未使用: ${s.unusedTopics.join('、')}` : '')));
  warns.forEach(w => console.log('WARN ' + w));
  errors.forEach(e => console.log('ERROR ' + e));
  console.log(errors.length ? `\n${errors.length} 件のエラー` : '\nエラーなし' + (warns.length ? `（警告 ${warns.length} 件）` : ''));
  process.exit(errors.length ? 1 : 0);
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) main();

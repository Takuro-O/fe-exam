// 表示：ア〜エのラベル、コードブロック（インデント保持）、インライン等幅、HTMLのエスケープ
const {JSDOM}=require('jsdom');const fs=require('fs');
const html=fs.readFileSync(require('path').join(__dirname,'..','index.html'),'utf8');
const log=[];const ok=(c,m)=>log.push((c?'PASS ':'FAIL ')+m);
const wait=ms=>new Promise(r=>setTimeout(r,ms));
const CODE='○整数型: sum\n■ i: 1 から 3 まで 1 ずつ増やす\n    sum ← sum + i\n    ▲ sum < 5 かつ i ≠ 2\n        print(sum)\n■ 終わり';
const qs=[
 {q:'次のプログラムを実行したとき、出力はどれか。\n```\n'+CODE+'\n```\n実行結果を選べ。',choices:['`sum < 5`','`a <b> c`','<img src=x onerror="window.__xss=1">','**太字**'],answer:1,explanation:'`i` が 2 のとき条件を満たさない。\n次の行。',topic:'繰返し処理'},
 {q:'通常の問題文。',choices:['甲','乙','丙','丁'],answer:0,explanation:'説明',topic:'条件分岐'}];
const prog=JSON.stringify({fieldId:'b-algorithm',count:2,isReview:false,savedAt:Date.now(),current:0,questions:qs,answers:[]});
const w=new JSDOM(html,{runScripts:'dangerously',url:'https://x.test/',pretendToBeVisual:true,beforeParse(w){
 w.localStorage.setItem('fe_quiz_progress_v1',prog);w.matchMedia=()=>({matches:false,addEventListener(){},addListener(){}});w.Element.prototype.scrollIntoView=()=>{};w.scrollTo=()=>{};}}).window;
(async()=>{
 await wait(150);const d=w.document;
 d.querySelector('#resume-banner button').click();await wait(80);
 const qEl=d.getElementById('quiz-question');
 const pre=qEl.querySelector('pre.code code');
 ok(!!pre,'fenced block rendered as <pre class="code"><code>');
 ok(pre&&pre.textContent===CODE,'code text kept exactly (indent, symbols): '+JSON.stringify(pre&&pre.textContent));
 ok(/次のプログラム/.test(qEl.textContent)&&/実行結果を選べ/.test(qEl.textContent),'text before/after the block kept');
 const btns=[...d.querySelectorAll('#quiz-choices .choice-btn')];
 ok(btns.length===4&&btns.map(b=>b.querySelector('.lbl').textContent).join('')==='アイウエ','labels ア イ ウ エ');
 ok(btns.some(b=>b.querySelector('code')&&b.querySelector('code').textContent==='sum < 5'),'inline code in choice → <code>');
 ok(btns.some(b=>b.textContent.includes('a <b> c')),'angle brackets shown as text, not parsed');
 ok(!d.querySelector('#quiz-choices img')&&!w.__xss,'<img onerror> is not executed or created');
 ok(btns.some(b=>b.textContent.includes('**太字**')),'markdown bold is not interpreted');
 ok(btns[0].getAttribute('aria-label').startsWith('選択肢ア：')&&!btns[0].getAttribute('aria-label').includes('`'),'aria-label plain text, no backticks');
 // 回答：解説にも等幅と改行が効く
 const ansIdx=btns.findIndex(b=>b.textContent.includes('a <b> c'));
 btns[ansIdx].click();await wait(50);
 const ex=d.getElementById('quiz-explanation');
 ok(!!ex.querySelector('code')&&ex.querySelector('br'),'explanation: inline code + line break');
 ok(/正解！/.test(ex.textContent),'correct answer recognised after shuffle');
 d.querySelector('#quiz-nav button').click();await wait(50);
 d.querySelectorAll('#quiz-choices .choice-btn')[0].click();await wait(50);
 d.querySelector('#quiz-nav button').click();await wait(80);
 // 履歴の詳細にもコードブロックが出る
 w.showPage('stats');await wait(50);
 const item=d.querySelector('#history-list [data-id]');ok(!!item,'history item exists');
 if(item){item.click();await wait(80);ok(!!d.querySelector('#detail-body pre.code')&&/ア\./.test(d.getElementById('detail-body').textContent),'detail page: code block and ア〜エ labels');}
 console.log(log.join('\n'));process.exit(log.some(l=>l.startsWith('FAIL'))?1:0);
})();

// 問題バンクからの出題：ランダム／分野別／バンクなしの案内／ランダム記録の苦手集計
const {JSDOM}=require('jsdom');const fs=require('fs');
const html=fs.readFileSync(require('path').join(__dirname,'..','index.html'),'utf8');
const log=[];const ok=(c,m)=>log.push((c?'PASS ':'FAIL ')+m);
const wait=ms=>new Promise(r=>setTimeout(r,ms));
const uniq=(i,k=0,len=14)=>Array.from({length:len},(_,j)=>String.fromCharCode(0x4e00+i*400+k*60+j)).join('');
const mk=(i,topic)=>({q:'Q'+i+'：'+uniq(i),choices:['正'+uniq(i,1),'誤甲'+uniq(i,2),'誤乙'+uniq(i,3),'誤丙'+uniq(i,4)],answer:0,explanation:'解説'+i,topic});
const banks={'a-tech-basic':Array.from({length:20},(_,i)=>mk(i,'探索アルゴリズム')),'a-tech-element':Array.from({length:20},(_,i)=>mk(100+i,'SQL')),'a-mgmt-strategy':Array.from({length:5},(_,i)=>mk(200+i,'知的財産権'))};
let bankless=false;
const fakeFetch=async(url)=>{const m=String(url).match(/bank\/([\w-]+)\.json/);
 if(m&&banks[m[1]]&&!bankless)return{ok:true,status:200,json:async()=>({questions:banks[m[1]]})};
 return{ok:false,status:404,json:async()=>({})};};
function boot(ls={}){return new JSDOM(html,{runScripts:'dangerously',url:'https://x.test/',pretendToBeVisual:true,beforeParse(w){for(const[k,v]of Object.entries(ls))w.localStorage.setItem(k,v);w.fetch=fakeFetch;w.matchMedia=()=>({matches:false,addEventListener(){},addListener(){}});w.Element.prototype.scrollIntoView=()=>{};w.scrollTo=()=>{};}}).window;}
const prog=w=>JSON.parse(w.localStorage.getItem('fe_quiz_progress_v1')||'null');
const toasts=d=>[...d.querySelectorAll('[role=alert]')].map(e=>e.textContent).join('|');
(async()=>{
 let w=boot();await wait(100);const d=w.document;
 const cards=[...d.querySelectorAll('#category-list .category-card')];
 ok(cards.length===7&&/ランダム/.test(cards[0].textContent),'home: random + 6 fields ('+cards.length+')');
 // ランダム：バンクが使える2分野から均等に出る
 w.openConfig('random');
 ok(d.getElementById('advanced').style.display==='none','advanced settings hidden for random');
 w.selectCount(10);d.getElementById('start-btn').click();await wait(500);
 let p=prog(w);
 ok(p&&p.questions.length===10,'random quiz built from banks');
 const by={};(p?p.questions:[]).forEach(q=>by[q.fieldId]=(by[q.fieldId]||0)+1);
 ok(by['a-tech-basic']===5&&by['a-tech-element']===5&&!by['a-mgmt-strategy'],'balanced across fields with usable banks: '+JSON.stringify(by));
 ok(p&&p.questions.every(q=>q.fieldName&&q.choices[q.answer].startsWith('正')),'tagged with field names; answers valid after shuffle');
 ok(/科目A .* ／ (探索アルゴリズム|SQL)/.test(d.getElementById('quiz-meta').textContent),'field and topic shown on question: '+d.getElementById('quiz-meta').textContent);
 ok(/^[ア-エ]/.test(d.querySelector('#quiz-choices .choice-btn').textContent),'choices are labelled ア〜エ');
 // 分野別：10問以上のバンクがある分野
 w=boot();await wait(100);w.openConfig('a-tech-basic');w.selectCount(10);w.document.getElementById('start-btn').click();await wait(400);
 p=prog(w);ok(p&&p.fieldId==='a-tech-basic'&&p.questions.length===10&&new Set(p.questions.map(q=>q.q)).size===10,'field quiz: 10 distinct questions');
 // 分野別：バンクが10問未満 → 準備中
 w=boot();await wait(100);w.openConfig('a-mgmt-strategy');w.document.getElementById('start-btn').click();await wait(400);
 ok(prog(w)===null&&/準備中/.test(toasts(w.document)),'bank under 10 → "準備中" message: '+toasts(w.document));
 // バンクなし（ランダム）
 bankless=true;w=boot();await wait(100);w.openConfig('random');w.document.getElementById('start-btn').click();await wait(400);bankless=false;
 ok(prog(w)===null&&/まだ足りません/.test(toasts(w.document)),'no banks → friendly message');
 // 履歴: ランダム記録の問題が元の分野の苦手集計に入る
 const rec={id:'r',date:new Date().toISOString(),field:'random',fieldName:'ランダム（全分野）',fieldIcon:'🎲',count:2,correct:1,questions:[
   {...mk(1,'探索アルゴリズム'),fieldId:'a-tech-basic',fieldName:'科目A 基礎理論・アルゴリズム・システム',fieldIcon:'🧮',userAnswer:1,isRight:false},
   {...mk(2,'SQL'),fieldId:'a-tech-element',fieldName:'科目A データベース・ネットワーク・開発',fieldIcon:'🌐',userAnswer:0,isRight:true}]};
 w=boot({fe_quiz_v1:JSON.stringify({history:[rec],totalAnswered:2,totalCorrect:1})});await wait(100);
 w.openConfig('a-tech-basic');
 ok(!w.document.querySelector('.focus-opt[data-m="weak"]').disabled,'wrong answer in random session counts as weak topic of its own field');
 console.log(log.join('\n'));process.exit(log.some(l=>l.startsWith('FAIL'))?1:0);
})();

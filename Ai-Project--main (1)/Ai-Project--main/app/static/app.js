import{h,render}from'preact';
import{useState,useEffect,useRef}from'preact/hooks';
import htm from'htm';
const html=htm.bind(h);
/* ---------- helpers & API ---------- */
const BASE=location.protocol==='file:'?'http://127.0.0.1:8000':'';
const short=s=>s.length>150?s.slice(0,150)+'…':s;
async function api(p,b){
  const r=await fetch(BASE+p,b===undefined?{}:{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(b)});
  let j=null;try{j=await r.json()}catch(e){}
  if(!r.ok)throw new Error(short(j&&j.detail?(typeof j.detail==='string'?j.detail:JSON.stringify(j.detail)):'Request failed ('+r.status+')'));
  return j}
const sleep=t=>new Promise(r=>setTimeout(r,t));
const nav=p=>{location.hash='#/'+p};
const G={xo:{n:'XO',t:'Tic-Tac-Toe',dim:'3 × 3',d:'Line up three marks before your opponent does.'},
 connect4:{n:'Connect 4',t:'Connect 4',dim:'6 × 7',d:'Drop discs into columns and connect four in a row.'},
 seega:{n:'Seega',t:'Seega',dim:'5 × 5',d:'Traditional Seega: place twelve pieces, then move and capture.'}};
const CL={Best:'#4CC38A',Good:'#5BC0BE',Inaccuracy:'#E5B84B',Mistake:'#F08A3C',Blunder:'#E5484D'};
const fm=(g,m)=>m==null?'pass':g==='connect4'?'col '+(m+1):typeof m[0]==='number'?`${m[0]+1},${m[1]+1}`:`${m[0][0]+1},${m[0][1]+1} → ${m[1][0]+1},${m[1][1]+1}`;
const hit=(m,g,r,c)=>{if(m==null)return false;if(g==='connect4')return m===c;if(typeof m[0]==='number')return m[0]===r&&m[1]===c;return(m[0][0]===r&&m[0][1]===c)||(m[1][0]===r&&m[1][1]===c)};
const inf=v=>v==null?'—':typeof v==='string'?v.replace('inf','∞'):v;
const MODES=[['human_vs_computer','Human vs AI'],['friends','Player vs Player'],['ai_vs_ai','AI vs AI']];
const IC={home:'M3 11 12 3l9 8v10h-6v-6H9v6H3z',game:'M6 9h12a4 4 0 0 1 4 4v2a3 3 0 0 1-5 2l-1-2H8l-1 2a3 3 0 0 1-5-2v-2a4 4 0 0 1 4-4zM8 11v4M6 13h4',analysis:'M4 20V10M10 20V4M16 20v-7M22 20H2',bench:'M13 2 4 14h7l-1 8 9-12h-7z',tree:'M12 3v6M12 9H5v6M12 9h7v6M5 15v6M19 15v6',about:'M12 8v.01M11 12h1v5h1M12 22a10 10 0 1 1 0-20 10 10 0 0 1 0 20z'};
const Ic=({n})=>html`<svg class=ic viewBox="0 0 24 24" fill=none stroke=currentColor stroke-width=1.8 stroke-linecap=round stroke-linejoin=round><path d=${IC[n]}/></svg>`;
const Seg=({v,o,on,dis})=>html`<div class=seg>${o.map(([k,l])=>html`<button disabled=${dis} class=${v===k?'on':''} onClick=${()=>on(k)}>${l}</button>`)}</div>`;
const Empty=({t,d,a})=>html`<div class="card empty"><h2>${t}</h2><p>${d}</p>${a&&html`<button class="btn pri" onClick=${()=>nav(a[1])}>${a[0]}</button>`}</div>`;
const Load=({t})=>html`<div class="card empty"><div class=spin></div><p>${t}</p></div>`;
const Tag=({k})=>html`<span class=tag style=${'background:'+CL[k]}>${k}</span>`;
const useRoute=()=>{const[r,s]=useState(location.hash.slice(2));useEffect(()=>{const f=()=>s(location.hash.slice(2));addEventListener('hashchange',f);return()=>removeEventListener('hashchange',f)},[]);return r};

/* ---------- shell ---------- */
const NAV=[['','Home','home'],['game','Game','game'],['analysis','Analysis','analysis'],['benchmark','Benchmark','bench'],['tree','Search Tree','tree'],['about','About','about']];
const Nav=({route})=>html`<aside class=side><div class=brand><svg viewBox="0 0 32 32" width=30 height=30><rect width=32 height=32 rx=8 fill=#FFD23F /><circle cx=11 cy=11 r=2.2 fill=#171717 /><circle cx=21 cy=11 r=2.2 fill=#171717 /><circle cx=11 cy=21 r=2.2 fill=#171717 /><circle cx=21 cy=21 r=2.2 fill=#171717 /><circle cx=16 cy=16 r=2.2 fill=#171717 /></svg><b>AI GAME LAB</b></div>
<nav>${NAV.map(([r,l,i])=>html`<a href=${'#/'+r} class=${route===r?'on':''}><${Ic} n=${i}/><span>${l}</span></a>`)}</nav></aside>`;
function App(){
  const route=useRoute();
  const[cfg,setCfg]=useState({game:'xo',mode:'human_vs_computer',level:'medium',algo:'alphabeta'});
  const[sess,setSess]=useState(null);const[review,setReview]=useState(null);
  const P={cfg,setCfg,sess,setSess,review,setReview};
  const Page={'':Home,game:Play,analysis:Analysis,benchmark:Bench,tree:Tree,about:About}[route]||Home;
  return html`<div class=app><${Nav} route=${route}/><main><div class=page><${Page} ...${P}/></div></main></div>`}

/* ---------- home ---------- */
const Ill=({g})=>{
  if(g==='xo')return html`<svg viewBox="0 0 90 90"><path d="M30 8v74M60 8v74M8 30h74M8 60h74" stroke=#555 stroke-width=3 stroke-linecap=round /><path d="M13 13l14 14M27 13 13 27M63 63l14 14M77 63 63 77M63 13l14 14M77 13 63 27" stroke=#E5484D stroke-width=4 stroke-linecap=round /><circle cx=45 cy=45 r=9 fill=none stroke=#E5E5E5 stroke-width=4 /><circle cx=20 cy=70 r=8 fill=none stroke=#E5E5E5 stroke-width=4 /></svg>`;
  const c4=g==='connect4',n=c4?7:5,r=c4?6:5,s=c4?13:16,d=[];
  for(let i=0;i<r;i++)for(let j=0;j<n;j++){const k=(i*3+j*5)%7;d.push(html`<circle cx=${s/2+j*s} cy=${s/2+i*s} r=${s*.38} fill=${k<2?'#E5484D':k<3?(c4?'#F5C451':'#E5E5E5'):'#303030'} stroke=${!c4&&k>=3?'#444':'none'} />`)}
  return html`<svg viewBox=${`0 0 ${n*s} ${r*s}`}>${d}</svg>`};
function Home({cfg,setCfg,setSess}){
  const set=o=>setCfg({...cfg,...o}),pvp=cfg.mode==='friends';
  return html`<section class=hero><div><h1>Play. Think. Analyze.</h1><p>Explore the power of AI in classic games.</p></div>
   <svg viewBox="0 0 180 150"><rect x=55 y=20 width=68 height=68 rx=16 fill=#ff6079 transform="rotate(-8 89 54)" stroke=#171717 stroke-width=7/><circle cx=132 cy=62 r=43 fill=#61b3ef stroke=#171717 stroke-width=7/><path d="M52 132 105 45l46 87z" fill=#f6f7ff stroke=#171717 stroke-width=7 stroke-linejoin=round/></svg></section>
  <h2>Choose a game</h2>
  <div class=games>${Object.entries(G).map(([k,g])=>html`<div class=${'gc'+(cfg.game===k?' on':'')} onClick=${()=>set({game:k})}>
    <div class=ill><${Ill} g=${k}/></div><div class=gh><b>${g.n}</b><span class=dim>${g.dim}</span></div><p>${g.d}</p>
    <button class=${'btn'+(cfg.game===k?' pri':'')}>${cfg.game===k?'Selected':'Select'}</button></div>`)}</div>
  <h2>Configure</h2>
  <div class="card cfg">
   <div class=row><label>Game mode</label><${Seg} v=${cfg.mode} o=${MODES} on=${v=>set({mode:v})}/></div>
   <div class=row><label>Difficulty</label><${Seg} v=${cfg.level} dis=${pvp} o=${[['easy','Easy'],['medium','Medium'],['hard','Hard']]} on=${v=>set({level:v})}/></div>
   <div class=row><label>Algorithm</label><${Seg} v=${cfg.algo} dis=${pvp} o=${[['minimax','Minimax'],['alphabeta','Alpha-Beta']]} on=${v=>set({algo:v})}/></div>
   <p class=note>${pvp?'Two players share the screen; AI settings are not used (hints still use Alpha-Beta).':cfg.mode==='ai_vs_ai'?'Both AIs use the chosen algorithm and level; the backend simulates the full match.':'You play first as Player 1. XO “Easy” and Seega placements by the AI are random (backend rules).'}</p>
   <div><button class="btn pri xl" onClick=${()=>{setSess(null);nav('game')}}>Start Game</button></div>
  </div>`}

/* ---------- boards ---------- */
const XO=({v})=>v==='human'?html`<svg viewBox="0 0 40 40"><path d="M8 8l24 24M32 8 8 32" stroke=#FF6079 stroke-width=7 stroke-linecap=round /></svg>`:v?html`<svg viewBox="0 0 40 40"><circle cx=20 cy=20 r=12 fill=#61B3EF /></svg>`:null;
function Board({gm,s,legal=[],sel,onCell,cells=[],last,hint,prev,off,scores}){
  const B=s.board,win=(r,c)=>cells.some(x=>x[0]===r&&x[1]===c);
  if(gm==='connect4'){
    const top=c=>B.findIndex(row=>row[c]),vals=(scores||[]).map(x=>x.score),mn=Math.min(...vals),mx=Math.max(...vals);
    return html`<div class=${'c4'+(off?' off':'')}>${[0,1,2,3,4,5,6].map(c=>{
      const it=(scores||[]).find(x=>x.move===c),t=top(c);
      return html`<div class=${'col'+(hint===c?' hint':'')} onClick=${()=>!off&&onCell(0,c)}>
       <div class=heat title=${it?'score '+it.score:''}>${it&&html`<i class=${it.score===mx?'best':''} style=${`height:${mx===mn?60:15+85*(it.score-mn)/(mx-mn)}%`}></i>`}</div>
       ${B.map((row,r)=>html`<div class=hole>${row[c]&&html`<div class=${'disc '+row[c]+(win(r,c)?' win':'')+(last===c&&r===t&&!win(r,c)?' last':'')}></div>`}</div>`)}</div>`})}</div>`}
  const sg=gm==='seega';
  return html`<div class=${'grid '+gm+(off?' off':'')}>${B.map((row,r)=>row.map((v,c)=>{
    const dest=sg&&sel&&legal.some(m=>Array.isArray(m[0])&&m[0][0]===sel[0]&&m[0][1]===sel[1]&&m[1][0]===r&&m[1][1]===c);
    const cl=['cell',win(r,c)&&'win',hit(last,gm,r,c)&&'last',hit(hint,gm,r,c)&&'hint',sel&&sel[0]===r&&sel[1]===c&&'sel',dest&&'dest',sg&&prev&&prev[r][c]&&!v&&'capt',sg&&r===2&&c===2&&'ctr'].filter(Boolean).join(' ');
    return html`<button class=${cl} aria-disabled=${off} tabindex=${off?-1:0} onClick=${()=>!off&&onCell(r,c)} aria-label=${`row ${r+1} column ${c+1}`}>${sg?(v&&html`<div class=${'pc '+v}></div>`):html`<${XO} v=${v}/>`}</button>`}))}</div>`}
const Sym=({gm,p})=>gm==='xo'?html`<div class=sym><${XO} v=${p}/></div>`:html`<div class=${`dot ${p} ${gm==='seega'?'seega':'c4'}`}></div>`;
const sum=(a,k)=>a.reduce((t,x)=>t+(x[k]||0),0);

/* ---------- game screen ---------- */
const simView=g=>{const k=g.step,H=g.sim.history,end=k>=H.length,st=k?H[k-1].state:g.init;
  return{...g,state:st,status:end?'terminal':'ongoing',winner:end?g.sim.winner:null,cells:end?g.sim.winning_cells:[],cur:st.player,last:k?H[k-1].move:null,prev:k>1?H[k-2].state.board:null,legal:[],msg:end?'Simulation finished.':k?`Step ${k} of ${H.length}`:'Press Play to start.'}};
const merge=(b,r,mv,ai)=>({...b,prev:b.state.board,state:r.state,status:r.status,winner:r.winner,cells:r.winning_cells||[],legal:r.legal_moves,msg:r.message,cur:r.current_player,moves:[...b.moves,mv],last:mv,hint:null,
  stat:ai?{nodes:(b.stat?.nodes||0)+r.nodes,ms:(b.stat?.ms||0)+r.time_ms,n:(b.stat?.n||0)+1}:b.stat,ai:ai?{nodes:r.nodes,ms:r.time_ms}:b.ai});
function Play({cfg,sess,setSess,setReview}){
  const[g,setG]=useState(sess);const[busy,setBusy]=useState(false);const[err,setErr]=useState('');const[sel,setSel]=useState(null);
  const gr=useRef(g);gr.current=g;
  const up=b=>{gr.current=b;setG(b);setSess(b)};
  useEffect(()=>{if(!g)start()},[]);
  useEffect(()=>{if(g&&g.sim&&g.playing){if(g.step>=g.sim.history.length)return up({...g,playing:false});const t=setTimeout(()=>up({...gr.current,step:gr.current.step+1}),750);return()=>clearTimeout(t)}},[g&&g.step,g&&g.playing]);
  useEffect(()=>{if(g&&g.sim)evalNow(g,simView(g).state)},[g&&g.sim&&g.step,g&&g.sim]);
  async function start(){
    setBusy(true);setErr('');setSel(null);
    try{const mode=cfg.mode==='friends'?'friends':'human_vs_computer';
      const n=await api(`/api/${cfg.game}/new`,{first_player:'human',mode});
      if(cfg.mode==='ai_vs_ai'){
        const sim=await api('/api/ai-vs-ai',{game:cfg.game,algo_a:cfg.algo,level_a:cfg.level,algo_b:cfg.algo,level_b:cfg.level,seed:Math.floor(Math.random()*1e6)});
        up({cfg:{...cfg},mode,sim,init:n.state,step:0,playing:false,labels:{human:'AI A',computer:'AI B'},ev:null});
      }
      else{const b={cfg:{...cfg},mode,state:n.state,status:n.status,winner:null,cells:[],legal:n.legal_moves,msg:n.message,cur:n.current_player,labels:n.player_labels,moves:[],hints:3,hint:null,ev:null,ai:null,last:null,prev:null};up(b);await settle(b)}
    }catch(x){setErr(x.message)}setBusy(false)}
  async function evalNow(b,st){try{const e=await api(`/api/${b.cfg.game}/eval`,{state:st||b.state});up({...gr.current,ev:e})}catch(x){}}
  async function settle(b){
    setBusy(true);
    try{for(let i=0;i<80&&b.status==='ongoing';i++){
        const ai=b.mode!=='friends'&&b.cur==='computer';
        if(!ai&&b.legal.length)break;
        const r=ai?await api(`/api/${b.cfg.game}/ai-move`,{state:b.state,algorithm:b.cfg.algo,level:b.cfg.level})
                  :await api(`/api/${b.cfg.game}/move`,{state:b.state,move:null,mode:b.mode});
        b=merge(b,r,r.move===undefined?null:r.move,ai);up(b);if(ai)await sleep(300)}
      const e=await api(`/api/${b.cfg.game}/eval`,{state:b.state});up({...b,ev:e})
    }catch(x){setErr(x.message)}setBusy(false)}
  async function play(mv){
    const b0=gr.current;if(busy||b0.status!=='ongoing')return;
    setErr('');setBusy(true);
    try{const r=await api(`/api/${b0.cfg.game}/move`,{state:b0.state,move:mv,mode:b0.mode,player:b0.cur});
      const b=merge(b0,r,mv,false);setSel(null);up(b);await settle(b)}catch(x){setErr(x.message);setBusy(false)}}
  async function hint(){
    setBusy(true);setErr('');
    try{const r=await api(`/api/${g.cfg.game}/hint`,{state:g.state,algorithm:g.cfg.algo==='minimax'?'minimax':'alphabeta'});
      if(r.best_move==null)setErr(r.message);else up({...g,hint:r,hints:g.hints-1})}catch(x){setErr(x.message)}setBusy(false)}
  async function analyze(){
    setBusy(true);setErr('');
    try{const sim=g.sim,mv=sim?sim.history.map(x=>x.move):g.moves;
      const r=await api(`/api/${g.cfg.game}/analyze`,{first_player:'human',mode:g.mode,moves:mv,depth_override:null});
      setReview({...r,stats:sim?{nodes:sum(sim.history,'nodes'),ms:sum(sim.history,'time_ms'),n:sim.history.length}:g.stat});nav('analysis')}catch(x){setErr(x.message)}setBusy(false)}
  function cell(r,c){
    const gm=g.cfg.game;
    if(gm==='xo')return play([r,c]);
    if(gm==='connect4')return play(c);
    if(g.state.phase==='placement')return play([r,c]);
    const L=g.legal;
    if(g.state.board[r][c]===g.cur&&L.some(m=>m[0][0]===r&&m[0][1]===c))return setSel([r,c]);
    if(sel&&L.some(m=>m[0][0]===sel[0]&&m[0][1]===sel[1]&&m[1][0]===r&&m[1][1]===c))return play([sel,[r,c]]);
    setSel(null)}
  if(!g)return err?html`<div class=err>${err}</div>`:html`<${Load} t="Starting game…"/>`;
  const c=g.cfg,gm=c.game,sim=g.sim,v=sim?simView(g):g,lab=p=>g.labels[p],over=v.status==='terminal',S=v.state;
  const pvc=!sim&&g.mode!=='friends',aiTurn=pvc&&v.cur==='computer';
  const st=over?(v.winner==='human'||v.winner==='computer'?`${lab(v.winner)} wins`:'Draw'):busy&&!sim?(aiTurn?'AI thinking…':'Working…'):(sim?lab(v.cur)+' to move':pvc?'Your turn':lab(v.cur)+"'s turn");
  const off=busy||over||sim||aiTurn,ev=g.ev;
  const lvl=g.mode==='friends'?'—':c.level[0].toUpperCase()+c.level.slice(1),alg=g.mode==='friends'?'—':c.algo==='minimax'?'Minimax':'Alpha-Beta';
  const Pl=p=>html`<div class=${'pl'+(!over&&v.cur===p?' turn':'')}><${Sym} gm=${gm} p=${p}/><b>${lab(p)}<small>${gm==='xo'?(p==='human'?'X':'O'):gm==='connect4'?(p==='human'?'Red':'Yellow'):(p==='human'?'Black':'White')}${gm==='seega'?` · ${S[p+'_pieces']} on board`+(S.phase==='placement'?` · ${S[p+'_placed']}/12 placed`:''):''}</small></b>
    ${(sim||(pvc&&p==='computer'))&&html`<span class=badge>AI</span>`}${!over&&v.cur===p&&html`<span class="pill live"><i></i>Turn</span>`}</div>`;
  return html`<div class=bar><button class="btn sm" onClick=${()=>nav('')}>← Home</button><h1>${G[gm].n}</h1>
    <span class=${'pill'+(busy?' live':'')}>${busy&&html`<i></i>`}${st}</span>
    <button class="btn sm" disabled=${busy&&!sim} onClick=${()=>{setSess(null);setG(null);start()}}>New Game</button></div>
   <div class=play><div class=stage>${err&&html`<div class=err style="position:absolute;top:12px;left:12px;right:12px">${err}</div>`}
     <${Board} gm=${gm} s=${S} legal=${v.legal} sel=${sel} onCell=${cell} cells=${v.cells} last=${v.last} prev=${v.prev} off=${off} hint=${g.hint&&g.hint.best_move} scores=${g.hint&&g.hint.scores_list}/></div>
    <div class=stack>
     <div class=card><h3>Players</h3>${Pl('human')}${Pl('computer')}</div>
     <div class=card><h3>Evaluation</h3>${ev?html`<div class=evb title="Player 1 win probability"><i style=${`width:${ev.p1_win_prob*100}%`}></i></div><div class=kv><span>${lab('human')} win chance</span><b>${Math.round(ev.p1_win_prob*100)}%</b></div>`:html`<p class=note>Not available yet.</p>`}</div>
     <div class=card><h3>Game info</h3>
      <div class=kv><span>Current player</span><b>${over?'—':lab(v.cur)}</b></div><div class=kv><span>Mode</span><b>${MODES.find(m=>m[0]===c.mode)[1]}</b></div>
      <div class=kv><span>Difficulty</span><b>${lvl}</b></div><div class=kv><span>Algorithm</span><b>${alg}</b></div>
      <div class=kv><span>Evaluation</span><b>${ev?ev.score:'—'}</b></div>
      ${gm==='seega'&&html`<div class=kv><span>Phase</span><b>${S.phase}${S.phase==='placement'?` (piece ${S.placed_this_turn+1}/2)`:''}</b></div><div class=kv><span>No-capture moves</span><b>${S.no_capture_counter}/40</b></div>`}
      ${(sim?v.step>0&&sim.history[v.step-1]:g.ai)&&html`<div class=kv><span>Last AI search</span><b>${(sim?sim.history[v.step-1]:g.ai).nodes} nodes · ${Math.round((sim?sim.history[v.step-1]:g.ai).time_ms??g.ai.ms)} ms</b></div>`}
      <div class=kv><span>Status</span><b>${over?'Finished':'Ongoing'}</b></div>
      ${v.msg&&html`<p class=note style="margin-top:8px">${v.msg}</p>`}
      ${gm==='seega'&&S.phase==='placement'&&!sim&&html`<p class=note>Place two pieces per turn. The centre square is empty until movement.</p>`}</div>
     <div class="card ctl">${sim?html`<button class="btn pri" disabled=${over} onClick=${()=>up({...g,playing:!g.playing})}>${g.playing?'Pause':'Play'}</button><button class=btn disabled=${over||g.playing} onClick=${()=>up({...g,step:g.step+1})}>Step</button>`
        :html`<button class=btn disabled=${busy||over||aiTurn||!g.hints} onClick=${hint}>Hint (${g.hints})</button><button class=btn disabled=${busy&&!sim} onClick=${()=>{setSess(null);setG(null);start()}}>New Game</button>`}
       <button class="btn pri full" disabled=${!over||busy} onClick=${analyze}>Analyze Game</button></div>
    </div></div>`}

/* ---------- analysis ---------- */
function Analysis({review:r}){
  const[i,setI]=useState(0);
  useEffect(()=>{const f=e=>{if(!r)return;if(e.key==='ArrowRight')setI(x=>Math.min(x+1,r.steps.length-1));if(e.key==='ArrowLeft')setI(x=>Math.max(x-1,0))};addEventListener('keydown',f);return()=>removeEventListener('keydown',f)},[r]);
  if(!r)return html`<${Empty} t="No analysis yet" d="Finish a game and press Analyze Game to review every move." a=${['Go to game','game']}/>`;
  const S=r.steps,s=S[Math.min(i,S.length-1)],gm=r.game,n=S.length,W=640,H=190,px=k=>n<2?W/2:24+k*(W-48)/(n-1),py=e=>H/2-e*(H/2-16);
  const pl=p=>p==='human'?r.player1.label:r.player2.label,cm=r.critical_moment;
  const Pc=(p,t)=>html`<div class=card><h3>${t}: ${p.label}</h3><div class=big>${p.accuracy}<small>% accuracy</small></div>
    <div class=hb>${Object.keys(CL).map(k=>html`<i title=${k} style=${`flex:${p.counts[k]||0};background:${CL[k]}`}></i>`)}</div>
    <div class=lg>${Object.keys(CL).map(k=>html`<span style=${'--c:'+CL[k]}>${k} ${p.counts[k]||0}</span>`)}</div></div>`;
  return html`<div class=bar><h1>Game Analysis · ${G[gm].n}</h1><span class=pill>${r.total_moves} moves</span><span class=pill>Depth ${r.eval_depth}</span></div>
   <div class=stats>${Pc(r.player1,'Player 1')}${Pc(r.player2,'Player 2')}
    <div class=card><h3>Search effort (AI moves)</h3>${r.stats?html`<div class=big>${r.stats.nodes.toLocaleString()}<small> nodes</small></div><div class=kv><span>Total search time</span><b>${Math.round(r.stats.ms)} ms</b></div><div class=kv><span>AI moves</span><b>${r.stats.n}</b></div>`:html`<p class=note>No search statistics were recorded for this game.</p>`}</div></div>
   <div class=card style="margin-top:18px"><div class=row><h3>Evaluation over time (+ favours Player 1)</h3>${cm&&html`<button class="btn sm" onClick=${()=>setI(cm.move_no-1)}>Jump to critical moment (#${cm.move_no})</button>`}</div>
    <svg viewBox=${`0 0 ${W} ${H}`} style="width:100%"><path d=${`M0 ${H/2}H${W}`} stroke=#555 stroke-dasharray="4 4" />
     <path d=${S.map((x,k)=>(k?'L':'M')+px(k)+' '+py(x.eval_after)).join('')} fill=none stroke=#8c8c8c stroke-width=2 />
     ${S.map((x,k)=>html`<circle cx=${px(k)} cy=${py(x.eval_after)} r=${k===i?7:4} fill=${CL[x.classification]} stroke=${k===i?'#fff':'none'} style="cursor:pointer" onClick=${()=>setI(k)}><title>#${x.move_no} ${x.classification}</title></circle>`)}</svg></div>
   <div class=two><div class=card><h3>Move history</h3><div class=scroll><table><thead><tr><th>#</th><th>Player</th><th>Played</th><th>Best</th><th>Class</th><th class=num>Loss</th></tr></thead><tbody>
     ${S.map((x,k)=>html`<tr class=${k===i?'hl':''} onClick=${()=>setI(k)}><td>${x.move_no}</td><td>${pl(x.player)}</td><td>${fm(gm,x.played)}</td><td>${fm(gm,x.best)}</td><td><${Tag} k=${x.classification}/></td><td class=num>${(x.loss*100).toFixed(1)}%</td></tr>`)}</tbody></table></div></div>
    <div class=card><div class=row><h3>Move #${s.move_no} · ${pl(s.player)}</h3><div><button class="btn sm" disabled=${i<1} onClick=${()=>setI(i-1)}>◀</button> <button class="btn sm" disabled=${i>=n-1} onClick=${()=>setI(i+1)}>▶</button></div></div>
     <div style="display:grid;place-items:center;margin:8px 0 14px;transform-origin:top"><${Board} gm=${gm} s=${s.state_after} last=${s.played} hint=${s.best} off=${true}/></div>
     <div class=kv><span>Classification</span><b><${Tag} k=${s.classification}/></b></div><div class=kv><span>Played</span><b>${fm(gm,s.played)} (${s.played_score})</b></div><div class=kv><span>Best</span><b>${fm(gm,s.best)} (${s.best_score})</b></div>
     <div class=kv><span>Win-chance loss</span><b>${(s.loss*100).toFixed(1)}%</b></div>${s.comment&&html`<p class=note>${s.comment}</p>`}<p class=note>Red outline: played move · green: engine's best. Use ← → keys.</p></div></div>`}

/* ---------- benchmark ---------- */
const ALG=[['Minimax','minimax'],['Alpha-Beta','alphabeta'],['Alpha-Beta + Ordering','alphabeta_ordered']];
function Bench(){
  const[gm,setGm]=useState('xo'),[n,setN]=useState(10),[d,setD]=useState(null),[ld,setLd]=useState(false),[er,setEr]=useState('');
  async function run(){setLd(true);setEr('');setD(null);try{setD(await api(`/api/benchmark/${gm}?n=${n}`))}catch(x){setEr(x.message)}setLd(false)}
  const A=d&&d.averages,Bars=(t,key,u)=>{const mx=Math.max(...ALG.map(([,k])=>A[`avg_${k}_${key}`]))||1;return html`<div class=card><h3>${t}</h3>${ALG.map(([l,k],j)=>html`<div class=hbar><span>${l}</span><div><i class=${j?'a':''} style=${`width:${Math.max(2,A[`avg_${k}_${key}`]/mx*100)}%`}></i></div><b class=num>${A[`avg_${k}_${key}`].toLocaleString()}${u}</b></div>`)}</div>`};
  return html`<div class=bar><h1>Algorithm Benchmark</h1></div>
   <div class="card cfg"><div class=row><label>Game</label><${Seg} v=${gm} o=${Object.entries(G).map(([k,g])=>[k,g.n])} on=${setGm}/></div>
    <div class=row><label>Positions</label><${Seg} v=${n} o=${[[5,'5'],[10,'10'],[20,'20'],[50,'50']]} on=${setN}/></div>
    <div><button class="btn pri" disabled=${ld} onClick=${run}>Run benchmark</button> <span class=note>Runs live on the backend using random mid-game positions${gm!=='xo'?' — may take a while for this game':''}.</span></div></div>
   ${er&&html`<div class=err style="margin-top:14px">${er}</div>`}${ld&&html`<div style="margin-top:18px"><${Load} t=${`Benchmarking ${G[gm].n} on ${n} positions…`}/></div>`}
   ${!d&&!ld&&!er&&html`<div style="margin-top:18px"><${Empty} t="No results yet" d="Choose a game and run the benchmark to compare Minimax with Alpha-Beta pruning."/></div>`}
   ${d&&html`<h2>${G[d.game].n} · search depth ${d.depth} · ${d.n_positions} positions</h2>
    <div class=stats>${ALG.map(([l,k],j)=>html`<div class=card style=${j===2?'border-color:var(--ac)':''}><h3>${l}</h3><div class=big>${A[`avg_${k}_nodes`].toLocaleString()}<small> avg nodes</small></div><div class=kv><span>Avg time</span><b>${A[`avg_${k}_time_ms`]} ms</b></div>${j>0&&html`<div class=kv><span>Node reduction</span><b style="color:var(--ok)">${j===1?A.avg_reduction_pct:A.avg_ordered_reduction_pct}%</b></div>`}</div>`)}</div>
    <div class=stats style="margin-top:14px">${Bars('Average nodes explored','nodes','')}${Bars('Average execution time','time_ms',' ms')}</div>
    <div class=card style="margin-top:14px"><h3>Per-position results</h3><div class=scroll><table><thead><tr><th>#</th><th class=num>Minimax</th><th class=num>Alpha-Beta</th><th class=num>+ Ordering</th><th class=num>Reduction</th><th class=num>With ordering</th><th>Same move</th></tr></thead><tbody>
     ${d.rows.map(x=>html`<tr><td>${x.position}</td><td class=num>${x.minimax_nodes}</td><td class=num>${x.alphabeta_nodes}</td><td class=num>${x.alphabeta_ordered_nodes}</td><td class=num>${x.reduction_pct}%</td><td class=num>${x.ordered_reduction_pct}%</td><td>${x.same_move?'✓':'✗'}</td></tr>`)}</tbody></table></div></div>`}`}

/* ---------- search tree ---------- */
const ST=70;
function lay(n,id,ex,d,o){n.id=id;n.dd=d;const ks=ex.has(id)?n.children:[];ks.forEach((k,i)=>lay(k,id+'.'+i,ex,d+1,o));n.x=ks.length?(ks[0].x+ks[ks.length-1].x)/2:o.l++*ST;o.ns.push(n);ks.forEach(k=>o.es.push([n,k]))}
const count=n=>n.children.reduce((a,k)=>({t:a.t+count(k).t,p:a.p+count(k).p}),{t:1,p:n.pruned?1:0});
function Tree({sess}){
  const[gm,setGm]=useState('xo'),[dp,setDp]=useState(2),[cur,setCur]=useState(false),[t,setT]=useState(null),[ld,setLd]=useState(false),[er,setEr]=useState('');
  const[ex,setEx]=useState(new Set(['r'])),[sl,setSl]=useState(null),[v,setV]=useState({x:30,y:20,k:1});const box=useRef(),drag=useRef();
  const canCur=sess&&!sess.sim&&sess.cfg.game===gm&&sess.status==='ongoing';
  async function run(){setLd(true);setEr('');try{
      const state=cur&&canCur?sess.state:(await api(`/api/${gm}/new`,{})).state;
      const r=await api(`/api/${gm}/tree-viz`,{state,depth:dp});setT(r);setEx(new Set(['r']));setSl(null);setV({x:30,y:20,k:1})}catch(x){setEr(x.message)}setLd(false)}
  const o={l:0,ns:[],es:[]};if(t)lay(t,'r',ex,0,o);
  const fit=()=>{const w=box.current.clientWidth,tw=Math.max(1,(o.l-1)*ST+60),k=Math.min(1,(w-16)/tw);setV({x:(w-((o.l-1)*ST+40)*k)/2,y:20,k})};
  const collect=(n,id='r')=>[id,...n.children.flatMap((k,i)=>collect(k,id+'.'+i))];
  const pd=e=>{drag.current={x:e.clientX,y:e.clientY,vx:v.x,vy:v.y,m:0}},pm=e=>{const d=drag.current;if(!d)return;const dx=e.clientX-d.x,dy=e.clientY-d.y;d.m=Math.max(d.m,Math.abs(dx)+Math.abs(dy));setV({...v,x:d.vx+dx,y:d.vy+dy})};
  const wh=e=>{e.preventDefault();const k=Math.min(2.5,Math.max(.15,v.k*(e.deltaY<0?1.12:.89))),r=box.current.getBoundingClientRect(),mx=e.clientX-r.left,my=e.clientY-r.top;setV({k,x:mx-(mx-v.x)*k/v.k,y:my-(my-v.y)*k/v.k})};
  const pick=n=>{if(drag.current&&drag.current.m>4)return;setSl(n);if(n.children.length){const e=new Set(ex);e.has(n.id)?e.delete(n.id):e.add(n.id);setEx(e)}};
  const cnt=t&&count(t);
  return html`<div class=bar><h1>Search Tree</h1></div>
   <div class="card cfg"><div class=row><label>Game</label><${Seg} v=${gm} o=${Object.entries(G).map(([k,g])=>[k,g.n])} on=${k=>{setGm(k);setDp(2);setCur(false)}}/></div>
    <div class=row><label>Depth</label><${Seg} v=${dp} o=${[[1,'1'],[2,'2'],[3,'3']]} dis=${false} on=${setDp}/></div>
    <div class=row><label>Position</label><${Seg} v=${cur&&canCur?'c':'s'} o=${[['s','Start position'],['c','Current game']]} on=${k=>setCur(k==='c'&&canCur)}/></div>
    <div><button class="btn pri" disabled=${ld||(gm!=='xo'&&dp>2)} onClick=${run}>Generate tree</button> <span class=note>Alpha-Beta from the backend. ${gm!=='xo'?'Depth 3 on this game can be very large — use depth ≤ 2.':'Depth ≤ 3 recommended.'}</span></div></div>
   ${er&&html`<div class=err style="margin-top:14px">${er}</div>`}${ld&&html`<div style="margin-top:18px"><${Load} t="Building search tree…"/></div>`}
   ${!t&&!ld&&html`<div style="margin-top:18px"><${Empty} t="No tree yet" d="Generate a tree to see Alpha-Beta’s search: values, α/β windows and pruned branches."/></div>`}
   ${t&&!ld&&html`<div class=two style="grid-template-columns:minmax(0,1fr) 300px"><div><div class=bar style="margin:0 0 10px"><span class=pill>${cnt.t} nodes</span><span class=pill>${cnt.p} pruned</span><span class=pill>Root value ${t.value}</span><span style="margin-left:auto"></span><button class="btn sm" onClick=${fit}>Fit</button><button class="btn sm" onClick=${()=>setEx(new Set(collect(t)))}>Expand all</button><button class="btn sm" onClick=${()=>setEx(new Set(['r']))}>Collapse</button></div>
     <div class=tree ref=${box} onPointerDown=${pd} onPointerMove=${pm} onPointerUp=${()=>setTimeout(()=>drag.current=null)} onPointerLeave=${()=>drag.current=null} onWheel=${wh}><svg><g transform=${`translate(${v.x} ${v.y}) scale(${v.k})`}>
      ${o.es.map(([a,b])=>html`<path d=${`M${a.x+20} ${a.dd*100+60}C${a.x+20} ${a.dd*100+100} ${b.x+20} ${b.dd*100+20} ${b.x+20} ${b.dd*100+40}`} fill=none stroke=${b.pruned?'#555':'#777'} stroke-dasharray=${b.pruned?'4 3':''} />`)}
      ${o.ns.map(n=>html`<g class=${'nd'+(n.pruned?' p':'')+(n.player==='human'?' h':'')+(sl&&sl.id===n.id?' s':'')} transform=${`translate(${n.x+20} ${n.dd*100+40})`} onClick=${()=>pick(n)}><title>${n.pruned?'pruned':'value '+n.value}</title><circle r=20 /><text y=4>${n.pruned?'✂':n.value}</text><text class=m y=36>${n.id==='r'?'root':fm(gm,n.move)}${n.children.length&&!ex.has(n.id)?' +':''}</text></g>`)}</g></svg></div>
     <p class=note style="margin-top:8px">Drag to pan, scroll to zoom, click a node to select and expand/collapse it. Crimson ring: Player 1 to move · dashed: pruned.</p></div>
    <div class=card><h3>Node details</h3>${sl?html`<div class=kv><span>Move</span><b>${sl.id==='r'?'root':fm(gm,sl.move)}</b></div><div class=kv><span>Player</span><b>${sl.player}</b></div><div class=kv><span>Remaining depth</span><b>${sl.depth}</b></div><div class=kv><span>α in</span><b>${inf(sl.alpha_in)}</b></div><div class=kv><span>β in</span><b>${inf(sl.beta_in)}</b></div><div class=kv><span>Value</span><b>${sl.value??'—'}</b></div><div class=kv><span>Pruned</span><b>${sl.pruned?'Yes':'No'}</b></div><div class=kv><span>Children</span><b>${sl.children.length}</b></div>`:html`<p class=note>Select a node to inspect it.</p>`}</div></div>`}`}

/* ---------- about ---------- */
function About(){
  const[ok,setOk]=useState(null);useEffect(()=>{api('/api/games').then(g=>setOk(g),()=>setOk(false))},[]);
  return html`<div class=bar><h1>About</h1><span class=pill>${ok===null?'Checking backend…':ok?'Backend connected':'Backend unreachable'}</span></div>
   <div class=card style="display:grid;gap:10px"><p>AI Game Lab is the front end for the CAI3101 pure-Python game AI engine. Games: XO, Connect 4 and Seega. All rules, search and analysis run on the backend; this interface only sends states and renders the results.</p>
    <p><b style="color:var(--tx)">Algorithms:</b> Minimax, Alpha-Beta pruning (with move ordering), and win-probability based post-game review.</p>
    <p><b style="color:var(--tx)">Backend:</b> ${BASE||location.origin} · Games reported: ${Array.isArray(ok)?ok.join(', '):'—'}</p></div>`}

render(html`<${App}/>`,document.getElementById('root'));

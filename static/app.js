// 墨核 AI Studio —— 前端逻辑
const $ = (s, r=document) => r.querySelector(s);
const $$ = (s, r=document) => [...r.querySelectorAll(s)];

let SESSION = null;
let busy = false;
let recognizing = false;
let SESSION_MODEL = "";   // 当前对话单独选择的模型（""=跟随全局）
let APPLIED_MODEL = null; // 已应用到后端的模型（避免重复提交）

// ---------- 线性 SVG 图标库（统一 currentColor 描边风格，告别 emoji 老款观感） ----------
const ICONS = {
  write:'<path d="M4 20l4-1 9-9-3-3-9 9-1 4z"/><path d="M14 5l3 3"/>',
  pen:'<path d="M4 20l4-1 9-9-3-3-9 9-1 4z"/><path d="M14 5l3 3"/>',
  image:'<rect x="3" y="4" width="18" height="16" rx="2.5"/><circle cx="9" cy="9.5" r="1.6"/><path d="M21 16l-5-5-6 6"/>',
  prompt:'<path d="M12 3l1.9 4.8L19 9l-5.1 1.2L12 15l-1.9-4.8L5 9l5.1-1.2z"/>',
  memory:'<rect x="6" y="6" width="12" height="12" rx="2.5"/><path d="M9 3v3M15 3v3M9 18v3M15 18v3M3 9h3M3 15h3M18 9h3M18 15h3"/>',
  knowledge:'<path d="M5 5a2 2 0 0 1 2-2h6v16H7a2 2 0 0 0-2 2z"/><path d="M19 5a2 2 0 0 0-2-2h-6v16h6a2 2 0 0 1 2 2z"/>',
  skills:'<rect x="7" y="7" width="10" height="10" rx="2.5"/><path d="M9 3v2M15 3v2M9 19v2M15 19v2M3 9h2M3 15h2M19 9h2M19 15h2"/>',
  terminal:'<path d="M5 8l4 4-4 4"/><path d="M12 17h7"/>',
  code:'<path d="M9 8l-4 4 4 4"/><path d="M15 8l4 4-4 4"/>',
  agent:'<rect x="7" y="7" width="10" height="10" rx="2.5"/><circle cx="12" cy="12" r="2"/><path d="M10 3v3M14 3v3M10 18v3M14 18v3M3 10h3M3 14h3M18 10h3M18 14h3"/>',
  fun:'<rect x="3" y="8" width="18" height="9" rx="4.5"/><path d="M7 12h2M8 11v2"/><circle cx="16" cy="12" r=".7"/><circle cx="18" cy="12" r=".7"/>',
  settings:'<circle cx="12" cy="12" r="3.2"/><path d="M12 3v3M12 18v3M3 12h3M18 12h3M5.6 5.6l2.1 2.1M16.3 16.3l2.1 2.1M18.4 5.6l-2.1 2.1M7.7 16.3l-2.1 2.1"/>',
  voice:'<rect x="9" y="3.5" width="6" height="11" rx="3"/><path d="M5 11a7 7 0 0 0 14 0"/><path d="M12 18v3"/>',
  vision:'<path d="M2 12s4-6.5 10-6.5S22 12 22 12s-4 6.5-10 6.5S2 12 2 12z"/><circle cx="12" cy="12" r="3"/>',
  export:'<path d="M12 4v10M8 10l4 4 4-4"/><path d="M5 19h14"/>',
  send:'<path d="M12 19V5M6 11l6-6 6 6"/>',
  play:'<path d="M5 5l14 7-14 7z"/>',
  stop:'<rect x="6" y="6" width="12" height="12" rx="2.5"/>',
  close:'<path d="M6 6l12 12M18 6L6 18"/>',
  plus:'<path d="M12 5v14M5 12h14"/>',
  chat:'<path d="M4 5h16v11H9l-4 3v-3H4z"/>',
  globe:'<circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3c3 3 3 15 0 18M12 3c-3 3-3 15 0 18"/>',
  doc:'<path d="M7 3h7l4 4v14H7z"/><path d="M14 3v4h4"/>',
  folder:'<path d="M3 7a2 2 0 0 1 2-2h4l2 2h8a2 2 0 0 1 2 2v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>',
  translate:'<path d="M4 6h9M8 4v3c0 4-2 6-5 7M14 20l4-8 4 8M16 16h4"/>',
  server:'<rect x="3" y="4" width="18" height="7" rx="2"/><rect x="3" y="13" width="18" height="7" rx="2"/><path d="M7 7.5h.01M7 16.5h.01"/>',
  list:'<path d="M4 6h16M4 10h16M4 14h10M4 18h7"/>',
  bulb:'<path d="M12 3a6 6 0 0 0-6 6c0 2 1 3 2 4v2h8v-2c1-1 2-2 2-4a6 6 0 0 0-6-6z"/><path d="M10 15h4"/><path d="M11 18h2"/>',
  tag:'<path d="M4 5a1 1 0 0 1 1-1h7l8 8-8 8-8-8V5z"/><circle cx="9" cy="9" r="1.5"/>',
  edit:'<path d="M4 16v4h4l10-10-4-4L4 16z"/><path d="M14 6l4 4"/>',
  trash:'<path d="M3 6h18M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/><path d="M10 11v6M14 11v6"/>',
  refresh:'<path d="M23 4v6h-6M1 20v-6h6"/><path d="M3.5 9a9 9 0 0 1 15.6-3.2L23 11M1 13l3.9 5.2A9 9 0 0 0 20.5 15"/>',
  check:'<path d="M20 6L9 17l-5-5"/>',
  warning:'<path d="M12 9v4M12 17h.01M10.3 3.9L1.8 18A2 2 0 0 0 3.6 21h16.8a2 2 0 0 0 1.8-3L13.7 3.9a2 2 0 0 0-3.4 0z"/>',
  dot:'<circle cx="12" cy="12" r="5" fill="currentColor"/>',
  maximize:'<path d="M4 9V4h5M20 9V4h-5M4 15v5h5M20 15v5h-5"/>',
  minimize:'<path d="M9 4v5H4M15 4v5h5M9 20v-5H4M15 20v-5h5"/>',
  // v2.2 新增：MCP / 子 Agent / 技能包
  plug:'<path d="M12 22v-5"/><path d="M9 8V2M15 8V2"/><path d="M18 8v4a6 6 0 0 1-12 0V8Z"/><path d="M6 8h12"/>',
  attach:'<path d="M21.4 11.1 12.3 20a5.5 5.5 0 0 1-7.8-7.8l9.2-9.1a3.7 3.7 0 0 1 5.2 5.2l-9.2 9.1a1.8 1.8 0 0 1-2.6-2.6l8.5-8.4"/>',
  bolt:'<path d="M13 2 3 14h9l-1 8 10-12h-9l1-8Z"/>',
  package:'<path d="m7.5 4.3 9 5.2M21 16V8a2 2 0 0 0-1-1.7l-8-4.6a2 2 0 0 0-2 0L2 6.3A2 2 0 0 0 1 8v8a2 2 0 0 0 1 1.7l8 4.6a2 2 0 0 0 2 0l8-4.6A2 2 0 0 0 21 16Z"/><path d="m1 8 11 6 11-6M12 14v8"/>',
  puzzle:'<path d="M10 3h4v2.5a2 2 0 1 1 3 1.7L19 10h-2.5a2 2 0 1 0 0 4H19l-2 2.8a2 2 0 1 1-1.7 3L14 17v3h-4v-3l-1.3 1.8a2 2 0 1 1-1.7-3L5 14h2.5a2 2 0 1 0 0-4H5l2-2.8a2 2 0 1 1 1.7-3L10 6z"/>',
};
function svg(name){
  const p = ICONS[name] || ICONS.chat;
  return `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${p}</svg>`;
}
function ic(name){ return `<i class="ic">${svg(name)}</i>`; }
function iconOrText(x){ const n=(x||"").trim(); return ICONS[n] ? ic(n) : (n?`<span style="margin-right:4px">${n}</span>`:""); }
function injectIcons(root=document){
  $$("[data-ic]", root).forEach(el=>{ if(el.dataset.ic && !el.dataset.done){ el.innerHTML = svg(el.dataset.ic); el.dataset.done="1"; } });
}

// ---------- 极简 Markdown 渲染 ----------
function md(src){
  if(!src) return "";
  // 1) 先保护代码块围栏，避免内部 $ 被当作公式
  const blocks=[];
  let s = src.replace(/```(\w*)\n([\s\S]*?)```/g, (m,lang,code)=>{
    blocks.push({lang:lang||"", code});
    return `@@C${blocks.length-1}@@`;
  });
  // 2) 保护公式：块级 $$...$$（可跨行）与 行内 $...$
  const maths=[];
  s = s.replace(/\$\$([\s\S]+?)\$\$/g, (m,tex)=>{ maths.push({tex:tex.trim(),disp:true}); return `@@MB${maths.length-1}@@`; });
  s = s.replace(/(?<!\\)\$(?!\s)([^$\n]+?)(?<!\s)\$/g, (m,tex)=>{ maths.push({tex,disp:false}); return `@@MI${maths.length-1}@@`; });
  // 3) 转义剩余文本（占位符为纯 ASCII，不受影响）
  s = s.replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;");
  // 4) 还原代码块（code 需转义后放入 <pre><code>）
  s = s.replace(/@@C(\d+)@@/g, (m,i)=>{
    const b=blocks[i];
    const code=b.code.replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/`/g,"");
    return `<pre><button class="copy-btn" onclick="copyCode(this)">复制</button><code${b.lang?` class="language-${b.lang}"`:""}>${code}</code></pre>`;
  });
  // 5) 表格
  s = s.replace(/((?:^\|.*\|\s*\n)+)/gm, (blk)=>{
    const rows = blk.trim().split("\n").filter(r=>r.includes("|"));
    let html = "<table>";
    rows.forEach((r,i)=>{
      const cells = r.split("|").slice(1,-1).map(c=>c.trim());
      if(i===1 && cells.every(c=>/^:?-+:?$/.test(c))) return;
      html += "<tr>"+cells.map(c=>`<${i===0?"th":"td"}>${inline(c)}</${i===0?"th":"td"}>`).join("")+"</tr>";
    });
    return html+"</table>";
  });
  const lines = s.split("\n");
  let out=[], i=0;
  while(i<lines.length){
    let line = lines[i];
    if(/^<(pre|table)/.test(line)){ out.push(line); i++; continue; }
    if(/^@@(MB|C)\d+@@$/.test(line.trim())){ out.push(line.trim()); i++; continue; }
    if(/^### /.test(line)){ out.push("<h3>"+inline(line.slice(4))+"</h3>"); i++; continue; }
    if(/^## /.test(line)){ out.push("<h2>"+inline(line.slice(3))+"</h2>"); i++; continue; }
    if(/^# /.test(line)){ out.push("<h1>"+inline(line.slice(2))+"</h1>"); i++; continue; }
    if(/^>\s?/.test(line)){ let q=[]; while(i<lines.length&&/^>\s?/.test(lines[i])){q.push(lines[i].replace(/^>\s?/,""));i++;} out.push("<blockquote>"+inline(q.join(" "))+"</blockquote>"); continue; }
    if(/^[-*]\s+/.test(line)){ let ul=[]; while(i<lines.length&&/^[-*]\s+/.test(lines[i])){ul.push("<li>"+inline(lines[i].replace(/^[-*]\s+/,""))+"</li>");i++;} out.push("<ul>"+ul.join("")+"</ul>"); continue; }
    if(/^\d+\.\s+/.test(line)){ let ol=[]; while(i<lines.length&&/^\d+\.\s+/.test(lines[i])){ol.push("<li>"+inline(lines[i].replace(/^\d+\.\s+/,""))+"</li>");i++;} out.push("<ol>"+ol.join("")+"</ol>"); continue; }
    if(line.trim()===""){ i++; continue; }
    let p=[]; while(i<lines.length&&lines[i].trim()!==""&&!/^(#|>|[-*]|\d+\.|```)/.test(lines[i])&&!/^<(pre|table)/.test(lines[i])&&!/^@@(MB|C)\d+@@$/.test(lines[i].trim())){p.push(lines[i]);i++;}
    out.push("<p>"+inline(p.join("<br>"))+"</p>");
  }
  let html = out.join("\n");
  // 6) 还原公式
  html = html.replace(/@@MB(\d+)@@/g, (m,i)=>`<div class="katex-block">${renderKatex(maths[i].tex,true)}</div>`);
  html = html.replace(/@@MI(\d+)@@/g, (m,i)=>renderKatex(maths[i].tex,false));
  return html;
}
function renderKatex(tex, disp){
  try{ if(window.katex) return katex.renderToString(tex, {displayMode:disp, throwOnError:false}); }catch(e){}
  return (disp?"<div>":"")+tex+(disp?"</div>":"");
}
function inline(t){
  return t
    .replace(/`([^`]+)`/g,"<code>$1</code>")
    .replace(/\*\*([^*]+)\*\*/g,"<b>$1</b>")
    .replace(/\[([^\]]+)\]\(([^)]+)\)/g,'<a href="$2" target="_blank">$1</a>');
}

// ---------- 消息渲染 ----------
function msgCount(){ return $$("#messages .msg").length; }
function buildMsg(role, html, imgObj, rawText, idx){
  const wrap = document.createElement("div");
  wrap.className = "msg "+role;
  if(rawText!=null) wrap.dataset.text = rawText;
  wrap.dataset.idx = (idx!=null) ? idx : msgCount();
  const av = document.createElement("div"); av.className="avatar avatar-hidden"; av.setAttribute("aria-hidden","true");
  const bub = document.createElement("div"); bub.className="bubble";
  if(html){
    bub.innerHTML = html;
    try{ if(window.hljs){ bub.querySelectorAll("pre code").forEach(b=>hljs.highlightElement(b)); } }catch(e){}
  }
  if(imgObj){
    if(imgObj.data && imgObj.data.startsWith("data:image")){
      const img = document.createElement("img");
      img.src = imgObj.data; img.style.maxWidth="260px";
      bub.appendChild(img);
    }
    if(imgObj.path){
      const a = document.createElement("div");
      const ext = (imgObj.format||"svg").toUpperCase();
      a.innerHTML = `<a href="${imgObj.path}" target="_blank" style="color:#7c5cff;font-size:12px">下载 ${ext} 封面</a>`;
      bub.appendChild(a);
    }
  }
  wrap.appendChild(av); wrap.appendChild(bub);
  return {wrap, bub};
}
function addMsg(role, html, imgObj, rawText, idx){
  const {wrap} = buildMsg(role, html, imgObj, rawText, idx);
  if(role==="assistant" && rawText){
    const acts=document.createElement("div"); acts.className="msg-acts";
    acts.innerHTML=`<button class="resend-btn" onclick="toggleSpeak(this)">朗读</button><button class="resend-btn" onclick="regenMsg(this)">重新生成</button>`;
    wrap.appendChild(acts);
  }
  if(role==="user" && rawText){
    const acts=document.createElement("div"); acts.className="msg-acts";
    acts.innerHTML=`<button class="resend-btn" onclick="resendMsg(this)">重发</button><button class="resend-btn" onclick="editMsg(this)">编辑</button>`;
    wrap.appendChild(acts);
  }
  $("#messages").appendChild(wrap);
  $("#messages").scrollTop = $("#messages").scrollHeight;
  return wrap;
}
// 流式消息：创建时返回 {wrap, bubble} 便于边收边渲染
function addMsgLive(role, html, imgObj, rawText, idx){
  const {wrap, bub} = buildMsg(role, html, imgObj, rawText, idx);
  if(role==="assistant"){
    const acts=document.createElement("div"); acts.className="msg-acts";
    acts.innerHTML=`<button class="resend-btn" onclick="toggleSpeak(this)">朗读</button><button class="resend-btn" onclick="regenMsg(this)">重新生成</button>`;
    wrap.appendChild(acts);
  }
  $("#messages").appendChild(wrap);
  $("#messages").scrollTop = $("#messages").scrollHeight;
  return {wrap, bubble:bub};
}
function renderLiveBubble(bub, text, highlight){
  if(!bub) return;
  bub.innerHTML = md(text||"");
  // 流式过程中不做高亮（开销大）；仅最终渲染时高亮
  if(highlight){ try{ if(window.hljs){ bub.querySelectorAll("pre code").forEach(b=>hljs.highlightElement(b)); } }catch(e){} }
  $("#messages").scrollTop = $("#messages").scrollHeight;
}
function attachImage(bub, imgObj){
  if(!bub || !imgObj) return;
  if(imgObj.data && imgObj.data.startsWith("data:image")){
    const img = document.createElement("img"); img.src = imgObj.data; img.style.maxWidth="260px"; bub.appendChild(img);
  }
  if(imgObj.path){
    const a = document.createElement("div");
    const ext = (imgObj.format||"svg").toUpperCase();
    a.innerHTML = `<a href="${imgObj.path}" target="_blank" style="color:#7c5cff;font-size:12px">下载 ${ext} 封面</a>`;
    bub.appendChild(a);
  }
}
function copyCode(btn){
  const code = btn.parentElement.querySelector("code");
  if(!code) return;
  navigator.clipboard.writeText(code.innerText).then(()=>{
    btn.textContent="已复制"; setTimeout(()=>btn.textContent="复制",1200);
  }).catch(()=>{ btn.textContent="复制失败"; setTimeout(()=>btn.textContent="复制",1200); });
}
function resendMsg(btn){
  const t = btn.closest(".msg").dataset.text;
  if(t) send(t);
}
function toggleSpeak(btn){
  const wrap=btn.closest('.msg');
  const raw=wrap.dataset.text||"";
  // 去掉代码块与常见 Markdown 标记，尽量朗读干净的文本
  const text=raw.replace(/```[\s\S]*?```/g,"")
    .replace(/\[([^\]]+)\]\([^)]+\)/g,"$1")
    .replace(/[#>*_`~]/g,"").replace(/\n{2,}/g,"\n").replace(/\s+/g," ").trim();
  if(window.__speaking && window.__spkBtn===btn){
    speechSynthesis.cancel(); window.__speaking=false; btn.textContent="朗读"; return;
  }
  speechSynthesis.cancel();
  const u=new SpeechSynthesisUtterance(text); u.lang="zh-CN";
  u.onend=()=>{ btn.textContent="朗读"; window.__speaking=false; window.__spkBtn=null; };
  u.onerror=()=>{ btn.textContent="朗读"; window.__speaking=false; };
  speechSynthesis.speak(u); window.__speaking=true; window.__spkBtn=btn; btn.textContent="停止";
}
function appendSources(sources){
  if(!sources||!sources.length) return;
  const wrap=document.createElement("div"); wrap.className="msg assistant";
  wrap.innerHTML=`<div class="avatar avatar-hidden" aria-hidden="true"></div><div class="bubble"><div class="src-title">参考来源（${sources.length}）</div>`+
    sources.map(s=>`<a class="src-link" href="${escapeHtml(s.url||'#')}" target="_blank" rel="noopener">${escapeHtml(s.title||s.url||'')} ↗</a>`).join("")+`</div>`;
  $("#messages").appendChild(wrap); $("#messages").scrollTop=$("#messages").scrollHeight;
}
function addGameCard(reply, path){
  const wrap = document.createElement("div");
  wrap.className="msg assistant";
  wrap.innerHTML = `<div class="avatar avatar-hidden" aria-hidden="true"></div><div class="bubble">
    ${md(reply)}
    <div class="game-card">
      <span class="game-tag">可玩 HTML</span>
      <button class="btn sec" style="width:auto;padding:6px 14px;display:inline-flex;align-items:center;justify-content:center;gap:6px" onclick="window.open('${path}','_blank')">${ic('play')}在浏览器打开</button>
    </div></div>`;
  $("#messages").appendChild(wrap);
  $("#messages").scrollTop = $("#messages").scrollHeight;
}
function thinking(){
  const wrap = document.createElement("div");
  wrap.className="msg assistant"; wrap.id="thinking";
  wrap.innerHTML = '<div class="avatar avatar-hidden" aria-hidden="true"></div><div class="bubble">思考中<span class="dots"></span></div>';
  $("#messages").appendChild(wrap);
  $("#messages").scrollTop = $("#messages").scrollHeight;
}
function unthinking(){ const t=$("#thinking"); if(t) t.remove(); }

// ---------- 按会话选模型 ----------
async function applyModel(){
  // 确保当前会话有 id，并把选择的模型提交给后端
  if(!SESSION) SESSION = (crypto.randomUUID?crypto.randomUUID():("s_"+Date.now()+"_"+Math.random().toString(16).slice(2)));
  if(SESSION_MODEL===APPLIED_MODEL) return;
  try{
    await fetch("/api/conversations/model",{method:"POST",headers:{"Content-Type":"application/json"},
      body:JSON.stringify({session_id:SESSION, model:SESSION_MODEL})});
    APPLIED_MODEL = SESSION_MODEL;
  }catch(e){}
}
function setSessionModel(model){
  SESSION_MODEL = model||"";
  const sel=$("#sessionModel");
  if(sel){
    if(SESSION_MODEL && ![...sel.options].some(o=>o.value===SESSION_MODEL)){
      const o=document.createElement("option"); o.value=SESSION_MODEL; o.textContent=SESSION_MODEL; sel.appendChild(o);
    }
    sel.value = SESSION_MODEL;
  }
  if(SESSION) applyModel();
}

// ---------- 发送（流式 + 可停止） ----------
function setSendState(kind, controller){
  const b=$("#sendBtn");
  // v2.3：必须用 <i class="ic"> 包裹，裸 SVG 拿不到 #sendBtn .ic 的白色样式，
  // 会变成「纯色圆块看不到图案」。
  if(kind==="stop"){
    b.innerHTML=`<i class="ic">${svg("stop")}</i>`; b.title="停止生成（Esc）"; b.classList.add("stopping");
    b.onclick=()=>{ if(controller) controller.abort(); };
  }else{
    b.innerHTML=`<i class="ic">${svg("send")}</i>`; b.title="发送"; b.classList.remove("stopping");
    b.onclick=()=>send();
  }
}
async function send(text, opts){
  opts = opts || {};
  text = (text||$("#input").value).trim();
  if(!text || busy) return;
  // v2.5：首条消息后收起整个欢迎态，并把输入框停靠到底部（1:1 预览的输入框位置在欢迎态时在内容流中）
  if(!opts.keep){
    const stage=$("#welcomeStage");
    if(stage){ parkComposer(); stage.remove(); }   // 输入框先移到安全区，再移除欢迎态
  }
  if(SESSION_MODEL && !opts.keep) await applyModel();   // 发送前确保模型覆盖已落库
  if(!opts.keep){ $("#input").value=""; autoGrow(); localStorage.removeItem("mohe_draft"); }
  if(!opts.regen){
    const ui = msgCount();
    addMsg("user", inline(text), null, text, ui);
    if(activeTab>=0 && TABS[activeTab]){ TABS[activeTab].title = text.slice(0,18) || "对话"; renderTabs(); }
  }
  busy=true; thinking();
  const controller=new AbortController(); window.__abort=controller; setSendState("stop", controller);
  try{
    const r = await fetch("/api/chat_stream",{method:"POST",headers:{"Content-Type":"application/json"},
      body:JSON.stringify({message:text, session_id:SESSION, keep:opts.keep, regen:opts.regen}), signal:controller.signal});
    const reader=r.body.getReader(); const dec=new TextDecoder(); let buf="";
    let meta=null, acc="", wrap=null, bubble=null, ended=false;
    let lastRender=0;   // 节流：最多每 ~60ms 重渲染一次，避免高频 token 卡顿
    while(!ended){
      const {done,value}=await reader.read();
      if(done){ ended=true; break; }
      buf += dec.decode(value,{stream:true});
      let i;
      while((i=buf.indexOf("\n\n"))>=0){
        const raw=buf.slice(0,i); buf=buf.slice(i+2);
        const line=raw.split("\n").find(l=>l.startsWith("data:")); if(!line) continue;
        let ev; try{ ev=JSON.parse(line.slice(5).trim()); }catch(e){ continue; }
        if(ev.type==="meta"){
          meta=ev; SESSION=ev.session_id;
          unthinking();
          const li=addMsgLive("assistant","", ev.image, null, msgCount());
          wrap=li.wrap; bubble=li.bubble;
        } else if(ev.type==="token"){
          acc += ev.text;
          const now=Date.now();
          if(now-lastRender>=120){ lastRender=now; renderLiveBubble(bubble, acc, false); }
        } else if(ev.type==="done"){
          ended=true;
          acc = ev.text || acc; renderLiveBubble(bubble, acc, true);
          if(wrap){ wrap.dataset.text=acc; if(meta && meta.image) attachImage(bubble, meta.image); }
          if(meta && meta.mode==="game"){ if(wrap) wrap.remove(); addGameCard(acc, meta.game_path); }
          if(meta && meta.mode==="code_run"){ setTimeout(()=>openCodeAuto(meta.code),350); }
          if(meta && meta.mode==="agent_run"){ setTimeout(()=>openAgentAuto(meta.goal, meta.steps),350); }
          if(meta && meta.mode==="terminal_run"){ setTimeout(()=>openTerminalAuto(meta.command),350); }
          else if(meta && meta.sources && meta.sources.length) appendSources(meta.sources);
        }
      }
    }
    try{ await reader.cancel(); }catch(e){}   // 释放底层连接（部分环境下服务器不会主动关闭）
    unthinking();
    if(activeTab>=0 && TABS[activeTab]){ TABS[activeTab].session=SESSION; TABS[activeTab].model=SESSION_MODEL; }
    loadConvs();
    loadArtifacts(SESSION);   // 改动12：每次对话后刷新产物条
  }catch(e){
    unthinking();
    if(e.name!=="AbortError"){ addMsg("assistant","连接失败："+e.message); }
  }
  busy=false; setSendState("send");
}
// Esc 停止生成
document.addEventListener("keydown", e=>{ if(e.key==="Escape" && busy && window.__abort) window.__abort.abort(); });

// ---------- 改动12：会话级产物缩略图条 ----------
async function loadArtifacts(sid){
  sid = sid || SESSION || "default";
  const strip=$("#artStrip"), box=$("#artThumbs"), cnt=$("#artCount");
  if(!strip||!box) return;
  let list=[];
  try{ const r=await fetch("/api/artifacts?session_id="+encodeURIComponent(sid)); list=await r.json(); }catch(e){ list=[]; }
  cnt.textContent=list.length;
  if(!list.length){ strip.style.display="none"; return; }
  strip.style.display="flex";
  box.innerHTML = list.slice().reverse().map(a=>{
    const isImg = a.type==="image";
    const inner = isImg ? `<img src="${a.thumb||a.path}" alt="">` : `<span class="art-emoji">${a.type==="game"?"🎮":a.type==="code"?"💻":"📄"}</span>`;
    const name=(a.title||a.type||"").slice(0,12);
    return `<div class="art-thumb" title="${(a.title||a.type||"").replace(/"/g,"")}" onclick="openArtifact('${a.path}')">${inner}<span class="art-name">${name}</span></div>`;
  }).join("");
}
function openArtifact(path){ if(path) window.open(path,"_blank"); }

// ---------- 消息编辑 / 重新生成（分支） ----------
function removeMsgsFrom(idx){
  $$("#messages .msg").forEach(m=>{ if(parseInt(m.dataset.idx||"0",10)>=idx) m.remove(); });
}
function editMsg(btn){
  if(busy) return;
  const wrap=btn.closest(".msg"); const idx=parseInt(wrap.dataset.idx||"0",10);
  const cur=wrap.dataset.text||""; const bub=wrap.querySelector(".bubble");
  bub.innerHTML=`<textarea class="edit-area">${escapeHtml(cur)}</textarea>
    <div style="display:flex;gap:8px;margin-top:6px;justify-content:flex-end">
    <button class="resend-btn" onclick="cancelEdit(this)">取消</button>
    <button class="resend-btn" onclick="commitEdit(this)">保存并重发</button></div>`;
  bub.querySelector("textarea").focus();
}
function cancelEdit(btn){
  const wrap=btn.closest(".msg"); const idx=parseInt(wrap.dataset.idx||"0",10);
  const txt=wrap.dataset.text||""; const bub=wrap.querySelector(".bubble");
  if(wrap.classList.contains("user")) bub.innerHTML=inline(txt);
  else { bub.innerHTML=md(txt); try{ if(window.hljs){ bub.querySelectorAll("pre code").forEach(b=>hljs.highlightElement(b)); } }catch(e){} }
}
function commitEdit(btn){
  const wrap=btn.closest(".msg"); const idx=parseInt(wrap.dataset.idx||"0",10);
  const ta=wrap.querySelector("textarea"); const newText=ta.value.trim(); if(!newText) return;
  removeMsgsFrom(idx);            // 丢弃该消息及其后的全部内容，开启新分支
  send(newText, {keep:idx});      // 后端从 keep 处截断并以新文本重跑
}
function regenMsg(btn){
  if(busy) return;
  const wrap=btn.closest(".msg"); const idx=parseInt(wrap.dataset.idx||"0",10);
  const userWrap=$$("#messages .msg")[idx-1];
  const userText=userWrap ? (userWrap.dataset.text||"") : "";
  removeMsgsFrom(idx);            // 丢弃该助手消息及其后
  send(userText, {keep:idx, regen:true});   // 后端保留用户消息、重跑该轮
}

// ---------- 视觉理解（图片上传） ----------
async function sendVision(file){
  if(!file) return;
  const dataUrl = await new Promise(res=>{
    const fr=new FileReader(); fr.onload=()=>res(fr.result); fr.readAsDataURL(file);
  });
  addMsg("user", "发送了一张图片", {data:dataUrl});
  busy=true; thinking();
  try{
    const r = await fetch("/api/vision",{method:"POST",headers:{"Content-Type":"application/json"},
      body:JSON.stringify({prompt:"请描述并分析这张图片", image:dataUrl})});
    const d = await r.json();
    unthinking();
    addMsg("assistant", md(d.reply));
  }catch(e){ unthinking(); addMsg("assistant","视觉识别失败："+e.message); }
  busy=false;
}

// ---------- 附件：按类型自动分流（v2.3） ----------
const _DOC_EXT = /\.(pdf|docx|txt|md|csv)$/i;
async function handleAttach(file){
  if(!file) return;
  if(file.type && file.type.startsWith("image/")){
    // 图片 → 视觉理解
    await sendVision(file);
    return;
  }
  if(_DOC_EXT.test(file.name)){
    // 文档 → 入知识库（RAG），并提示用户可继续提问
    await uploadDoc(file);
    toast("已加入知识库：" + file.name + "，现在可以就它提问了");
    return;
  }
  toast("暂不支持该类型：" + (file.name||"未知文件"));
}

// ---------- 会话列表（含删除/重命名/搜索） ----------
async function loadConvs(){
  try{
    const box = $("#convList"); box.innerHTML="";
    const kw = ($("#convSearch").value||"").trim();
    let items=[], snippetOf={};
    if(kw){
      const r = await fetch("/api/search?q="+encodeURIComponent(kw));
      items = await r.json();
      items.forEach(c=>{ snippetOf[c.id]=c.snippet; c.group=""; });
    }else{
      const r = await fetch("/api/conversations"); const list = await r.json();
      items = list.slice().reverse();
    }
    if(!items.length){ box.innerHTML='<div class="conv-empty">'+(kw?"没有匹配的对话":"暂无对话")+'</div>'; return; }
    const groups={};
    items.forEach(c=>{ const g=c.group||"默认"; (groups[g]=groups[g]||[]).push(c); });
    const label=g=> g==="_archived"?"已归档":g;
    const order=Object.keys(groups).sort((a,b)=> a==="默认"?-1 : b==="默认"?1 : a==="_archived"?1 : b==="_archived"?-1 : a.localeCompare(b));
    order.forEach(g=>{
      const sec=document.createElement("div"); sec.className="conv-group";
      sec.innerHTML=`<div class="conv-group-title">${escapeHtml(label(g))} <small>(${groups[g].length})</small></div>`;
      groups[g].forEach(c=> sec.appendChild(buildConvItem(c, snippetOf[c.id])));
      box.appendChild(sec);
    });
  }catch(e){}
}
function buildConvItem(c, snip){
  const d=document.createElement("div"); d.className="conv-item"; d.dataset.id=c.id;
  const title = escapeHtml(c.title||"对话");
  const s = snip ? `<div class="conv-snip">${escapeHtml(snip)}</div>` : "";
  d.innerHTML = `<span class="conv-title">${title}</span>${s}
    <span class="conv-acts">
      <button class="conv-act" data-act="group" title="移动到分组">${ic('folder')}</button>
      <button class="conv-act" data-act="rename" title="重命名">${ic('edit')}</button>
      <button class="conv-act" data-act="del" title="删除">${ic('trash')}</button>
    </span>`;
  d.onclick=(e)=>{ if(e.target.closest(".conv-act")) return; openConversation(c.id); };
  d.querySelector('[data-act="del"]').onclick=async(e)=>{
    e.stopPropagation();
    if(!confirm("确定删除该对话？")) return;
    await fetch("/api/conversations?id="+c.id,{method:"DELETE"});
    loadConvs();
    if(SESSION===c.id){ SESSION=null; APPLIED_MODEL=null; SESSION_MODEL=""; setSessionModel(""); if($("#welcomeStage")) parkComposer(); $("#messages").innerHTML=""; renderWelcome(); $("#chatTitle").textContent="新的对话"; }
  };
  d.querySelector('[data-act="rename"]').onclick=async(e)=>{
    e.stopPropagation();
    const t=prompt("重命名对话：", c.title); if(!t) return;
    await fetch("/api/conversations",{method:"POST",headers:{"Content-Type":"application/json"},
      body:JSON.stringify({id:c.id, title:t})});
    loadConvs();
    if(SESSION===c.id) $("#chatTitle").textContent=t;
  };
  d.querySelector('[data-act="group"]').onclick=async(e)=>{ e.stopPropagation(); moveConvPrompt(c.id); };
  return d;
}
async function moveConvPrompt(sid){
  const g=prompt("移动到分组（输入分组名；留空=默认分组；_archived=归档）：","");
  if(g===null) return;
  await moveConv(sid, g.trim());
}
async function moveConv(sid, group){
  await fetch("/api/conversations",{method:"POST",headers:{"Content-Type":"application/json"},
    body:JSON.stringify({id:sid, group})});
  loadConvs();
}

async function openConversation(sid){
  try{
    const r = await fetch("/api/conversations/"+sid); if(!r.ok) return;
    const d = await r.json();
    SESSION = sid;
    $("#chatTitle").textContent = d.title || "对话";
    setSessionModel(d.model||""); APPLIED_MODEL = d.model||"";
    if($("#welcomeStage")) parkComposer();   // v2.5：欢迎区存在时先保护输入框
    $("#messages").innerHTML = "";
    (d.messages||[]).forEach((m,i)=>{
      if(m.role==="user") addMsg("user", escapeHtml(m.content), null, m.content, i);
      else addMsg("assistant", md(m.content), null, m.content, i);
    });
    if(activeTab>=0 && TABS[activeTab]){
      TABS[activeTab].session=sid; TABS[activeTab].model=d.model||""; TABS[activeTab].title=d.title||"对话";
      TABS[activeTab].html=$("#messages").innerHTML; renderTabs();
    }
    loadArtifacts(sid);   // 改动12：切换对话时同步切换产物条
  }catch(e){}
}
function escapeHtml(s){ return (s||"").replace(/[&<>"]/g, c=>({"&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;"}[c])); }

// ---------- 记忆 ----------
async function refreshMemory(){
  const r = await fetch("/api/memory?session_id="+(SESSION||"default"));
  const m = await r.json();
  const box=$("#memBody"); if(!box) return;
  const empty = !m.style && !(m.characters||[]).length && !(m.facts||[]).length && !(m.world||[]).length;
  if(empty){
    box.innerHTML = `<div class="conv-empty">记忆库还是空的～ 在对话里告诉我主角名字、题材或风格，我会自动记住，长篇创作防丢稿 / 防幻觉。<br><br>例如：「主角叫苏无尘，仙侠题材，文风清冷」</div>`;
    return;
  }
  box.innerHTML =
    `<div class="mem-row"><span>风格偏好</span><b>${m.style||"—"}</b></div>`+
    `<div class="mem-row"><span>人物</span><b>${(m.characters||[]).join("、")||"—"}</b></div>`+
    `<div class="mem-row"><span>事实/设定</span><b>${(m.facts||[]).join("；")||"—"}</b></div>`+
    `<div class="mem-row"><span>世界观</span><b>${(m.world||[]).join("、")||"—"}</b></div>`;
}

// ---------- 用户配置（多用户） ----------
async function loadProfiles(){
  const r = await fetch("/api/profiles"); const d = await r.json();
  const sel = $("#profileSel"); if(!sel) return; sel.innerHTML="";
  (d.profiles||[]).forEach(p=>{
    const o=document.createElement("option"); o.value=p; o.textContent=p; if(p===d.active)o.selected=true; sel.appendChild(o);
  });
  const o=document.createElement("option"); o.value="__new__"; o.textContent="新建用户"; sel.appendChild(o);
}
async function switchProfile(name){
  if(name==="__new__"){
    const n=prompt("输入新用户名（用于隔离记忆/会话/技能）：");
    if(!n) return loadProfiles();
    await fetch("/api/profiles",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({name:n})});
  }else{
    await fetch("/api/profiles",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({name})});
  }
  SESSION=null; $("#messages").innerHTML=""; $("#chatTitle").textContent="新的对话";
  await loadProfiles(); loadConvs();
}

// ---------- 状态徽标 ----------
async function updateStatus(){
  try{
    const r=await fetch("/api/config"); const c=await r.json();
    const dot=$("#statusDot");
    let txt="本地引擎";
    if(c.llm&&c.llm.enabled){
      txt="大模型已接入"; if(dot) dot.classList.add("on");
    } else { if(dot) dot.classList.remove("on"); }
    if(c.vision&&c.vision.enabled) txt="多模态已接入";
    $("#statusText").textContent=txt;
  }catch(e){}
}

// ---------- 面板 ----------
function pHero(icon, title, desc){
  return `<div class="pcard pcard-grad phero">
    <div class="picon">${ic(icon)}</div>
    <div><h4>${title}</h4><p>${desc}</p></div>
  </div>`;
}
const PANELS = {
  write: ()=>pHero('write','写作助手','直接在对话里描述需求即可，支持短篇、小说、公众号、脚本、润色改写等多种创作场景。')+
    `<div class="psec-title">常用模板</div>
    <div class="pchips">
      <button class="pchip" onclick="send('写一段都市悬疑短篇，约 800 字，先给标题和人设')">都市悬疑短篇</button>
      <button class="pchip" onclick="send('帮我规划一个仙侠长篇小说的世界观与大纲')">长篇大纲</button>
      <button class="pchip" onclick="send('写一篇公众号干货文：普通人如何用 AI 提效')">公众号文章</button>
      <button class="pchip" onclick="send('续写我刚才的故事，往下发展 500 字')">续写</button>
      <button class="pchip" onclick="send('把上面这段改写得更口语化、更有网感')">改写润色</button>
    </div>
    <div class="psec-title">示例指令</div>
    <ul class="plist">
      <li>「写一段仙侠短篇，主角叫苏无尘」</li>
      <li>「来一篇公众号文章：如何高效阅读」</li>
      <li>「写个 3 分钟都市短剧脚本」</li>
      <li>写过的角色与风格会自动记入右侧「记忆」</li>
    </ul>`,
  image: ()=>pHero('image','AI 生图','输入画面描述即可生成小说封面、配图或场景图；支持中文提示词，无需背诵英文咒语。')+
    `<div class="pcard">
      <div class="psec-title">画面描述</div>
      <input class="field" id="imgPrompt" placeholder="例如：仙侠小说封面，主角持剑立于山巅" style="margin-bottom:10px">
      <button class="btn" onclick="genImage()">生成图片</button>
    </div>
    <div class="pcard cover-prev" id="coverPrev"><p style="text-align:center;color:var(--txt-3);font-size:13px;margin:0">预览区</p></div>`,
  prompt: ()=>pHero('prompt','提示词生成','把模糊想法转写成高质量 AI 提示词，适用于生图、写作、角色设定等场景。')+
    `<div class="psec-title">快捷示例</div>
    <div class="pchips">
      <button class="pchip" onclick="send('给我一个赛博朋克城市的生图提示词')">赛博朋克城市</button>
      <button class="pchip" onclick="send('古风仙侠少女的生图提示词')">古风仙侠少女</button>
      <button class="pchip" onclick="send('帮我把「一只猫在月球上」改写成电影感提示词')">电影感改写</button>
    </div>
    <div class="psec-title">用法</div>
    <ul class="plist">
      <li>在对话里说「给我一个__的生图提示词」</li>
      <li>会自动补齐风格、光影、镜头与负面提示词</li>
    </ul>`,
  memory: ()=>pHero('memory','记忆库','长篇创作防丢稿 / 防幻觉。对话中提及的主角名、题材、风格会被自动捕获并复用。')+
    `<div class="pcard"><div id="memBody"><div class="mem-row"><span>状态</span><b>加载中…</b></div></div></div>
    <div class="psec-title">自动捕获</div>
    <ul class="plist">
      <li>主角姓名、世界观设定</li>
      <li>常用语气、文风偏好</li>
      <li>已确认的剧情节点</li>
    </ul>`,
  knowledge: ()=>pHero('knowledge','知识库（RAG）','上传 PDF / Word / TXT / MD / CSV，对话时会做本地语义检索辅助创作，无需向量库。')+
    `<div class="pcard">
      <div class="psec-title">文档</div>
      <button class="btn" onclick="$('#docInput').click()" style="display:inline-flex;align-items:center;justify-content:center;gap:6px">${ic('plus')}上传文档</button>
      <div id="docList" class="doc-list" style="margin-top:10px"></div>
    </div>
    <ul class="plist">
      <li>上传后会自动切分为语义片段</li>
      <li>对话中引用知识库可提高专业性</li>
    </ul>`,
  skills: renderSkills,
  terminal: ()=>pHero('terminal','终端','在电脑上真实执行命令；危险/写操作前会弹窗确认，也可开启只读沙箱模式。')+
    `<div class="pcard">
      <div class="psec-title">输出</div>
      <div class="term-out" id="termOut">$ 就绪。危险命令/写操作已被拦截。</div>
    </div>
    <div class="pcard">
      <div class="psec-title">输入</div>
      <input class="term-in" id="termIn" placeholder="输入命令，如 ls -la，然后回车">
      <label class="ck" style="margin-top:8px"><input type="checkbox" id="readonlyChk"> 只读沙箱模式（禁用 rm/cp/mv 等写操作）</label>
    </div>
    <ul class="plist">
      <li>支持「下载 https://x/y.zip」</li>
      <li>支持「连 b站」等快捷说法</li>
    </ul>`,
  code: ()=>pHero('code','代码运行','编写 Python 代码并真实运行，结果直接返回；适合数据处理、脚本测试与快速原型。')+
    `<div class="pcard">
      <div class="psec-title">编辑器</div>
      <textarea class="code-area" id="codeArea">print("Hello, 墨核 AI")
# 在这里写 Python，点运行</textarea>
      <button class="btn" style="margin-top:10px;display:inline-flex;align-items:center;justify-content:center;gap:6px" onclick="runCode()">${ic('play')}运行</button>
    </div>
    <div class="pcard">
      <div class="psec-title">运行结果</div>
      <div class="term-out" id="codeOut"></div>
    </div>`,
  agent: ()=>pHero('agent','Agent 搭建','定义目标与多步任务，服务端按顺序调用搜索/生图/代码/终端/文档/写作工具编排执行。')+
    `<div class="pcard">
      <div class="psec-title">目标</div>
      <input class="field" id="agentGoal" placeholder="目标：分析热榜并写一份选题报告">
    </div>
    <div class="pcard">
      <div class="psec-title">执行步骤</div>
      <div id="agentSteps"></div>
      <button class="btn sec" onclick="addStep()" style="margin-top:8px;display:inline-flex;align-items:center;justify-content:center;gap:6px">${ic('plus')}添加步骤</button>
    </div>
    <div style="display:flex;gap:8px;align-items:center;flex-wrap:wrap">
      <button class="btn" id="agentRunBtn" style="display:inline-flex;align-items:center;justify-content:center;gap:6px" onclick="runAgent()">${ic('agent')}运行 Agent</button>
      <button class="btn sec" id="agentStopBtn" style="display:none" onclick="stopAgent()">⏹ 停止</button>
    </div>
    <div class="pcard" id="agentTimelineCard" style="display:none">
      <div class="psec-title">任务进度 <span id="agentStepBadge" style="opacity:.6;font-size:12px"></span></div>
      <div id="agentTimeline"></div>
    </div>
    <div class="pcard">
      <div class="psec-title">结果</div>
      <div class="term-out" id="agentOut"></div>
    </div>`,
  fun: renderFuns,
  settings: renderSettings,
  ollama: renderOllama,
  // v2.2：M6 能力补前端入口
  mcp: renderMcp,
  subagent: renderSubagent,
  skillpack: renderSkillPack,
};
async function openPanel(key){
  const titles={write:"写作",image:"AI 生图",prompt:"提示词",memory:"记忆",
    knowledge:"知识库",skills:"技能",terminal:"终端",code:"代码",agent:"Agent",fun:"离谱玩法",ollama:"本地模型",settings:"设置",
    mcp:"MCP 客户端",subagent:"子 Agent 并行",skillpack:"技能包"};
  $("#panelTitle").textContent = titles[key]||"面板";
  // 仅工作型面板（知识库/终端/代码/Agent/离谱玩法）显示「全屏覆盖聊天区」按钮
  const MAX_PANELS = new Set(["knowledge","terminal","code","agent","fun","mcp","subagent","skillpack"]);
  $("#panelHead").dataset.max = MAX_PANELS.has(key) ? "1" : "0";
  $("#panel").classList.remove("fullscreen");   // 切换面板时退出全屏
  $("#panel").classList.remove("hidden");
  const fn = PANELS[key];
  // renderSettings / renderKnowledge / renderSkills 是 async，需 await 其返回的 Promise，
  // 否则 innerHTML 会被赋成 "[object Promise]"，面板内容永远不显示。
  $("#panelBody").innerHTML = (typeof fn==="function") ? await fn() : "";
  if(key==="memory") refreshMemory();
  if(key==="terminal") bindTerm();
  if(key==="knowledge") loadDocs();
  if(key==="mcp") loadMcpServers();
  if(key==="skillpack") loadSkillPacks();
}
function togglePanelMax(){
  const p = $("#panel");
  p.classList.toggle("fullscreen");
  const on = p.classList.contains("fullscreen");
  $("#panelMax").querySelector(".ic").setAttribute("data-ic", on ? "minimize" : "maximize");
}
function closePanel(){ $("#panel").classList.add("hidden"); }

// ---------- 设置弹窗 ----------
let _settingsConfig = null;  // 当前渲染时的配置快照
let _settingsProvider = "custom";
async function openSettings(){
  $("#settingsMask").classList.remove("hidden");
  $("#settingsBody").innerHTML = await renderSettings();
  switchSettingsTab("provider");
  selectProvider((_settingsConfig && _settingsConfig.provider) || "custom", true);
}
function closeSettings(){ $("#settingsMask").classList.add("hidden"); }
function switchSettingsTab(tab){
  $$("#settingsTabs .settings-tab").forEach(b=> b.classList.toggle("active", b.dataset.tab===tab));
  $$("#settingsBody .settings-section").forEach(s=> s.classList.toggle("active", s.dataset.section===tab));
  if(tab==="mcp"){ loadMcpCfg(); setTimeout(switchMcpTransport, 0); }
}
function selectProvider(key, init){
  _settingsProvider = key;
  const p = (_settingsConfig && _settingsConfig.providers && _settingsConfig.providers[key]) || {};
  const local = (key==="embedded" || key==="ollama");
  $$("#settProvList .sett-prov").forEach(b=> b.classList.toggle("active", b.dataset.p===key));
  const sel = $("#settModelSel");
  if(sel){
    const curModel = (_settingsConfig && _settingsConfig.llm && _settingsConfig.llm.model) || "";
    let opts = (p.models||[]).slice();
    const curInOpts = curModel && opts.includes(curModel);
    if(curModel && !curInOpts) opts.unshift(curModel);
    const selected = init ? curModel : (curInOpts ? curModel : (p.model||""));
    sel.innerHTML = opts.map(m=>`<option value="${m}" ${m===selected?'selected':''}>${m}</option>`).join('');
    if(!sel.value && p.model) sel.value = p.model;
  }
  if(!init){ const url=$("#settLlmUrl"); if(url && p.base_url && !url.dataset.touched) url.value=p.base_url; }
  const keyIn=$("#settLlmKey");
  if(keyIn){
    keyIn.placeholder = local ? "本地模型无需 Key" : "API Key（仅保存在本机）";
    // #5 切换供应商时，回填该供应商自己记住的 Key（不与其他供应商混用）
    if(!local && !init){
      const pk=(_settingsConfig&&_settingsConfig.provider_keys&&_settingsConfig.provider_keys[key])||{};
      keyIn.value = pk.api_key || "";
    }
  }
  const lf=$("#settLlmFields"); if(lf) lf.style.display = local ? "none":"block";
  const eb=$("#settEmbBox"); if(eb) eb.style.display = (key==="embedded") ? "block":"none";
  const st=$("#settLlmStatus");
  if(st){
    if(local){ st.className="sett-status ok"; st.innerHTML="本地 / 离线运行，无需 Key"; }
    else if(keyIn && !keyIn.value.trim()){ st.className="sett-status warn"; st.innerHTML="需要填写 API Key 才能联网调用"; }
    else { st.className="sett-status ok"; st.innerHTML="配置完整，可联网调用"; }
  }
}

// ---------- 执行前确认（真实运行于本机的安全闸门） ----------
const SAFE_CMD_PREFIX = ["ls","cat","pwd","echo","grep","head","tail","df","du","whoami",
  "date","wc","sort","uniq","awk","sed","tree","find","ps","top","free","uname","type","which","man","history"];
function cmdNeedsConfirm(cmd){
  const c = cmd.trim().toLowerCase();
  return !SAFE_CMD_PREFIX.some(p => c===p || c.startsWith(p+" ") || c.startsWith(p+"\t"));
}
let _confirmResolve = null;
function confirmRun(title, detail, cmd){
  $("#confirmTitle").textContent = title;
  $("#confirmDetail").textContent = detail;
  const box = $("#confirmCmd");
  box.textContent = cmd || ""; box.style.display = cmd ? "block" : "none";
  $("#confirmMask").classList.remove("hidden");
  return new Promise(res=>{ _confirmResolve = res; });
}
function bindConfirm(){
  const close=(v)=>{ $("#confirmMask").classList.add("hidden"); const r=_confirmResolve; _confirmResolve=null; if(r) r(v); };
  $("#confirmYes").onclick=()=>close(true);
  $("#confirmNo").onclick=()=>close(false);
  $("#confirmMask").addEventListener("click",(e)=>{ if(e.target===$("#confirmMask")) close(false); });
}

// ---------- 本地模型（Ollama）管理 ----------
async function renderOllama(){
  const r = await fetch("/api/ollama/models"); const d = await r.json();
  const running = d.running;
  let html = pHero('server','本地模型（Ollama）','管理本机运行的 Ollama 模型，零 Key 离线推理。需先安装并启动 Ollama（免费，ollama.com）。');
  html += `<div class="pcard">
    <div class="psec-title">运行状态</div>
    <div style="display:flex;align-items:center;justify-content:space-between;gap:8px;margin-top:6px">
      <div style="font-size:13px;color:var(--txt-2)">Ollama 服务：<b style="color:${running?'var(--ok)':'var(--danger)'}">${running?'已运行':'未运行'}</b></div>
      <button class="conv-act" onclick="refreshOllama()" title="刷新状态">${ic('refresh')}</button>
    </div>
  </div>`;
  html += `<div class="pcard">
    <div class="psec-title">已安装模型</div>
    <div id="olList" class="doc-list" style="margin-top:8px">`;
  (d.models||[]).forEach(m=>{
    html += `<div class="doc-item"><span>${ic('doc')} ${m}</span><span class="conv-acts">
      <button class="conv-act" onclick="useOllama('${m.replace(/'/g,"\\'")}')" title="使用此模型">${ic('check')}</button>
      <button class="conv-act" onclick="delOllama('${m.replace(/'/g,"\\'")}')" title="删除">${ic('trash')}</button></span></div>`;
  });
  html += `</div>`;
  if(!(d.models||[]).length) html += `<div class="conv-empty" style="margin-top:8px">${running?'还没有模型，拉一个试试。':'未检测到 Ollama，请先安装并启动。'}</div>`;
  html += `</div>`;
  html += `<div class="pcard">
    <div class="psec-title">拉取新模型</div>
    <input class="field" id="olPull" placeholder="模型名，如 llama3 / qwen2.5 / gemma2" style="margin:8px 0 10px">
    <button class="btn" id="olPullBtn" onclick="pullOllama()" style="display:inline-flex;align-items:center;justify-content:center;gap:6px">${ic('export')}拉取</button>
    ${!running?'<p style="font-size:12px;color:var(--txt-3);margin:8px 0 0">Ollama 未运行，拉取命令会尝试自动启动本地服务；若未安装则会失败。</p>':''}
    <div id="olLog" class="term-out" style="margin-top:10px;display:none"></div>
  </div>`;
  return html;
}
function ollamaTarget(){ return $("#ollamaBox") || $("#panelBody"); }
async function refreshOllama(){
  const pb=ollamaTarget(); if(pb) pb.innerHTML = await renderOllama();
}
async function useOllama(m){
  await fetch("/api/ollama/use",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({model:m})});
  updateStatus(); toast("已切换到本地模型："+m);
  const pb=ollamaTarget(); if(pb) pb.innerHTML = await renderOllama();
}
async function delOllama(m){
  if(!confirm("确定删除本地模型 "+m+"？")) return;
  await fetch("/api/ollama/delete",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({model:m})});
  toast("已删除："+m);
  const pb=ollamaTarget(); if(pb) pb.innerHTML = await renderOllama();
}
async function pullOllama(){
  const name=$("#olPull").value.trim(); if(!name) return;
  const btn=$("#olPullBtn"); const log=$("#olLog");
  btn.textContent="拉取中…"; btn.disabled=true; log.style.display="block"; log.textContent="正在拉取 "+name+" …";
  try{
    const r=await fetch("/api/ollama/pull",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({model:name})});
    const d=await r.json();
    log.textContent = d.ok ? ("完成 ✅\n"+(d.output||"")) : ("失败 ❌\n"+(d.error||"未知错误"));
    if(d.ok){ const pb=ollamaTarget(); if(pb) pb.innerHTML = await renderOllama(); }
  }catch(e){ log.textContent="请求失败："+e.message; }
  btn.textContent="拉取"; btn.disabled=false;
}

// ---------- 终端 ----------
function bindTerm(){
  const inp = $("#termIn"); if(!inp) return;
  const ro = $("#readonlyChk");
  if(ro){ ro.onchange=async()=>{
    await fetch("/api/config",{method:"POST",headers:{"Content-Type":"application/json"},
      body:JSON.stringify({sandbox:{readonly:ro.checked}})});
    $("#termOut").textContent += `\n[只读沙箱=${ro.checked?"开":"关"}]`;
  };}
  inp.addEventListener("keydown", async (e)=>{
    if(e.key==="Enter"){
      const cmd = inp.value; if(!cmd) return;
      // 未开启只读沙箱时，非安全只读命令需用户确认（真实执行于本机）
      if(ro && !ro.checked && cmdNeedsConfirm(cmd)){
        const yes = await confirmRun("确认在本地执行命令",
          "当前未开启只读沙箱，该命令将在你的电脑上真实运行。请确认无误再继续。", cmd);
        if(!yes){ $("#termOut").textContent += `\n$ ${cmd}  [已取消]`; return; }
      }
      $("#termOut").textContent += "\n$ "+cmd;
      inp.value="";
      const r = await fetch("/api/terminal",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({command:cmd})});
      const d = await r.json();
      $("#termOut").textContent += "\n"+d.output;
      $("#termOut").scrollTop = $("#termOut").scrollHeight;
    }
  });
}
async function genImage(){
  const p = $("#imgPrompt").value; if(!p) return;
  const r = await fetch("/api/image",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({prompt:p,session_id:SESSION})});
  const d = await r.json();
  const src = d.data || "";
  const ext = (d.format||"svg").toUpperCase();
  $("#coverPrev").innerHTML = `<img src="${src}" style="max-width:100%"><div style="margin-top:6px"><a href="${d.path}" target="_blank" style="color:#7c5cff;font-size:12px">下载 ${ext}</a></div>`;
}
async function runCode(){
  const code = $("#codeArea").value;
  const yes = await confirmRun("确认运行 Python 代码",
    "代码将在本地真实运行（可能访问你的文件系统或网络）。确认执行？", code);
  if(!yes){ $("#codeOut").textContent = "[已取消]"; return; }
  const r = await fetch("/api/code",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({code})});
  const d = await r.json();
  $("#codeOut").textContent = d.output;
}

// ---------- 知识库（RAG 文档） ----------
async function loadDocs(){
  const r = await fetch("/api/docs"); const list = await r.json();
  const box = $("#docList"); if(!box) return;
  if(!list.length){ box.innerHTML='<div class="conv-empty">还没有文档，先上传一个吧。</div>'; return; }
  box.innerHTML = list.map(d=>`<div class="doc-item">
    <span>${ic('doc')} ${d.name} <small>(${d.chunks} 片段)</small></span>
    <span class="conv-acts"><button class="conv-act" onclick="delDoc('${d.id}')">${ic('trash')}</button></span></div>`).join("");
}
async function uploadDoc(file){
  const fd = new FormData(); fd.append("file", file);
  const r = await fetch("/api/docs",{method:"POST",body:fd});
  const d = await r.json();
  if(d.ok){ loadDocs(); }
  else { alert("上传失败："+(d.error||"未知错误")); }
}

// =========================================================
// v2.2：M6 能力的前端入口（MCP / 子 Agent / SKILL.md 技能包）
// =========================================================
// ---------- MCP 客户端 ----------
function renderMcp(){
  return pHero('plug','MCP 客户端','连接外部 MCP Server（stdio / HTTP），它的工具会自动注册进 Agent 注册表，可直接被编排调用。')+
    `<div class="pcard">
      <div class="psec-title">已连接服务器</div>
      <div id="mcpList" class="srv-list"><div class="empty-hint">加载中…</div></div>
    </div>
    <div class="pcard">
      <div class="psec-title">操作</div>
      <div class="pchips">
        <button class="pchip" onclick="refreshMcp()">${ic('refresh')}刷新工具列表</button>
        <button class="pchip" onclick="openSettings();switchSettingsTab('mcp')">${ic('plus')}添加 MCP Server</button>
      </div>
      <ul class="plist" style="margin-top:10px">
        <li>在「设置 → MCP」里填写 stdio 命令或 HTTP 地址</li>
        <li>刷新后工具即刻可用，Agent 无需改动即可调用</li>
      </ul>
    </div>`;
}
async function loadMcpServers(){
  const box=$("#mcpList"); if(!box) return;
  try{
    const r=await fetch("/api/mcp/servers"); const d=await r.json();
    const list=d.servers||[];
    if(!list.length){
      box.innerHTML='<div class="empty-hint">还没有配置 MCP Server<br>在「设置 → MCP」里添加一个（stdio 命令或 HTTP 地址）</div>';
      return;
    }
    box.innerHTML = list.map(s=>`<div class="srv-row">
      <span class="srv-dot ${s.ok?'':'off'}"></span>
      <span class="srv-name">${s.name}<small>${s.transport}${s.ok?'':' · '+(s.error||'连接失败')}</small></span>
      <span class="srv-tools">${s.ok? (s.tools.length+' 个工具') : '未连接'}</span>
    </div>`).join("");
  }catch(e){ box.innerHTML='<div class="empty-hint">加载失败：'+e.message+'</div>'; }
}
async function refreshMcp(){
  try{
    const r=await fetch("/api/mcp/refresh",{method:"POST"}); const d=await r.json();
    if(d.ok) alert("已刷新，注入了 "+d.total+" 个工具。");
    else alert("刷新失败："+(d.error||"未知错误"));
  }catch(e){ alert("刷新失败："+e.message); }
  loadMcpServers();
}

// ---------- MCP 设置（新增 / 删除服务器） ----------
function switchMcpTransport(){
  const t=$("#mcpTransport").value;
  $("#mcpCmd").style.display = t==="stdio" ? "" : "none";
  $("#mcpUrl").style.display  = t==="http"   ? "" : "none";
}
async function addMcpServer(){
  const name=($("#mcpName").value||"").trim();
  const transport=$("#mcpTransport").value;
  if(!name){ alert("请填写名称"); return; }
  const body={name:name, transport:transport};
  if(transport==="stdio"){
    body.command=($("#mcpCmd").value||"").trim();
    if(!body.command){ alert("请填写命令"); return; }
  }else{
    body.url=($("#mcpUrl").value||"").trim();
    if(!body.url){ alert("请填写 HTTP 地址"); return; }
  }
  try{
    const r=await fetch("/api/mcp/servers",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(body)});
    const d=await r.json();
    if(!d.ok){ alert("添加失败："+(d.error||"未知错误")); return; }
    $("#mcpName").value=""; $("#mcpCmd").value=""; $("#mcpUrl").value="";
    loadMcpCfg();
  }catch(e){ alert("添加失败："+e.message); }
}
async function delMcpServer(name){
  if(!confirm("确定移除 MCP Server「"+name+"」？")) return;
  try{
    await fetch("/api/mcp/servers?name="+encodeURIComponent(name),{method:"DELETE"});
    loadMcpCfg();
  }catch(e){ alert("移除失败："+e.message); }
}
async function loadMcpCfg(){
  const box=$("#mcpCfgList"); if(!box) return;
  try{
    const r=await fetch("/api/mcp/servers"); const d=await r.json();
    const list=d.servers||[];
    if(!list.length){ box.innerHTML='<div class="empty-hint">还没有配置 MCP Server</div>'; return; }
    box.innerHTML=list.map(s=>`<div class="srv-row">
      <span class="srv-dot ${s.ok?'':'off'}"></span>
      <span class="srv-name">${s.name}<small>${s.transport}${s.ok?'':' · '+(s.error||'连接失败')}</small></span>
      <span class="srv-tools">${s.ok?(s.tools.length+' 工具'):'未连接'}</span>
      <button class="conv-act" title="移除" onclick="delMcpServer('${s.name}')">${ic('trash')}</button>
    </div>`).join("");
  }catch(e){ box.innerHTML='<div class="empty-hint">加载失败：'+e.message+'</div>'; }
}

// ---------- 子 Agent 并行 ----------
function renderSubagent(){
  return pHero('bolt','子 Agent 并行','把长任务拆成多个独立子任务并行执行，各自拥有独立上下文，主对话只收到结论摘要，不会被工具日志淹没。')+
    `<div class="pcard">
      <div class="psec-title">子任务（每行一个）</div>
      <textarea class="code-area" id="subGoals" style="min-height:96px">搜索竞品最新资料
整理用户评价
生成对比表格</textarea>
      <button class="btn" id="subRunBtn" style="margin-top:10px;display:inline-flex;align-items:center;justify-content:center;gap:6px" onclick="runSubagent()">${ic('bolt')}并行运行</button>
    </div>
    <div class="pcard">
      <div class="psec-title">执行状态</div>
      <div id="subTasks" style="margin-top:8px"><div class="empty-hint">等待运行…</div></div>
    </div>
    <div class="pcard">
      <div class="psec-title">汇总摘要</div>
      <div class="term-out" id="subOut" style="margin-top:8px">等待运行…</div>
    </div>`;
}
async function runSubagent(){
  const goals=$("#subGoals").value.split("\n").map(s=>s.trim()).filter(Boolean);
  if(!goals.length){ alert("请先填写至少一个子任务"); return; }
  const box=$("#subTasks"), out=$("#subOut");
  box.innerHTML = goals.map(g=>`<div class="sub-task"><span class="st run"></span>
    <span class="sub-goal">${g.replace(/</g,"&lt;")}</span><span class="sub-state run">运行中</span></div>`).join("");
  out.textContent="并行执行中…";
  try{
    const r=await fetch("/api/subagent",{method:"POST",headers:{"Content-Type":"application/json"},
      body:JSON.stringify({goals:goals.map(g=>({goal:g}))})});
    const d=await r.json();
    if(!d.ok){ out.textContent="失败："+(d.error||"未知错误"); return; }
    const results=d.results||[];
    box.innerHTML = results.map((x,i)=>{
      const ok=x.ok!==false;
      const st=ok?"完成":(x.error||"失败");
      return `<div class="sub-task"><span class="st ${ok?'':'err'}"></span>
        <span class="sub-goal">${goals[i]||""}</span>
        <span class="sub-state ${ok?'':'err'}">${st}</span></div>`;
    }).join("");
    out.textContent = d.summary || results.map(x=>x.summary||x.answer||"").join("\n\n") || "（无摘要）";
  }catch(e){
    out.textContent="请求失败："+e.message;
    box.innerHTML = goals.map(g=>`<div class="sub-task"><span class="st err"></span>
      <span class="sub-goal">${g}</span><span class="sub-state err">失败</span></div>`).join("");
  }
}

// ---------- SKILL.md 技能包（与原有技能系统打通） ----------
function renderSkillPack(){
  return pHero('package','SKILL.md 技能包','标准化技能包：一份 SKILL.md（元数据 + 指令 + 可选脚本）打包成 zip，可导入导出分享。与左侧「技能」共用同一份技能库。')+
    `<div class="pcard">
      <div class="psec-title">已安装技能包</div>
      <div id="packList" style="margin-top:8px"><div class="empty-hint">加载中…</div></div>
    </div>
    <div class="pcard">
      <div class="psec-title">操作</div>
      <div class="pchips">
        <button class="pchip" onclick="$('#skillPackImport').click()">${ic('export')}导入 .zip</button>
        <button class="pchip" onclick="exportSkillPack()">${ic('export')}导出选中</button>
        <button class="pchip" onclick="validateSkillPack()">${ic('check')}校验 SKILL.md</button>
      </div>
      <textarea class="code-area" id="packText" style="min-height:84px;margin-top:10px"
        placeholder="粘贴 SKILL.md 内容以校验：&#10;---&#10;name: my-skill&#10;description: 做什么的&#10;---&#10;指令正文…"></textarea>
      <div id="packCheck" style="margin-top:8px"></div>
    </div>
    <ul class="plist">
      <li>技能包与「技能」面板共用 skills.json，装一次两处都能用</li>
      <li>导出得到 .zip，可直接发给别人导入</li>
    </ul>`;
}
async function loadSkillPacks(){
  const box=$("#packList"); if(!box) return;
  try{
    const r=await fetch("/api/skills"); const list=await r.json();
    if(!list.length){ box.innerHTML='<div class="empty-hint">还没有技能<br>导入一个 .zip 技能包，或在「技能」面板里新建</div>'; return; }
    box.innerHTML = list.map(s=>`<div class="pack-row">
      <span class="pk-i">${ic('package')}</span>
      <span class="pack-name">${s.name}<small>${s.desc||""}</small></span>
      <span class="srv-tools">${s.version||"1.0"}</span>
      <button class="conv-act" title="导出为 .zip" onclick="exportSkillPack('${s.id}')">${ic('export')}</button>
    </div>`).join("");
  }catch(e){ box.innerHTML='<div class="empty-hint">加载失败：'+e.message+'</div>'; }
}
async function exportSkillPack(id){
  if(!id){ alert("请先在列表里点导出按钮，选择一个技能包"); return; }
  try{
    const r=await fetch("/api/skill/export",{method:"POST",headers:{"Content-Type":"application/json"},
      body:JSON.stringify({id:id})});
    if(!r.ok){ const e=await r.json().catch(()=>({})); alert("导出失败："+(e.error||r.status)); return; }
    const blob=await r.blob();
    const a=document.createElement("a");
    a.href=URL.createObjectURL(blob); a.download=(id+".zip");
    document.body.appendChild(a); a.click(); a.remove();
  }catch(e){ alert("导出失败："+e.message); }
}
async function validateSkillPack(){
  const text=$("#packText").value; const box=$("#packCheck");
  if(!text.trim()){ box.innerHTML='<div class="empty-hint">请先粘贴 SKILL.md 内容</div>'; return; }
  try{
    const r=await fetch("/api/skill/validate",{method:"POST",headers:{"Content-Type":"application/json"},
      body:JSON.stringify({text:text})});
    const d=await r.json();
    if(d.ok){
      const meta=(d.data&&d.data.name)?d.data:{};
      box.innerHTML=`<div class="empty-hint" style="border-color:var(--mint);color:var(--mint)">校验通过：${meta.name||"未命名"} ${meta.version||""}</div>`;
    }else{
      const errs=(d.errors||[]).join("；")||d.error||"未知问题";
      box.innerHTML=`<div class="empty-hint" style="border-color:var(--danger);color:var(--danger)">校验未通过：${errs}</div>`;
    }
  }catch(e){ box.innerHTML='<div class="empty-hint">校验失败：'+e.message+'</div>'; }
}
async function importSkillPack(file){
  const fd=new FormData(); fd.append("file", file);
  try{
    const r=await fetch("/api/skill/import",{method:"POST",body:fd});
    const d=await r.json();
    if(d.ok){ alert("已导入技能包："+(d.skill&&d.skill.name||"未命名")); loadSkillPacks(); }
    else alert("导入失败："+(d.error||"未知错误"));
  }catch(e){ alert("导入失败："+e.message); }
}
async function delDoc(id){
  await fetch("/api/docs?id="+id,{method:"DELETE"}); loadDocs();
}
// ---------- 技能 ----------
async function renderSkills(){
  const r = await fetch("/api/skills"); const list = await r.json();
  let html = pHero('skills','技能（插件系统）','把常用指令封装成可复用的技能插件，支持提示词型与人设型，可导入导出。');
  html += `<div class="pcard">
    <div class="psec-title">管理</div>
    <div class="pchips">
      <button class="pchip" onclick="$('#skillImport').click()">${ic('export')}导入 JSON</button>
      <button class="pchip" onclick="exportSkills()">${ic('export')}导出 JSON</button>
      <button class="pchip" onclick="openPanel('skillpack')">${ic('package')}技能包</button>
    </div>
    <div class="sett-tip" style="margin-top:10px">技能与「技能包」共用同一份技能库：这里的技能可用「导出 JSON」分享，也能在「技能包」面板里导出成 .zip 分享给他人。</div>
  </div>`;
  html += `<div class="pcard">
    <div class="psec-title">技能市场</div>
    <div id="skillMarket" class="doc-list" style="margin:8px 0 10px">加载中…</div>
    <div style="display:flex;gap:6px">
      <input class="field" id="skillUrl" placeholder="粘贴社区技能 JSON 链接" style="margin:0">
      <button class="btn sec" style="margin:0;width:auto;padding:0 12px" onclick="importSkillUrl()">从链接导入</button>
    </div>
  </div>`;
  html += `<div class="pcard">
    <div class="psec-title">我的技能</div>
    <div id="skillList" style="margin-top:8px">`;
  list.forEach(s=>{
    html += `<div class="skill-card"><div class="sc-top">${iconOrText(s.icon)} ${s.name}
      <span class="sc-del" onclick="delSkill('${s.id}')">删除</span></div>
      <div class="sc-desc">${s.desc}</div>
      <div class="fun-list" style="font-size:11px">触发词：${(s.trigger||[]).join(" / ")} ｜ 类型：${s.type}</div>
      <div style="margin-top:6px"><button class="conv-act" style="color:var(--accent);display:inline-flex;align-items:center;justify-content:center" title="导出为 SKILL.md 技能包(.zip)" onclick="exportSkillPack('${s.id}')">${ic('package')}导出技能包</button></div></div>`;
  });
  html += `</div></div>`;
  html += `<div class="pcard">
    <div class="psec-title">新建技能</div>
    <input class="field" id="skName" placeholder="技能名，如：剧情诊所">
    <input class="field" id="skIcon" placeholder="图标名（如 skill/write/agent）或任意符号">
    <input class="field" id="skDesc" placeholder="一句话描述">
    <input class="field" id="skTrig" placeholder="触发词（逗号分隔），如 剧情,卡文">
    <select class="field" id="skType"><option value="prompt">提示词型（包装需求输出）</option><option value="persona">人设型（角色扮演）</option></select>
    <textarea class="field" id="skContent" placeholder="提示词内容 / 人设设定"></textarea>
    <button class="btn" onclick="addSkill()">创建技能</button>
  </div>`;
  setTimeout(loadGallery, 0);
  return html;
}
async function loadGallery(){
  const box=$("#skillMarket"); if(!box) return;
  try{
    const r=await fetch("/api/skills/gallery"); const list=await r.json();
    box.innerHTML = list.length? list.map(s=>{
      const addBtn = s.installed?'<span style="color:#3ddc84;font-size:11px">已添加</span>':`<button class="conv-act" style="color:#7c5cff;display:inline-flex;align-items:center;justify-content:center" onclick="addGallerySkill('${s.id}')">${ic('plus')}</button>`;
      return `<div class="doc-item">
        <span>${iconOrText(s.icon)} ${s.name} <small>${s.desc}</small></span>
        <span class="conv-acts">${addBtn}</span></div>`;
    }).join("") : '<div class="conv-empty">市场暂无技能</div>';
  }catch(e){ box.innerHTML='<div class="conv-empty">市场加载失败</div>'; }
}
async function addGallerySkill(id){
  const r=await fetch("/api/skills/gallery"); const list=await r.json();
  const s=list.find(x=>x.id===id); if(!s) return;
  const {id:_, installed, ...body}=s;
  await fetch("/api/skills",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(body)});
  loadGallery();
}
async function importSkillUrl(){
  const url=$("#skillUrl").value.trim(); if(!url) return;
  const r=await fetch("/api/skills/import_url",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({url})});
  const d=await r.json();
  if(d.ok){ alert("已导入 "+d.added+" 个技能，去「技能」列表查看。"); openPanel("skills"); }
  else alert("导入失败："+(d.error||"未知错误"));
}
async function addSkill(){
  const body = {name:$("#skName").value, icon:$("#skIcon").value||"skill", desc:$("#skDesc").value,
    trigger:$("#skTrig").value.split(/[,，]/).map(x=>x.trim()).filter(Boolean),
    type:$("#skType").value, content:$("#skContent").value};
  await fetch("/api/skills",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(body)});
  openPanel("skills");
}
async function delSkill(id){
  await fetch("/api/skills?id="+id,{method:"DELETE"});
  openPanel("skills");
}
function exportSkills(){
  window.open("/api/skills/export","_blank");
}
async function importSkills(file){
  const text = await file.text();
  try{
    const data = JSON.parse(text);
    await fetch("/api/skills/import",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(data)});
    openPanel("skills");
  }catch(e){ alert("导入失败：JSON 解析错误"); }
}

// ---------- 离谱玩法：用户自建 / 导入导出（改动4） ----------
async function renderFuns(){
  let list=[];
  try{ const r=await fetch("/api/funs"); list=await r.json(); }catch(e){ list=[]; }
  let html = pHero('fun','离谱玩法','一些由用户共创的趣味用法，让 AI 不止于聊天。点卡片即可触发，也可自建 / 导入更多玩法。');
  html += `<div class="pcard">
    <div class="psec-title">管理</div>
    <div class="pchips">
      <button class="pchip" onclick="$('#funImport').click()">${ic('export')}导入 JSON</button>
      <button class="pchip" onclick="exportFuns()">${ic('export')}导出 JSON</button>
    </div>
    <input type="file" id="funImport" accept=".json" hidden onchange="importFuns(this.files[0])">
  </div>`;
  html += `<div class="pcard">
    <div class="psec-title">新建玩法</div>
    <input class="field" id="funName" placeholder="玩法名，如：AI 占卜">
    <input class="field" id="funEmoji" placeholder="图标 emoji，如 🔮">
    <input class="field" id="funDesc" placeholder="一句话描述">
    <input class="field" id="funPrompt" placeholder="触发语（点卡片会发给 AI 的内容），如 给我算一卦">
    <button class="btn" onclick="addFun()">创建玩法</button>
  </div>`;
  html += `<div class="pcard">
    <div class="psec-title">玩法列表（${list.length}）</div>
    <div class="pgrid" style="margin-top:8px">`;
  list.forEach(f=>{
    const emoji=(f.emoji||"🎯"); const prompt=(f.prompt||"").replace(/'/g,"\\'").replace(/"/g,"&quot;");
    html += `<div class="pfeat" onclick="send('${prompt}')"><b>${emoji} ${f.name||'玩法'}</b><small>${f.desc||''}</small>
      <span class="sc-del" onclick="event.stopPropagation();delFun('${f.id}')">删除</span></div>`;
  });
  if(!list.length) html += `<div class="conv-empty">还没有玩法，新建一个吧。</div>`;
  html += `</div></div>`;
  return html;
}
async function addFun(){
  const body={name:$("#funName").value, emoji:$("#funEmoji").value||"🎯", desc:$("#funDesc").value, prompt:$("#funPrompt").value};
  if(!body.name||!body.prompt){ alert("请填写玩法名与触发语"); return; }
  await fetch("/api/funs",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(body)});
  openPanel("fun");
}
async function delFun(id){ await fetch("/api/funs?id="+id,{method:"DELETE"}); openPanel("fun"); }
function exportFuns(){ window.open("/api/funs/export","_blank"); }
async function importFuns(file){
  const text=await file.text();
  try{ const data=JSON.parse(text); await fetch("/api/funs/import",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(data)}); openPanel("fun"); }
  catch(e){ alert("导入失败：JSON 解析错误"); }
}

// ---------- 全局热键录制 ----------
let _hkRecording=false, _hkHandler=null;
function recordHotkey(btn){
  const inp=$("#settHkInput");
  if(_hkRecording){ // 取消录制
    if(_hkHandler) window.removeEventListener("keydown", _hkHandler, true);
    _hkRecording=false; btn.textContent="录制"; return;
  }
  btn.textContent="按下组合键…"; _hkRecording=true;
  _hkHandler=(e)=>{
    e.preventDefault();
    const mods=[];
    if(e.ctrlKey) mods.push("ctrl");
    if(e.altKey) mods.push("alt");
    if(e.shiftKey) mods.push("shift");
    let key=e.key.toLowerCase();
    if(["control","alt","shift","meta"].includes(key)) return; // 等待非修饰键
    if(key===" ") key="space";
    inp.value=mods.concat(key).join("+");
    window.removeEventListener("keydown", _hkHandler, true);
    _hkRecording=false; btn.textContent="录制";
  };
  window.addEventListener("keydown", _hkHandler, true);
}
// ---------- 设置（弹窗 tab 式：AI 提供商 / 参数 / 外观 / 数据 / 关于） ----------
async function renderSettings(){
  const r = await fetch("/api/config"); const c = await r.json(); _settingsConfig = c;
  const l=c.llm||{}, im=c.image||{}, vi=c.vision||{}, sb=c.sandbox||{};
  const curTheme = localStorage.getItem("mohe_theme")||"warm";
  const curFont = parseInt(localStorage.getItem("mohe_font")||"14",10);
  const curScale = parseInt(localStorage.getItem("mohe_scale")||"100",10);
  const hk = c.hotkey || "ctrl+alt+m";
  let emb = {};
  try { emb = await (await fetch("/api/embedded/status")).json(); } catch(e){ emb = {}; }
  const embModels = (emb.models && Object.entries(emb.models) || []).map(([k,v])=>
    `<option value="${k}" ${k===emb.model?'selected':''}>${v.label}${v.ready?' 已下载':''}</option>`).join("");
  const embStatTxt = emb.error ? `⚠ ${emb.error}`
    : emb.ready ? "✓ 模型已就绪，可直接对话（已自动切换为本地内置）"
    : (emb.downloading ? `下载中 ${Math.round((emb.progress||0)*100)}%${emb.source==="mirror"?"（国内镜像）":(emb.source==="official"?"（官方源）":"")}`
    : (emb.llama_available===false ? "⚠ 未检测到本地推理引擎：请卸载后重装最新版安装包（新版本已强制内置）"
    : "尚未下载模型权重"));
  const provDesc = {openai:"官方 GPT 系列",deepseek:"深度求索 高性价比",qwen:"阿里通义千问",moonshot:"Kimi 长上下文",
    glm:"智谱 GLM",ollama:"本机运行 零 Key",custom:"兼容 OpenAI 接口",embedded:"离线内置 免 Ollama"};
  const curProv = c.provider||"custom";
  const provCards = Object.entries(c.providers||{}).map(([k,v])=>{
    const cnt = (v.models&&v.models.length)||0;
    return `<button class="sett-prov ${k===curProv?'active':''}" data-p="${k}" onclick="selectProvider('${k}')">
      <span class="name">${v.label||k}</span>
      <span class="desc">${provDesc[k]||''} · ${cnt} 个模型</span>
    </button>`;
  }).join("");
  const temp = (typeof l.temperature==="number")?l.temperature:0.9;
  return `
  <section class="settings-section active" data-section="provider">
    <div class="sett-tip">选择一个 AI 提供商，下方会列出它支持的模型。选好模型、填好 Key 即可联网对话；「本地内置 / Ollama」免 Key、可离线。</div>
    <div class="sett-grid" id="settProvList">${provCards}</div>
    <label class="sett-ck"><input type="checkbox" id="settLlmOn" ${l.enabled?'checked':''}> 启用真实大模型（关闭则用本地模板应答）</label>
    <div class="group">
      <label class="sett-label">模型</label>
      <select class="sett-field" id="settModelSel"></select>
    </div>
    <div id="settLlmFields">
      <label class="sett-label">API Base</label>
      <input class="sett-field" id="settLlmUrl" value="${l.base_url||''}" oninput="this.dataset.touched='1'" placeholder="https://api.openai.com/v1">
      <label class="sett-label" style="margin-top:10px">API Key</label>
      <input class="sett-field" id="settLlmKey" type="password" value="${l.api_key||''}" placeholder="API Key（仅保存在本机）">
      <div class="sett-status" id="settLlmStatus" style="margin-top:10px"></div>
      <label class="sett-ck" style="margin-top:8px"><input type="checkbox" id="settInheritKeys"> 把本 Key 同时用于「生图 / 视觉」（免重复填写，切换供应商可再勾）</label>
    </div>
    <div id="settEmbBox" style="display:none">
      <label class="sett-label">内置模型</label>
      <select class="sett-field" id="embModel">${embModels||''}</select>
      <div id="embStat" class="sett-status" style="margin-top:10px">${embStatTxt}</div>
      <div id="embBar" style="height:8px;background:var(--bg);border-radius:4px;overflow:hidden;margin-top:8px;display:${emb.downloading?'block':'none'}"><div id="embBarFill" style="height:100%;width:${Math.round((emb.progress||0)*100)}%;background:#7c5cff"></div></div>
      <button class="btn sec" id="embDl" type="button" onclick="downloadEmbedded()" style="margin-top:10px">${emb.ready?'已就绪':'下载模型（约 1.1GB）'}</button>
    </div>
  </section>

  <section class="settings-section" data-section="params">
    <div class="sett-h3">全局热键</div>
    <div class="sett-row">
      <div class="group"><input class="sett-field" id="settHkInput" value="${hk}" placeholder="如 ctrl+alt+m"></div>
      <button class="btn sec" type="button" id="hkRec" onclick="recordHotkey(this)" style="width:auto;flex:0 0 auto">录制</button>
    </div>
    <p class="sett-sub">点击「录制」后按下组合键，保存后重启桌面程序生效。</p>
    <div class="sett-h3">创造力（温度）</div>
    <input class="sett-range" type="range" id="settLlmTemp" min="0" max="1" step="0.1" value="${temp}" oninput="document.getElementById('tempVal').textContent=this.value">
    <div class="sett-sub">当前：<b id="tempVal">${temp}</b>（越低越严谨，越高越发散）</div>
    <label class="sett-ck" style="margin-top:6px"><input type="checkbox" id="settRoOn" ${sb.readonly?'checked':''}> 终端沙箱只读模式（禁用 rm/cp/mv 等写操作）</label>
    <div class="sett-h3" style="margin-top:6px">绘图模型</div>
    <label class="sett-ck"><input type="checkbox" id="imgOn" ${im.enabled?'checked':''}> 启用真实绘图</label>
    <input class="sett-field" id="imgUrl" value="${im.base_url||''}" placeholder="API Base" style="margin-top:8px">
    <input class="sett-field" id="imgKey" value="${im.api_key||''}" placeholder="API Key" style="margin-top:8px">
    <input class="sett-field" id="imgModel" value="${im.model||''}" placeholder="模型，如 gpt-image-1 / dall-e-3" style="margin-top:8px">
    <div class="sett-h3" style="margin-top:6px">视觉模型</div>
    <label class="sett-ck"><input type="checkbox" id="viOn" ${vi.enabled?'checked':''}> 启用视觉模型</label>
    <input class="sett-field" id="viUrl" value="${vi.base_url||''}" placeholder="API Base（与供应商一致即可）" style="margin-top:8px">
    <input class="sett-field" id="viKey" value="${vi.api_key||''}" placeholder="API Key" style="margin-top:8px">
    <input class="sett-field" id="viModel" value="${vi.model||''}" placeholder="模型，如 gpt-4o-mini" style="margin-top:8px">
  </section>

  <section class="settings-section" data-section="appearance">
    <div class="sett-h3">主题</div>
    <select class="sett-field" id="themeSel" onchange="setAppearance('theme',this.value)">
      <option value="warm" ${'warm'===curTheme?'selected':''}>暖调墨紫（默认）</option>
      <option value="dark" ${'dark'===curTheme?'selected':''}>暗色</option>
    </select>
    <div class="sett-h3" style="margin-top:6px">正文字号：<b id="fsVal">${curFont}</b>px</div>
    <input class="sett-range" type="range" id="fontSize" min="12" max="20" step="1" value="${curFont}" oninput="document.getElementById('fsVal').textContent=this.value;setAppearance('font',this.value)">
    <div class="sett-h3" style="margin-top:6px">界面缩放：<b id="scVal">${curScale}</b>%</div>
    <input class="sett-range" type="range" id="uiScale" min="80" max="130" step="5" value="${curScale}" oninput="document.getElementById('scVal').textContent=this.value;setAppearance('scale',this.value)">
  </section>

  <section class="settings-section" data-section="data">
    <div class="sett-h3">自动更新</div>
    <div id="verBox" class="sett-sub">当前版本：v${c.version||'?'}</div>
    <input class="sett-field" id="updateUrl" value="${c.update_url||''}" placeholder="更新清单地址 version.json" style="margin-top:8px">
    <button class="btn sec" style="margin-top:8px" onclick="checkUpdate()">检查更新</button>
    <div id="updateMsg" class="sett-sub" style="margin-top:8px"></div>
    <div class="sett-h3" style="margin-top:6px">数据备份 / 恢复</div>
    <div style="display:flex;flex-direction:column;gap:8px">
      <button class="btn sec" onclick="backupData()" style="display:inline-flex;align-items:center;justify-content:center;gap:6px">备份全部数据（导出 zip）</button>
      <button class="btn sec" onclick="$('#restoreInput').click()" style="display:inline-flex;align-items:center;justify-content:center;gap:6px">从备份恢复（覆盖本地）</button>
    </div>
    <input type="file" id="restoreInput" accept=".zip" hidden onchange="restoreData(this.files[0])">
  </section>

  <section class="settings-section" data-section="ollama">
    <div class="sett-tip">本地内置模型无需 Ollama、零 Key、可完全离线。权重首次使用时自动下载（约 1.1GB），优先走国内镜像（hf-mirror.com），失败自动回退官方源；下载进度会显示当前使用的源与实时速度。</div>
    <div id="ollamaBox">${await renderOllama()}</div>
  </section>

  <section class="settings-section" data-section="mcp">
    <div class="sett-tip">MCP（Model Context Protocol）让你接入外部工具服务。stdio 模式填写可执行命令，HTTP 模式填写服务地址。保存后在「MCP」面板刷新即可使用。</div>
    <div class="pcard" style="margin-top:12px">
      <div class="psec-title">新增服务器</div>
      <div style="display:flex;gap:8px;flex-wrap:wrap">
        <input class="field" id="mcpName" placeholder="名称，如 filesystem" style="flex:1;min-width:120px;margin:0">
        <select class="field" id="mcpTransport" style="width:120px;margin:0">
          <option value="stdio">stdio</option>
          <option value="http">http</option>
        </select>
      </div>
      <input class="field" id="mcpCmd" placeholder="命令，如 npx -y @modelcontextprotocol/server-filesystem ." style="margin:8px 0 0">
      <input class="field" id="mcpUrl" placeholder="HTTP 地址，如 http://127.0.0.1:3000/mcp" style="margin:8px 0 0;display:none">
      <button class="btn" style="margin-top:10px" onclick="addMcpServer()">${ic('plus')}添加 MCP Server</button>
    </div>
    <div class="pcard" style="margin-top:12px">
      <div class="psec-title">已配置</div>
      <div id="mcpCfgList" style="margin-top:8px"><div class="empty-hint">加载中…</div></div>
    </div>
  </section>

  <section class="settings-section" data-section="about">
    <div class="about" style="margin:0;background:transparent;border:none;box-shadow:none;padding:0;display:flex;gap:14px;align-items:center">
      <img src="/static/icon.png" class="about-logo" style="width:52px;height:52px;border-radius:12px;object-fit:cover;background:transparent">
      <div class="about-meta">
        <div class="about-name">墨核 AI Studio (InkCore) <span class="ver">v${c.version||'?'}</span></div>
        <div class="about-sub">桌面端全能 AI 助手 · 写作 / 生图 / 代码 / Agent / 本地模型</div>
      </div>
    </div>
    <div class="sett-tip">所有配置仅保存在本机，不会上传。兼容 OpenAI 接口；选好供应商后会自动带入 Base 与模型。未启用真实模型时用本地模板应答。</div>
  </section>`;
}
async function saveSettings(){
  const provider = _settingsProvider || "custom";
  const model = ($("#settModelSel")||{}).value || "";
  const llm={enabled:$("#settLlmOn").checked, base_url:$("#settLlmUrl").value, api_key:$("#settLlmKey").value, model, temperature:parseFloat($("#settLlmTemp").value||"0.9")};
  // #5 把当前供应商的 Key 单独存档（其余供应商的 Key 保留不动）
  const pk = Object.assign({}, (_settingsConfig&&_settingsConfig.provider_keys)||{});
  pk[provider] = {api_key:llm.api_key, base_url:llm.base_url, model:llm.model};
  const body={ provider, model, llm,
    image:{enabled:$("#imgOn").checked, base_url:$("#imgUrl").value, api_key:$("#imgKey").value, model:$("#imgModel").value},
    vision:{enabled:$("#viOn").checked, base_url:$("#viUrl").value, api_key:$("#viKey").value, model:$("#viModel").value},
    // #7 勾选则把 LLM 的 Key+Base 继承给生图/视觉
    inherit_keys: ($("#settInheritKeys")||{checked:false}).checked,
    provider_keys: pk,
    sandbox:{readonly:$("#settRoOn").checked},
    hotkey:($("#settHkInput").value||"ctrl+alt+m").trim() };
  await fetch("/api/config",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(body)});
  updateStatus(); alert("已保存，重启对话即可生效。");
}
// ---------- 本地内置模型：下载 + 进度轮询 ----------
let _embTimer = null;
async function downloadEmbedded(){
  const sel = document.getElementById('embModel');
  const model = sel ? sel.value : null;
  const btn = document.getElementById('embDl');
  if(btn){ btn.disabled = true; btn.textContent = '下载中…'; }
  try { await fetch('/api/embedded/download',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({model})}); }
  catch(e){}
  pollEmbedded();
}
// v2.3：下载状态展示当前源（镜像/官方）、实时速度、已下载大小
function _fmtSize(bytes){
  const b = Number(bytes)||0;
  if(b < 1024) return b + " B";
  if(b < 1024*1024) return (b/1024).toFixed(0) + " KB";
  if(b < 1024*1024*1024) return (b/1024/1024).toFixed(1) + " MB";
  return (b/1024/1024/1024).toFixed(2) + " GB";
}
function _fmtSpeed(bps){
  const s = Number(bps)||0;
  if(s <= 0) return "—";
  return _fmtSize(s) + "/s";
}
async function pollEmbedded(){
  const stat=document.getElementById('embStat'), bar=document.getElementById('embBar'),
        fill=document.getElementById('embBarFill'), btn=document.getElementById('embDl');
  let s={};
  try { s = await (await fetch('/api/embedded/status')).json(); } catch(e){ return; }
  const srcName = s.source==="mirror" ? "国内镜像" : (s.source==="official" ? "官方源" : "");
  if(stat){
    if(s.error){
      // v2.4：GGUF 校验失败 / 下载失败要醒目提示，不再默默显示「尚未下载」
      stat.textContent = "⚠ " + s.error;
      stat.style.color = "var(--danger)";
    }else if(s.ready){
      stat.textContent = "✓ 模型已就绪，可直接对话（已自动切换为本地内置）";
      stat.style.color = "var(--mint)";
    }else if(s.downloading){
      stat.style.color = "";
      const pct = Math.round((s.progress||0)*100);
      stat.textContent = `下载中 ${pct}%` +
        (srcName ? ` · ${srcName}` : "") +
        ` · ${_fmtSize(s.downloaded_bytes)} / ${_fmtSize(s.total_bytes)}` +
        ` · ${_fmtSpeed(s.speed)}`;
    }else if(s.llama_available===false){
      stat.textContent = "⚠ 未检测到本地推理引擎：请卸载后重装最新版（新版已强制内置引擎）";
      stat.style.color = "var(--warn)";
    }else{
      stat.textContent = "尚未下载模型权重";
      stat.style.color = "";
    }
  }
  if(bar&&fill){ bar.style.display = s.downloading?'block':'none'; fill.style.width = Math.round((s.progress||0)*100)+'%'; }
  if(btn){
    if(s.downloading){ btn.disabled=true; btn.textContent = srcName ? `下载中（${srcName}）…` : '下载中…'; }
    else if(s.ready){ btn.disabled=true; btn.textContent='已就绪'; }
    else { btn.disabled=false; btn.textContent='下载模型（约 1.1GB）'; }
  }
  if(s.error && stat){
    // 下载失败：明确告知镜像与官方源都已尝试
    const tried = (s.attempts||[]).map(a=>a.source==="mirror"?"国内镜像":"官方源").join("、");
    stat.textContent = '下载失败：' + s.error + (tried ? `（已尝试：${tried}）` : "");
    if(btn){ btn.disabled=false; btn.textContent='重试下载'; }
  }
  if(s.downloading){ if(!_embTimer) _embTimer=setInterval(pollEmbedded,800); }
  else { if(_embTimer){ clearInterval(_embTimer); _embTimer=null; } }
}
async function checkUpdate(){
  const url=$("#updateUrl").value.trim();
  const msg=$("#updateMsg"); if(!msg) return;
  msg.textContent="检查中…";
  try{
    const r=await fetch("/api/check_update",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({url})});
    const d=await r.json();
    if(d.error){ msg.innerHTML=`<span style="color:#ffb86b">${d.error}</span>`; return; }
    if(d.update_available){
      msg.innerHTML=`<span style="color:#3ddc84">发现新版本 v${d.latest}！</span><br>${d.notes||''}`+
        (d.download_url?`<br><a href="${d.download_url}" target="_blank" style="color:#7c5cff">前往下载</a>`:"");
    }else{
      msg.innerHTML=`<span style="color:#3ddc84">已是最新（v${d.current}）</span>`;
    }
  }catch(e){ msg.textContent="检查失败："+e.message; }
}

// ---------- 导出（Word/MD/PDF/公众号/长图/XMind） ----------
async function exportAs(fmt){
  if(!SESSION){ alert("请先开始一段对话再导出。"); return; }
  const map={docx:"墨核AI创作.docx", md:"墨核AI创作.md", pdf:"墨核AI创作.pdf", wechat:"墨核AI创作.html"};
  try{
    const r = await fetch("/api/export/"+fmt,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({session_id:SESSION})});
    if(!r.ok){ alert("导出失败：该会话不存在。"); return; }
    const blob = await r.blob();
    const url = URL.createObjectURL(blob);
    const a=document.createElement("a"); a.href=url; a.download=map[fmt]||"export"; a.click();
    URL.revokeObjectURL(url);
  }catch(e){ alert("导出失败："+e.message); }
}
async function exportLongImage(){
  const msgs=$("#messages");
  if(!msgs.querySelector(".msg")){ alert("请先开始一段对话再导出长图。"); return; }
  toast("正在生成长图…");
  try{
    const canvas=await html2canvas(msgs, {backgroundColor: getComputedStyle(document.body).backgroundColor||"#0f1117", scale:2, logging:false});
    const url=canvas.toDataURL("image/png");
    const a=document.createElement("a"); a.href=url; a.download="墨核AI对话长图.png"; a.click();
    toast("长图已导出");
  }catch(e){ alert("长图导出失败："+e.message); }
}
async function exportXMind(){
  if(!SESSION){ alert("请先开始一段对话再导出思维导图。"); return; }
  try{
    const r=await fetch("/api/export/xmind",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({session_id:SESSION})});
    if(!r.ok){ alert("导出失败：该会话不存在。"); return; }
    const blob=await r.blob(); const url=URL.createObjectURL(blob);
    const a=document.createElement("a"); a.href=url; a.download="墨核AI创作.xmind"; a.click(); URL.revokeObjectURL(url);
  }catch(e){ alert("导出失败："+e.message); }
}

// ---------- 会话状态 ----------
// v2.3：移除了顶部多会话标签栏（与左侧「最近对话」功能重复，且 ✕ 在只剩一个标签时静默失效）。
// 现在只保留一个轻量状态槽，供标题/会话 id 同步用；历史会话一律走左侧列表。
let TABS=[]; let activeTab=-1; let WELCOME_HTML="";
// v2.5：欢迎区整体（含标语/熊猫/输入框/快捷词/卡片）会被记录重建。
// 输入框初始位于欢迎区内容流中（1:1 预览），首条消息后停靠到底部 inputDock。
// 关键：输入框 DOM 实例必须唯一且不被 innerHTML 重建，否则事件绑定丢失。
function parkComposer(){                       // 把输入框移到安全区 inputDock（不会被 messages.innerHTML 清空）
  const c=$("#composer"), dock=$("#inputDock");
  if(c && dock && c.parentElement!==dock) dock.appendChild(c);
}
function placeComposerHome(){                  // 把输入框放回欢迎区内容流
  const c=$("#composer"), home=$("#composerHome");
  if(c && home && c.parentElement!==home) home.appendChild(c);
}
function captureWelcome(){
  const w=$("#welcomeStage"); if(!w) return;
  parkComposer();                                        // 临时移出输入框
  WELCOME_HTML=w.outerHTML;                              // 记录不含输入框的欢迎区
  placeComposerHome();                                   // 立即放回，保持首屏 1:1
}
function rebindChips(){
  $$("#messages .chip, #messages .wcard").forEach(c=> c.onclick=()=>send(c.dataset.cmd));
  // 智能体卡片：有 data-cmd 的发预设词，有 data-panel 的开对应面板
  $$("#messages .card[data-cmd]").forEach(c=> c.onclick=()=>send(c.dataset.cmd));
  $$("#messages .card[data-panel]").forEach(c=> c.onclick=()=>openPanel(c.dataset.panel));
}
function renderWelcome(){
  if(!WELCOME_HTML) return;
  parkComposer();                                        // 输入框先移到安全区，避免被 innerHTML 波及
  $("#messages").innerHTML=WELCOME_HTML;
  placeComposerHome();                                   // 放回新 welcomeStage 的 composerHome
  rebindChips();
}
function saveTabState(){
  if(activeTab>=0 && TABS[activeTab]){ TABS[activeTab].html=$("#messages").innerHTML; TABS[activeTab].session=SESSION; TABS[activeTab].model=SESSION_MODEL; }
}
// v2.3：不再渲染标签栏
function renderTabs(){ /* 标签栏已移除，保留空实现以兼容既有调用点 */ }
function initTabs(){
  TABS=[{id:"t"+Date.now(), session:null, title:"新对话", model:"", html:""}];
  activeTab=0; renderTabs();
}
// v2.3：标签栏已移除，「新对话」按钮改为直接开一个新会话（走侧栏会话体系）
function newTab(){
  if(busy) return;
  SESSION=null; APPLIED_MODEL=null; SESSION_MODEL=""; setSessionModel("");
  $("#messages").innerHTML=""; renderWelcome(); $("#chatTitle").textContent="新的对话";
  loadArtifacts(null);
}
function switchTab(i){ /* 标签栏已移除，保留空实现以兼容既有调用点 */ }
function closeTab(i){ /* 标签栏已移除，保留空实现以兼容既有调用点 */ }

// ---------- Agent（服务端编排） ----------
let stepN=0;
function addStep(){ stepN++;
  const box=$("#agentSteps");
  const d=document.createElement("div"); d.className="agent-step";
  d.innerHTML=`<input class="field" placeholder="步骤${stepN}：如 搜索今日热榜">`;
  box.appendChild(d);
}
let _agentRunId=null, _agentAbort=null;
function stopAgent(){
  if(!_agentRunId) return;
  fetch("/api/agent/stop",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({run_id:_agentRunId})})
    .then(()=>{ toast("已请求停止 Agent"); })
    .catch(()=>{});
}
function _agentTimelineAdd(icon,text,status){
  const card=$("#agentTimelineCard"); if(card) card.style.display="";
  const box=$("#agentTimeline"); if(!box) return;
  const row=document.createElement("div");
  row.style.cssText="display:flex;gap:8px;align-items:flex-start;padding:6px 0;border-bottom:1px solid rgba(128,128,128,.12);font-size:13px";
  const mark=status==="ok"?"✅":status==="error"?"❌":status==="run"?"⏳":"•";
  row.innerHTML=`<span style="flex:0 0 auto">${mark}</span><span style="flex:1"><b>${icon}</b> ${text}</span>`;
  box.appendChild(row);
  box.scrollTop=box.scrollHeight;
}
async function runAgent(){
  const goal=$("#agentGoal").value.trim();
  const steps=[...$$("#agentSteps input")].map(i=>i.value.trim()).filter(Boolean);
  if(!goal && !steps.length){ alert("请填写目标或至少一个步骤。"); return; }
  const out=$("#agentOut"); if(out) out.textContent="";
  const tl=$("#agentTimeline"); if(tl) tl.innerHTML="";
  const badge=$("#agentStepBadge"); if(badge) badge.textContent="";
  const runBtn=$("#agentRunBtn"), stopBtn=$("#agentStopBtn");
  if(runBtn) runBtn.style.display="none";
  if(stopBtn) stopBtn.style.display="inline-flex";
  _agentAbort=new AbortController();
  let fullText="";
  try{
    const r=await fetch("/api/agent_stream",{method:"POST",headers:{"Content-Type":"application/json"},
      body:JSON.stringify({goal:goal||steps[0],steps}),signal:_agentAbort.signal});
    const reader=r.body.getReader(), dec=new TextDecoder();
    let buf="";
    while(true){
      const {done,value}=await reader.read();
      if(done) break;
      buf+=dec.decode(value,{stream:true});
      let idx;
      while((idx=buf.indexOf("\n\n"))>=0){
        const chunk=buf.slice(0,idx); buf=buf.slice(idx+2);
        const line=chunk.split("\n").find(l=>l.startsWith("data:"));
        if(!line) continue;
        let e; try{ e=JSON.parse(line.slice(5).trim()); }catch(_){ continue; }
        if(e.type==="meta"){
          _agentRunId=e.run_id;
        }else if(e.type==="plan_update"){
          if(badge) badge.textContent=`第 ${e.step}/${e.max_steps} 步`;
        }else if(e.type==="tool_call"){
          _agentTimelineAdd(e.name,JSON.stringify(e.arguments||{}),"run");
        }else if(e.type==="tool_result"){
          _agentTimelineAdd(e.name,e.ok?"成功":(e.error||"失败"),e.ok?"ok":"error");
        }else if(e.type==="error"){
          if(out) out.textContent+="\n[错误] "+e.message;
        }else if(e.type==="done"){
          if(badge) badge.textContent=`完成（${e.tool_calls} 次工具调用）`;
          fullText=e.reply||"";  // 最终结果随 done 事件返回，避免重复执行一次 Agent
        }
      }
    }
    if(fullText && out) out.textContent=fullText;
    if(fullText) addMsg("assistant", md(fullText.split("[Agent] 完成")[0]||fullText));
  }catch(e){
    if(e.name!=="AbortError" && out) out.textContent="[Agent] 调用失败："+e.message;
  }finally{
    _agentRunId=null; _agentAbort=null;
    if(runBtn) runBtn.style.display="inline-flex";
    if(stopBtn) stopBtn.style.display="none";
  }
}
// ---------- 改动3：聊天说一句 → 自动打开并铺满对应工作面板，内容已填好 ----------
function _enterFullscreen(){
  $("#panel").classList.add("fullscreen");
  const mx=$("#panelMax"); if(mx) mx.querySelector(".ic").setAttribute("data-ic","minimize");
}
async function openCodeAuto(code){
  await openPanel("code");
  const ta=$("#codeArea"); if(ta) ta.value = code||"";
  _enterFullscreen(); toast("代码已生成并填入，点「运行」执行");
}
async function openAgentAuto(goal, steps){
  await openPanel("agent");
  const g=$("#agentGoal"); if(g) g.value = goal||"";
  const box=$("#agentSteps");
  if(box){ box.innerHTML=""; stepN=0; (steps||[]).forEach(s=>{ addStep(); const inp=box.lastElementChild.querySelector("input"); if(inp) inp.value=s; }); if(!(steps&&steps.length)) addStep(); }
  _enterFullscreen(); toast("Agent 目标与步骤已生成");
}
async function openTerminalAuto(cmd){
  await openPanel("terminal");
  const ti=$("#termIn"); if(ti) ti.value = cmd||"";
  _enterFullscreen(); toast("终端命令已填入，回车执行（写操作会确认）");
}

// ---------- 语音输入（Web Speech API） ----------
function toggleVoice(){
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  if(!SR){ alert("当前环境不支持语音输入（需要 Chrome / Edge）。"); return; }
  if(recognizing){
    recognition.stop(); return;
  }
  recognition = new SR();
  recognition.lang="zh-CN"; recognition.interimResults=false; recognition.continuous=false;
  recognition.onstart=()=>{ recognizing=true; $("#voiceBtn").classList.add("rec"); };
  recognition.onresult=(e)=>{ const t=e.results[0][0].transcript; $("#input").value=(($("#input").value||"")+" "+t).trim(); autoGrow(); };
  recognition.onerror=()=>{ $("#voiceBtn").classList.remove("rec"); recognizing=false; };
  recognition.onend=()=>{ $("#voiceBtn").classList.remove("rec"); recognizing=false; };
  recognition.start();
}

// ---------- 事件绑定 ----------
function autoGrow(){ const el=$("#input"); el.style.height="auto"; el.style.height=Math.min(el.scrollHeight,140)+"px"; }
// 输入框草稿自动保存：刷新/重开不丢未发送的内容
$("#input").addEventListener("input", ()=>{ try{ localStorage.setItem("mohe_draft", $("#input").value); }catch(e){} });
(function restoreDraft(){ try{ const d=localStorage.getItem("mohe_draft"); if(d){ $("#input").value=d; autoGrow(); } }catch(e){} })();
$("#sendBtn").onclick=()=>send();
$("#input").addEventListener("keydown",e=>{ if(e.key==="Enter"&&!e.shiftKey){e.preventDefault();send();} });
$("#input").addEventListener("input",autoGrow);
$("#newChatBtn").onclick=()=>newTab();
$("#sessionModel").onchange=(e)=>{ setSessionModel(e.target.value); };
$("#panelClose").onclick=closePanel;
$("#panelMax").onclick=togglePanelMax;
$("#artToggle").onclick=()=> $("#artStrip").classList.toggle("collapsed");
$("#settingsBtn").onclick=()=>openSettings();
$("#settingsClose").onclick=closeSettings;
$("#settingsMask").addEventListener("click",(e)=>{ if(e.target===$("#settingsMask")) closeSettings(); });
$("#settingsTabs").addEventListener("click",(e)=>{ const t=e.target.closest(".settings-tab"); if(t) switchSettingsTab(t.dataset.tab); });
$("#profileSel").onchange=(e)=>switchProfile(e.target.value);
$$(".nav-item").forEach(b=> b.onclick=()=>{
  // 侧栏分组列表：点谁高亮谁（active 只在同一分组内切换视觉，其余清空）
  $$(".nav-item").forEach(x=> x.classList.remove("active"));
  b.classList.add("active");
  if(b.dataset.panel==="ollama"){ openSettings(); switchSettingsTab("ollama"); }
  else openPanel(b.dataset.panel);
});
$$(".chip, .wcard").forEach(c=> c.onclick=()=>send(c.dataset.cmd));
$$(".card[data-cmd]").forEach(c=> c.onclick=()=>send(c.dataset.cmd));       // v2.5：智能体卡片
$$(".card[data-panel]").forEach(c=> c.onclick=()=>openPanel(c.dataset.panel));

// 导出下拉菜单
$("#exportBtn").onclick=(e)=>{ e.stopPropagation(); $("#exportMenu").classList.toggle("hidden"); };
$("#exportMenu").querySelectorAll("[data-exp]").forEach(it=> it.onclick=()=>{
  const k=it.dataset.exp;
  if(k==="longimg") exportLongImage();
  else if(k==="xmind") exportXMind();
  else exportAs(k);
  $("#exportMenu").classList.add("hidden");
});
document.addEventListener("click",()=> $("#exportMenu").classList.add("hidden"));

// 会话搜索
$("#convSearch").addEventListener("input", loadConvs);

// 语音 / 视觉
$("#voiceBtn").onclick=toggleVoice;
$("#visionBtn").onclick=()=>{ if(busy){alert("请稍候，正在处理上一条消息…");return;} $("#visionInput").click(); };
$("#visionInput").onchange=(e)=>{ const f=e.target.files[0]; if(f) sendVision(f); e.target.value=""; };
// v2.3：输入框「添加文件」按钮 —— 图片走视觉理解，文档入知识库
$("#attachBtn").onclick=()=>{ if(busy){alert("请稍候，正在处理上一条消息…");return;} $("#attachInput").click(); };
$("#attachInput").onchange=(e)=>{ const f=e.target.files[0]; if(f) handleAttach(f); e.target.value=""; };

// 文件输入：知识库文档 / 技能导入
$("#docInput").onchange=(e)=>{ const f=e.target.files[0]; if(f) uploadDoc(f); e.target.value=""; };
$("#skillImport").onchange=(e)=>{ const f=e.target.files[0]; if(f) importSkills(f); e.target.value=""; };
$("#skillPackImport").onchange=(e)=>{ const f=e.target.files[0]; if(f) importSkillPack(f); e.target.value=""; };

// v2.5：预览新布局的轻量交互
$("#sideNewChat").onclick=()=>newTab();                    // 侧栏「新对话」按钮
$("#settingsCancel").onclick=closeSettings;                // 设置弹窗「取消」
$$(".tabs .tab").forEach(t=> t.onclick=()=>{               // 会话 / 空间 标签切换
  $$(".tabs .tab").forEach(x=>x.classList.remove("active")); t.classList.add("active");
});
(function(){ const d=$("#deepThink"); if(d) d.onclick=()=> d.classList.toggle("on"); })();  // 深度思考开关
(function(){ const m=$("#agentsMore"); if(m) m.onclick=()=> openPanel("agent"); })();         // 智能体「查看全部」

// ---------- 拖拽：图片→视觉理解；文件→知识库 ----------
const inputEl = $("#input");
["dragover","dragenter"].forEach(ev=> inputEl.addEventListener(ev, e=>{ e.preventDefault(); inputEl.classList.add("drag"); }));
inputEl.addEventListener("dragleave", ()=> inputEl.classList.remove("drag"));
inputEl.addEventListener("drop", e=>{
  e.preventDefault(); inputEl.classList.remove("drag");
  const f = e.dataTransfer.files[0];
  if(f && f.type.startsWith("image/")){ sendVision(f); return; }
  const txt = e.dataTransfer.getData("text/plain").trim();
  if(txt){ inputEl.value=(inputEl.value+" "+txt).trim(); autoGrow(); }
});
const panelBody = $("#panelBody");
panelBody.addEventListener("dragover", e=>{ e.preventDefault(); if($("#docList")) panelBody.classList.add("drag"); });
panelBody.addEventListener("dragleave", e=>{ if(e.target===panelBody) panelBody.classList.remove("drag"); });
panelBody.addEventListener("drop", async e=>{
  e.preventDefault(); panelBody.classList.remove("drag");
  if(!$("#docList")) return;   // 仅知识库面板接收文档
  for(const f of e.dataTransfer.files){ await uploadDoc(f); }
});

loadConvs(); loadProfiles(); updateStatus();

// ---------- 首跑引导（零 Key 的 Ollama 本地路径） ----------
function showOnboard(){ $("#onboardMask").classList.remove("hidden"); }
function hideOnboard(){ $("#onboardMask").classList.add("hidden"); localStorage.setItem("mohe_onboard_done","1"); }
function toast(msg){
  const t=document.createElement("div");
  t.textContent=msg;
  t.style.cssText="position:fixed;left:50%;bottom:32px;transform:translateX(-50%);background:rgba(20,22,28,.94);color:#fff;padding:10px 16px;border-radius:10px;font-size:13px;z-index:9999;box-shadow:0 8px 24px rgba(0,0,0,.35);border:1px solid var(--line)";
  document.body.appendChild(t); setTimeout(()=>t.remove(),2400);
}
function setAppearance(key,val){
  try{
    if(key==="theme") localStorage.setItem("mohe_theme",val);
    else if(key==="font") localStorage.setItem("mohe_font",val);
    else if(key==="scale") localStorage.setItem("mohe_scale",val);
    applyAppearance();
  }catch(e){}
}
function applyAppearance(){
  // v2.4：默认暖调墨紫（浅色）。旧版默认 dark 导致每次打开都是深色。
  const t=localStorage.getItem("mohe_theme")||"warm";
  document.body.setAttribute("data-theme",t);
  const fs=parseInt(localStorage.getItem("mohe_font")||"14",10);
  document.documentElement.style.setProperty("--font-base",fs+"px");
  const sc=parseInt(localStorage.getItem("mohe_scale")||"100",10);
  try{ document.documentElement.style.zoom=sc/100; }catch(e){}
}
async function backupData(){
  try{
    const r=await fetch("/api/backup"); const blob=await r.blob();
    const url=URL.createObjectURL(blob); const a=document.createElement("a"); a.href=url; a.download="MoHeAI_backup.zip"; a.click(); URL.revokeObjectURL(url);
  }catch(e){ alert("备份失败："+e.message); }
}
async function restoreData(file){
  if(!file) return;
  const fd=new FormData(); fd.append("file",file);
  try{
    const r=await fetch("/api/restore",{method:"POST",body:fd}); const d=await r.json();
    toast(d.ok?"已恢复，重启应用生效":"恢复失败："+(d.error||""));
  }catch(e){ toast("恢复失败："+e.message); }
}
async function maybeOnboard(){
  try{
    const r=await fetch("/api/config"); const c=await r.json();
    if(!(c.llm && c.llm.enabled) && !localStorage.getItem("mohe_onboard_done")) showOnboard();
  }catch(e){}
}
$("#obEmbedded").onclick=async()=>{
  const msg=$("#obMsg"); msg.textContent="正在启用本地内置模型…";
  await fetch("/api/config",{method:"POST",headers:{"Content-Type":"application/json"},
    body:JSON.stringify({provider:"embedded",llm:{enabled:true,api_key:""}})});
  hideOnboard(); updateStatus();
  toast("已启用本地内置模型；首次需下载权重（约 1.1GB），可在「设置」里查看进度。");
  // 直接触发后台下载，打开设置面板展示进度
  try{
    await fetch("/api/embedded/download",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({})});
    openSettings(); pollEmbedded();
  }catch(e){}
};
$("#obOllama").onclick=async()=>{
  const msg=$("#obMsg"); msg.textContent="正在检测本机 Ollama…";
  try{
    const ck=await fetch("/api/ollama/check"); const j=await ck.json();
    if(!j.running){ msg.textContent="未检测到 Ollama。请先安装并启动（免费，ollama.com），再回来点这里。"; return; }
  }catch(e){ msg.textContent="未检测到 Ollama。请先安装并启动（免费，ollama.com），再回来点这里。"; return; }
  await fetch("/api/config",{method:"POST",headers:{"Content-Type":"application/json"},
    body:JSON.stringify({provider:"ollama",llm:{enabled:true,api_key:""}})});
  hideOnboard(); updateStatus(); toast("已启用 Ollama 本地模型，去聊聊试试！");
};
$("#obKey").onclick=()=>{ hideOnboard(); openSettings(); };
$("#obLater").onclick=()=>{ hideOnboard(); };
$("#onboardMask").addEventListener("click",(e)=>{ if(e.target===$("#onboardMask")) hideOnboard(); });

injectIcons();          // 把 <i data-ic> 渲染成线性 SVG
applyAppearance();      // 应用保存的主题 / 字号 / 缩放
bindConfirm();          // 绑定执行前确认弹窗
captureWelcome();       // 记录欢迎区 HTML，供「新建对话」标签复用
initTabs();             // v2.3：初始化会话状态（标签栏已移除）
maybeOnboard();         // 未配置大模型时弹出首跑引导


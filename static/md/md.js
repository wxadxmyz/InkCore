/* 墨核 Markdown 编辑器 —— 自研 UI 与解析器，仅复用 KaTeX / highlight.js / html2canvas（均 MIT）。零上游代码复制。*/
(function(){
  const $ = s => document.querySelector(s);
  const editor = $('#editor'), preview = $('#preview');
  const LS_KEY = 'inkcore_md_content';
  let aiUsable = false, convList = [];

  /* ---------- 工具 ---------- */
  function toast(msg){ const t=$('#toast'); t.textContent=msg; t.classList.add('show'); clearTimeout(t._t); t._t=setTimeout(()=>t.classList.remove('show'),1800); }
  function download(blob, name){ const a=document.createElement('a'); a.href=URL.createObjectURL(blob); a.download=name; a.click(); setTimeout(()=>URL.revokeObjectURL(a.href),2000); }
  function setSave(on){ $('#saveDot').style.background = on?'var(--warn)':'var(--ok)'; $('#saveState').textContent = on?'未保存':'已自动保存'; }

  /* ---------- Markdown 解析（块级 + 行内，自研） ---------- */
  function escapeHtml(s){ return s.replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c])); }
  function escAttr(u){ return escapeHtml(u).replace(/javascript:/gi,''); }

  function inlineMd(s){
    const codes=[];
    s = s.replace(/`([^`]+)`/g,(m,c)=>{ codes.push(c); return '\u0000'+(codes.length-1)+'\u0000'; });
    s = s.replace(/!\[([^\]]*)\]\(([^)\s]+)\)/g,(m,t,u)=>`<img alt="${escapeHtml(t)}" src="${escAttr(u)}">`);
    s = s.replace(/\[([^\]]+)\]\(([^)\s]+)\)/g,(m,t,u)=>`<a href="${escAttr(u)}" target="_blank" rel="noopener">${t}</a>`);
    s = s.replace(/\*\*([^*]+)\*\*/g,'<strong>$1</strong>');
    s = s.replace(/\*([^*]+)\*/g,'<em>$1</em>');
    s = s.replace(/~~([^~]+)~~/g,'<del>$1</del>');
    s = s.replace(/\u0000(\d+)\u0000/g,(m,i)=>`<code>${escapeHtml(codes[+i])}</code>`);
    return s;
  }

  function mdToHtml(src){
    const lines = src.replace(/\r\n/g,'\n').split('\n');
    let html='', i=0, listType=null, listBuf=[];
    const flush=()=>{ if(listBuf.length){ html+=`<${listType}>`+listBuf.map(x=>`<li>${inlineMd(x)}</li>`).join('')+`</${listType}>`; listBuf=[]; listType=null; } };
    while(i<lines.length){
      const line=lines[i];
      if(/^```/.test(line)){ flush(); const lm=/^```\s*([\w+#.-]*)/.exec(line); const lang=(lm&&lm[1]||'').toLowerCase(); const buf=[]; i++; while(i<lines.length && !/^```/.test(lines[i])){ buf.push(lines[i]); i++; } i++; const cls=lang?` class="language-${lang}"`:''; html+=`<pre><code${cls}>${escapeHtml(buf.join('\n'))}</code></pre>`; continue; }
      if(/^\s*\|/.test(line) && i+1<lines.length && /^\s*\|?[\s:|-]+\|?\s*$/.test(lines[i+1])){
        flush();
        const head=line.trim().replace(/^\||\|$/g,'').split('|').map(c=>c.trim());
        i+=2; const rows=[];
        while(i<lines.length && /^\s*\|/.test(lines[i])){ rows.push(lines[i].trim().replace(/^\||\|$/g,'').split('|').map(c=>c.trim())); i++; }
        html+='<table><thead><tr>'+head.map(h=>`<th>${inlineMd(h)}</th>`).join('')+'</tr></thead><tbody>'
             +rows.map(r=>'<tr>'+r.map(c=>`<td>${inlineMd(c)}</td>`).join('')+'</tr>').join('')+'</tbody></table>';
        continue;
      }
      const hm=line.match(/^(#{1,6})\s+(.*)$/);
      if(hm){ flush(); const l=hm[1].length; html+=`<h${l}>${inlineMd(hm[2])}</h${l}>`; i++; continue; }
      if(/^>{1,}\s/.test(line)){ flush(); html+=`<blockquote>${inlineMd(line.replace(/^>{1,}\s?/,''))}</blockquote>`; i++; continue; }
      if(/^\s*[-*+]\s+/.test(line)){ if(listType!=='ul'){flush();listType='ul';} listBuf.push(line.replace(/^\s*[-*+]\s+/,'')); i++; continue; }
      if(/^\s*\d+\.\s+/.test(line)){ if(listType!=='ol'){flush();listType='ol';} listBuf.push(line.replace(/^\s*\d+\.\s+/,'')); i++; continue; }
      if(/^(\s*[-*_]){3,}\s*$/.test(line)){ flush(); html+='<hr>'; i++; continue; }
      if(line.trim()===''){ flush(); i++; continue; }
      flush(); html+=`<p>${inlineMd(line)}</p>`; i++;
    }
    flush();
    return html;
  }

  function renderMath(root){
    if(!window.katex) return;
    const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, null, false);
    const nodes=[]; let n;
    while((n=walker.nextNode())) nodes.push(n);
    for(const node of nodes){
      const p = node.parentElement;
      if(p && (p.tagName==='CODE' || p.tagName==='PRE' || p.closest('pre code'))) continue;
      let t = node.nodeValue;
      // 块级公式
      let s = t.replace(/\$\$([\s\S]+?)\$\$/g,(m,tex)=>{
        try{ return katex.renderToString(tex.trim(),{displayMode:true,throwOnError:false}); }catch(e){ return m; }
      });
      // 行内公式（与主应用保持相同正则）
      s = s.replace(/(?<!\\)\$(?!\s)([^$\n]+?)(?<!\s)\$/g,(m,tex)=>{
        try{ return katex.renderToString(tex,{displayMode:false,throwOnError:false}); }catch(e){ return m; }
      });
      if(s !== t){
        const span=document.createElement('span');
        // 临时 DOM 解析 KaTeX 生成的 HTML
        span.innerHTML=s;
        node.parentNode.replaceChild(span,node);
      }
    }
  }
  function render(){
    preview.innerHTML = mdToHtml(editor.value);
    renderMath(preview);
    preview.querySelectorAll('pre code').forEach(b=>{ try{ if(window.hljs && b.className.indexOf('language-')>=0) hljs.highlightElement(b); }catch(e){} });
    $('#charCount').textContent = editor.value.length + ' 字';
  }

  /* ---------- 自动保存 ---------- */
  let saveTimer=null;
  function onInput(){
    setSave(true);
    clearTimeout(saveTimer);
    saveTimer=setTimeout(()=>{ try{ localStorage.setItem(LS_KEY, editor.value); }catch(e){} setSave(false); }, 500);
    render();
  }
  editor.addEventListener('input', onInput);

  /* ---------- 工具栏 ---------- */
  function surround(before, after, placeholder){
    const s=editor.selectionStart, e=editor.selectionEnd, v=editor.value;
    const sel=v.slice(s,e)||placeholder||'';
    editor.value=v.slice(0,s)+before+sel+after+v.slice(e);
    editor.focus();
    editor.selectionStart=s+before.length; editor.selectionEnd=s+before.length+sel.length;
    onInput();
  }
  function linePrefix(prefix){
    const s=editor.selectionStart, v=editor.value;
    const lineStart=v.lastIndexOf('\n',s-1)+1;
    editor.value=v.slice(0,lineStart)+prefix+v.slice(lineStart);
    editor.focus(); onInput();
  }
  const acts={
    h1:()=>linePrefix('# '), h2:()=>linePrefix('## '), h3:()=>linePrefix('### '),
    bold:()=>surround('**','**','加粗'), italic:()=>surround('*','*','斜体'), strike:()=>surround('~~','~~','删除'),
    ul:()=>linePrefix('- '), ol:()=>linePrefix('1. '), quote:()=>linePrefix('> '),
    code:()=>surround('`','`','code'), codeblock:()=>surround('\n```\n','\n```\n','代码'),
    link:()=>surround('[','](https://)','链接文字'), img:()=>surround('![','](https://)','描述'),
    hr:()=>linePrefix('\n---\n'), table:()=>surround('','',
      '| 列1 | 列2 |\n| --- | --- |\n| 单元格 | 单元格 |\n'),
    layout:()=>toggleLayout()
  };
  $('#toolbar').addEventListener('click',e=>{ const b=e.target.closest('button'); if(!b)return; const a=b.dataset.act; if(acts[a])acts[a](); });

  /* ---------- 布局切换 ---------- */
  let layout=0; // 0 双栏 1 编辑 2 预览
  function toggleLayout(){
    layout=(layout+1)%3;
    editor.style.display = layout===2?'none':'block';
    preview.style.display = layout===1?'none':'block';
    $('#gutter').style.display = layout===0?'block':'none';
    toast(['双栏','仅编辑','仅预览'][layout]);
  }

  /* ---------- 拖拽导入 ---------- */
  ['dragover','drop'].forEach(ev=>editor.addEventListener(ev,e=>e.preventDefault()));
  editor.addEventListener('drop',e=>{
    const f=e.dataTransfer.files[0]; if(!f)return;
    if(/\.(md|txt|markdown)$/i.test(f.name)){ const r=new FileReader(); r.onload=()=>{ editor.value=r.result; onInput(); toast('已导入 '+f.name); }; r.readAsText(f); }
    else toast('仅支持 .md / .txt');
  });

  /* ---------- 导出 ---------- */
  const extOf={md:'md',txt:'txt',html:'html',docx:'docx',xlsx:'xlsx',pdf:'pdf',png:'png'};
  async function doExport(fmt){
    const content=editor.value, title=(convName||'墨核文档');
    if(fmt==='png'){
      if(!window.html2canvas){ toast('html2canvas 未加载'); return; }
      const c=await html2canvas(preview,{backgroundColor:'#ffffff',scale:2});
      download(await (await fetch(c.toDataURL('image/png'))).blob(), title+'.png'); return;
    }
    const r=await fetch('/api/md/export',{method:'POST',headers:{'Content-Type':'application/json'},
      body:JSON.stringify({content,title,fmt})});
    if(!r.ok){ const e=await r.json().catch(()=>({})); toast('导出失败：'+(e.error||r.status)); return; }
    download(await r.blob(), title+'.'+extOf[fmt]);
    toast('已导出 '+extOf[fmt].toUpperCase());
  }
  $('#exportPop').addEventListener('click',e=>{ const d=e.target.closest('[data-fmt]'); if(!d)return; $('#exportPop').classList.add('hidden'); doExport(d.dataset.fmt); });

  /* ---------- 笔记 ---------- */
  let convName='墨核文档';
  async function loadStatus(){
    try{ const r=await fetch('/api/md/status'); const j=await r.json(); aiUsable=!!j.ai_usable;
      $('#aiState').textContent = aiUsable?'🟢 AI 可用':'🔴 AI 未配置（设置里启用大模型/本地内置模型）';
      renderNotes(j.notes||[]);
    }catch(e){}
  }
  function renderNotes(notes){
    const box=$('#noteList'); box.innerHTML='';
    if(!notes.length){ box.innerHTML='<div style="color:var(--txt2)">还没有笔记</div>'; return; }
    notes.forEach(n=>{
      const d=document.createElement('div');
      d.innerHTML=`<span>${n.name}</span><small>${new Date(n.mtime*1000).toLocaleString()}</small>`;
      d.onclick=()=>openNote(n.name);
      d.ondblclick=()=>{ if(confirm('删除笔记「'+n.name+'」？')) delNote(n.name); };
      box.appendChild(d);
    });
  }
  async function openNote(name){
    const r=await fetch('/api/notes/'+encodeURIComponent(name)); if(!r.ok)return;
    const j=await r.json(); editor.value=j.content; convName=name; onInput(); $('#notesPop').classList.add('hidden'); toast('已打开 '+name);
  }
  async function saveNote(){
    const name=($('#noteName') && $('#noteName').value || '').trim() || convName || '我的笔记';
    const r=await fetch('/api/notes',{method:'POST',headers:{'Content-Type':'application/json'},
      body:JSON.stringify({name,content:editor.value})});
    if(r.ok){ convName=name; toast('已保存为笔记：'+name); loadStatus(); } else toast('保存失败');
  }
  async function delNote(name){
    const r=await fetch('/api/notes?name='+encodeURIComponent(name),{method:'DELETE'});
    if(r.ok){ toast('已删除 '+name); loadStatus(); }
  }

  /* ---------- 对话导入 ---------- */
  async function loadConvs(){
    try{ const r=await fetch('/api/conversations'); convList=await r.json(); }catch(e){ convList=[]; }
    const pop=$('#convPop'); pop.innerHTML='';
    if(!convList.length){ pop.innerHTML='<div style="color:var(--txt2)">还没有对话</div>'; return; }
    convList.forEach(c=>{ const d=document.createElement('div'); d.textContent=(c.title||'未命名')+'  ('+c.count+'条)';
      d.onclick=()=>importConv(c.id); pop.appendChild(d); });
  }
  async function importConv(sid){
    const r=await fetch('/api/conversations/'+encodeURIComponent(sid)); if(!r.ok){ toast('读取对话失败'); return; }
    const j=await r.json();
    const md=j.messages.map(m=>`**${m.role==='user'?'你':'墨核 AI'}：**\n${m.content}`).join('\n\n');
    editor.value=md; convName=j.title||'对话导出'; onInput(); $('#convPop').classList.add('hidden'); toast('已导入对话：'+(j.title||sid));
  }

  /* ---------- AI 桥接 ---------- */
  async function aiAct(action){
    const s=editor.selectionStart, e=editor.selectionEnd, v=editor.value;
    const sel=v.slice(s,e);
    if(!sel.trim()){ toast('请先选中要处理的文字'); return; }
    if(!aiUsable){ toast('AI 未配置：请先在设置里启用大模型或本地内置模型'); return; }
    const btn=event&&event.target;
    const r=await fetch('/api/md/ai',{method:'POST',headers:{'Content-Type':'application/json'},
      body:JSON.stringify({text:sel,action})});
    const j=await r.json().catch(()=>({result:'(AI 返回异常)'}));
    const res=(j.result||'').trim();
    if(!res){ toast('AI 未返回内容'); return; }
    editor.value=v.slice(0,s)+res+v.slice(e); editor.focus();
    editor.selectionStart=s; editor.selectionEnd=s+res.length; onInput(); toast('AI '+action+' 完成');
  }
  $('#aiBar').addEventListener('click',e=>{ const b=e.target.closest('[data-ai]'); if(!b)return; aiAct(b.dataset.ai); });

  /* ---------- 弹出菜单 ---------- */
  function bindPop(btnId,popId){ const b=$('#'+btnId), p=$('#'+popId);
    b.addEventListener('click',e=>{ e.stopPropagation(); document.querySelectorAll('.pop').forEach(x=>{if(x!==p)x.classList.add('hidden');}); p.classList.toggle('hidden'); }); }
  bindPop('exportBtn','exportPop'); bindPop('notesBtn','notesPop'); bindPop('importConvBtn','convPop');
  // 拉取对话列表（修复：原仅切换弹窗可见性，从未真正加载数据）
  $('#importConvBtn').addEventListener('click', ()=>{ loadConvs(); });
  document.addEventListener('click',()=>document.querySelectorAll('.pop').forEach(p=>p.classList.add('hidden')));

  $('#saveNoteBtn').onclick=(e)=>{ e.stopPropagation(); $('#notesPop').classList.remove('hidden'); $('#noteName').value=convName; $('#noteName').focus(); };
  $('#noteSaveNow').onclick=saveNote;
  $('#backBtn').onclick=()=>location.href='/';

  /* ---------- 初始化 ---------- */
  editor.value = localStorage.getItem(LS_KEY) || '# 欢迎使用墨核 Markdown 编辑器\n\n- 左侧写作，右侧实时预览\n- 选中文字点 **AI** 按钮可润色 / 总结 / 翻译\n- 顶部可 **保存为笔记** 或 **导出** 多种格式（md / txt / html / docx / xlsx / pdf / png）\n\n## 示例\n\n支持 **加粗**、*斜体*、`代码`、[链接](https://github.com)、列表与表格：\n\n| 功能 | 说明 |\n| --- | --- |\n| 离线 | 本地运行，数据不出本机 |\n| 多格式 | 一键导出 Word / Excel / PDF |\n';
  onInput(); loadStatus();
})();

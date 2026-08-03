// chat_ui.js v4.5 - 内置浏览器 + 直接 eval DevTools
let ENGINES={bazi:{i:"🔮",n:"八字排盘"},liuren:{i:"🌊",n:"大六壬"},qimen:{i:"🚪",n:"奇门遁甲"},liuyao:{i:"🪙",n:"六爻纳甲"},qizheng:{i:"⭐",n:"七政四余"},bazhai:{i:"🏠",n:"八宅+紫白"},ziwei:{i:"🧭",n:"紫微斗数"},huangli:{i:"📅",n:"黄历"},fengshui:{i:"🧭",n:"玄空风水"},xingming:{i:"📛",n:"姓名学"},haoma:{i:"🔢",n:"号码吉凶"},reading:{i:"📖",n:"命盘解读"},hehun:{i:"💑",n:"八字合婚"},yunshi:{i:"📊",n:"每日运势"},stock:{i:"📈",n:"股票行情"},security:{i:"🛡️",n:"安全工具"},location:{i:"📍",n:"经纬度查询"},timeconvert:{i:"🕐",n:"时间转换"}};
let messages=[],activePanel="chat",subAgents=[];
let CURRENT_MODEL="easyclaw/deepseek.deepseek-v4-pro";

// 全部 17 个免费模型（¥0 输入/输出），全部支持文本，部分支持图片
const MODELS=[
  // === 字节跳动·豆包 Seed ===
  {id:"easyclaw/bytepluses.seed-2.1-pro",cn:"豆包 Seed 2.1 Pro",icon:"🌱",group:"字节跳动·豆包 Seed",desc:"多模态全能·256K窗口·图像+文本理解",trait:"全能旗舰"},
  {id:"easyclaw/bytepluses.seed-2.1-turbo",cn:"豆包 Seed 2.1 Turbo",icon:"💨",group:"字节跳动·豆包 Seed",desc:"极速多模态·256K窗口·性价比最优",trait:"极速先锋"},
  {id:"easyclaw/bytepluses.seed-2.0-pro",cn:"豆包 Seed 2.0 Pro",icon:"✨",group:"字节跳动·豆包 Seed",desc:"成熟多模态·256K窗口·稳定可靠",trait:"稳重大将"},
  {id:"easyclaw/bytepluses.seed-1.8",cn:"豆包 Seed 1.8",icon:"🫘",group:"字节跳动·豆包 Seed",desc:"经典多模态·256K窗口·老牌劲旅",trait:"经典之选"},
  // === 深度求索 ===
  {id:"easyclaw/deepseek.deepseek-v4-pro",cn:"DeepSeek V4 Pro",icon:"🐋",group:"深度求索·DeepSeek",desc:"旗舰全能·最强推理·编程/数学/写作皆精",trait:"通用王者"},
  {id:"easyclaw/deepseek.deepseek-v4-flash",cn:"DeepSeek V4 Flash",icon:"⚡",group:"深度求索·DeepSeek",desc:"极速响应·性价比之选·日常对话首选",trait:"速度先锋"},
  // === MiniMax·海螺 ===
  {id:"easyclaw/minimax.m3",cn:"海螺 M3",icon:"🐚",group:"Minimax·海螺",desc:"多模态旗舰·1M超大窗口·图像+文本",trait:"海量窗口"},
  {id:"easyclaw/minimax.m2.7",cn:"海螺 M2.7",icon:"🔮",group:"Minimax·海螺",desc:"多模态均衡·196K窗口·长文创作",trait:"长文利器"},
  // === 月之暗面·Kimi ===
  {id:"easyclaw/moonshot.kimi-k3",cn:"Kimi K3",icon:"🌙",group:"月之暗面·Kimi",desc:"深度推理旗舰·1M窗口·多模态·深度思考",trait:"推理大师"},
  {id:"easyclaw/moonshot.kimi-k2.7-code",cn:"Kimi K2.7 代码版",icon:"💻",group:"月之暗面·Kimi",desc:"代码专精·262K窗口·编程利器",trait:"代码专家"},
  {id:"easyclaw/moonshot.kimi-k2.6",cn:"Kimi K2.6",icon:"📝",group:"月之暗面·Kimi",desc:"多模态均衡·262K窗口·扎实可靠",trait:"全面均衡"},
  // === 阿里·通义千问 ===
  {id:"easyclaw/qwen.qwen3.7-max",cn:"通义千问 3.7 Max",icon:"☁️",group:"阿里·通义千问",desc:"旗舰推理·1M超大窗口·纯文本王者",trait:"超大窗口"},
  {id:"easyclaw/qwen.qwen3.7-plus",cn:"通义千问 3.7 Plus",icon:"💡",group:"阿里·通义千问",desc:"多模态增强·1M窗口·图像+文本",trait:"多维能手"},
  {id:"easyclaw/qwen.qwen3.5-plus",cn:"通义千问 3.5 Plus",icon:"🎯",group:"阿里·通义千问",desc:"多模态均衡·1M窗口·稳定高效",trait:"稳定之选"},
  // === 小米 ===
  {id:"easyclaw/xiaomi.mimo-v2.5-pro",cn:"小米 MiMo 2.5 Pro",icon:"📱",group:"小米·MiMo",desc:"自研旗舰·1M窗口·深度推理",trait:"自研突破"},
  // === 智谱·GLM ===
  {id:"easyclaw/zai.glm-5.2",cn:"智谱 GLM 5.2",icon:"🧠",group:"智谱·GLM",desc:"最新旗舰·1M窗口·深度推理",trait:"清华智脑"},
  {id:"easyclaw/zai.glm-5.1",cn:"智谱 GLM 5.1",icon:"🔬",group:"智谱·GLM",desc:"经典旗舰·200K窗口·学术严谨",trait:"学术底蕴"},
];

document.addEventListener("DOMContentLoaded",function(){
  buildWelcome();buildHardware();buildSchedule();updateOverview();
  setActivePanel("chat");
  hwTimer=setInterval(updateHardware,3000);updateHardware();
  buildBookmarks();
  // 默认收起浏览器面板
  // Browser starts hidden (inline browser is display:none by default)
});

// 同域 sandbox iframe — 直接 contentWindow.eval 执行 JS
function iframeEval(code){
  let frame=document.getElementById("browserFrame");
  if(!frame||!frame.contentWindow)return null;
  try{return frame.contentWindow.eval(code)}catch(e){return null}
}

// === 聊天模式选择器 ===
let CHAT_MODE="auto";
const CHAT_MODES=[
  {id:"auto",cn:"智能路由",icon:"🧭",desc:"自动识别意图·排盘/搜索/对话智能分发",color:"#8b5cf6"},
  {id:"think",cn:"深度思考",icon:"🧠",desc:"强制AI推理·显示完整思考链与工具调用",color:"#a855f7"},
  {id:"quick",cn:"快速问答",icon:"⚡",desc:"秒回模式·仅匹配寒暄/功能/时间等快捷",color:"#f59e0b"},
  {id:"pan",cn:"玄学排盘",icon:"🔮",desc:"专注排盘·八字紫微六壬奇门六爻七政八宅",color:"#ec4899"},
  {id:"search",cn:"联网搜索",icon:"🌐",desc:"强制搜索·获取最新信息与网页内容",color:"#06b6d4"},
  {id:"code",cn:"代码执行",icon:"💻",desc:"直接运行代码·无需对话直接输出结果",color:"#10b981"},
];
function buildModeSelector(){
  let el=document.getElementById("modeDropdown");if(!el)return;
  let h='<div class="model-grid">';
  CHAT_MODES.forEach(m=>{
    let sel=m.id===CHAT_MODE?' selected':'';
    h+='<div class="model-option'+sel+'" onclick="selectMode(\''+m.id+'\')"><div class="mo-top"><span class="mo-icon">'+m.icon+'</span><span class="mo-name">'+m.cn+'</span></div><div class="mo-desc">'+m.desc+'</div></div>';
  });h+='</div>';el.innerHTML=h;
}
function toggleModeMenu(){
  let menu=document.getElementById("modeDropdown");
  if(!menu){menu=document.createElement("div");menu.id="modeDropdown";menu.className="model-dropdown";menu.style.position="absolute";menu.style.right="20px";menu.style.bottom="90px";var mc=document.querySelector(".main-chat");if(mc){mc.appendChild(menu);var mw=mc.clientWidth;var mh=mc.clientHeight;var dw=Math.min(mw-40,340);menu.style.maxWidth=dw+"px";menu.style.maxHeight=Math.min(mh-120,480)+"px";}buildModeSelector();}
  let mm=document.getElementById("modelDropdown");if(mm)mm.style.display="none";
  if(menu.style.display==="block"){menu.style.display="none";return;}
  buildModeSelector();menu.style.display="block";
  setTimeout(function(){document.addEventListener("click",function hideModeMenu(e){if(!e.target.closest("#modeSelector")&&!e.target.closest("#modeDropdown")){menu.style.display="none";document.removeEventListener("click",hideModeMenu)}},{once:true})},50);
}
function selectMode(id){
  CHAT_MODE=id;
  let label=document.getElementById("currentModeLabel");
  let m=CHAT_MODES.find(function(x){return x.id===id});
  if(label&&m){label.textContent=m.cn;let icon=document.querySelector("#modeSelector .ms-icon");if(icon)icon.textContent=m.icon;}
  let menu=document.getElementById("modeDropdown");if(menu)menu.style.display="none";
}

function setActivePanel(panel){
  activePanel=panel;
  document.querySelectorAll(".nav-item").forEach(e=>e.classList.remove("active"));
  let navMap={chat:0,skills:1,experts:2,automation:3,schedule:4,browser:5};
  let items=document.querySelectorAll(".nav-item");
  let idx=navMap[panel];if(items[idx])items[idx].classList.add("active");
  document.querySelectorAll(".panel-view").forEach(e=>e.classList.remove("active"));
  let pel=document.getElementById("panel-"+panel);if(pel)pel.classList.add("active");
  let sb=document.getElementById("sidebar"),ov=document.getElementById("overviewPanel");
  if(panel==="browser"){
    // Keep chat panel active, show inline browser on top
    let chatEl=document.getElementById("panel-chat");
    if(chatEl)chatEl.classList.add("active");
    toggleInlineBrowser(true);
  }
}

function buildSchedule(){let c=document.getElementById("scheduleList");if(!c)return;c.innerHTML='<div class="pv-empty"><div>🕐</div><div style="margin-top:8px">暂无定时任务</div></div>'}

// === Built-in Browser ===
let browserHistoryStack=[],browserHistoryIdx=-1;
function browserGoTo(url){
  if(!url||!url.trim())return;
  if(!/^https?:\/\//.test(url)&&!/^\//.test(url))url="https://"+url;
  let frame=document.getElementById("browserFrame");
  let home=document.getElementById("browserHome");
  let urlInput=document.getElementById("browserUrl");
  if(frame)frame.src="/bproxy?url="+encodeURIComponent(url);
  if(home)home.classList.add("hidden");
  if(urlInput)urlInput.value=url;
  if(browserHistoryIdx<0||browserHistoryStack[browserHistoryIdx]!==url){
    browserHistoryStack=browserHistoryStack.slice(0,browserHistoryIdx+1);
    browserHistoryStack.push(url);browserHistoryIdx=browserHistoryStack.length-1;
  }
  fetch("/api/browser/history?url="+encodeURIComponent(url)+"&title="+encodeURIComponent(url));
}
function browserGo(){let inp=document.getElementById("browserUrl");if(inp)browserGoTo(inp.value.trim());}
function browserNav(action){
  let frame=document.getElementById("browserFrame");if(!frame||!frame.contentWindow)return;
  if(action==="back"){if(browserHistoryIdx>0){browserHistoryIdx--;frame.src="/bproxy?url="+encodeURIComponent(browserHistoryStack[browserHistoryIdx]);document.getElementById("browserUrl").value=browserHistoryStack[browserHistoryIdx]}}
  else if(action==="forward"){if(browserHistoryIdx<browserHistoryStack.length-1){browserHistoryIdx++;frame.src="/bproxy?url="+encodeURIComponent(browserHistoryStack[browserHistoryIdx]);document.getElementById("browserUrl").value=browserHistoryStack[browserHistoryIdx]}}
  else if(action==="reload"){frame.src=frame.src}
}
function browserPopout(){let url=document.getElementById("browserUrl").value;if(url)window.open(url,"_blank");else if(browserHistoryStack.length>0)window.open(browserHistoryStack[browserHistoryIdx],"_blank");}

// 浏览器三模式: 0=嵌入, 1=全屏, 2=收起
// Inline browser: toggle show/hide inside panel-chat
function toggleInlineBrowser(show){
  let ib=document.getElementById("inlineBrowser");
  if(!ib)return;
  if(show===undefined) show=(ib.style.display==="none");
  if(show){
    ib.style.display="flex";
    let wrap=ib.querySelector(".browser-frame-wrap");
    let dtbar=ib.querySelector(".devtools-bar");
    if(wrap)wrap.style.display="";
    if(dtbar)dtbar.style.display="";
  }else{
    ib.style.display="none";
  }
}

function toggleBookmarkBar(){let bar=document.getElementById("bookmarkBar");if(bar)bar.style.display=bar.style.display==="none"?"flex":"none";buildBookmarks();}
function buildBookmarks(){
  let el=document.getElementById("bookmarkList");if(!el)return;
  fetch("/api/bookmarks").then(r=>r.json()).then(d=>{
    let bms=d.bookmarks||[];
    el.innerHTML=bms.map(b=>'<div class="bm-item" onclick="browserGoTo(\''+escapeHtmlAttr(b.url)+'\')" title="'+escapeHtml(b.url)+'"><span>'+escapeHtml(b.title)+"</span><button class='bm-del' onclick='event.stopPropagation();deleteBookmark(\""+escapeHtmlAttr(b.url)+"\")' title='删除'>×</button></div>").join("");
  }).catch(()=>{});
}
function deleteBookmark(url){
  if(!confirm("确定删除此收藏?"))return;
  fetch("/api/bookmarks",{method:"DELETE",headers:{"Content-Type":"application/json"},body:JSON.stringify({url:url})}).then(r=>r.json()).then(d=>{if(d.ok)buildBookmarks()});
}
function escapeHtml(s){return(s||"").replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;")}
function escapeHtmlAttr(s){return(s||"").replace(/'/g,"\\'").replace(/"/g,"&quot;")}

// Lightweight Markdown → HTML renderer (line-by-line parser)
function renderMarkdown(md){
  if(!md)return"";
  // Step 0: extract code blocks (```...```) so inner markdown isn't processed
  var codeBlocks=[];
  var text=md.replace(/```(\w*)\n([\s\S]*?)```/g,function(_,lang,code){
    var idx=codeBlocks.length;
    codeBlocks.push('<pre class="md-code"><code>'+(lang?'<span class="md-code-lang">'+lang+'</span>\n':'')+escapeHtml(code.replace(/\n$/,''))+'</code></pre>');
    return'\u0001CODEBLOCK'+idx+'\u0001';
  });
  // Inline escape: keep raw for scanning, escape later
  function esc(s){return(s||"").replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;")}

  var lines=text.split('\n');
  var out=[];
  var i=0; var inTable=false; var tableRows=[]; var inList=null;

  function flushList(){if(inList){out.push(inList.close);inList=null;}}
  function flushTable(){
    if(!inTable||tableRows.length<2)return;
    var h='<table class="md-table"><thead>'+tableRows[0]+'</thead><tbody>';
    for(var r=1;r<tableRows.length;r++){if(tableRows[r]==='<!--sep-->')continue; h+=tableRows[r];}
    h+='</tbody></table>';out.push(h);inTable=false;tableRows=[];
  }
  function isTableSep(row){return /^\|?[\s]*:?-{3,}:?[\s]*\|[\s:|-]*\|?$/.test(row);}

  for(i=0;i<lines.length;i++){
    var raw=lines[i];
    // Restore code blocks
    var cbMatch=raw.match(/\u0001CODEBLOCK(\d+)\u0001/);
    if(cbMatch){ flushList(); flushTable(); out.push(codeBlocks[parseInt(cbMatch[1])]); continue; }

    // Blank line
    if(raw.trim()===''){
      if(inTable){ flushTable(); }
      else if(inList){ flushList(); }
      if(out.length>0&&out[out.length-1]!=='')out.push('');
      continue;
    }

    // Table
    if(/^\|/.test(raw)&&/\|$/.test(raw)){
      flushList();
      if(!inTable){ inTable=true; tableRows=[]; }
      if(isTableSep(raw)&&tableRows.length===1){ tableRows.push('<!--sep-->'); continue; }
      if(isTableSep(raw)&&tableRows.length>1){ flushTable(); continue; }
      var cells=raw.replace(/^\||\|$/g,'').split('|').map(function(c){return esc(c.trim())});
      var tag=tableRows.length===0?'th':'td';
      tableRows.push('<tr>'+cells.map(function(c){return'<'+tag+'>'+c+'</'+tag+'>'}).join('')+'</tr>');
      continue;
    }
    flushTable();

    // Inline processing helper
    var s=esc(raw);
    // Headings
    if(/^### (.+)/.test(s)){ flushList(); out.push('<h4 class="md-h4">'+s.replace(/^### /,'')+'</h4>'); continue; }
    if(/^## (.+)/.test(s)){ flushList(); out.push('<h3 class="md-h3">'+s.replace(/^## /,'')+'</h3>'); continue; }
    if(/^# (.+)/.test(s)){ flushList(); out.push('<h2 class="md-h2">'+s.replace(/^# /,'')+'</h2>'); continue; }
    // HR
    if(/^-{3,}$/.test(s.trim())){ flushList(); out.push('<hr class="md-hr">'); continue; }
    // Blockquote
    if(/^&gt; /.test(s)){ flushList(); out.push('<blockquote class="md-quote"><p>'+s.replace(/^&gt; /,'')+'</p></blockquote>'); continue; }
    // Unordered list
    if(/^[*-] (.+)/.test(s)){
      var item=s.replace(/^[*-] /,'');
      if(inList!=='ul'){ flushList(); inList={type:'ul',buf:[],close:'</ul>'}; out.push('<ul class="md-ul">'); }
      out.push('<li class="md-li">'+item+'</li>');
      continue;
    }
    // Ordered list
    if(/^\d+\. (.+)/.test(s)){
      var item=s.replace(/^\d+\. /,'');
      if(inList!=='ol'){ flushList(); inList={type:'ol',buf:[],close:'</ol>'}; out.push('<ol class="md-ol">'); }
      out.push('<li class="md-li-o">'+item+'</li>');
      continue;
    }
    flushList();

    // Inline formatting
    s=s.replace(/\*\*\*(.+?)\*\*\*/g,'<strong><em>$1</em></strong>');
    s=s.replace(/\*\*(.+?)\*\*/g,'<strong>$1</strong>');
    s=s.replace(/\*([^\*]+)\*/g,'<em>$1</em>');
    s=s.replace(/`([^`]+)`/g,'<code class="md-inline">$1</code>');
    s=s.replace(/!\[([^\]]*)\]\(([^)]+)\)/g,'<img src="$2" alt="$1" class="md-img" loading="lazy">');
    s=s.replace(/\[([^\]]+)\]\(([^)]+)\)/g,'<a href="$2" target="_blank" rel="noopener" class="md-link">$1</a>');

    out.push('<p class="md-p">'+s+'</p>');
  }
  flushTable(); flushList();

  // Join with newlines for code blocks to preserve formatting
  var result=out.filter(function(x){return x!==''}).join('\n');
  // Restore any remaining code block markers (shouldn't happen)
  result=result.replace(/\u0001CODEBLOCK(\d+)\u0001/g,function(_,idx){return codeBlocks[parseInt(idx)]||''});
  return result;
}
function addBookmark(){
  let url=document.getElementById("browserUrl").value;
  let frame=document.getElementById("browserFrame");
  let pageTitle="";
  if(url&&url.startsWith("http")){
    try{let u=new URL(url);pageTitle=""}
    catch(e){}
  }else if(frame&&frame.contentDocument&&frame.contentDocument.title){
    url=frame.src;
    pageTitle=frame.contentDocument.title;
  }
  if(!url||(!url.startsWith("http")&&!url.startsWith("/bproxy"))){alert("请先打开一个网页");return}
  let title=prompt("收藏名称:",pageTitle||url);
  if(!title)return;
  fetch("/api/bookmarks",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({url:url,title:title})}).then(r=>r.json()).then(d=>{if(d.ok)buildBookmarks()});
}
function importBookmarks(input){
  let file=input.files[0];if(!file)return;
  let reader=new FileReader();
  reader.onload=function(e){
    let html=e.target.result;
    let cnt=0;
    let re=/<A[^>]*HREF="([^"]+)"[^>]*>([^<]*)<\/A>/gi;
    let match,batch=[];
    while((match=re.exec(html))!==null){
      let url=match[1],title=match[2];
      if(!url||url.startsWith("javascript:"))continue;
      batch.push({url:url,title:title||url});
    }
    let promises=batch.slice(0,50).map(b=>fetch("/api/bookmarks",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(b)}).then(r=>r.json()));
    Promise.all(promises).then(()=>{alert("导入了 "+batch.length+" 个书签");buildBookmarks()});
  };
  reader.readAsText(file);
  input.value="";
}

// === DevTools (直接 eval 模式) ===
let dtConsoleHist=[],dtConsoleHistIdx=-1;

function toggleDevTool(tool){
  let panel=document.getElementById("devtoolsPanel");
  let title=document.getElementById("dtTitle");
  let body=document.getElementById("dtBody");
  if(!panel||!title||!body)return;
  let frame=document.getElementById("browserFrame");
  if(!frame||!frame.src||frame.src==="about:blank"){alert("请先打开一个网页");return}
  panel.style.display="block";
  if(tool==="elements"){
    title.textContent="🔍 元素检查 (DOM Live)";
    let html=iframeEval("document.documentElement.outerHTML");
    if(html){let size=html.length;body.innerHTML='<pre class="dt-html-pre">'+escapeHtml(html.substring(0,20000))+'</pre><div style="padding:4px 8px;color:var(--text4);font-size:10px">Live DOM (直接eval) | 截取前20KB | 总大小: '+size+' 字节</div>';}
    else{body.innerHTML='<div class="dt-err">无法访问 iframe DOM（跨域/sandbox 限制）<br><span style="font-size:11px">iframe 需同域且 loaded</span></div>';}
  }else if(tool==="console"){
    title.textContent="📋 JS 控制台 (直接eval)";
    body.innerHTML='<input type="text" class="dt-console-input" id="dtConsoleInput" placeholder="输入JS代码，回车执行 (上下翻历史)" onkeydown="devConsoleKey(event)"><div id="dtConsoleOutput"><span style="color:var(--accent)">四方阁控制台 - 同域直接eval</span><br><span style="font-size:11px;color:var(--text4)">在iframe内执行任意JavaScript</span></div>';
  }else if(tool==="source"){
    title.textContent="🗂 页面源码 (服务器原始)";
    body.innerHTML='<div style="padding:8px;color:var(--text4)">加载中...</div>';
    let proxyUrl=frame.src;
    if(proxyUrl.includes("/bproxy")){let m=proxyUrl.match(/url=([^&]+)/);
      if(m)fetch("/api/browser/source?url="+encodeURIComponent(decodeURIComponent(m[1]))).then(r=>r.json()).then(d=>{
        if(d.source)body.innerHTML='<pre style="max-height:500px;overflow-y:auto;font-size:10px;line-height:1.4;padding:8px;tab-size:2">'+escapeHtml(d.source.substring(0,50000))+'</pre><div style="padding:4px 8px;color:var(--text4);font-size:10px">已截取前50KB | 总: '+(d.size||0)+'B | HTTP:'+d.status+'</div>';
        else body.innerHTML='<div class="dt-err">加载失败: '+(d.error||"未知")+'</div>';});}
  }else if(tool==="network"){
    title.textContent="📡 网络请求 (Performance API)";
    let perf=iframeEval("JSON.stringify(performance.getEntriesByType('resource').map(function(r){return{name:r.name,type:r.initiatorType,duration:Math.round(r.duration),size:r.transferSize||0}}))");
    if(perf){try{let entries=JSON.parse(perf);
      if(entries.length===0){body.innerHTML='<div style="padding:8px;color:var(--text4)">无资源请求记录（页面无外部资源）</div>';}
      else{let h='<div style="padding:4px 8px;color:var(--accent);font-size:11px">iframe内资源 ('+entries.length+'条)</div>';
        entries.forEach(function(e){h+='<div style="display:flex;padding:2px 8px;font-size:11px;border-bottom:1px solid var(--border1);color:var(--text2)">';
          h+='<span style="width:50px;color:var(--'+(e.duration>500?'orange':'green')+')">'+(e.duration||0)+'ms</span>';
          h+='<span style="width:60px;color:var(--text4)">'+e.type+'</span>';
          h+='<span style="overflow:hidden;text-overflow:ellipsis;white-space:nowrap;flex:1">'+escapeHtml(e.name.substring(0,90))+'</span>';
          h+='<span style="margin-left:8px;color:var(--text4)">'+formatBytes(e.size)+'</span></div>';});
        body.innerHTML=h;}}
      catch(e){body.innerHTML='<div class="dt-err">解析失败: '+escapeHtml(e.message)+'</div>';}}
    else{body.innerHTML='<div class="dt-err">无法访问 iframe Performance API</div>';}}
}

function devConsoleKey(e){
  if(e.key==="Enter"){devConsoleEval();return}
  if(e.key==="ArrowUp"){e.preventDefault();if(dtConsoleHistIdx>0){dtConsoleHistIdx--;document.getElementById("dtConsoleInput").value=dtConsoleHist[dtConsoleHistIdx]}else if(dtConsoleHist.length>0){dtConsoleHistIdx=0;document.getElementById("dtConsoleInput").value=dtConsoleHist[0]}return}
  if(e.key==="ArrowDown"){e.preventDefault();if(dtConsoleHistIdx<dtConsoleHist.length-1){dtConsoleHistIdx++;document.getElementById("dtConsoleInput").value=dtConsoleHist[dtConsoleHistIdx]}else{document.getElementById("dtConsoleInput").value="";dtConsoleHistIdx=dtConsoleHist.length}return}
}

function devConsoleEval(){
  let input=document.getElementById("dtConsoleInput");let output=document.getElementById("dtConsoleOutput");
  if(!input||!output)return;let code=input.value.trim();if(!code)return;
  if(code!==dtConsoleHist[dtConsoleHist.length-1]){dtConsoleHist.push(code);dtConsoleHistIdx=dtConsoleHist.length}
  output.innerHTML+='<div style="color:var(--green);font-size:11px">&gt; '+escapeHtml(code)+'</div>';
  let r=iframeEval(code);
  if(r!==null)output.innerHTML+='<div class="dt-result">'+escapeHtml(String(r))+'</div>';
  else output.innerHTML+='<div class="dt-err-line">无法执行（跨域/sandbox限制）</div>';
  output.scrollTop=output.scrollHeight;input.value="";}

function formatBytes(b){if(!b||b<0)return '0B';if(b<1024)return b+'B';if(b<1048576)return (b/1024).toFixed(1)+'KB';return (b/1048576).toFixed(1)+'MB'}

function buildWelcome(){let g=document.getElementById("wsQuickActions");if(!g)return;let t8=["bazi","ziwei","liuyao","huangli","yunshi","hehun","location","timeconvert"];g.innerHTML=t8.map(id=>{let e=ENGINES[id];return'<div class="ws-card" onclick="quickPan(\''+id+'\')"><span class="wsc-icon">'+e.i+'</span>'+e.n+'</div>'}).join("")}

function buildHardware(){let el=document.getElementById("ovHardware");if(!el)return;el.innerHTML='<div class="hw-loading">获取硬件状态...</div>';}

function updateHardware(){
  let el=document.getElementById("ovHardware");if(!el)return;
  fetch("/api/hardware").then(r=>r.json()).then(d=>{
    let h='';let cpuBar=barClass(d.cpu.percent);
    h+='<div class="hw-row"><span class="hw-label">CPU</span><div class="hw-bar-wrap"><div class="hw-bar '+cpuBar+'" style="width:'+d.cpu.percent+'%"></div></div><span class="hw-val">'+d.cpu.percent+'%</span></div>';
    if(d.cpu.per_core&&d.cpu.per_core.length){h+='<div class="hw-cores">';d.cpu.per_core.forEach(v=>{let cb=barClass(v);h+='<div class="hw-core" style="background:var(--'+(cb==='hw-bar-low'?'green':cb==='hw-bar-mid'?'yellow':'red')+')" title="'+v+'%"></div>'});h+='</div>';}
    h+='<div class="hw-sub">'+d.cpu.cores+'C/'+d.cpu.logical+'T @ '+d.cpu.freq+'MHz</div>';
    let memBar=barClass(d.memory.percent),diskBar=barClass(d.disk.percent);
    h+='<div class="hw-row"><span class="hw-label">RAM</span><div class="hw-bar-wrap"><div class="hw-bar '+memBar+'" style="width:'+d.memory.percent+'%"></div></div><span class="hw-val">'+d.memory.used+'/'+d.memory.total+'G</span></div>';
    h+='<div class="hw-row"><span class="hw-label">DISK</span><div class="hw-bar-wrap"><div class="hw-bar '+diskBar+'" style="width:'+d.disk.percent+'%"></div></div><span class="hw-val">'+d.disk.used+'/'+d.disk.total+'G</span></div>';
    h+='<div class="hw-sub">API: '+d.process.api_memory_mb+'MB/'+d.process.api_threads+'线程 | 系统:'+d.process.total_processes+'进程</div>';
    let ut=(d.uptime_seconds||0),hrs=Math.floor(ut/3600),mins=Math.floor((ut%3600)/60);h+='<div class="hw-sub">运行: '+hrs+'h'+mins+'m</div>';
    el.innerHTML=h;}).catch(()=>{el.innerHTML='<div class="hw-err">硬件状态获取失败</div>'});}

function barClass(v){return v<40?'hw-bar-low':v<75?'hw-bar-mid':'hw-bar-high'}

function updateOverview(){let ac=document.getElementById("ovAgentsList"),tc=document.getElementById("ovTasksList");if(ac){let a=[{name:"界面复刻",status:"完成",label:"已完成",icon:"🎨"},{name:"数据查询",status:"运行中",label:"运行中",icon:"🔍"}];let all=subAgents.length>0?subAgents:a;let h="";for(let x of all.slice(0,3)){h+='<div class="ov-agent-item"><div class="oa-avatar">'+(x.icon||"🤖")+'</div><span class="oa-name">'+escapeHtml(x.name)+'</span><span class="oa-status '+x.status+'">'+(x.label||x.status)+'</span></div>'}ac.innerHTML=h}if(tc){tc.innerHTML=messages.length===0?'<div class="ov-empty">暂无任务</div>':'<div class="ov-task-item"><div class="ot-check"></div>聊天分析</div><div class="ov-task-item"><div class="ot-check"></div>关键词提取</div>'}}

function buildModelSelector(){let el=document.getElementById("modelDropdown");if(!el)return;let groups={};MODELS.forEach(m=>{if(!groups[m.group])groups[m.group]=[];groups[m.group].push(m)});let h='<div class="model-grid">';Object.keys(groups).forEach(g=>{h+='<div class="model-group"><div class="model-group-label">'+g+'</div>';groups[g].forEach(m=>{let sel=m.id===CURRENT_MODEL?' selected':'';h+='<div class="model-option'+sel+'" onclick="selectModel(\''+m.id+'\')"><div class="mo-top"><span class="mo-icon">'+m.icon+'</span><span class="mo-name">'+m.cn+'</span><span class="mo-trait">'+m.trait+'</span></div><div class="mo-desc">'+m.desc+'</div></div>'});h+='</div>'});h+='</div>';el.innerHTML=h;}

function toggleModelMenu(){let menu=document.getElementById("modelDropdown");if(!menu){menu=document.createElement("div");menu.id="modelDropdown";menu.className="model-dropdown";menu.style.position="absolute";menu.style.right="20px";menu.style.bottom="90px";var mc=document.querySelector(".main-chat");if(mc){mc.appendChild(menu);var mw=mc.clientWidth;var mh=mc.clientHeight;var dw=Math.min(mw-40,340);menu.style.maxWidth=dw+"px";menu.style.maxHeight=Math.min(mh-120,480)+"px";}buildModelSelector();}
  if(menu.style.display==="block"){menu.style.display="none";return;}
  buildModelSelector();menu.style.display="block";
  setTimeout(function(){document.addEventListener("click",function hideModelMenu(e){if(!e.target.closest("#modelSelector")&&!e.target.closest("#modelDropdown")){menu.style.display="none";document.removeEventListener("click",hideModelMenu);}},{once:true})},50);
}

function selectModel(id){
  CURRENT_MODEL=id;
  let label=document.getElementById("currentModelLabel");
  let m=MODELS.find(function(x){return x.id===id});
  if(label&&m)label.textContent=m.name;
  let menu=document.getElementById("modelDropdown");if(menu)menu.style.display="none";
}
function toggleOverview(){let ov=document.getElementById("overviewPanel"),btn=document.getElementById("ovCollapseBtn");if(!ov)return;let collapsed=ov.classList.contains("collapsed");if(collapsed){ov.classList.remove("collapsed");if(btn)btn.innerHTML="◀ 收起面板";}else{ov.classList.add("collapsed");if(btn)btn.innerHTML="▶ 展开面板";}}

function quickPan(id){let e=ENGINES[id];if(!e)return;let inp=document.getElementById("chatInput");let d=new Date(),ds=d.getFullYear()+"-"+(d.getMonth()+1).toString().padStart(2,'0')+"-"+d.getDate().toString().padStart(2,'0'),ts=d.getHours().toString().padStart(2,'0')+":"+d.getMinutes().toString().padStart(2,'0');if(inp)inp.value="Pan "+e.n+"排盘，"+ds+" "+ts+"，男";setActivePanel("chat");if(inp)inp.focus();}

function sendMsg(){let inp=document.getElementById("chatInput");if(!inp)return;let txt=inp.value.trim();if(!txt)return;inp.value="";
  // 根据聊天模式处理
  if(CHAT_MODE==="quick"){doAIChat(txt);return;}
  if(CHAT_MODE==="pan"){let panMatch=txt.match(/Pan\s*(.{1,6}?)(?:排盘)?[，,]\s*(\d{4}-\d{2}-\d{2})\s+(\d{2}:\d{2})[，,]?\s*(.?)/)||txt.match(/(.{1,6}?)(?:排盘)?[，,]?\s*(\d{4}-\d{2}-\d{2})\s+(\d{2}:\d{2})[，,]?\s*(.?)/);if(panMatch){let engName=panMatch[1].trim(),engId=null;for(let k in ENGINES){if(ENGINES[k].n.includes(engName)||engName.includes(k)){engId=k;break}}if(engId){doQuickPan(engId,panMatch[2],panMatch[3],panMatch[4]||"男",txt);return;}}addMessage({id:"msg-"+Date.now(),role:"system",text:"⚠️ 排盘模式：请输入日期和时间\n格式：引擎名, 2025-08-15 14:30, 男\n\n可用引擎：八字/紫微/六壬/奇门/六爻/七政/八宅/黄历/风水/姓名/号码",ts:Date.now()});return;}
  if(CHAT_MODE==="search"){txt="[联网搜索模式] "+txt;}
  if(CHAT_MODE==="code"){txt="[代码执行模式] 直接在本地执行以下请求，返回运行结果："+txt;}
  if(CHAT_MODE==="think"){txt="[深度思考模式] 请仔细推理并展示完整思考过程："+txt;}
  // auto 模式走原始逻辑
  let panMatch=txt.match(/Pan\s*(.{1,6}?)(?:排盘)?[，,]\s*(\d{4}-\d{2}-\d{2})\s+(\d{2}:\d{2})[，,]?\s*(.?)/);if(CHAT_MODE==="auto"&&panMatch){let engName=panMatch[1].trim(),engId=null;for(let k in ENGINES){if(ENGINES[k].n.includes(engName)||engName.includes(k)){engId=k;break}}if(engId){doQuickPan(engId,panMatch[2],panMatch[3],panMatch[4]||"男",txt);return;}}doAIChat(txt);}

function doQuickPan(engine,date,time,gender,orig){let msgId="msg-"+Date.now();addMessage({id:msgId,role:"user",text:orig,ts:Date.now()});let replyId="msg-"+Date.now();addMessage({id:replyId,role:"assistant",text:"",ts:Date.now(),loading:true});fetch("/api/pan?engine="+engine+"&date="+date+"&time="+time+"&gender="+gender).then(r=>r.json()).then(d=>{let r=d.result||{},result=formatPanResult(engine,r);updateMsg(replyId,result);}).catch(e=>{updateMsg(replyId,"排盘请求失败: "+e.message)});}

function doAIChat(txt){let userMsgId="msg-"+Date.now();addMessage({id:userMsgId,role:"user",text:txt,ts:Date.now()});let replyId="msg-"+Date.now();addMessage({id:replyId,role:"assistant",text:"",ts:Date.now(),loading:true});let sessionId="webchat-"+Date.now();fetch("/api/chat/stream",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({message:txt,session_id:sessionId,model:CURRENT_MODEL})}).then(r=>{if(!r.ok)throw new Error("HTTP "+r.status);let reader=r.body.getReader(),decoder=new TextDecoder(),buffer="",accumulatedText="",steps=[];function process(){reader.read().then(({done,value})=>{if(done){updateMsg(replyId,accumulatedText||"(无回复)",steps);return}buffer+=decoder.decode(value,{stream:true});let lines=buffer.split("\n");buffer=lines.pop()||"";lines.forEach(line=>{if(line.startsWith("data:")){let payload=line.substring(5).trim();if(payload==="[DONE]")return;try{let data=JSON.parse(payload);if(data.type==="error")throw new Error(data.error||"AI error");if(data.content){accumulatedText+=data.content;updateMsg(replyId,accumulatedText,steps)}if(data.reply){accumulatedText=data.reply;updateMsg(replyId,accumulatedText,steps)}if(data.text)steps.push(data.text);if(data.token&&data.token.token)accumulatedText+=data.token.token;updateMsg(replyId,accumulatedText,steps)}catch(e){if(e.message&&e.message!=="AI error")console.warn("SSE parse error:",e)}}});process()})}process();}).catch(e=>{updateMsg(replyId,"AI请求失败: "+e.message)});}

function addMessage(msg){messages.push(msg);let ws=document.getElementById("welcomeScreen");let cb=document.getElementById("chatBody");if(ws)ws.style.display="none";if(cb)cb.style.display="";let container=cb;if(!container)return null;let div=document.createElement("div");div.id=msg.id;let rowClass=msg.role==="user"?"msg-row user":"msg-row ai";div.className=rowClass;let bubbleClass=msg.role==="user"?"msg-bubble user":"msg-bubble ai";if(msg.loading)div.innerHTML='<div class="msg-avatar">'+(msg.role==="user"?"🧑":"🐲")+'</div><div class="'+bubbleClass+'"><div class="分析过程-spinner"></div><span class="分析过程-text">正在分析...</span></div>';else div.innerHTML='<div class="msg-avatar">'+(msg.role==="user"?"🧑":"🐲")+'</div><div class="'+bubbleClass+' markdown-body">'+(msg.role==="user"?escapeHtml(msg.text):renderMarkdown(msg.text))+'</div>';container.appendChild(div);container.scrollTop=container.scrollHeight;return div;}

function updateMsg(id,text,steps){let el=document.getElementById(id);if(!el)return;let bubble=el.querySelector(".msg-bubble");if(!bubble)return;bubble.classList.add("markdown-body");let stepsHtml=steps&&steps.length?'<div class="分析过程-text" style="margin-bottom:6px">'+steps.map(s=>'<span>'+escapeHtml(s)+'</span>').join(' → ')+'</div>':'';bubble.innerHTML=stepsHtml+'<div class="streaming-text">'+renderMarkdown(text)+'</div>';let container=document.getElementById("chatBody");if(container)container.scrollTop=container.scrollHeight;}

function formatDuration(ms){if(!ms)return"";if(ms<1000)return ms+"ms";return (ms/1000).toFixed(1)+"s"}

function fmt(label){let map={"WuXing":"五行","Pattern":"格局","Life":"命宫","Gong":"宫","Yi":"宜","Ji":"忌","Chong":"冲","Sha":"煞","Center":"中宫","Total":"总格","Heavenly":"天干","Earthly":"地支","Hidden":"藏干"};return map[label]||label;}

function formatPanResult(engine,result){if(!result)return"暂无结果";if(result.error)return"排盘错误: "+result.error;if(result.text)return result.text;try{let js=JSON.stringify(result,null,2);if(js.length>3000)js=js.substring(0,3000)+"\n... (已截断)";return"<pre style='font-size:11px;line-height:1.3;max-height:500px;overflow-y:auto'>"+escapeHtml(js)+"</pre>"}catch(e){return String(result)}}

// === 截图 / 上传 / 语音 ===
function handleScreenshotClick(){
  // 直接截屏
  handleScreenshot({files:null});
}
function handleScreenshot(input){
  // 如果选择了本地图片，走文件读取；否则直接调用屏幕截图 API
  if(input.files&&input.files[0]){
    let f=input.files[0];
    if(!f.type.startsWith("image/")){addChatMsg("system","⚠️ 请选择图片文件");return;}
    let reader=new FileReader();
    reader.onload=function(e){
      let msgId="msg-"+Date.now();
      addMessage({id:msgId,role:"user",text:e.target.result,isImage:true,ts:Date.now()});
      addChatMsg("system","📷 图片已就绪，可输入问题后发送");
    };
    reader.readAsDataURL(f);
    input.value="";
    return;
  }
  // 屏幕截图
  let msgId="msg-"+Date.now();
  addMessage({id:msgId,role:"user",text:"📷 正在截屏...",ts:Date.now(),loading:true});
  fetch("/api/screenshot",{method:"POST"}).then(r=>r.json()).then(d=>{
    if(d.ok&&d.image){
      let el=document.getElementById(msgId);
      if(el){
        let bubble=el.querySelector(".msg-bubble");
        if(bubble)bubble.innerHTML='<img src="'+d.image+'" style="max-width:100%;border-radius:8px;border:1px solid var(--border)" alt="屏幕截图">';
      }
    }else{
      updateMsg(msgId,"⚠️ 截图失败: "+(d.error||"未知错误"));
    }
  }).catch(e=>{updateMsg(msgId,"⚠️ 截图失败: "+e.message)});
}
function handleFileUpload(input){
  if(!input.files||!input.files[0])return;
  let f=input.files[0],name=f.name,size=f.size;
  let sizeStr=size<1024?size+"B":size<1048576?(size/1024).toFixed(1)+"KB":(size/1048576).toFixed(1)+"MB";
  let msgId="msg-"+Date.now();
  addMessage({id:msgId,role:"user",text:"📁 "+name+" ("+sizeStr+")",isFile:true,fileName:name,ts:Date.now()});
  let info="📁 文件已接收: "+name+" ("+sizeStr+")";
  if(f.type&&f.type.startsWith("text/")){
    let reader=new FileReader();
    reader.onload=function(e){updateMsg(msgId,"📁 "+name+" ("+sizeStr+")\n"+e.target.result.substring(0,1000))};
    reader.readAsText(f);
  }
  addChatMsg("system",info);
  input.value="";
}
function startVoice(){
  if(!("webkitSpeechRecognition" in window||"SpeechRecognition" in window)){
    addChatMsg("system","⚠️ 此浏览器不支持语音输入，请使用Chrome");return;
  }
  let SR=window.SpeechRecognition||window.webkitSpeechRecognition,rec=new SR();
  rec.lang="zh-CN";rec.interimResults=false;rec.continuous=false;
  let btn=document.querySelector(".it-btn[title='语音输入']");
  if(btn){btn.style.color="var(--accent)";btn.textContent="🔴";}
  rec.onresult=function(e){let txt=e.results[0][0].transcript;let inp=document.getElementById("chatInput");if(inp)inp.value=txt;if(btn){btn.style.color="";btn.textContent="🎙️";}};
  rec.onerror=function(e){
    if(btn){btn.style.color="";btn.textContent="🎙️";}
    if(e.error==="not-allowed")addChatMsg("system","⚠️ 麦克风权限被拒绝，请在浏览器设置中允许");
    else if(e.error!=="aborted")addChatMsg("system","⚠️ 语音识别错误: "+e.error);
  };
  rec.onend=function(){if(btn){btn.style.color="";btn.textContent="🎙️";}};
  try{rec.start()}catch(e){if(btn){btn.style.color="";btn.textContent="🎙️";}addChatMsg("system","⚠️ 语音启动失败: "+e.message)}
}
function addChatMsg(role,text){let msgId="msg-"+Date.now();addMessage({id:msgId,role:role,text:text,ts:Date.now()});}

// ===== 键盘快捷键 =====
// Ctrl+1: 按第几次→模式切换 (1=全屏, 2=弹出, 3=嵌入)
// Ctrl+1: toggle inline browser; Ctrl+2: close inline browser
document.addEventListener("keydown",function(e){
  if(e.ctrlKey&&e.key==="1"){
    e.preventDefault();
    toggleInlineBrowser();
  }
  if(e.ctrlKey&&e.key==="2"){
    e.preventDefault();
    toggleInlineBrowser(false);
  }
});

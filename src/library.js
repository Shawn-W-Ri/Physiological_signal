const $ = id => document.getElementById(id);
const esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const safeUrl = value => { try { const u = new URL(value); return /^https?:$/.test(u.protocol) ? esc(u.href) : '#'; } catch { return '#'; } };
let data, catalog=[], sensors=[], methods=[], imports={entries:[]}, repository='', active='全部主题', date='', view='topics', section='papers';
const names = () => [...catalog.map(t=>t.name),'待分类'];
const hasTopic = i => active==='全部主题' || (active==='待分类' ? !i.tags?.length || i.tags.includes('待分类') : i.tags?.includes(active));
const unique = list => [...new Map(list.map(i=>[i.id,i])).values()];
const allPapers = () => unique(data.days.filter(d=>!d.demo).flatMap(d=>d.items).filter(i=>i.kind==='paper'));
const tags = values => `<div class="tags">${(values||[]).map(t=>`<span>${esc(t)}</span>`).join('')}</div>`;
const empty = message => `<div class="empty">${message}</div>`;
function paperCard(i) {
  return `<article><div class="meta"><span>${esc(i.source)}</span><span>${i.kind==='paper' && i.source==='arXiv'?'预印本 · 未经同行评审':i.kind==='paper'?'论文索引':'新闻'}</span><span>发表 ${esc(i.published||'日期未知')}</span><span>收录 ${esc(i.collected)}</span></div><h4><a href="${safeUrl(i.url)}" target="_blank" rel="noopener noreferrer">${esc(i.titleZh||i.title)} ↗</a></h4>${i.titleZh?`<p class="original">${esc(i.title)}</p>`:''}<p class="summary">${esc(i.summaryZh||i.summary||'来源未提供摘要，请查看原文。')}</p><div class="article-bottom">${tags(i.tags?.length?i.tags:['待分类'])}<span class="language">${i.titleZh?'AI 中文内容 · 请核对原文':'原文摘录'}</span></div></article>`;
}
function sensorCard(s) {
  return `<article class="resource-card"><p class="eyebrow">SENSOR / ${esc(s.id)}</p><h3>${esc(s.name)}</h3><p>${esc(s.summary)}</p><dl><dt>采集接口</dt><dd>${esc(s.interface)}</dd><dt>使用前确认</dt><dd>${esc(s.considerations)}</dd></dl>${tags(s.tags)}<p class="resource-actions"><a href="${safeUrl(s.url)}" target="_blank" rel="noopener noreferrer">${esc(s.source)} ↗</a></p></article>`;
}
function methodCard(m) {
  const related=sensors.filter(s=>(m.sensorIds||[]).includes(s.id));
  return `<article class="resource-card"><p class="eyebrow">METHOD / ${esc(m.id)}</p><h3>${esc(m.title)}</h3><p>${esc(m.summary)}</p><ol>${m.steps.map(s=>`<li>${esc(s)}</li>`).join('')}</ol><p class="method-note">${esc(m.note)}</p>${related.length?`<p class="muted">相关设备：${related.map(s=>esc(s.name)).join('、')}</p>`:''}${tags(m.tags)}<p class="resource-actions"><a href="${safeUrl(m.url)}" target="_blank" rel="noopener noreferrer">${esc(m.source)} ↗</a></p></article>`;
}
function renderTopics() {
  const papers=allPapers();
  const collections={papers:papers.filter(hasTopic),sensors:sensors.filter(hasTopic),methods:methods.filter(hasTopic)};
  $('view-title').textContent=active==='全部主题'?'研究主题':active;$('total-count').textContent='';
  $('view-subtitle').textContent=active==='全部主题'?'按信号类型组织论文、传感器和使用方法。':catalog.find(t=>t.name===active)?.description||'暂无明确主题匹配的论文，可人工补充标签。';
  $('category-tabs').hidden=false;
  $('category-tabs').innerHTML=[['papers','论文'],['sensors','传感器'],['methods','使用方法']].map(([key,label])=>`<button type="button" data-section="${key}" aria-pressed="${section===key}" class="${section===key?'selected':''}">${label}<span>${collections[key].length}</span></button>`).join('');
  const overview=active==='全部主题'?`<div class="topic-grid">${catalog.map(t=>`<button type="button" class="topic-card" data-topic="${esc(t.name)}"><strong>${esc(t.name)}</strong><span>${esc(t.description)}</span><small>${papers.filter(i=>i.tags?.includes(t.name)).length} 篇论文 · ${sensors.filter(i=>i.tags.includes(t.name)).length} 个传感器 · ${methods.filter(i=>i.tags.includes(t.name)).length} 篇方法</small></button>`).join('')}</div>`:'';
  const selected=collections[section], renderer={papers:paperCard,sensors:sensorCard,methods:methodCard}[section];
  $('results').innerHTML=overview+`<section class="category"><div class="category-title"><span class="section-no">${{papers:'01',sensors:'02',methods:'03'}[section]}</span><h3>${{papers:'论文库 · 全部收录日期',sensors:'传感器资料',methods:'使用方法'}[section]}</h3><span class="count">${selected.length}</span></div>${selected.length?selected.map(renderer).join(''):empty(section==='papers'?'这个主题尚未收录论文。可点击“添加论文”提交链接。':'这个主题的资料尚未添加。')}</section>`;
}
function renderDaily() {
  const items=(data.days.find(d=>d.date===date)?.items||[]).filter(hasTopic);
  $('view-title').textContent='每日更新';$('total-count').textContent=`${items.length} 条`;
  $('view-subtitle').textContent='按首次收录日查看新闻与论文。';$('category-tabs').hidden=true;
  $('results').innerHTML=[['news','行业 / 科研新闻'],['paper','最新科研论文']].map(([kind,title],n)=>{
    const list=items.filter(i=>i.kind===kind);
    return `<section class="category"><div class="category-title"><span class="section-no">0${n+1}</span><h3>${title}</h3><span class="count">${list.length}</span></div>${list.length?list.map(paperCard).join(''):empty('本日期与主题下暂无新收录内容。')}</section>`;
  }).join('');
}
function renderImport() {
  $('view-title').textContent='添加论文';$('total-count').textContent='';$('category-tabs').hidden=true;
  $('view-subtitle').textContent='一次提交多个链接，自动读取元数据并按研究主题归类。';
  const action=repository ? repository.replace(/\/$/,'')+'/actions/workflows/daily.yml' : '';
  $('results').innerHTML=`<article class="import-guide"><h3>在 GitHub 中提交论文链接</h3><ol><li>打开下方工作流，点击 <b>Run workflow</b>。</li><li>将链接粘贴到 <b>paper_links</b>，用空格或换行分隔，然后运行。</li><li>等待导入、保存和部署完成，在对应研究主题的“论文”分类中查看。</li></ol><p>支持 arXiv 摘要 / PDF 链接、PubMed 链接、DOI 链接或 DOI 编号。出版社网页请先复制其中的 DOI。仅仓库有权限的成员可运行导入。</p>${action?`<a class="primary-link" href="${safeUrl(action)}" target="_blank" rel="noopener noreferrer">打开 GitHub 导入入口 ↗</a>`:empty('请在 public/data/site.json 中配置仓库地址。')}<p class="muted">也可在仓库 config/papers.txt 中每行添加一个链接。关键词分类无需 API key；多主题论文会同时显示在多个类别。未匹配的论文进入“待分类”。</p></article><section class="category"><div class="category-title"><h3>链接处理记录</h3><span class="count">${imports.entries.length}</span></div>${imports.entries.length?imports.entries.map(e=>`<article><div class="meta"><span>${esc({imported:'已收录',duplicate:'已存在',failed:'导入失败',queued:'排队中'}[e.status]||e.status)}</span></div><p class="import-url">${esc(e.input)}</p><p>${esc(e.message)}</p>${tags(e.tags)}</article>`).join(''):empty('尚未提交链接。这里会显示逐条结果；读取失败的链接会在后续任务中重试。')}</section>`;
}
function render() {
  if(!data)return;
  const day=data.days.find(d=>d.date===date);
  $('issue-date').textContent=view==='daily'?(date||'尚未收录'):'主题知识库';
  $('issue-label').textContent=view==='daily'?'本期收录日期 · 北京时间':'持续积累 · 按研究方向组织';
  const latest=data.lastImport||data.lastRun;
  $('update-state').textContent=latest?`最近${data.lastImport?'导入':'采集'} ${new Date(latest).toLocaleString('zh-CN',{timeZone:'Asia/Shanghai',hour12:false})}`:'等待首次更新';
  $('notice').textContent=view!=='daily'?'':day?.demo?'示例内容，不代表实际新闻或论文。':data.status==='partial'?'部分来源采集失败，当前显示已获取内容与历史归档。':data.status==='failed'?'最近一次采集失败，历史归档仍可查看。':'';
  $('archives').hidden=view!=='daily';$('reset').hidden=view==='import';
  document.querySelectorAll('[data-view]').forEach(b=>{b.classList.toggle('selected',b.dataset.view===view);b.setAttribute('aria-pressed',String(b.dataset.view===view));});
  const countItems=view==='daily'?(day?.items||[]):allPapers();
  $('topics').innerHTML=['全部主题',...names()].map(t=>`<button type="button" data-topic="${esc(t)}" class="topic ${active===t?'active':''}" aria-pressed="${active===t}"><span>${esc(t)}</span><span>${t==='全部主题'?countItems.length:countItems.filter(i=>t==='待分类'?!i.tags?.length||i.tags.includes(t):i.tags?.includes(t)).length}</span></button>`).join('');
  $('topic-count-label').textContent=view==='daily'?'数字为当日条目数':'数字为全部日期的论文数';
  if(view==='daily')renderDaily();else if(view==='import')renderImport();else renderTopics();
}
function navigate() {
  const p=new URLSearchParams(location.hash.slice(1));
  view=['topics','daily','import'].includes(p.get('view'))?p.get('view'):p.has('date')?'daily':'topics';
  active=names().includes(p.get('topic'))?p.get('topic'):'全部主题';
  section=['papers','sensors','methods'].includes(p.get('section'))?p.get('section'):'papers';
  date=data.days.some(d=>d.date===p.get('date'))?p.get('date'):data.days[0]?.date||'';
  $('date-select').value=date;render();
}
function save() {
  const p=new URLSearchParams({view});if(active!=='全部主题')p.set('topic',active);
  if(view==='topics')p.set('section',section);if(view==='daily'&&date)p.set('date',date);
  history.replaceState(null,'',`#${p}`);render();
}
document.addEventListener('click',e=>{
  if(!data)return;
  const t=e.target.closest('[data-topic]'),v=e.target.closest('[data-view]'),s=e.target.closest('[data-section]');
  if(t){active=t.dataset.topic;if(view==='import')view='topics';save();}
  if(v){view=v.dataset.view;save();}
  if(s){section=s.dataset.section;save();}
});
$('date-select').addEventListener('change',e=>{date=e.target.value;save();});
$('reset').addEventListener('click',()=>{if(!data)return;active='全部主题';section='papers';date=data.days[0]?.date||'';$('date-select').value=date;save();});
window.addEventListener('hashchange',()=>{if(data)navigate();});
const readJson = async path => {const r=await fetch(`./data/${path}`);if(!r.ok)throw Error(path);return r.json();};
Promise.all([readJson('index.json'),readJson('topics.json'),readJson('sensors.json'),readJson('methods.json'),readJson('imports.json').catch(()=>({entries:[]})),readJson('site.json')]).then(([d,t,s,m,i,site])=>{
  data=d;catalog=t;sensors=s;methods=m;imports=i;repository=site.repository||'';
  $('date-select').innerHTML=data.days.map(d=>`<option value="${esc(d.date)}">${esc(d.date)} · ${d.items.length} 条</option>`).join('')||'<option value="">暂无归档</option>';navigate();
}).catch(()=>{$('update-state').textContent='读取失败';$('notice').textContent='资料无法加载，请检查 data 目录是否完整上传，然后刷新页面。';});

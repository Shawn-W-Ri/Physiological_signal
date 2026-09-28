import './style.css';
const topics = ['ECG/心电','EEG/脑电','EMG/肌电','PPG','EDA/皮电','呼吸','睡眠','可穿戴设备'];
const $ = id => document.getElementById(id);
let data, active = '全部主题', date = '';
const esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const safeUrl = value => { try { const u = new URL(value); return /^https?:$/.test(u.protocol) ? u.href : '#'; } catch { return '#'; } };
function render() {
  const day = data.days.find(d => d.date === date);
  const all = day?.items || [];
  const items = all.filter(i => active === '全部主题' || i.tags.includes(active));
  $('issue-date').textContent = date || '尚未收录';
  $('total-count').textContent = `${items.length} 条`;
  $('update-state').textContent = data.lastRun ? `最近采集 ${new Date(data.lastRun).toLocaleString('zh-CN', {timeZone:'Asia/Shanghai',hour12:false})}` : '等待首次采集';
  $('notice').textContent = day?.demo ? '示例预览：以下为演示条目，不代表真实新闻或论文；首次成功采集后自动移除。' : data.status === 'partial' ? '部分来源采集失败，当前展示已获取的内容及历史归档。' : data.status === 'failed' ? '最近一次采集失败，历史内容仍可阅读。' : '';
  $('topics').innerHTML = ['全部主题',...topics].map(t=>`<button type="button" data-topic="${esc(t)}" class="topic ${active===t?'active':''}" aria-pressed="${active===t}"><span>${esc(t)}</span><span>${t==='全部主题'?all.length:all.filter(i=>i.tags.includes(t)).length}</span></button>`).join('');
  $('results').innerHTML = [['news','01','行业 / 科研新闻','NEWS & INSIGHTS'],['paper','02','最新科研论文','RESEARCH PAPERS']].map(([kind,num,title,en])=>{
    const list = items.filter(i=>i.kind===kind);
    return `<section class="category"><div class="category-title"><span class="section-no">${num}</span><h3>${title}</h3><span class="en">${en}</span><span class="count">${list.length}</span></div>${list.length?list.map(i=>`<article><div class="meta"><span>${esc(i.source)}</span><span>${kind==='paper' && i.source==='arXiv'?'预印本 · 未经同行评审':kind==='paper'?'论文索引':'新闻'}</span><span>发表 ${esc(i.published || '日期未知')}</span></div><h4><a href="${safeUrl(i.url)}" target="_blank" rel="noopener noreferrer">${esc(i.titleZh||i.title)} <span>↗</span></a></h4>${i.titleZh?`<p class="original">${esc(i.title)}</p>`:''}<p class="summary">${esc(i.summaryZh||i.summary||'来源未提供摘要，请查看原文。')}</p><div class="article-bottom"><div class="tags">${i.tags.map(t=>`<span>${esc(t)}</span>`).join('')}</div><span class="language">${i.titleZh?'AI 中文摘要 · 请核对原文':'原文摘录'}</span></div></article>`).join(''):'<div class="empty">本日期与主题下暂无内容。可切换主题或查看其他归档。</div>'}</section>`;
  }).join('');
}
function navigate() { const p = new URLSearchParams(location.hash.slice(1)); date = p.get('date') || data.days[0]?.date || ''; active = topics.includes(p.get('topic')) ? p.get('topic') : '全部主题'; $('date-select').value = date; render(); }
function save() { const p = new URLSearchParams(); if(date)p.set('date',date); if(active!=='全部主题')p.set('topic',active); history.replaceState(null,'',`#${p}`); render(); }
$('topics').addEventListener('click',e=>{const b=e.target.closest('[data-topic]');if(b){active=b.dataset.topic;save();}});
$('date-select').addEventListener('change',e=>{date=e.target.value;save();});
$('reset').addEventListener('click',()=>{if(!data)return;active='全部主题';date=data.days[0]?.date||'';$('date-select').value=date;save();});
window.addEventListener('hashchange',()=>{if(data && location.hash!=='#archives')navigate();});
fetch(`${import.meta.env.BASE_URL}data/index.json`).then(r=>{if(!r.ok)throw Error();return r.json();}).then(d=>{data=d;$('date-select').innerHTML=d.days.map(day=>`<option value="${esc(day.date)}">${esc(day.date)} · ${day.items.length} 条${day.demo?' · 示例':''}</option>`).join('')||'<option value="">暂无归档</option>';navigate();}).catch(()=>{$('update-state').textContent='读取失败';$('notice').textContent='日报数据暂时无法加载，请刷新页面重试。';});

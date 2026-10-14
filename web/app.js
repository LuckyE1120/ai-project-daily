'use strict';
const reports = JSON.parse(document.getElementById('report-data').textContent);
const months = JSON.parse(document.getElementById('monthly-data').textContent);
const $ = id => document.getElementById(id);
const escapeHTML = str => String(str).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
let query = '';
let selected = reports[0];
let selectedMonth = months[0];
let view = 'daily';
let category = '';
let initialized = false;
const monthlyText = m => [m.month,m.summary,m.text||'',...m.insights,...m.projects.map(p=>Object.values(p).join(' '))].join(' ').toLocaleLowerCase();
const matches = report => !query || report.text.toLocaleLowerCase().includes(query);
function renderArchive() {
  const monthly = view === 'monthly';
  const pool = monthly ? months : reports;
  const filtered = monthly ? pool.filter(m=>!query||monthlyText(m).includes(query)) : pool.filter(matches);
  $('archive-label').textContent = monthly ? '月度归档' : '日报归档';
  $('archive-count').textContent = pool.length + ' 期';
  $('daily-tab').setAttribute('aria-current',monthly?'false':'page');
  $('monthly-tab').setAttribute('aria-current',monthly?'page':'false');
  $('archive').innerHTML = filtered.map(r=>{
    const active = monthly ? r.month===selectedMonth?.month : r.date===selected.date;
    const label = monthly ? r.month.slice(5)+' 月' : r.date.slice(5).replace('-',' / ');
    const year = (monthly?r.month:r.date).slice(0,4);
    const detail = monthly ? (r.status==='published'?'正式月报':'采样预览') : (r.date===reports[0].date?'最新日报':'往期观察');
    return `<a class="archive-item ${active?'active':''}" href="${monthly?'#view=monthly&month='+r.month:'#date='+r.date}" ${active?'aria-current="page"':''}><span>${label}<small>${year}</small></span><span class="archive-detail">${detail}<small>${r.projects.length} 个项目</small></span><span class="arrow">↗</span></a>`;
  }).join('');
  $('search-status').textContent = query ? (filtered.length ? `找到 ${filtered.length} 期相关${monthly?'月度观察':'日报'}，点击归档阅读。` : '没有匹配的报告，试试 Agent、视频或测试。') : '';
}
function renderProjects() {
  const pool = query ? reports.flatMap(r=>r.projects.map(p=>({...p,date:r.date}))) : selected.projects;
  const seen = new Set();
  const projects = pool.filter(p=>{
    if(query && !(p.name+' '+p.description).toLowerCase().includes(query)) return false;
    if(seen.has(p.url)) return false;
    seen.add(p.url); return true;
  });
  $('project-heading').textContent = query ? '项目搜索结果' : '本期关注';
  $('project-count').textContent = projects.length+' 个项目';
  $('projects').innerHTML = projects.length ? projects.map((p,i)=>`<a class="project-card" href="${escapeHTML(p.url)}" target="_blank" rel="noopener noreferrer"><div class="card-top"><span class="card-number">${String(i+1).padStart(2,'0')}</span><span class="card-date">${p.date||selected.date}</span><span>↗</span></div><h3>${escapeHTML(p.name)}</h3><p>${escapeHTML(p.description)}</p><span class="card-source">官方仓库 · GitHub</span></a>`).join('') : '<p class="empty">未匹配到项目卡片。左侧全文搜索仍可找到正文中的关键词。</p>';
}
function topCards(m,kind) {
  if(!m[kind+'_top'].length) return `<div class="top-empty"><span aria-hidden="true">✳</span><h4>${m.status==='preview'?'评选在月初揭晓':'本期暂不授予名额'}</h4><p>${m.status==='preview'?'月末汇总样本，再核验候选项目与评选依据。':'现有证据不足，不强行补足 Top 3。'}</p></div>`;
  return m[kind+'_top'].map((p,i)=>`<div class="top-card"><div class="winner-line"><span class="winner-rank">0${i+1}</span><span class="winner-score">${p[kind+'_score']}<small> / 100 · 编辑评分</small></span></div><h4><a href="${escapeHTML(p.url)}" target="_blank" rel="noopener noreferrer">${escapeHTML(p.name)} ↗</a></h4><p>${escapeHTML(p[kind+'_reason'])}</p><div class="winner-trial"><strong>先验证什么</strong><p>${escapeHTML(p.trial)}</p></div><details><summary>评分依据、来源与限制</summary><p>分项：${p[kind+'_scores'].join(' / ')}（每项 1—5 分）</p><p>证据等级：${escapeHTML(p.evidence_level)}</p><p>${escapeHTML(p.caveat)}</p>${p.evidence.map(e=>`<p><a href="${escapeHTML(e.url)}" target="_blank" rel="noopener noreferrer">${escapeHTML(e.note)} ↗</a><small> · 核验 ${escapeHTML(e.checked_at)}</small></p>`).join('')}</details></div>`).join('');
}
function renderMonthly() {
  const m = selectedMonth;
  if(!m){$('monthly-panel').innerHTML='<p class="empty">尚无月度样本，日报积累后在这里展示。</p>';return;}
  const published = m.status==='published';
  const projects = m.projects.filter(p=>(!category||p.category===category)&&(!query||(p.name+' '+p.description+' '+p.category+' '+(p.idea_reason||'')+' '+(p.value_reason||'')).toLocaleLowerCase().includes(query)));
  const largest = m.categories[0];
  $('monthly-panel').innerHTML=`<div class="month-heading"><div><span class="eyebrow">THE MONTH IN REVIEW</span><h2>${m.month.replace('-',' 年 ')} 月 <span class="month-status">${published?'正式月报':'采样预览'}</span></h2></div>${published?`<a class="download" download href="./monthlies/${encodeURIComponent(m.filename)}">下载月报 ↓</a>`:''}</div><div class="month-notice">${published?`发布于 ${m.published_at} · 本站归档样本的编辑评选`:'每月 1 日 10:15 汇总上个月。当前是已归档样本的预览，尚未进行正式排名。'}</div><div class="month-stats"><div><strong>${m.report_count}</strong><span>期样本日报</span></div><div><strong>${m.project_count}</strong><span>个去重项目</span></div><div><strong>${m.coverage}%</strong><span>自然日覆盖率</span></div></div><div class="monthly-analysis"><h3>这个月，项目在做什么？</h3><p>${escapeHTML(m.summary)}</p>${m.insights.length?'<ul>'+m.insights.map(i=>'<li>'+escapeHTML(i)+'</li>').join('')+'</ul>':`<p>${largest?`当前样本中，${escapeHTML(largest.name)}最多，共 ${largest.count} 个（${largest.percent}%）。`:''}样本${m.start?'覆盖 '+m.start+' 至 '+m.end:'尚未积累'}，不代表整个 AI 行业。</p>`}</div><div class="category-section"><div class="section-top"><div><h3>项目类型分布</h3><p class="muted">按主要用途归入一个类型；仓库去重；点击类型查看项目。</p></div></div><div class="category-bars">${m.categories.map(c=>`<button type="button" class="category-row ${category===c.name?'chosen':''}" data-category="${escapeHTML(c.name)}" aria-pressed="${category===c.name}"><span>${escapeHTML(c.name)}</span><span class="bar-track"><span style="width:${c.percent}%"></span></span><span class="category-number">${c.count} · ${c.percent}%</span></button>`).join('')}</div></div><div class="awards"><section class="award-column"><div class="award-label">IDEA / 创意</div><h3>最有想法 <span>Top 3</span></h3><p class="award-criteria">新颖性 40% · 工作流设计 35% · 可扩展性 25%</p>${topCards(m,'idea')}</section><section class="award-column"><div class="award-label">IMPACT / 实用</div><h3>最有落地价值 <span>Top 3</span></h3><p class="award-criteria">实际问题 40% · 上手成本 30% · 可验证性 30%</p>${topCards(m,'value')}</section></div><details class="methodology"><summary>评选规则与样本边界</summary><p>两个榜单独立评分，同一项目可以同时入选。每项 1—5 分，按权重换算至 100 分；并列按仓库名排列。Star 不参与评分，证据不足时少选或空榜。评分是编辑判断，不是性能基准。</p><p>按规范化 GitHub 仓库地址去重，包含新增介绍和跟踪观察。${m.report_count} / ${m.calendar_days} 个自然日有归档日报，覆盖率 ${m.coverage}%。未采样日期不计作没有项目。</p><p>正式月报保留评选时的资料快照。具体评分理由、官方来源、核验日期、体验方式和限制随入选项目展示。</p></details><div class="section-top"><h3>${category?escapeHTML(category):'本月项目清单'}</h3><div><span class="muted">${projects.length} 个</span> ${category?'<button type="button" class="clear-category">显示全部</button>':''}</div></div><div class="monthly-candidates">${projects.length?projects.map(p=>`<div class="candidate"><div><a href="${escapeHTML(p.url)}" target="_blank" rel="noopener noreferrer">${escapeHTML(p.name)} ↗</a><span>${escapeHTML(p.category)}</span></div><p>${escapeHTML(p.description)}</p><small>收录 ${p.dates.length} 天 · ${p.dates.join('、')}${p.eligible===false?' · 未参评：'+escapeHTML(p.exclusion_reason):''}</small></div>`).join(''):'<p class="empty">当前筛选没有匹配项目。</p>'}</div>${published?`<details class="monthly-full"><summary>阅读完整月报与全量来源</summary><article>${m.html}</article></details>`:''}`;
  $('monthly-panel').querySelectorAll('[data-category]').forEach(button=>button.addEventListener('click',()=>{category=category===button.dataset.category?'':button.dataset.category;renderMonthly();}));
  $('monthly-panel').querySelector('.clear-category')?.addEventListener('click',()=>{category='';renderMonthly();});
}
function selectRoute() {
  if(initialized && ['#reader','#monthly-panel'].includes(location.hash)) return;
  initialized = true;
  const params = new URLSearchParams(location.hash.slice(1));
  view = params.get('view')==='monthly' || location.hash==='#monthly-panel' ? 'monthly' : 'daily';
  selected = reports.find(r=>r.date===params.get('date')) || reports[0];
  selectedMonth = months.find(m=>m.month===params.get('month')) || months[0];
  category = '';
  const monthly = view==='monthly';
  document.querySelector('.intro').hidden=monthly;
  document.querySelector('.skip').href=monthly?'#monthly-panel':'#reader';
  $('search').setAttribute('aria-label',monthly?'搜索月报与候选项目':'搜索所有日报全文');
  $('search').placeholder=monthly?'搜索月报或项目':'搜索项目或关键词';
  $('daily-projects').hidden=monthly; $('reader').hidden=monthly; $('monthly-panel').hidden=!monthly;
  if(!monthly){
    $('report').innerHTML = selected.html;
    $('reader-date').textContent = selected.date;
    $('reader-title').textContent = selected.date + ' · 完整日报';
    $('download').href = './reports/'+encodeURIComponent(selected.filename);
    $('download').setAttribute('download',selected.filename);
  }
  $('issue-label').textContent = monthly ? '月度观察 / '+(selectedMonth?.month||'待积累') : '最新收录 / '+reports[0].date;
  document.title = (monthly?(selectedMonth?.month||'月度')+' · AI 项目月报':selected.date+' · AI 项目日报');
  renderArchive(); monthly?renderMonthly():renderProjects();
}
$('stat-issues').textContent=reports.length;
$('stat-projects').textContent=new Set(reports.flatMap(r=>r.projects.map(p=>p.url.toLowerCase()))).size;
$('last-updated').textContent='日报截至 '+reports[0].date+' · 月报每月 1 日';
$('search').addEventListener('input',event=>{
  query=event.target.value.trim().toLocaleLowerCase(); renderArchive(); view==='monthly'?renderMonthly():renderProjects();
});
document.addEventListener('keydown',event=>{
  if(event.key==='/' && !['INPUT','TEXTAREA'].includes(document.activeElement.tagName)) { event.preventDefault(); $('search').focus(); }
  if(event.key==='Escape' && document.activeElement===$('search')) { $('search').value=''; query=''; renderArchive(); view==='monthly'?renderMonthly():renderProjects(); }
});
window.addEventListener('hashchange',selectRoute);
selectRoute();

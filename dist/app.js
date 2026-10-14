'use strict';
const reports = JSON.parse(document.getElementById('report-data').textContent);
const $ = id => document.getElementById(id);
const escapeHTML = str => str.replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
let query = '';
let selected = reports[0];
const matches = report => !query || report.text.toLocaleLowerCase().includes(query);
function renderArchive() {
  const filtered = reports.filter(matches);
  $('archive-count').textContent = reports.length + ' 期';
  $('archive').innerHTML = filtered.map(r=>`<a class="archive-item ${r.date===selected.date?'active':''}" href="#date=${r.date}" ${r.date===selected.date?'aria-current="page"':''}><span>${r.date.slice(5).replace('-',' / ')}<small>${r.date.slice(0,4)}</small></span><span class="archive-detail">${r.date===reports[0].date?'最新日报':'往期观察'}<small>${r.projects.length} 个项目</small></span><span class="arrow">↗</span></a>`).join('');
  $('search-status').textContent = query ? (filtered.length ? `找到 ${filtered.length} 期相关日报，点击日期阅读。` : '没有匹配的日报，试试 Agent、视频或测试。') : '';
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
function selectDate() {
  if(location.hash==='#reader') return;
  const date = new URLSearchParams(location.hash.slice(1)).get('date');
  selected = reports.find(r=>r.date===date) || reports[0];
  $('report').innerHTML = selected.html;
  $('reader-date').textContent = selected.date;
  $('reader-title').textContent = selected.date + ' · 完整日报';
  $('download').href = './reports/'+encodeURIComponent(selected.filename);
  $('download').setAttribute('download',selected.filename);
  $('issue-label').textContent = '最新收录 / '+reports[0].date;
  document.title = selected.date+' · AI 项目日报';
  renderArchive(); renderProjects();
}
$('stat-issues').textContent=reports.length;
$('stat-projects').textContent=new Set(reports.flatMap(r=>r.projects.map(p=>p.url))).size;
$('last-updated').textContent='内容截至 '+reports[0].date;
$('search').addEventListener('input',event=>{
  query=event.target.value.trim().toLocaleLowerCase(); renderArchive(); renderProjects();
});
document.addEventListener('keydown',event=>{
  if(event.key==='/' && !['INPUT','TEXTAREA'].includes(document.activeElement.tagName)) { event.preventDefault(); $('search').focus(); }
  if(event.key==='Escape' && document.activeElement===$('search')) { $('search').value=''; query=''; renderArchive(); renderProjects(); }
});
window.addEventListener('hashchange',selectDate);
selectDate();

"""Aggregate archived evidence; require an editorial review to publish Top lists."""
import argparse
import calendar
from collections import Counter
from datetime import date, datetime, timedelta
import hashlib
import json
from pathlib import Path
import re
from urllib.parse import urlparse
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent
CATEGORIES = ['AI 编程与工程 Skill', 'Agent 基础能力', 'Agent 协作与编排', '自动化测试', '设计与可视化', '音视频创作', '软件分析与研究', '其他', '待分类']
WEIGHTS = {'idea': [40, 35, 25], 'value': [40, 30, 30]}

def previous_month(today):
    return (today.replace(day=1)-timedelta(days=1)).strftime('%Y-%m')

def repo_key(url):
    parsed = urlparse(url)
    parts = parsed.path.strip('/').split('/')
    if parsed.scheme != 'https' or parsed.netloc.lower() != 'github.com' or len(parts) != 2:
        raise ValueError('Project must use a canonical GitHub repository URL: '+url)
    return '/'.join(parts).removesuffix('.git').lower()

def snapshot(reports, month, catalog=None):
    if not re.fullmatch(r'\d{4}-(0[1-9]|1[0-2])',month):
        raise ValueError('Month must be YYYY-MM')
    catalog = catalog if catalog is not None else json.loads((ROOT/'catalog.json').read_text())
    selected = sorted([r for r in reports if r['date'].startswith(month+'-')], key=lambda r:r['date'])
    projects = {}
    for report in selected:
        # Full descriptions from the lead table take priority over follow-up observations.
        for p in report['projects'] + report.get('observations', []):
            key = repo_key(p['url'])
            if key not in projects:
                projects[key] = {**p, 'key':key, 'category':catalog.get(key,'待分类'), 'dates':[]}
            if report['date'] not in projects[key]['dates']:
                projects[key]['dates'].append(report['date'])
    candidates = sorted(projects.values(),key=lambda p:p['key'])
    counts = Counter(p['category'] for p in candidates)
    days = calendar.monthrange(int(month[:4]),int(month[5:]))[1]
    fingerprint = hashlib.sha256(json.dumps([(r['filename'],r['text']) for r in selected],ensure_ascii=False).encode()).hexdigest()
    return {'month':month,'status':'preview','title':month+' · 月度采样预览', 'report_count':len(selected),'project_count':len(candidates),'calendar_days':days,'coverage':round(len(selected)/days*100,1),'start':selected[0]['date'] if selected else None,'end':selected[-1]['date'] if selected else None,'report_dates':[r['date'] for r in selected],'source_fingerprint':fingerprint,'projects':candidates,'categories':[{'name':name,'count':n,'percent':round(n/len(candidates)*100,1)} for name,n in sorted(counts.items(),key=lambda v:(-v[1],v[0]))],'idea_top':[],'value_top':[],'summary':'基于已归档日报的采样预览，尚未完成月度评选。','insights':[]}

def score(values, kind):
    if not isinstance(values,list) or len(values)!=3 or any(type(v) is not int or not 1 <= v <= 5 for v in values):
        raise ValueError('Each score requires three integers between 1 and 5')
    return round(sum(v*w for v,w in zip(values,WEIGHTS[kind]))/5,1)

def finalize(sample, review, as_of):
    if sample['month'] >= as_of.strftime('%Y-%m'):
        raise ValueError('Only completed calendar months may be published')
    if review.get('month') != sample['month'] or review.get('source_fingerprint') != sample['source_fingerprint']:
        raise ValueError('Review month/evidence snapshot does not match; prepare and review again')
    if not isinstance(review.get('summary'),str) or not review['summary'].strip():
        raise ValueError('An editorial summary is required')
    if not isinstance(review.get('insights'),list) or any(not isinstance(s,str) or not s.strip() for s in review['insights']):
        raise ValueError('Insights must be a list of nonempty statements')
    entries = review.get('projects',{})
    if set(entries) != {p['key'] for p in sample['projects']}:
        raise ValueError('Review every sampled project, including explicit exclusions')
    result = {**sample,'status':'published','title':sample['month']+' · AI 项目月报','published_at':as_of.isoformat(),'summary':review['summary'],'insights':review['insights']}
    evaluated = []
    for p in sample['projects']:
        entry = entries[p['key']]
        category = entry.get('category')
        if category not in CATEGORIES or category == '待分类':
            raise ValueError('Classify every project before publication: '+p['key'])
        item = {**p,'category':category}
        if type(entry.get('eligible')) is not bool:
            raise ValueError('Explicit eligibility is required: '+p['key'])
        item['eligible'] = entry['eligible']
        if not entry['eligible']:
            reason = entry.get('exclusion_reason')
            if not isinstance(reason,str) or not reason.strip():
                raise ValueError('Explain exclusions: '+p['key'])
            item['exclusion_reason']=reason
        else:
            for field in ['idea_reason','value_reason','trial','caveat','evidence_level']:
                if not isinstance(entry.get(field),str) or not entry[field].strip():
                    raise ValueError('Missing '+field+': '+p['key'])
                item[field]=entry[field]
            evidence = entry.get('evidence',[])
            if not evidence:
                raise ValueError('Evidence is required: '+p['key'])
            for e in evidence:
                if not isinstance(e,dict) or urlparse(e.get('url','')).scheme!='https' or not urlparse(e['url']).netloc or not e.get('note'):
                    raise ValueError('Use HTTPS evidence links and notes')
                checked = date.fromisoformat(e.get('checked_at',''))
                if checked > as_of:
                    raise ValueError('Evidence check cannot be in the future')
            item['evidence']=evidence
            for kind in WEIGHTS:
                item[kind+'_scores']=entry.get(kind+'_scores')
                item[kind+'_score']=score(item[kind+'_scores'],kind)
        evaluated.append(item)
    result['projects']=evaluated
    counts=Counter(p['category'] for p in evaluated)
    result['categories']=[{'name':n,'count':c,'percent':round(c/len(evaluated)*100,1)} for n,c in sorted(counts.items(),key=lambda v:(-v[1],v[0]))]
    for kind in WEIGHTS:
        result[kind+'_top']=sorted([p for p in evaluated if p['eligible']],key=lambda p:(-p[kind+'_score'],p['key']))[:3]
    result['filename']='AI项目月报-'+sample['month']+'.md'
    result['text']=render_markdown(result)
    return result

def render_markdown(month):
    safe=lambda s: str(s).replace('|',' / ').replace('\n',' ')
    lines=['# '+month['title'],'',f"统计月份：{month['month']}；发布日期：{month['published_at']}（北京时间）",'',f"样本：{month['report_count']} 期日报、{month['project_count']} 个去重项目；覆盖 {month['coverage']}% 的自然日。仅代表本站样本，不代表整个行业。",'', '## 月度分析','',month['summary'],'']
    lines += ['- '+v for v in month['insights']]
    lines += ['', '## 项目类型分布','','每个项目按主要用途归入一个类型，按规范化仓库地址去重；跟踪项目也计入。','','| 类型 | 项目数 | 占比 |','|---|---|---|']
    lines += [f"| {c['name']} | {c['count']} | {c['percent']}% |" for c in month['categories']]
    lines += ['','## 评选方法','','以下评分是依据来源的编辑判断，不是性能基准或行业排名。Star 不参与评分。最有想法：新颖性 40%、工作流设计 35%、可扩展性 25%；最有落地价值：解决实际问题 40%、上手成本 30%、可验证性 30%。每项 1—5 分，换算为 100 分；并列时按仓库名排序。同一项目可入选两榜；证据不足时少选或空榜。','','## 最有想法 Top 3','']
    for kind,label in [('idea','创意'),('value','落地价值')]:
        if kind=='value': lines+=['','## 最有落地价值 Top 3','']
        if not month[kind+'_top']: lines+=['本期没有证据充分的候选项目，不强行补足名额。']
        for i,p in enumerate(month[kind+'_top'],1):
            lines += [f"### {i}. [{p['name']}]({p['url']}) · {p[kind+'_score']} 分",'',p[kind+'_reason'],'',f"建议验证：{p['trial']}",'',f"限制：{p['caveat']}；证据等级：{p['evidence_level']}。",'']
            lines += [f"- [{safe(e['note'])}]({e['url']})（核验 {e['checked_at']}）" for e in p['evidence']]
    lines+=['','## 全量项目与评选覆盖','','| 项目 | 类型 | 收录日期 | 评选状态 |','|---|---|---|---|']
    for p in month['projects']:
        state = '参与两榜评分' if p['eligible'] else '未参评：'+p['exclusion_reason']
        lines.append(f"| [{safe(p['name'])}]({p['url']}) | {p['category']} | {', '.join(p['dates'])} | {safe(state)} |")
    lines+=['','## 原始日报','','- '+ '\n- '.join(f"[日报 {d}](https://luckye1120.github.io/ai-project-daily/#date={d})" for d in month['report_dates']) if month['report_dates'] else '本月无归档日报。','']
    return '\n'.join(lines)

def collect_monthlies(reports):
    from build import markdown
    completed={}
    for path in sorted((ROOT/'monthlies').glob('*.json')):
        m=json.loads(path.read_text())
        if m.get('status')!='published' or path.stem!=m.get('month'):
            raise ValueError('Invalid published monthly report: '+str(path))
        if not (ROOT/'monthlies'/m['filename']).exists():
            raise ValueError('Monthly Markdown is missing')
        if (ROOT/'monthlies'/m['filename']).read_text() != m['text']:
            raise ValueError('Monthly Markdown and reviewed snapshot disagree')
        m['html']=markdown(m['text'])
        completed[m['month']]=m
    for month in {r['date'][:7] for r in reports}:
        if month not in completed:
            completed[month]=snapshot(reports,month)
    return sorted(completed.values(),key=lambda m:m['month'],reverse=True)

def main():
    from build import collect
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--month',help='YYYY-MM; defaults to previous month in Asia/Shanghai')
    parser.add_argument('--as-of',help='Validation date YYYY-MM-DD; defaults to today in Asia/Shanghai')
    parser.add_argument('--review',type=Path,help='Publish a completed month using an editorial review JSON')
    args=parser.parse_args()
    today=date.fromisoformat(args.as_of) if args.as_of else datetime.now(ZoneInfo('Asia/Shanghai')).date()
    sample=snapshot(collect(),args.month or previous_month(today))
    if args.review:
        result=finalize(sample,json.loads(args.review.read_text()),today)
        folder=ROOT/'monthlies'; folder.mkdir(exist_ok=True)
        (folder/(sample['month']+'.json')).write_text(json.dumps(result,ensure_ascii=False,indent=2))
        (folder/result['filename']).write_text(result['text'])
        print('Published monthly files: '+result['filename'])
    else:
        folder=ROOT/'monthly_work'; folder.mkdir(exist_ok=True)
        (folder/(sample['month']+'-candidates.json')).write_text(json.dumps(sample,ensure_ascii=False,indent=2))
        review={'month':sample['month'],'source_fingerprint':sample['source_fingerprint'],'summary':'','insights':[],'projects':{p['key']:{'category':p['category'],'eligible':False,'exclusion_reason':'','idea_scores':[1,1,1],'value_scores':[1,1,1],'idea_reason':'','value_reason':'','trial':'','caveat':'','evidence_level':'','evidence':[]} for p in sample['projects']}}
        target=folder/(sample['month']+'-review.json')
        if not target.exists(): target.write_text(json.dumps(review,ensure_ascii=False,indent=2))
        print(f"Prepared {sample['month']}: {sample['project_count']} projects; review at {target}")

if __name__=='__main__':
    main()

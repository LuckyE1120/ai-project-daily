"""Build the static reading site from reports/*.md using Python's standard library."""
import html
import hashlib
import json
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DIST = ROOT / 'dist'

def inline(text):
    text = html.escape(text)
    tokens = []
    def token(value):
        tokens.append(value)
        return f'\x00{len(tokens)-1}\x00'
    text = re.sub(r'`([^`]+)`', lambda m: token('<code>'+m[1]+'</code>'), text)
    def link(label, url):
        if url.startswith('./') and url.endswith('.md'):
            date = re.search(r'\d{4}-\d{2}-\d{2}', url)
            return token(f'<a href="#date={date[0]}">{label}</a>') if date else label
        if not re.match(r'^https?://', url):
            return label
        return token(f'<a href="{url}" target="_blank" rel="noopener noreferrer">{label} ↗</a>')
    text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', lambda m: link(m[1], m[2]), text)
    text = re.sub(r'&lt;(https?://[^\s]+?)&gt;', lambda m: link(m[1], m[1]), text)
    text = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', text)
    return re.sub(r'\x00(\d+)\x00', lambda m: tokens[int(m[1])], text)

def markdown(text):
    lines = text.splitlines()
    output, i = [], 0
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
            continue
        if line.startswith('```'):
            code = []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith('```'):
                code.append(lines[i]); i += 1
            output.append('<pre><code>'+html.escape('\n'.join(code))+'</code></pre>')
        elif line.startswith('|') and i+1 < len(lines) and re.match(r'^\|[\s:|\-]+\|$', lines[i+1].strip()):
            cells = lambda row: [inline(c.strip()) for c in row.strip().strip('|').split('|')]
            headers = cells(line)
            i += 2
            rows = []
            while i < len(lines) and lines[i].strip().startswith('|'):
                rows.append('<tr>'+''.join('<td>'+v+'</td>' for v in cells(lines[i]))+'</tr>'); i += 1
            output.append('<div class="table-scroll" tabindex="0" aria-label="可横向滚动的项目表格"><table><thead><tr>'+''.join('<th scope="col">'+h+'</th>' for h in headers)+'</tr></thead><tbody>'+''.join(rows)+'</tbody></table></div>')
            continue
        elif re.match(r'^#{1,6} ', line):
            level = min(len(line.split(' ')[0])+1, 6)
            output.append(f'<h{level}>'+inline(line.split(' ',1)[1])+f'</h{level}>')
        elif line.startswith('- '):
            items = []
            while i < len(lines) and lines[i].strip().startswith('- '):
                items.append('<li>'+inline(lines[i].strip()[2:])+'</li>'); i += 1
            output.append('<ul>'+''.join(items)+'</ul>')
            continue
        elif line.startswith('> '):
            output.append('<blockquote>'+inline(line[2:])+'</blockquote>')
        else:
            para = [line]; i += 1
            while i < len(lines) and lines[i].strip() and not re.match(r'^(#|\||```|- |> )',lines[i].strip()):
                para.append(lines[i].strip()); i += 1
            output.append('<p>'+inline(' '.join(para))+'</p>')
            continue
        i += 1
    return '\n'.join(output)

def extract_projects(text, all_tables=False):
    projects = []
    in_first_table = False
    for line in text.splitlines():
        if line.startswith('|'):
            in_first_table = True
            cells = [c.strip() for c in line.strip('|').split('|')]
            name = re.search(r'\[([^]]+)\]\((https://github.com/[^)]+)\)', cells[0])
            if name and len(cells) >= 3:
                projects.append({'name': name[1], 'url': name[2], 'description': cells[1], 'signal': cells[2]})
        elif in_first_table and not all_tables:
            break
    return projects

def collect():
    reports = []
    for path in sorted((ROOT/'reports').glob('*.md'), reverse=True):
        match = re.search(r'\d{4}-\d{2}-\d{2}',path.name)
        if not match:
            raise ValueError(f'Report filename needs date: {path.name}')
        text = path.read_text()
        projects = extract_projects(text)
        title = text.splitlines()[0].lstrip('# ')
        date = match[0]
        reports.append({'date':date,'title':title,'filename':path.name,'text':text,'html':markdown(text),'projects':projects,'observations':extract_projects(text, all_tables=True)})
    reports.sort(key=lambda r:r['date'],reverse=True)
    if len({r['date'] for r in reports}) != len(reports):
        raise ValueError('Only one report per date is supported')
    return reports

def build():
    import monthly
    reports = collect()
    if not reports:
        raise ValueError('At least one report is required')
    DIST.mkdir(exist_ok=True)
    for name in ['index.html','style.css','app.js']:
        shutil.copy2(ROOT/'web'/name,DIST/name)
    # Inline data keeps local-file preview and private hosting independent of fetch routing.
    data = json.dumps(reports,ensure_ascii=False).replace('<','\\u003c')
    template = (DIST/'index.html').read_text()
    for asset in ['style.css','app.js']:
        version = hashlib.sha256((DIST/asset).read_bytes()).hexdigest()[:12]
        template = template.replace('./'+asset, './'+asset+'?v='+version)
    months = monthly.collect_monthlies(reports)
    month_data = json.dumps(months,ensure_ascii=False).replace('<','\\u003c')
    (DIST/'index.html').write_text(template.replace('/* REPORT_DATA */',data).replace('/* MONTH_DATA */',month_data))
    if (DIST/'reports').exists():
        shutil.rmtree(DIST/'reports')
    shutil.copytree(ROOT/'reports',DIST/'reports')
    if (DIST/'monthlies').exists():
        shutil.rmtree(DIST/'monthlies')
    shutil.copytree(ROOT/'monthlies',DIST/'monthlies')
    (DIST/'data.json').write_text(json.dumps(reports,ensure_ascii=False,indent=2))
    (DIST/'monthly-data.json').write_text(json.dumps(months,ensure_ascii=False,indent=2))
    print(f'Built {len(reports)} reports, {len({p["url"] for r in reports for p in r["projects"]})} projects → dist/')

if __name__ == '__main__':
    build()

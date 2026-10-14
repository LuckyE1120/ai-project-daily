from copy import deepcopy
from datetime import date
import unittest
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import monthly

def report(day, projects, followups=None):
    return {'date':day,'filename':day+'.md','text':str(projects),'projects':projects,'observations':followups or []}

def project(name, url):
    return {'name':name,'url':url,'description':'可验证的工具用途','signal':'第三方热度，不参与排名'}

def sample():
    return monthly.snapshot([
        report('2026-10-03',[project('A','https://github.com/a/one'),project('B','https://github.com/b/two')]),
        report('2026-10-04',[project('C','https://github.com/c/three')],[project('A','https://github.com/A/One/')]),
        report('2026-11-01',[project('D','https://github.com/d/four')]),
    ],'2026-10',{'a/one':'自动化测试','b/two':'音视频创作','c/three':'设计与可视化'})

def review_for(s):
    return {'month':s['month'],'source_fingerprint':s['source_fingerprint'],'summary':'样本内的编辑分析','insights':['两个自然日的有限样本'], 'projects':{
        p['key']:{'category':p['category'],'eligible':True,'idea_scores':([5,5,5] if p['key']=='a/one' else [3,3,3]),'value_scores':([5,5,5] if p['key']=='b/two' else [3,3,3]),'idea_reason':'设计思路有明确来源','value_reason':'对应具体任务','trial':'用一个小任务验证','caveat':'尚未安装实测','evidence_level':'官方说明已核验，未实测','evidence':[{'url':p['url'],'note':'官方仓库','checked_at':'2026-11-01'}]}
        for p in s['projects']}}

class MonthlyTests(unittest.TestCase):
    def test_year_boundary_and_leap_year(self):
        self.assertEqual(monthly.previous_month(date(2027,1,1)),'2026-12')
        self.assertEqual(monthly.previous_month(date(2024,3,1)),'2024-02')

    def test_deduplicates_followups_and_excludes_next_month(self):
        s=sample()
        self.assertEqual(s['project_count'],3)
        self.assertEqual(s['report_count'],2)
        self.assertEqual(s['coverage'],6.5)
        self.assertEqual(s['projects'][0]['dates'],['2026-10-03','2026-10-04'])
        self.assertEqual(sum(c['count'] for c in s['categories']),3)

    def test_independent_top_lists_and_evidence_rendering(self):
        s=sample(); m=monthly.finalize(s,review_for(s),date(2026,11,1))
        self.assertEqual(m['idea_top'][0]['key'],'a/one')
        self.assertEqual(m['value_top'][0]['key'],'b/two')
        self.assertEqual(m['idea_top'][0]['idea_score'],100)
        self.assertIn('核验 2026-11-01',m['text'])
        self.assertIn('#date=2026-10-03',m['text'])

    def test_current_month_cannot_be_published(self):
        s=sample()
        with self.assertRaisesRegex(ValueError,'completed'):
            monthly.finalize(s,review_for(s),date(2026,10,14))

    def test_stale_incomplete_and_unsupported_reviews_rejected(self):
        s=sample(); r=review_for(s)
        r['source_fingerprint']='stale'
        with self.assertRaisesRegex(ValueError,'snapshot'):
            monthly.finalize(s,r,date(2026,11,1))
        r=review_for(s); r['projects'].pop('a/one')
        with self.assertRaisesRegex(ValueError,'every'):
            monthly.finalize(s,r,date(2026,11,1))
        r=review_for(s); r['projects']['a/one']['evidence']=[]
        with self.assertRaisesRegex(ValueError,'Evidence'):
            monthly.finalize(s,r,date(2026,11,1))
        for values in [[6,2,3],[True,2,3],[1,2],None]:
            with self.assertRaises(ValueError): monthly.score(values,'idea')

    def test_no_forced_awards_when_evidence_is_insufficient(self):
        s=sample(); r=review_for(s)
        for entry in r['projects'].values():
            entry.update(eligible=False,exclusion_reason='官方资料不足')
        m=monthly.finalize(s,r,date(2026,11,1))
        self.assertEqual(m['idea_top'],[])
        self.assertEqual(m['value_top'],[])
        self.assertIn('不强行补足名额',m['text'])

    def test_empty_month_is_explicit(self):
        s=monthly.snapshot([],'2026-09',{})
        r={'month':s['month'],'source_fingerprint':s['source_fingerprint'],'summary':'本月无归档资料','insights':[],'projects':{}}
        m=monthly.finalize(s,r,date(2026,10,1))
        self.assertEqual(m['project_count'],0)
        self.assertEqual(m['categories'],[])

    def test_star_signal_does_not_change_ranking(self):
        s=sample(); r=review_for(s)
        baseline=monthly.finalize(s,r,date(2026,11,1))
        inflated=deepcopy(s)
        for p in inflated['projects']: p['signal']='一亿 Star（测试数据）'
        changed=monthly.finalize(inflated,r,date(2026,11,1))
        self.assertEqual([p['key'] for p in baseline['idea_top']],[p['key'] for p in changed['idea_top']])

    def test_published_snapshot_and_markdown_are_loaded_together(self):
        s=sample(); m=monthly.finalize(s,review_for(s),date(2026,11,1))
        with TemporaryDirectory() as directory:
            root=Path(directory); (root/'monthlies').mkdir()
            (root/'monthlies'/'2026-10.json').write_text(json.dumps(m))
            (root/'monthlies'/m['filename']).write_text(m['text'])
            with patch.object(monthly,'ROOT',root):
                loaded=monthly.collect_monthlies([])
            self.assertEqual(len(loaded),1)
            self.assertEqual(loaded[0]['status'],'published')
            self.assertIn('最有想法',loaded[0]['html'])
            self.assertEqual(loaded[0]['idea_top'][0]['name'],'A')

    def test_rankings_are_limited_to_three(self):
        s=sample()
        fourth={**s['projects'][0],'key':'d/four','name':'D','url':'https://github.com/d/four'}
        s['projects'].append(fourth); s['project_count']=4
        m=monthly.finalize(s,review_for(s),date(2026,11,1))
        self.assertEqual(len(m['idea_top']),3)
        self.assertEqual(len(m['value_top']),3)

if __name__=='__main__': unittest.main()

import json
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import build

class BuildTests(unittest.TestCase):
    def test_inline_does_not_allow_markup_or_javascript_links(self):
        result = build.inline('<script>alert(1)</script> [bad](javascript:alert)')
        self.assertNotIn('<script>',result)
        self.assertNotIn('href="javascript:',result)

    def test_cross_report_navigation_and_sources(self):
        result = build.inline('[昨日](./AI项目日报-2026-10-13.md) <https://github.com/a/b>')
        self.assertIn('href="#date=2026-10-13"',result)
        self.assertIn('href="https://github.com/a/b"',result)

    def test_code_and_tables_render(self):
        result = build.markdown('| 项目 | 用途 |\n|---|---|\n| A | B |\n\n```bash\nnpx test <arg>\n```')
        self.assertIn('<td>A</td>',result)
        self.assertIn('npx test &lt;arg&gt;',result)
        self.assertIn('tabindex="0"',result)

    def test_all_reports_present_in_build(self):
        reports = build.collect()
        self.assertTrue(reports)
        self.assertEqual(reports,sorted(reports,key=lambda r:r['date'],reverse=True))
        built = json.loads((build.DIST/'data.json').read_text())
        self.assertEqual(built,reports)
        for report in reports:
            self.assertTrue(report['projects'])
            self.assertEqual((build.DIST/'reports'/report['filename']).read_text(),report['text'])

if __name__ == '__main__':
    unittest.main()

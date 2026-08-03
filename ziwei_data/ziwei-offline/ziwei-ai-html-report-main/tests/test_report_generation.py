import json
import pathlib
import re
import subprocess
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import generate_report as gr  # noqa: E402
import render_prompts as rp  # noqa: E402
import report_validators as rv  # noqa: E402
import ziwei_offline as zw  # noqa: E402

FILLER = (
    "依据命宫主星与三方四正，结合福德宫性情、官禄宫事业、财帛宫财源、夫妻宫情感、"
    "迁移宫外出、交友宫人脉、疾厄宫体质，吉凶并陈并给出可执行建议。"
) * 12


def _make_natal_html(chart: dict) -> str:
    life = chart["lifePalace"]
    parts = [
        "<h3>壹· 命格总断</h3>",
        f"<ul><li><strong>格局层次</strong>：{life['name']}在{life['branch']}宫，{FILLER}</li>"
        f"<li><strong>性情剖析</strong>：福德宫、命宫互参，{FILLER}</li></ul>",
        "<h3>贰· 事业与财运</h3>",
        f"<ul><li><strong>官禄方向</strong>：官禄宫主星定行业，{FILLER}</li>"
        f"<li><strong>财运机缘</strong>：财帛宫见禄忌，{FILLER}</li></ul>",
        "<h3>叁· 婚姻与情感</h3>",
        f"<ul><li><strong>姻缘概况</strong>：夫妻宫星情，{FILLER}</li>"
        f"<li><strong>相处之道</strong>：身宫提示，{FILLER}</li></ul>",
        "<h3>肆· 六亲与人际</h3>",
        f"<ul><li><strong>人际关系</strong>：迁移宫、交友宫，{FILLER}</li>"
        f"<li><strong>家庭关系</strong>：父母子女缘，{FILLER}</li></ul>",
        "<h3>伍· 运势隐忧与建议</h3>",
        f"<ul><li><strong>健康提醒</strong>：疾厄宫体质，{FILLER}</li>"
        f"<li><strong>趋吉避凶</strong>：化忌落点，{FILLER}</li></ul>",
        "<h3>陆· 命格金句</h3>",
        f"<blockquote>命在宫，势在运，{FILLER}</blockquote>",
    ]
    return "\n".join(parts)


def _make_yearly_html(chart: dict, year: int) -> str:
    yearly = chart["yearly"]
    decadal = yearly["currentDecadal"]
    return "\n".join([
        f"<h3>壹· 年度总象</h3><ul><li><strong>流年定调</strong>：{year}年关键词。</li>"
        f"<li><strong>核心际遇</strong>：流年命宫叠宫至{yearly['palaceName']}，"
        f"流年四化：{'、'.join(yearly['mutagens'])}；当前大限四化：{'、'.join(decadal['mutagens'])}。"
        f"{FILLER}</li></ul>",
        f"<h3>贰· 名利机缘</h3><ul><li><strong>事业走势</strong>：官禄宫，{FILLER}</li>"
        f"<li><strong>求财建议</strong>：财帛宫，{FILLER}</li></ul>",
        f"<h3>叁· 情感与家宅</h3><ul><li><strong>流年姻缘</strong>：夫妻宫，{FILLER}</li>"
        f"<li><strong>家宅平安</strong>：田宅宫，{FILLER}</li></ul>",
        f"<h3>肆· 月令趋势</h3><ul><li><strong>吉运月份</strong>：农历三月宜签约；九月宜进修。</li>"
        f"<li><strong>注意月份</strong>：农历六月忌冲动投资；十二月注意作息。</li></ul>",
        f"<h3>伍· 锦囊寄语</h3><ul><li><strong>行事准则</strong>：宜守不宜攻。</li>"
        f"<li><strong>关键提醒</strong>：关注健康与咽喉。{FILLER}</li></ul>",
    ])


class ReportGenerationTests(unittest.TestCase):
    def setUp(self):
        self.chart = zw.generate_chart(
            1996, 1, 6, 11, "female", 2026, minute=30, use_true_solar_time=False
        )
        self.payload = zw.build_payload(self.chart, 2026)
        self.kline = self.payload["klineData"]
        self.natal_html = _make_natal_html(self.chart)
        self.yearly_html = _make_yearly_html(self.chart, 2026)

    def test_assemble_report_produces_valid_html(self):
        template = (ROOT / "report-template.html").read_text(encoding="utf-8")
        html = gr.assemble_report(
            template, self.chart, 2026, self.natal_html, self.yearly_html, self.kline
        )
        ok, errors = rv.validate_report_inputs(
            chart=self.chart,
            natal_html=self.natal_html,
            yearly_html=self.yearly_html,
            kline_rows=self.kline,
            assembled_html=html,
        )
        self.assertTrue(ok, msg=errors)
        self.assertIn("<!DOCTYPE html>", html)
        self.assertIn("术数推演仅供参考", html)
        self.assertIn('"palaces":', html)
        self.assertIn('"age":1', html)
        self.assertNotIn('"engine":', html)
        self.assertNotIn('"brightnessSource":', html)
        self.assertNotIn('id="meta-engine"', html)
        self.assertNotIn('id="meta-brightness-source"', html)
        self.assertNotIn("排盘：", html)
        self.assertNotIn("亮度：", html)

    def test_chart_embed_omits_engine_and_brightness_metadata(self):
        embed = gr.build_chart_embed(self.chart, 2026)
        self.assertNotIn("engine", embed)
        self.assertNotIn("engineVersion", embed)
        self.assertNotIn("brightnessSource", embed)

    def test_merge_kline_briefs_does_not_override_ohlc(self):
        original = self.kline[0]
        merged = gr.merge_kline_briefs(
            [original],
            [{"age": 1, "brief": "新文案", "reason": "工具定数", "open": 0, "close": 0}],
        )

        self.assertEqual(merged[0]["open"], original["open"])
        self.assertEqual(merged[0]["close"], original["close"])
        self.assertEqual(merged[0]["brief"], "新文案")
        self.assertEqual(merged[0]["reason"], "工具定数")

    def test_cli_uses_payload_kline_data_without_kline_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = pathlib.Path(tmp)
            payload = tmp_path / "payload.json"
            natal = tmp_path / "natal.html"
            yearly = tmp_path / "yearly.html"
            brief = tmp_path / "kline-brief.json"
            out = tmp_path / "out.html"
            payload.write_text(json.dumps(self.payload, ensure_ascii=False), encoding="utf-8")
            natal.write_text(self.natal_html, encoding="utf-8")
            yearly.write_text(self.yearly_html, encoding="utf-8")
            brief.write_text(json.dumps([{"age": 1, "brief": "平稳起步"}], ensure_ascii=False), encoding="utf-8")

            proc = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "tools" / "generate_report.py"),
                    "--payload-json",
                    str(payload),
                    "--natal-html",
                    str(natal),
                    "--yearly-html",
                    str(yearly),
                    "--kline-brief-json",
                    str(brief),
                    "-o",
                    str(out),
                ],
                text=True,
                capture_output=True,
                cwd=ROOT,
            )

            self.assertEqual(proc.returncode, 0, msg=proc.stderr)
            html = out.read_text(encoding="utf-8")
            self.assertIn('"brief":"平稳起步"', html)
            self.assertIn('"open":50.0', html)

    def test_cli_rejects_invalid_kline(self):
        bad_kline = self.kline[:99]
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = pathlib.Path(tmp)
            natal = tmp_path / "natal.html"
            yearly = tmp_path / "yearly.html"
            kline = tmp_path / "kline.json"
            out = tmp_path / "out.html"
            natal.write_text(self.natal_html, encoding="utf-8")
            yearly.write_text(self.yearly_html, encoding="utf-8")
            kline.write_text(json.dumps(bad_kline), encoding="utf-8")
            proc = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "tools" / "generate_report.py"),
                    "--solar",
                    "1996-01-06",
                    "--time",
                    "11:30",
                    "--gender",
                    "female",
                    "--target-year",
                    "2026",
                    "--natal-html",
                    str(natal),
                    "--yearly-html",
                    str(yearly),
                    "--kline-json",
                    str(kline),
                    "-o",
                    str(out),
                ],
                text=True,
                capture_output=True,
                cwd=ROOT,
            )
            self.assertEqual(proc.returncode, 2)
            self.assertIn("100", proc.stderr)


class DangerousHtmlValidatorTests(unittest.TestCase):
    def setUp(self):
        self.chart = zw.generate_chart(
            1996, 1, 6, 11, "female", 2026, minute=30, use_true_solar_time=False
        )
        self.natal_html = _make_natal_html(self.chart)
        self.yearly_html = _make_yearly_html(self.chart, 2026)
        self.kline = zw.build_payload(self.chart, 2026)["klineData"]

    def test_rejects_script_tag_in_natal_fragment(self):
        bad = self.natal_html + '<script>alert(1)</script>'
        ok, msg = rv.validate_safe_html_fragment(bad, label="综合批注")
        self.assertFalse(ok)
        self.assertIn("<script>", msg)

    def test_rejects_event_handler_in_yearly_fragment(self):
        bad = '<img src="x" onerror="alert(1)">' + self.yearly_html
        ok, msg = rv.validate_safe_html_fragment(bad, label="流年报告")
        self.assertFalse(ok)
        self.assertIn("事件属性", msg)

    def test_rejects_javascript_url_in_fragment(self):
        bad = self.natal_html + '<a href="javascript:alert(1)">x</a>'
        ok, msg = rv.validate_safe_html_fragment(bad, label="综合批注")
        self.assertFalse(ok)
        self.assertIn("javascript:", msg)

    def test_report_inputs_reject_dangerous_natal_html(self):
        bad = self.natal_html + "<script></script>"
        ok, errors = rv.validate_report_inputs(
            chart=self.chart,
            natal_html=bad,
            yearly_html=self.yearly_html,
            kline_rows=self.kline,
        )
        self.assertFalse(ok)
        self.assertTrue(any("综合批注" in e and "<script>" in e for e in errors))

    def test_assembled_html_rejects_external_script_src(self):
        template = (ROOT / "report-template.html").read_text(encoding="utf-8")
        html = gr.assemble_report(
            template, self.chart, 2026, self.natal_html, self.yearly_html, self.kline
        )
        injected = html.replace(
            "</body>",
            '<script src="https://evil.example/x.js"></script></body>',
            1,
        )
        ok, msg = rv.validate_html_delivery(injected)
        self.assertFalse(ok)
        self.assertIn("外链脚本", msg)

    def test_valid_fragments_pass_safe_html_check(self):
        for fragment, label in (
            (self.natal_html, "综合批注"),
            (self.yearly_html, "流年报告"),
        ):
            ok, msg = rv.validate_safe_html_fragment(fragment, label=label)
            self.assertTrue(ok, msg=msg)


class EndToEndReportWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.chart = zw.generate_chart(
            1996, 1, 6, 11, "female", 2026, minute=30, use_true_solar_time=False
        )
        self.payload = zw.build_payload(self.chart, 2026)
        self.natal_html = _make_natal_html(self.chart)
        self.yearly_html = _make_yearly_html(self.chart, 2026)

    def test_payload_render_generate_pipeline(self):
        with tempfile.TemporaryDirectory() as tmp:
            work = pathlib.Path(tmp)
            payload_path = work / "payload.json"
            payload_path.write_text(
                json.dumps(self.payload, ensure_ascii=False), encoding="utf-8"
            )

            rp.render_all_prompts(self.payload, work, work_root=work)
            self.assertTrue((work / "prompt-manifest.json").exists())
            self.assertTrue((work / "prompts" / "natal.system.md").exists())

            (work / "natal.html").write_text(self.natal_html, encoding="utf-8")
            (work / "yearly.html").write_text(self.yearly_html, encoding="utf-8")
            (work / "kline-brief.json").write_text(
                json.dumps([{"age": 1, "brief": "平稳起步"}], ensure_ascii=False),
                encoding="utf-8",
            )
            out = work / "report.html"

            proc = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "tools" / "generate_report.py"),
                    "--payload-json",
                    str(payload_path),
                    "--natal-html",
                    str(work / "natal.html"),
                    "--yearly-html",
                    str(work / "yearly.html"),
                    "--kline-brief-json",
                    str(work / "kline-brief.json"),
                    "-o",
                    str(out),
                ],
                text=True,
                capture_output=True,
                cwd=ROOT,
            )
            self.assertEqual(proc.returncode, 0, msg=proc.stderr)

            html = out.read_text(encoding="utf-8")
            self.assertIn("<!DOCTYPE html>", html)
            self.assertIn('id="content-natal"', html)
            self.assertIn('id="content-yearly"', html)
            self.assertIn('id="chart-data"', html)
            self.assertIn('id="kline-data"', html)
            self.assertIn("壹·", html)
            self.assertIn('"brief":"平稳起步"', html)
            self.assertIn('"open":50.0', html)

            delivery_ok, delivery_msg = rv.validate_html_delivery(html)
            self.assertTrue(delivery_ok, msg=delivery_msg)

            natal_block = re.search(
                r'id="content-natal"[^>]*>([\s\S]*?)</div>',
                html,
            )
            yearly_block = re.search(
                r'id="content-yearly"[^>]*>([\s\S]*?)</div>',
                html,
            )
            self.assertIsNotNone(natal_block)
            self.assertIsNotNone(yearly_block)
            for block in (natal_block.group(1), yearly_block.group(1)):
                self.assertNotRegex(block, r"请填入|\{\{[A-Z_]+\}\}")

            chart_match = re.search(
                r'<script type="application/json" id="chart-data">(.*?)</script>',
                html,
                re.DOTALL,
            )
            kline_match = re.search(
                r'<script type="application/json" id="kline-data">(.*?)</script>',
                html,
                re.DOTALL,
            )
            self.assertIsNotNone(chart_match)
            self.assertIsNotNone(kline_match)
            chart_data = json.loads(chart_match.group(1))
            kline_data = json.loads(kline_match.group(1))
            self.assertEqual(len(chart_data["palaces"]), 12)
            self.assertEqual(len(kline_data), 100)
            self.assertEqual(kline_data[0]["brief"], "平稳起步")

            ok, errors = rv.validate_report_inputs(
                chart=self.chart,
                natal_html=self.natal_html,
                yearly_html=self.yearly_html,
                kline_rows=kline_data,
                assembled_html=html,
            )
            self.assertTrue(ok, msg=errors)


if __name__ == "__main__":
    unittest.main()

import json
import pathlib
import shutil
import subprocess
import sys
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
SEMANTIC_FILE = ROOT / "tools" / "knowledge_semantics.json"
DOC_FILES = [
    ROOT / "README.md",
    ROOT / "SKILL.md",
    ROOT / "prompts.md",
    ROOT / "RULE_MATRIX.md",
]
sys.path.insert(0, str(ROOT / "tools"))

import ziwei_offline as zw  # noqa: E402


def run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(ROOT / "tools" / "ziwei_offline.py"), *args],
        text=True,
        capture_output=True,
    )


class LunarCalendarTests(unittest.TestCase):
    def test_converts_chinese_new_year_2024(self):
        lunar = zw.solar_to_lunar(2024, 2, 10)

        self.assertEqual((lunar.year, lunar.month, lunar.day, lunar.is_leap), (2024, 1, 1, False))

    def test_converts_2020_leap_fourth_month(self):
        lunar = zw.solar_to_lunar(2020, 5, 23)

        self.assertEqual((lunar.year, lunar.month, lunar.day, lunar.is_leap), (2020, 4, 1, True))

    def test_late_zi_hour_advances_lunar_day(self):
        chart = zw.generate_chart(2024, 2, 9, 23, "male", target_year=2026)

        self.assertEqual((chart["lunar"]["year"], chart["lunar"]["month"], chart["lunar"]["day"]), (2024, 1, 1))
        self.assertEqual(chart["birth"]["timeBranch"], "子")
        self.assertTrue(chart["birth"]["lateZi"])


class CorePlacementTests(unittest.TestCase):
    def test_life_and_body_palace_examples_match_algorithm_docs(self):
        self.assertEqual(zw.life_palace_branch(5, 2), "辰")
        self.assertEqual(zw.body_palace_branch(5, 2), "申")

    def test_leap_month_placement_uses_next_month_after_day_15(self):
        self.assertEqual(zw.effective_lunar_month_for_placement(zw.LunarDate(2020, 4, 15, True)), 4)
        self.assertEqual(zw.effective_lunar_month_for_placement(zw.LunarDate(2020, 4, 16, True)), 5)

    def test_ziwei_position_examples_match_algorithm_docs(self):
        self.assertEqual(zw.ziwei_position(22, 3), "亥")
        self.assertEqual(zw.ziwei_position(27, 4), "未")

    def test_major_star_series_from_documented_midday_example(self):
        stars = zw.arrange_major_stars("午")

        self.assertEqual(stars["紫微"], "午")
        self.assertEqual(stars["天机"], "巳")
        self.assertEqual(stars["太阳"], "卯")
        self.assertEqual(stars["天府"], "戌")

    def test_major_star_placements_match_iztro_golden_cases(self):
        cases = [
            (
                (1996, 1, 6, 11, 30, "female"),
                {
                    "财帛宫": [],
                    "子女宫": [],
                    "夫妻宫": ["天同"],
                    "兄弟宫": ["武曲", "破军"],
                    "命宫": ["太阳"],
                    "父母宫": ["天府"],
                    "福德宫": ["天机", "太阴"],
                    "田宅宫": ["紫微", "贪狼"],
                    "官禄宫": ["巨门"],
                    "交友宫": ["天相"],
                    "迁移宫": ["天梁"],
                    "疾厄宫": ["廉贞", "七杀"],
                },
            ),
            (
                (1990, 1, 1, 12, 0, "male"),
                {
                    "疾厄宫": ["紫微", "天府"],
                    "财帛宫": ["太阴"],
                    "子女宫": ["贪狼"],
                    "夫妻宫": ["巨门"],
                    "兄弟宫": ["廉贞", "天相"],
                    "命宫": ["天梁"],
                    "父母宫": ["七杀"],
                    "福德宫": ["天同"],
                    "田宅宫": ["武曲"],
                    "官禄宫": ["太阳"],
                    "交友宫": ["破军"],
                    "迁移宫": ["天机"],
                },
            ),
            (
                (2024, 2, 10, 0, 30, "male"),
                {
                    "命宫": [],
                    "父母宫": [],
                    "福德宫": ["天同"],
                    "田宅宫": ["武曲", "破军"],
                    "官禄宫": ["太阳"],
                    "交友宫": ["天府"],
                    "迁移宫": ["天机", "太阴"],
                    "疾厄宫": ["紫微", "贪狼"],
                    "财帛宫": ["巨门"],
                    "子女宫": ["天相"],
                    "夫妻宫": ["天梁"],
                    "兄弟宫": ["廉贞", "七杀"],
                },
            ),
            (
                (1988, 8, 8, 23, 30, "female"),
                {
                    "疾厄宫": ["天机", "太阴"],
                    "财帛宫": ["紫微", "贪狼"],
                    "子女宫": ["巨门"],
                    "夫妻宫": ["天相"],
                    "兄弟宫": ["天梁"],
                    "命宫": ["廉贞", "七杀"],
                    "父母宫": [],
                    "福德宫": [],
                    "田宅宫": ["天同"],
                    "官禄宫": ["武曲", "破军"],
                    "交友宫": ["太阳"],
                    "迁移宫": ["天府"],
                },
            ),
        ]
        for (year, month, day, hour, minute, gender), expected in cases:
            with self.subTest(year=year, month=month, day=day, hour=hour, minute=minute, gender=gender):
                chart = zw.generate_chart(
                    year,
                    month,
                    day,
                    hour,
                    gender,
                    target_year=2026,
                    minute=minute,
                    use_true_solar_time=False,
                )
                actual = {
                    palace["name"]: [star["name"] for star in palace["majorStars"]]
                    for palace in chart["palaces"]
                }
                self.assertEqual(actual, expected)

    def test_auxiliary_stars_includes_tianma(self):
        stars = zw.auxiliary_stars(lunar_month=1, hour_idx=0, year_stem="甲", year_branch="午")
        self.assertEqual(stars["天马"], "申")

    def test_sihua_table_matches_reference(self):
        self.assertEqual(zw.SIHUA_TABLE["甲"]["化禄"], "廉贞")
        self.assertEqual(zw.SIHUA_TABLE["辛"]["化忌"], "文昌")

    def test_decadal_direction_yang_male_and_yang_female(self):
        forward = zw.decadal_ranges("寅", 3, "甲", "male")
        backward = zw.decadal_ranges("寅", 3, "甲", "female")
        self.assertEqual(forward["寅"], "3-12")
        self.assertEqual(forward["卯"], "13-22")
        self.assertEqual(backward["寅"], "3-12")
        self.assertEqual(backward["丑"], "13-22")

    def test_longitude_correction_direction(self):
        self.assertLess(zw.compute_longitude_correction_minutes(113.3), 0)
        self.assertGreater(zw.compute_longitude_correction_minutes(126.0), 0)

    def test_equation_of_time_is_finite(self):
        value = zw.compute_equation_of_time_minutes(zw._dt.date(2026, 1, 6))
        self.assertTrue(isinstance(value, float))
        self.assertGreater(value, -30)
        self.assertLess(value, 30)

    def test_true_solar_time_shifts_by_longitude(self):
        local_dt = zw._dt.datetime(1996, 1, 6, 11, 30)
        true_dt, lng_delta, eot = zw.compute_true_solar_datetime(local_dt, 113.2932)
        self.assertLess(lng_delta, 0)
        self.assertLess((true_dt - local_dt).total_seconds(), 0)
        self.assertTrue(isinstance(eot, float))

    def test_geocode_hybrid_falls_back_to_offline(self):
        original = zw._geocode_online
        try:
            zw._geocode_online = lambda _: None
            lng, lat, src = zw.resolve_coordinates("广东省佛山市顺德区", None, None, geocode_mode="hybrid")
            self.assertEqual(src, "offline")
            self.assertAlmostEqual(lng, 113.2932, places=3)
            self.assertAlmostEqual(lat, 22.8054, places=3)
        finally:
            zw._geocode_online = original

    def test_true_solar_time_can_change_hour_branch(self):
        chart = zw.generate_chart(
            1996,
            1,
            6,
            23,
            "female",
            target_year=2026,
            minute=30,
            longitude=113.2932,
            latitude=22.8054,
            use_true_solar_time=True,
        )
        self.assertEqual(chart["birth"]["timeBranch"], "亥")
        self.assertFalse(chart["birth"]["lateZi"])

    def test_location_fallbacks_cover_virtual_profile_birthplaces(self):
        for birthplace in [
            "北京市",
            "上海市",
            "广东省佛山市顺德区",
            "深圳市",
            "杭州市",
            "成都市",
            "喀什市",
            "拉萨市",
            "哈尔滨市",
            "乌鲁木齐市",
            "厦门市",
            "海口市",
            "重庆市",
            "兰州市",
            "大连市",
        ]:
            with self.subTest(birthplace=birthplace):
                lng, lat, src = zw.resolve_coordinates(birthplace, None, None, geocode_mode="offline")
                self.assertEqual(src, "offline")
                self.assertIsInstance(lng, float)
                self.assertIsInstance(lat, float)


class IztroAlignmentTests(unittest.TestCase):
    IZTRO_CASES = [
        ("1912-01-01", "00:30", "male"),
        ("1912-06-15", "11:30", "male"),
        ("1912-12-31", "22:30", "female"),
        ("1936-01-01", "00:30", "male"),
        ("1936-06-15", "11:30", "male"),
        ("1936-12-31", "22:30", "female"),
        ("1949-01-01", "00:30", "male"),
        ("1949-06-15", "11:30", "male"),
        ("1949-12-31", "22:30", "female"),
        ("1966-01-01", "00:30", "male"),
        ("1966-06-15", "11:30", "male"),
        ("1966-12-31", "22:30", "female"),
        ("1978-01-01", "00:30", "male"),
        ("1978-06-15", "11:30", "male"),
        ("1978-12-31", "22:30", "female"),
        ("1984-01-01", "00:30", "male"),
        ("1984-06-15", "11:30", "male"),
        ("1984-12-31", "22:30", "female"),
        ("1990-01-01", "00:30", "male"),
        ("1990-06-15", "11:30", "male"),
        ("1990-12-31", "22:30", "female"),
        ("1996-01-01", "00:30", "male"),
        ("1996-06-15", "11:30", "male"),
        ("1996-12-31", "22:30", "female"),
        ("2000-01-01", "00:30", "male"),
        ("2000-06-15", "11:30", "male"),
        ("2000-12-31", "22:30", "female"),
        ("2008-01-01", "00:30", "male"),
        ("2008-06-15", "11:30", "male"),
        ("2008-12-31", "22:30", "female"),
        ("2020-01-01", "00:30", "male"),
        ("2020-06-15", "11:30", "male"),
        ("2020-12-31", "22:30", "female"),
        ("2024-01-01", "00:30", "male"),
        ("2024-06-15", "11:30", "male"),
        ("2024-12-31", "22:30", "female"),
        ("2033-01-01", "00:30", "male"),
        ("2033-06-15", "11:30", "male"),
        ("2050-01-01", "00:30", "male"),
        ("2050-06-15", "11:30", "male"),
        ("2050-12-31", "22:30", "female"),
        ("2077-01-01", "00:30", "male"),
        ("2077-06-15", "11:30", "male"),
        ("2077-12-31", "22:30", "female"),
        ("2099-01-01", "00:30", "male"),
        ("2099-06-15", "11:30", "male"),
        ("2099-12-31", "22:30", "female"),
        ("2020-05-23", "11:30", "male"),
        ("2020-06-06", "11:30", "male"),
        ("2020-06-07", "11:30", "male"),
        ("2020-06-15", "11:30", "male"),
        ("2077-06-15", "11:30", "male"),
    ]
    VIRTUAL_PROFILES = [
        ("林晚舟", "1992-03-18", "06:42", "female", "北京市"),
        ("陈星野", "1987-11-02", "23:18", "male", "上海市"),
        ("许明澈", "2001-05-23", "00:36", "male", "广东省佛山市顺德区"),
        ("周若岚", "1976-08-09", "12:08", "female", "深圳市"),
        ("何知夏", "1999-12-31", "22:54", "female", "杭州市"),
        ("陆远山", "1965-01-14", "04:21", "male", "成都市"),
        ("顾北辰", "1994-07-01", "23:50", "male", "喀什市"),
        ("沈清和", "1982-02-19", "00:12", "female", "拉萨市"),
        ("唐景曜", "1979-10-05", "05:55", "male", "哈尔滨市"),
        ("宋遥", "2004-04-04", "13:27", "female", "乌鲁木齐市"),
        ("叶初宁", "1991-09-28", "21:43", "female", "厦门市"),
        ("赵衡", "1968-12-22", "01:05", "male", "海口市"),
        ("孟青川", "2010-06-06", "15:16", "male", "重庆市"),
        ("韩予安", "1955-03-03", "18:39", "female", "兰州市"),
        ("秦疏影", "2032-11-14", "23:41", "female", "大连市"),
    ]
    RELEASE_AUDIT_PROFILES = [
        ("深圳上午男盘", "1996-03-16", "08:40", "male", "广东省深圳市"),
        ("喀什边界男盘", "1994-07-01", "23:50", "male", "喀什市"),
        ("厦门夜间女盘", "1991-09-28", "21:43", "female", "厦门市"),
    ]

    @classmethod
    def setUpClass(cls):
        if not shutil.which("node"):
            raise unittest.SkipTest("node is required for iztro alignment tests")
        proc = subprocess.run(
            ["node", "-e", "require('iztro')"],
            cwd=ROOT,
            text=True,
            capture_output=True,
        )
        if proc.returncode != 0:
            raise unittest.SkipTest("iztro dependency is not installed")

    @staticmethod
    def _compact_core(chart):
        return {
            "lunar": chart["lunar"],
            "yearGanZhi": chart["yearGanZhi"]["text"],
            "lifePalace": chart["lifePalace"],
            "bodyPalace": chart["bodyPalace"],
            "fiveElementsNumber": chart["fiveElementsNumber"],
            "effectiveSolar": chart["birth"]["effectiveSolar"],
            "timeBranch": chart["birth"]["timeBranch"],
            "majorStars": {
                palace["name"]: [star["name"] for star in palace["majorStars"]]
                for palace in chart["palaces"]
            },
            "minorStars": {
                palace["name"]: [star["name"] for star in palace["minorStars"]]
                for palace in chart["palaces"]
            },
        }

    @staticmethod
    def _load_iztro_chart(solar, time_value, gender):
        iztro = subprocess.run(
            [
                "node",
                str(ROOT / "tools" / "chart_iztro.cjs"),
                "--solar",
                solar,
                "--time",
                time_value,
                "--gender",
                gender,
            ],
            cwd=ROOT,
            check=True,
            text=True,
            capture_output=True,
        )
        proc = subprocess.run(
            [
                sys.executable,
                str(ROOT / "tools" / "ziwei_offline.py"),
                "--from-chart-json",
                "--target-year",
                "2026",
                "--format",
                "json",
            ],
            input=iztro.stdout,
            cwd=ROOT,
            check=True,
            text=True,
            capture_output=True,
        )
        return json.loads(proc.stdout)["chart"]

    @staticmethod
    def _emit_iztro_birth_json(solar, time_value, gender, birthplace):
        return subprocess.run(
            [
                sys.executable,
                str(ROOT / "tools" / "ziwei_offline.py"),
                "--solar",
                solar,
                "--time",
                time_value,
                "--gender",
                gender,
                "--birthplace",
                birthplace,
                "--geocode-mode",
                "offline",
                "--target-year",
                "2026",
                "--emit-iztro-birth-json",
            ],
            cwd=ROOT,
            check=True,
            text=True,
            capture_output=True,
        ).stdout

    def test_offline_python_core_chart_matches_iztro_cases(self):
        for solar, time_value, gender in self.IZTRO_CASES:
            with self.subTest(solar=solar, time=time_value, gender=gender):
                hour, minute = map(int, time_value.split(":"))
                year, month, day = map(int, solar.split("-"))
                offline = zw.generate_chart(
                    year,
                    month,
                    day,
                    hour,
                    gender,
                    target_year=2026,
                    minute=minute,
                    use_true_solar_time=False,
                )
                iztro = self._load_iztro_chart(solar, time_value, gender)
                self.assertEqual(self._compact_core(offline), self._compact_core(iztro))

    def test_chart_iztro_accepts_four_element_class(self):
        chart = self._load_iztro_chart("2024-01-01", "00:30", "male")
        self.assertEqual(chart["fiveElementsNumber"], 4)

    def test_virtual_profiles_with_birthplace_match_iztro_true_solar_pipeline(self):
        for name, solar, time_value, gender, birthplace in self.VIRTUAL_PROFILES:
            with self.subTest(name=name, solar=solar, time=time_value, gender=gender, birthplace=birthplace):
                hour, minute = map(int, time_value.split(":"))
                year, month, day = map(int, solar.split("-"))
                offline = zw.generate_chart(
                    year,
                    month,
                    day,
                    hour,
                    gender,
                    target_year=2026,
                    minute=minute,
                    birthplace=birthplace,
                    geocode_mode="offline",
                )
                birth_json = self._emit_iztro_birth_json(solar, time_value, gender, birthplace)
                iztro = subprocess.run(
                    ["node", str(ROOT / "tools" / "chart_iztro.cjs"), "--birth-json", "-"],
                    input=birth_json,
                    cwd=ROOT,
                    check=True,
                    text=True,
                    capture_output=True,
                )
                proc = subprocess.run(
                    [
                        sys.executable,
                        str(ROOT / "tools" / "ziwei_offline.py"),
                        "--from-chart-json",
                        "--target-year",
                        "2026",
                        "--format",
                        "json",
                    ],
                    input=iztro.stdout,
                    cwd=ROOT,
                    check=True,
                    text=True,
                    capture_output=True,
                )
                chart = json.loads(proc.stdout)["chart"]
                self.assertEqual(offline["birth"]["coordinates"]["source"], "offline")
                self.assertTrue(offline["birth"]["trueSolar"]["applied"])
                self.assertEqual(self._compact_core(offline), self._compact_core(chart))

    def test_release_audit_profiles_match_iztro_true_solar_pipeline(self):
        for name, solar, time_value, gender, birthplace in self.RELEASE_AUDIT_PROFILES:
            with self.subTest(name=name, solar=solar, time=time_value, gender=gender, birthplace=birthplace):
                hour, minute = map(int, time_value.split(":"))
                year, month, day = map(int, solar.split("-"))
                offline = zw.generate_chart(
                    year,
                    month,
                    day,
                    hour,
                    gender,
                    target_year=2026,
                    minute=minute,
                    birthplace=birthplace,
                    geocode_mode="offline",
                )
                birth_json = self._emit_iztro_birth_json(solar, time_value, gender, birthplace)
                iztro = subprocess.run(
                    ["node", str(ROOT / "tools" / "chart_iztro.cjs"), "--birth-json", "-"],
                    input=birth_json,
                    cwd=ROOT,
                    check=True,
                    text=True,
                    capture_output=True,
                )
                proc = subprocess.run(
                    [
                        sys.executable,
                        str(ROOT / "tools" / "ziwei_offline.py"),
                        "--from-chart-json",
                        "--target-year",
                        "2026",
                        "--format",
                        "json",
                    ],
                    input=iztro.stdout,
                    cwd=ROOT,
                    check=True,
                    text=True,
                    capture_output=True,
                )
                chart = json.loads(proc.stdout)["chart"]
                self.assertEqual(self._compact_core(offline), self._compact_core(chart))
                yearly_keys = ("year", "stem", "branch", "mutagens", "palaceName")
                self.assertEqual(
                    {key: offline["yearly"][key] for key in yearly_keys},
                    {key: chart["yearly"][key] for key in yearly_keys},
                )
                decadal_keys = ("age", "palaceName", "branch", "stem", "mutagens")
                self.assertEqual(
                    {key: offline["yearly"]["currentDecadal"][key] for key in decadal_keys},
                    {key: chart["yearly"]["currentDecadal"][key] for key in decadal_keys},
                )
                ok, msg = zw.validate_kline_data(zw.build_payload(chart, 2026)["klineData"])
                self.assertTrue(ok, msg)

    def test_emit_iztro_birth_json_uses_effective_solar_and_time_index(self):
        birth_json = json.loads(self._emit_iztro_birth_json("1987-11-02", "23:18", "male", "上海市"))
        self.assertEqual(birth_json["solarDate"], "1987-11-03")
        self.assertEqual(birth_json["time"], "23:40")
        self.assertEqual(birth_json["timeIndex"], 0)


class ContextOutputTests(unittest.TestCase):
    def test_emit_iztro_birth_json_shape(self):
        proc = run_cli(
            "--solar",
            "1990-01-01",
            "--time",
            "12:00",
            "--gender",
            "male",
            "--target-year",
            "2026",
            "--emit-iztro-birth-json",
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        emit = json.loads(proc.stdout.strip())
        self.assertIn("solarDate", emit)
        self.assertIn("time", emit)
        self.assertEqual(emit.get("gender"), "male")
        self.assertIn("trueSolarApplied", emit)

    def test_from_chart_json_matches_generate_chart_payload(self):
        chart = zw.generate_chart(1990, 1, 1, 12, "male", target_year=2026)
        proc = subprocess.run(
            [sys.executable, str(ROOT / "tools" / "ziwei_offline.py"), "--from-chart-json", "--target-year", "2026", "--format", "json"],
            input=json.dumps(chart, ensure_ascii=False),
            text=True,
            capture_output=True,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        payload = json.loads(proc.stdout)
        ref = zw.build_payload(chart, 2026)
        self.assertIn("natalContext", payload)
        self.assertEqual(payload["natalContext"], ref["natalContext"])

    def test_generate_chart_contains_required_context_blocks(self):
        chart = zw.generate_chart(1990, 1, 1, 12, "male", target_year=2026)
        context = zw.build_prompt_context(chart)
        yearly = zw.build_yearly_context(chart, 2026)

        self.assertEqual(len(chart["palaces"]), 12)
        self.assertEqual(
            sum(1 for p in chart["palaces"] if p.get("isLifePalace")),
            1,
        )
        self.assertIn("fiveElementsClass", chart)
        self.assertIn("【命盘完整信息】", context)
        self.assertIn("## 十二宫星曜分布", context)
        self.assertIn("## 十二大限", context)
        self.assertIn("【流年盘信息】", yearly)
        self.assertIn("## 当前大限", yearly)
        self.assertIn("宫位要点", context)
        self.assertIn("简述：", context)
        self.assertIn("优点：", context)
        self.assertIn("适配场景：", context)
        self.assertIn("来源：docs/rules-baseline.md", context)

    def test_cli_outputs_json(self):
        proc = subprocess.run(
            [
                sys.executable,
                str(ROOT / "tools" / "ziwei_offline.py"),
                "--solar",
                "2024-02-10",
                "--hour",
                "0",
                "--gender",
                "male",
                "--target-year",
                "2026",
                "--format",
                "json",
            ],
            check=True,
            text=True,
            capture_output=True,
        )

        payload = json.loads(proc.stdout)
        self.assertEqual(payload["chart"]["lunar"]["year"], 2024)
        self.assertIn("natalContext", payload)
        self.assertIn("yearlyContext", payload)
        self.assertIn("trueSolar", payload["chart"]["birth"])

    def test_cli_supports_time_and_birthplace(self):
        proc = run_cli(
            "--solar",
            "1996-01-06",
            "--time",
            "11:30",
            "--gender",
            "female",
            "--birthplace",
            "广东省佛山市顺德区",
            "--target-year",
            "2026",
            "--format",
            "json",
        )
        self.assertEqual(proc.returncode, 0, msg=proc.stderr)
        payload = json.loads(proc.stdout)
        birth = payload["chart"]["birth"]
        self.assertEqual(birth["localTime"], "11:30")
        self.assertIn(birth["coordinates"]["source"], {"online", "offline", "manual"})

    def test_cli_accepts_chinese_gender_promised_by_docs(self):
        proc = run_cli(
            "--solar",
            "1996-03-16",
            "--time",
            "08:40",
            "--gender",
            "男",
            "--birthplace",
            "广东省深圳市",
            "--geocode-mode",
            "offline",
            "--target-year",
            "2026",
            "--format",
            "json",
        )
        self.assertEqual(proc.returncode, 0, msg=proc.stderr)
        payload = json.loads(proc.stdout)
        self.assertEqual(payload["chart"]["birth"]["gender"], "male")

    def test_cli_offline_geocode_mode_hits_local_fallback(self):
        proc = run_cli(
            "--solar",
            "1996-01-06",
            "--time",
            "11:30",
            "--gender",
            "female",
            "--birthplace",
            "广东省佛山市顺德区",
            "--geocode-mode",
            "offline",
            "--target-year",
            "2026",
            "--format",
            "json",
        )
        self.assertEqual(proc.returncode, 0, msg=proc.stderr)
        payload = json.loads(proc.stdout)
        self.assertEqual(payload["chart"]["birth"]["coordinates"]["source"], "offline")

    def test_cli_manual_coordinates_override_geocode(self):
        proc = run_cli(
            "--solar",
            "1996-01-06",
            "--time",
            "11:30",
            "--gender",
            "female",
            "--birthplace",
            "广东省佛山市顺德区",
            "--longitude",
            "113.2932",
            "--latitude",
            "22.8054",
            "--target-year",
            "2026",
            "--format",
            "json",
        )
        self.assertEqual(proc.returncode, 0, msg=proc.stderr)
        payload = json.loads(proc.stdout)
        self.assertEqual(payload["chart"]["birth"]["coordinates"]["source"], "manual")

    def test_cli_rejects_invalid_time_shape(self):
        proc = run_cli(
            "--solar",
            "1996-01-06",
            "--time",
            "7:5",
            "--gender",
            "female",
        )
        self.assertEqual(proc.returncode, 2)
        self.assertIn("time 格式必须为 HH:mm", proc.stderr)

    def test_cli_rejects_invalid_time_range(self):
        proc = run_cli(
            "--solar",
            "1996-01-06",
            "--time",
            "11:77",
            "--gender",
            "female",
        )
        self.assertEqual(proc.returncode, 2)
        self.assertIn("time 分钟必须在 00-59 之间", proc.stderr)

    def test_cli_rejects_invalid_hour_range(self):
        proc = run_cli(
            "--solar",
            "1996-01-06",
            "--hour",
            "24",
            "--gender",
            "female",
        )
        self.assertEqual(proc.returncode, 2)
        self.assertIn("hour 必须在 0-23 之间", proc.stderr)

    def test_cli_requires_time_or_hour(self):
        proc = run_cli(
            "--solar",
            "1996-01-06",
            "--gender",
            "female",
        )
        self.assertEqual(proc.returncode, 2)
        self.assertIn("必须提供 --time 或 --hour", proc.stderr)

    def test_cli_rejects_partial_coordinates(self):
        proc = run_cli(
            "--solar",
            "1996-01-06",
            "--time",
            "11:30",
            "--gender",
            "female",
            "--longitude",
            "113.2932",
        )
        self.assertEqual(proc.returncode, 2)
        self.assertIn("longitude 与 latitude 必须同时提供", proc.stderr)

    def test_cli_rejects_out_of_range_date(self):
        proc = run_cli(
            "--solar",
            "1899-12-31",
            "--time",
            "11:30",
            "--gender",
            "female",
        )
        self.assertEqual(proc.returncode, 2)
        self.assertIn("仅支持 1900-01-31 至 2100-12-31 的阳历日期", proc.stderr)

    def test_chart_integrity_validator_rejects_incomplete_chart(self):
        chart = zw.generate_chart(1990, 1, 1, 12, "male", target_year=2026)
        chart["palaces"] = chart["palaces"][:11]
        with self.assertRaises(ValueError):
            zw.validate_chart_integrity(chart)

    def test_kline_validator_accepts_valid_100_rows(self):
        rows = []
        prev = 50.0
        for age in range(1, 101):
            close = min(100.0, prev + 0.1)
            rows.append({
                "age": age,
                "open": prev,
                "close": close,
                "high": max(prev, close) + 0.2,
                "low": min(prev, close) - 0.2,
                "brief": "稳",
            })
            prev = close
        ok, msg = zw.validate_kline_data(rows)
        self.assertTrue(ok)
        self.assertEqual(msg, "ok")

    def test_kline_validator_rejects_non_continuous_open(self):
        rows = [
            {"age": 1, "open": 50, "close": 52, "high": 55, "low": 49, "brief": "起"},
            {"age": 2, "open": 53, "close": 54, "high": 56, "low": 52, "brief": "升"},
        ] + [
            {"age": i, "open": 54, "close": 54, "high": 54, "low": 54, "brief": "平"}
            for i in range(3, 101)
        ]
        ok, msg = zw.validate_kline_data(rows)
        self.assertFalse(ok)
        self.assertIn("open 必须等于上一年 close", msg)

    def test_generate_kline_data_is_deterministic_and_valid(self):
        chart = zw.generate_chart(1995, 7, 19, 11, "male", target_year=2026, minute=40)

        rows1 = zw.generate_kline_data(chart)
        rows2 = zw.generate_kline_data(chart)
        ok, msg = zw.validate_kline_data(rows1)

        self.assertEqual(rows1, rows2)
        self.assertTrue(ok, msg)
        self.assertEqual(len(rows1), 100)
        self.assertEqual(rows1[0]["open"], 50)
        self.assertEqual(rows1[31]["year"], 2026)
        self.assertIn("daYunRange", rows1[31])
        highs = [float(row["high"]) for row in rows1]
        closes = [float(row["close"]) for row in rows1]
        lows = [float(row["low"]) for row in rows1]
        self.assertLessEqual(max(highs), zw.KLINE_HIGH_CAP, msg="K-line high should stay below cap")
        self.assertLessEqual(max(closes), zw.KLINE_CLOSE_CAP, msg="K-line close should stay below cap")
        self.assertGreater(max(highs) - min(lows), 25.0)

    def test_generate_kline_data_has_sparse_peaks_without_long_ceiling_plateau(self):
        chart = zw.generate_chart(
            1996,
            1,
            6,
            11,
            "female",
            target_year=2026,
            minute=40,
            birthplace="深圳市",
            geocode_mode="offline",
        )

        rows = zw.generate_kline_data(chart)
        closes = [float(row["close"]) for row in rows]
        highs = [float(row["high"]) for row in rows]

        self.assertGreaterEqual(max(highs), 97.0)
        self.assertLessEqual(sum(1 for value in closes if value >= 95.0), 8)
        self.assertLessEqual(sum(1 for value in highs if value >= 98.0), 8)

        longest_peak_run = 0
        current_run = 0
        for value in closes:
            if value >= 95.0:
                current_run += 1
            else:
                longest_peak_run = max(longest_peak_run, current_run)
                current_run = 0
        longest_peak_run = max(longest_peak_run, current_run)
        self.assertLessEqual(longest_peak_run, 2)

    def test_python_chart_includes_major_star_brightness_matching_iztro(self):
        chart = zw.generate_chart(
            1996,
            1,
            6,
            11,
            "female",
            target_year=2026,
            minute=40,
            birthplace="广东省深圳市",
            geocode_mode="offline",
        )

        def major_brightness(palace_name: str) -> dict[str, str]:
            palace = next(p for p in chart["palaces"] if p["name"] == palace_name)
            return {star["name"]: star.get("brightness", "") for star in palace["majorStars"]}

        self.assertEqual(chart["fiveElementsClass"], "木三局")
        self.assertEqual(major_brightness("命宫"), {"太阳": "旺"})
        self.assertEqual(major_brightness("迁移宫"), {"天梁": "庙"})
        self.assertEqual(major_brightness("官禄宫"), {"巨门": "陷"})
        self.assertEqual(major_brightness("田宅宫"), {"紫微": "旺", "贪狼": "利"})
        self.assertEqual(major_brightness("福德宫"), {"天机": "得", "太阴": "利"})

    def test_minor_stars_use_canonical_order(self):
        chart = zw.generate_chart(
            1996,
            1,
            6,
            11,
            "female",
            target_year=2026,
            minute=40,
            use_true_solar_time=False,
        )
        brother = next(p for p in chart["palaces"] if p["name"] == "兄弟宫")
        self.assertEqual([s["name"] for s in brother["minorStars"]], ["天马", "地空", "地劫"])

    def test_payload_includes_algorithmic_kline_data(self):
        chart = zw.generate_chart(1995, 7, 19, 11, "male", target_year=2026, minute=40)

        payload = zw.build_payload(chart, 2026)

        self.assertIn("klineData", payload)
        ok, msg = zw.validate_kline_data(payload["klineData"])
        self.assertTrue(ok, msg)


class SemanticConsistencyTests(unittest.TestCase):
    def test_semantic_maps_cover_all_major_stars_and_palaces(self):
        semantics = json.loads(SEMANTIC_FILE.read_text(encoding="utf-8"))
        expected_stars = {
            "紫微", "天机", "太阳", "武曲", "天同", "廉贞",
            "天府", "太阴", "贪狼", "巨门", "天相", "天梁", "七杀", "破军",
        }
        expected_palaces = set(zw.PALACE_NAMES)
        self.assertEqual(set(semantics["major_star_descriptions"].keys()), expected_stars)
        profiles = semantics["major_star_profiles"]
        self.assertEqual(set(profiles.keys()), expected_stars)
        for name, prof in profiles.items():
            self.assertIn("优点", prof, msg=name)
            self.assertIn("风险", prof, msg=name)
            self.assertIn("适配场景", prof, msg=name)
        self.assertEqual(set(semantics["major_star_sources"].keys()), expected_stars)
        self.assertEqual(set(semantics["palace_focus"].keys()), expected_palaces)
        self.assertEqual(set(semantics["palace_focus_sources"].keys()), expected_palaces)

    def test_pattern_rule_sources_match_rule_ids(self):
        semantics = json.loads(SEMANTIC_FILE.read_text(encoding="utf-8"))
        ids = {rule["id"] for rule in semantics["pattern_rules"]}
        source_ids = set(semantics["pattern_rule_sources"].keys())
        self.assertEqual(ids, source_ids)

    def test_detect_patterns_includes_traceable_source(self):
        mocked = {
            "lifePalace": {"branch": "寅", "majorStars": [{"name": "紫微"}, {"name": "天府"}], "minorStars": []},
            "palaces": [{"majorStars": [{"name": "紫微"}, {"name": "天府"}], "minorStars": []}],
        }
        patterns = zw.detect_patterns(mocked)
        self.assertTrue(any("来源：" in p for p in patterns))

    def test_same_palace_rule_not_triggered_by_global_presence(self):
        mocked = {
            "lifePalace": {"branch": "寅", "majorStars": [{"name": "紫微"}], "minorStars": []},
            "palaces": [
                {"majorStars": [{"name": "紫微"}], "minorStars": []},
                {"majorStars": [{"name": "天府"}], "minorStars": []},
            ],
        }
        patterns = zw.detect_patterns(mocked)
        self.assertFalse(any("紫府同宫" in p for p in patterns))

    def test_huotan_rule_requires_same_palace_major_minor(self):
        mocked = {
            "lifePalace": {"branch": "子", "majorStars": [{"name": "天同"}], "minorStars": []},
            "palaces": [
                {"majorStars": [{"name": "贪狼"}], "minorStars": [{"name": "火星"}]},
                {"majorStars": [{"name": "破军"}], "minorStars": []},
            ],
        }
        patterns = zw.detect_patterns(mocked)
        self.assertTrue(any("火贪/铃贪倾向" in p for p in patterns))


class ReleaseHardeningTests(unittest.TestCase):
    def test_release_support_files_exist(self):
        expected = [
            ROOT / "LICENSE",
            ROOT / ".gitignore",
            ROOT / ".github" / "workflows" / "ci.yml",
            ROOT / "RELEASE_CHECKLIST.md",
        ]
        for path in expected:
            self.assertTrue(path.exists(), msg=f"missing release file: {path}")

    def test_docs_do_not_reference_private_or_missing_symbols(self):
        banned = [
            ".claude/skills/ziwei-ai-html-report",
            "MATCH_PROMPT",
            "buildPromptContext",
            "extractKnowledge",
            "buildYearlyContext",
            "report-template.js",
        ]
        for path in DOC_FILES:
            text = path.read_text(encoding="utf-8")
            for token in banned:
                self.assertNotIn(token, text, msg=f"{path.name} still references {token}")

    def test_readme_mentions_release_guarantees_and_failure_contract(self):
        text = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("GitHub 发布版保证", text)
        self.assertIn("失败契约", text)
        self.assertIn("常见问题", text)
        self.assertIn("日期格式不对或超出范围", text)

    def test_quickstart_script_uses_offline_mode_for_determinism(self):
        text = (ROOT / "examples" / "quickstart.sh").read_text(encoding="utf-8")
        self.assertIn("--geocode-mode offline", text)

    def test_quickstart_script_runs_and_emits_json(self):
        proc = subprocess.run(
            ["bash", str(ROOT / "examples" / "quickstart.sh")],
            text=True,
            capture_output=True,
            cwd=ROOT,
        )
        self.assertEqual(proc.returncode, 0, msg=proc.stderr)
        payload = json.loads(proc.stdout)
        self.assertIn("chart", payload)
        self.assertEqual(payload["chart"]["birth"]["coordinates"]["source"], "offline")


class AgeDisplayTests(unittest.TestCase):
    def test_nominal_and_actual_ages_for_1995_birth_in_2026(self):
        chart = zw.generate_chart(
            1995, 8, 21, 11, "male", 2026, minute=40, use_true_solar_time=False
        )
        info = zw.compute_age_info(chart, 2026, reference=__import__("datetime").date(2026, 5, 21))
        self.assertEqual(info["nominalAge"], 32)
        self.assertEqual(info["actualAgeAtYearEnd"], 31)
        self.assertEqual(info["actualAgeAtReference"], 30)

    def test_yearly_context_lists_both_age_types(self):
        chart = zw.generate_chart(1995, 8, 21, 11, "male", 2026, use_true_solar_time=False)
        ctx = zw.build_yearly_context(chart, 2026)
        self.assertIn("当前虚岁：32岁", ctx)
        self.assertIn("截至2026-12-31 为 31 岁", ctx)

    def test_payload_includes_age_info(self):
        chart = zw.generate_chart(1995, 8, 21, 11, "male", 2026, use_true_solar_time=False)
        payload = zw.build_payload(chart, 2026)
        self.assertEqual(payload["ageInfo"]["nominalAge"], 32)
        self.assertEqual(payload["ageInfo"]["actualAgeAtYearEnd"], 31)


class ReportTemplateTests(unittest.TestCase):
    def test_chart_section_before_natal_in_template(self):
        """report-template.html：紫微排盘图须先于紫微命盘综合批注。"""
        path = ROOT / "report-template.html"
        text = path.read_text(encoding="utf-8")
        i_chart = text.find('id="section-chart"')
        i_natal = text.find('id="section-natal"')
        self.assertGreater(i_chart, -1, msg="missing section-chart in report-template.html")
        self.assertGreater(i_natal, -1, msg="missing section-natal in report-template.html")
        self.assertLess(
            i_chart,
            i_natal,
            msg="report-template.html: section-chart must appear before section-natal",
        )

    def test_template_has_age_meta_span(self):
        text = (ROOT / "report-template.html").read_text(encoding="utf-8")
        self.assertIn('id="meta-age"', text)
        self.assertNotIn('id="meta-engine"', text)
        self.assertNotIn('id="meta-brightness-source"', text)


if __name__ == "__main__":
    unittest.main()

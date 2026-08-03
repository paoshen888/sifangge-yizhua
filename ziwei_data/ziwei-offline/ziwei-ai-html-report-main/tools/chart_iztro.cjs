#!/usr/bin/env node
/**
 * 使用 iztro 生成与 app/src/lib/astro.ts 一致的命盘结构，供 ziwei_offline.py --from-chart-json 消费。
 *
 * 时辰索引与 App 一致：0=早子(00-01)，1-11=丑…亥，12=晚子(23-00)。
 *
 * 两种入口：
 * 1) --solar + --time：按该钟表时刻排盘（与当前 App 输入一致，不做真太阳时）。
 * 2) --birth-json - ：读取 ziwei_offline.py --emit-iztro-birth-json 的一行 JSON（真太阳时后的阳历日+时刻），
 *    与纯 Python 真太阳时口径对齐后再走 iztro。
 */
"use strict";

const fs = require("fs");
const { astro } = require("iztro");

const MAJOR_DESC = {
  紫微: "帝座之星，主尊贵、统御、格局。",
  天机: "谋略之星，主机变、思虑、技术。",
  太阳: "光明之星，主名望、外显、助人。",
  武曲: "财帛之星，主执行、理财、刚毅。",
  天同: "福德之星，主温和、享受、人缘。",
  廉贞: "囚杀之星，主原则、欲望、变化。",
  天府: "库藏之星，主稳重、资源、包容。",
  太阴: "阴柔之星，主财富、情感、细腻。",
  贪狼: "桃花才艺之星，主欲望、交际、才华。",
  巨门: "口舌暗曜，主表达、疑虑、是非。",
  天相: "印绶之星，主辅佐、制度、体面。",
  天梁: "荫寿之星，主护持、原则、长辈缘。",
  七杀: "将星，主开创、决断、波折。",
  破军: "耗星，主破旧立新、变革、起伏。",
};

const SHICHEN = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"];
const MINOR_STAR_ORDER = [
  "左辅",
  "右弼",
  "文昌",
  "文曲",
  "天魁",
  "天钺",
  "禄存",
  "天马",
  "擎羊",
  "陀罗",
  "火星",
  "铃星",
  "地空",
  "地劫",
];

/** 与 app/src/lib/astro.ts hourToTimeIndex 对齐（支持分钟） */
function hourToTimeIndex(hour, minute) {
  const t = hour + minute / 60;
  if (t >= 23) return 12;
  if (t < 1) return 0;
  return Math.floor((t + 1) / 2);
}

function timeIndexToBranchName(index) {
  if (index === 12) return "子";
  if (index === 0) return "子";
  return SHICHEN[index] || "";
}

function parseArgs(argv) {
  const out = {
    solar: null,
    time: null,
    gender: null,
    birthplace: "",
    birthJson: null,
    timeIndex: null,
  };
  for (let i = 2; i < argv.length; i++) {
    const a = argv[i];
    if (a === "--solar") out.solar = argv[++i];
    else if (a === "--time") out.time = argv[++i];
    else if (a === "--gender") out.gender = argv[++i];
    else if (a === "--birthplace") out.birthplace = argv[++i] || "";
    else if (a === "--birth-json") out.birthJson = argv[++i];
    else if (a === "--help" || a === "-h") out.help = true;
  }
  return out;
}

function parseHm(time) {
  const m = /^(\d{2}):(\d{2})$/.exec((time || "").trim());
  if (!m) throw new Error("time 须为 HH:mm");
  const hh = parseInt(m[1], 10);
  const mm = parseInt(m[2], 10);
  if (hh < 0 || hh > 23 || mm < 0 || mm > 59) throw new Error("time 不合法");
  return [hh, mm];
}

function normGender(g) {
  const x = (g || "").toLowerCase();
  if (x === "male" || g === "男") return "male";
  if (x === "female" || g === "女") return "female";
  throw new Error("gender 须为 male/female 或 男/女");
}

function genderToIztro(g) {
  return g === "male" ? "男" : "女";
}

function normMutagen(m) {
  if (!m) return "";
  const map = { 禄: "化禄", 权: "化权", 科: "化科", 忌: "化忌" };
  return map[m] || (String(m).startsWith("化") ? String(m) : "");
}

function palaceFullName(name) {
  const map = {
    命宫: "命宫",
    兄弟: "兄弟宫",
    夫妻: "夫妻宫",
    子女: "子女宫",
    财帛: "财帛宫",
    疾厄: "疾厄宫",
    迁移: "迁移宫",
    仆役: "交友宫",
    官禄: "官禄宫",
    田宅: "田宅宫",
    福德: "福德宫",
    父母: "父母宫",
  };
  if (map[name]) return map[name];
  return name.endsWith("宫") ? name : name + "宫";
}

function parseFiveElementsNumber(classStr) {
  const map = { 二: 2, 三: 3, 四: 4, 五: 5, 六: 6 };
  const m = classStr && classStr.match(/([二三四五六])局/);
  return m ? map[m[1]] || 0 : 0;
}

function mapStar(s) {
  const o = { name: s.name };
  if (s.brightness) o.brightness = s.brightness;
  const mu = normMutagen(s.mutagen);
  if (mu) o.mutagen = mu;
  const d = MAJOR_DESC[s.name];
  if (d) o.description = d;
  return o;
}

function mapMinor(s) {
  const o = { name: s.name };
  const mu = normMutagen(s.mutagen);
  if (mu) o.mutagen = mu;
  return o;
}

function sortMinorStars(stars) {
  return stars.slice().sort((a, b) => {
    const ai = MINOR_STAR_ORDER.indexOf(a.name);
    const bi = MINOR_STAR_ORDER.indexOf(b.name);
    const ao = ai === -1 ? MINOR_STAR_ORDER.length : ai;
    const bo = bi === -1 ? MINOR_STAR_ORDER.length : bi;
    return ao - bo || String(a.name).localeCompare(String(b.name), "zh-Hans-CN");
  });
}

function natalMutagensFromPalaces(palaces) {
  const r = [];
  for (const p of palaces) {
    for (const s of p.majorStars) {
      const mu = normMutagen(s.mutagen);
      if (mu) r.push({ star: s.name, sihua: mu, palace: p.name });
    }
    for (const s of p.minorStars) {
      const mu = normMutagen(s.mutagen);
      if (mu) r.push({ star: s.name, sihua: mu, palace: p.name });
    }
  }
  return r;
}

function buildChart(ast, opts) {
  const { solarStr, hour, minute, gender, birthplace, trueSolarFromPython } = opts;
  const raw = ast.rawDates || {};
  const lunar = raw.lunarDate || {};
  const ch = raw.chineseDate || {};
  const yearlyStem = ch.yearly && ch.yearly[0];
  const yearlyBranch = ch.yearly && ch.yearly[1];

  const Palaces = ast.palaces.map((p) => {
    const name = palaceFullName(p.name);
    const dr = p.decadal && p.decadal.range;
    const rangeStr = dr ? `${dr[0]}-${dr[1]}` : "";
    const majors = (p.majorStars || []).map(mapStar);
    const minors = sortMinorStars((p.minorStars || []).map(mapMinor));
    return {
      name,
      branch: p.earthlyBranch,
      stem: p.heavenlyStem,
      majorStars: majors,
      minorStars: minors,
      adjectiveStars: [],
      isLifePalace: name === "命宫",
      isBodyPalace: !!p.isBodyPalace,
      decadalRange: rangeStr,
    };
  });

  const lifePalace = Palaces.find((x) => x.name === "命宫");
  const bodyPalace = Palaces.find((x) => x.isBodyPalace);

  let iztroVersion = "unknown";
  try {
    iztroVersion = require("iztro/package.json").version;
  } catch (_) {}

  const timeIndex = hourToTimeIndex(hour, minute);
  const chart = {
    engine: "iztro-js",
    engineVersion: iztroVersion,
    calendarRange: "依 iztro/lunar-lite",
    birth: {
      solar: solarStr,
      effectiveSolar: solarStr,
      hour,
      minute,
      localTime: `${String(hour).padStart(2, "0")}:${String(minute).padStart(2, "0")}`,
      timeBranch: timeIndexToBranchName(timeIndex),
      lateZi: hour === 23,
      gender,
      birthplace: birthplace || "",
      coordinates: { longitude: null, latitude: null, source: "n/a" },
      trueSolar: {
        enabled: !!trueSolarFromPython,
        applied: !!trueSolarFromPython,
        time: `${solarStr} ${String(hour).padStart(2, "0")}:${String(minute).padStart(2, "0")}`,
        longitudeCorrectionMinutes: 0,
        equationOfTimeMinutes: 0,
        totalCorrectionMinutes: 0,
        fallbackUsed: false,
        note: trueSolarFromPython
          ? "阳历日与时刻来自 ziwei_offline.py 真太阳时（--emit-iztro-birth-json），再交给 iztro 安星；与 App 内仅输入钟表时间可能不同。"
          : "iztro 模式：与 App 一致，按出生钟表标准时换算时辰；未做真太阳时修正。",
      },
    },
    lunar: {
      year: lunar.lunarYear,
      month: lunar.lunarMonth,
      day: lunar.lunarDay,
      isLeapMonth: !!lunar.isLeap,
    },
    yearGanZhi: {
      stem: yearlyStem || "",
      branch: yearlyBranch || "",
      text: yearlyStem && yearlyBranch ? yearlyStem + yearlyBranch : "",
    },
    fiveElementsClass: ast.fiveElementsClass || "",
    fiveElementsNumber: parseFiveElementsNumber(ast.fiveElementsClass),
    lifePalace: lifePalace
      ? { name: lifePalace.name, branch: lifePalace.branch, stem: lifePalace.stem }
      : { name: "命宫", branch: "", stem: "" },
    bodyPalace: bodyPalace
      ? { name: bodyPalace.name, branch: bodyPalace.branch, stem: bodyPalace.stem }
      : { name: "命宫", branch: "", stem: "" },
    palaces: Palaces,
    natalMutagens: natalMutagensFromPalaces(Palaces),
    patterns: [],
  };

  return chart;
}

function main() {
  const args = parseArgs(process.argv);
  if (args.help) {
    console.error(
      "用法:\n" +
        "  node chart_iztro.cjs --solar YYYY-MM-DD --time HH:mm --gender male|female\n" +
        "  node chart_iztro.cjs --birth-json -   # 从 stdin 读一行 JSON（ziwei_offline.py --emit-iztro-birth-json）\n" +
        "输出: 一行 JSON（chart 对象），供 ziwei_offline.py --from-chart-json 使用。"
    );
    process.exit(0);
  }

  let trueSolarFromPython = false;
  if (args.birthJson) {
    const raw =
      args.birthJson === "-"
        ? fs.readFileSync(0, "utf8")
        : fs.readFileSync(args.birthJson, "utf8");
    const b = JSON.parse(raw.trim());
    args.solar = b.solarDate;
    args.time = b.time;
    args.gender = b.gender;
    if (Number.isInteger(b.timeIndex) && b.timeIndex >= 0 && b.timeIndex <= 12) {
      args.timeIndex = b.timeIndex;
    }
    trueSolarFromPython = !!b.trueSolarApplied;
  }

  if (!args.solar || !args.time || !args.gender) {
    console.error("error: 必须提供 --solar/--time/--gender，或 --birth-json");
    process.exit(2);
  }
  const gender = normGender(args.gender);
  const [hour, minute] = parseHm(args.time);

  astro.config({
    yearDivide: "normal",
    horoscopeDivide: "normal",
    ageDivide: "normal",
    dayDivide: "forward",
    algorithm: "zhongzhou",
  });

  const timeIndex = args.timeIndex ?? hourToTimeIndex(hour, minute);
  const ast = astro.bySolar(args.solar, timeIndex, genderToIztro(gender), true);
  const chart = buildChart(ast, {
    solarStr: args.solar,
    hour,
    minute,
    gender,
    birthplace: args.birthplace,
    trueSolarFromPython,
  });
  process.stdout.write(JSON.stringify(chart));
}

main();

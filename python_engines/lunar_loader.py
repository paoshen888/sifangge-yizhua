"""APK lunar_python loader - execs inline source into sys.modules"""
import sys, os, types as _types

_LP_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "lunar_python")
_sources = {}

_sources["EightChar"] = """\
# -*- coding: utf-8 -*-
from .util import LunarUtil


class EightChar:
    """
    八字
    """

    MONTH_ZHI = ("", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥", "子", "丑")

    CHANG_SHENG = ("长生", "沐浴", "冠带", "临官", "帝旺", "衰", "病", "死", "墓", "绝", "胎", "养")

    __CHANG_SHENG_OFFSET = {
        "甲": 1,
        "丙": 10,
        "戊": 10,
        "庚": 7,
        "壬": 4,
        "乙": 6,
        "丁": 9,
        "己": 9,
        "辛": 0,
        "癸": 3
    }

    def __init__(self, lunar):
        self.__sect = 2
        self.__lunar = lunar

    @staticmethod
    def fromLunar(lunar):
        return EightChar(lunar)

    def toString(self):
        return self.getYear() + " " + self.getMonth() + " " + self.getDay() + " " + self.getTime()

    def __str__(self):
        return self.toString()

    def getSect(self):
        return self.__sect

    def setSect(self, sect):
        self.__sect = sect

    def getYear(self):
        """
        获取年柱
        :return: 年柱
        """
        return self.__lunar.getYearInGanZhiExact()

    def getYearGan(self):
        """
        获取年干
        :return: 天干
        """
        return self.__lunar.getYearGanExact()

    def getYearZhi(self):
        """
        获取年支
        :return: 地支
        """
        return self.__lunar.getYearZhiExact()

    def getYearHideGan(self):
        """
        获取年柱地支藏干，由于藏干分主气、余气、杂气，所以返回结果可能为1到3个元素
        :return: 天干
        """
        return LunarUtil.ZHI_HIDE_GAN.get(self.getYearZhi())

    def getYearWuXing(self):
        """
        获取年柱五行
        :return: 五行
        """
        return LunarUtil.WU_XING_GAN.get(self.getYearGan()) + LunarUtil.WU_XING_ZHI.get(self.getYearZhi())

    def getYearNaYin(self):
        """
        获取年柱纳音
        :return: 纳音
        """
        return LunarUtil.NAYIN.get(self.getYear())

    def getYearShiShenGan(self):
        """
        获取年柱天干十神
        :return: 十神
        """
        return LunarUtil.SHI_SHEN.get(self.getDayGan() + self.getYearGan())

    def __getShiShenZhi(self, zhi):
        hide_gan = LunarUtil.ZHI_HIDE_GAN.get(zhi)
        arr = []
        for gan in hide_gan:
            arr.append(LunarUtil.SHI_SHEN.get(self.getDayGan() + gan))
        return arr

    def getYearShiShenZhi(self):
        """
        获取年柱地支十神，由于藏干分主气、余气、杂气，所以返回结果可能为1到3个元素
        :return: 十神
        """
        return self.__getShiShenZhi(self.getYearZhi())

    def getDayGanIndex(self):
        return self.__lunar.getDayGanIndexExact2() if 2 == self.__sect else self.__lunar.getDayGanIndexExact()

    def getDayZhiIndex(self):
        return self.__lunar.getDayZhiIndexExact2() if 2 == self.__sect else self.__lunar.getDayZhiIndexExact()

    def __getDiShi(self, zhi_index):
        index = self.__CHANG_SHENG_OFFSET.get(self.getDayGan()) + (zhi_index if self.getDayGanIndex() % 2 == 0 else -zhi_index)
        if index >= 12:
            index -= 12
        if index < 0:
            index += 12
        return EightChar.CHANG_SHENG[index]

    def getYearDiShi(self):
        """
        获取年柱地势（长生十二神）
        :return: 地势
        """
        return self.__getDiShi(self.__lunar.getYearZhiIndexExact())

    def getMonth(self):
        """
        获取月柱
        :return: 月柱
        """
        return self.__lunar.getMonthInGanZhiExact()

    def getMonthGan(self):
        """
        获取月干
        :return: 天干
        """
        return self.__lunar.getMonthGanExact()

    def getMonthZhi(self):
        """
        获取月支
        :return: 地支
        """
        return self.__lunar.getMonthZhiExact()

    def getMonthHideGan(self):
        """
        获取月柱地支藏干，由于藏干分主气、余气、杂气，所以返回结果可能为1到3个元素
        :return: 天干
        """
        return LunarUtil.ZHI_HIDE_GAN.get(self.getMonthZhi())

    def getMonthWuXing(self):
        """
        获取月柱五行
        :return: 五行
        """
        return LunarUtil.WU_XING_GAN.get(self.getMonthGan()) + LunarUtil.WU_XING_ZHI.get(self.getMonthZhi())

    def getMonthNaYin(self):
        """
        获取月柱纳音
        :return: 纳音
        """
        return LunarUtil.NAYIN.get(self.getMonth())

    def getMonthShiShenGan(self):
        """
        获取月柱天干十神
        :return: 十神
        """
        return LunarUtil.SHI_SHEN.get(self.getDayGan() + self.getMonthGan())

    def getMonthShiShenZhi(self):
        """
        获取月柱地支十神，由于藏干分主气、余气、杂气，所以返回结果可能为1到3个元素
        :return: 十神
        """
        return self.__getShiShenZhi(self.getMonthZhi())

    def getMonthDiShi(self):
        """
        获取月柱地势（长生十二神）
        :return: 地势
        """
        return self.__getDiShi(self.__lunar.getMonthZhiIndexExact())

    def getDay(self):
        """
        获取日柱
        :return: 日柱
        """
        return self.__lunar.getDayInGanZhiExact2() if 2 == self.__sect else self.__lunar.getDayInGanZhiExact()

    def getDayGan(self):
        """
        获取日干
        :return: 天干
        """
        return self.__lunar.getDayGanExact2() if 2 == self.__sect else self.__lunar.getDayGanExact()

    def getDayZhi(self):
        """
        获取日支
        :return: 地支
        """
        return self.__lunar.getDayZhiExact2() if 2 == self.__sect else self.__lunar.getDayZhiExact()

    def getDayHideGan(self):
        """
        获取日柱地支藏干，由于藏干分主气、余气、杂气，所以返回结果可能为1到3个元素
        :return: 天干
        """
        return LunarUtil.ZHI_HIDE_GAN.get(self.getDayZhi())

    def getDayWuXing(self):
        """
        获取日柱五行
        :return: 五行
        """
        return LunarUtil.WU_XING_GAN.get(self.getDayGan()) + LunarUtil.WU_XING_ZHI.get(self.getDayZhi())

    def getDayNaYin(self):
        """
        获取日柱纳音
        :return: 纳音
        """
        return LunarUtil.NAYIN.get(self.getDay())

    def getDayShiShenGan(self):
        """
        获取日柱天干十神，也称日元、日干
        :return: 十神
        """
        return "日主"

    def getDayShiShenZhi(self):
        """
        获取日柱地支十神，由于藏干分主气、余气、杂气，所以返回结果可能为1到3个元素
        :return: 十神
        """
        return self.__getShiShenZhi(self.getDayZhi())

    def getDayDiShi(self):
        """
        获取日柱地势（长生十二神）
        :return: 地势
        """
        return self.__getDiShi(self.getDayZhiIndex())

    def getTime(self):
        """
        获取时柱
        :return: 时柱
        """
        return self.__lunar.getTimeInGanZhi()

    def getTimeGan(self):
        """
        获取时干
        :return: 天干
        """
        return self.__lunar.getTimeGan()

    def getTimeZhi(self):
        """
        获取时支
        :return: 地支
        """
        return self.__lunar.getTimeZhi()

    def getTimeHideGan(self):
        """
        获取时柱地支藏干，由于藏干分主气、余气、杂气，所以返回结果可能为1到3个元素
        :return: 天干
        """
        return LunarUtil.ZHI_HIDE_GAN.get(self.getTimeZhi())

    def getTimeWuXing(self):
        """
        获取时柱五行
        :return: 五行
        """
        return LunarUtil.WU_XING_GAN.get(self.getTimeGan()) + LunarUtil.WU_XING_ZHI.get(self.getTimeZhi())

    def getTimeNaYin(self):
        """
        获取时柱纳音
        :return: 纳音
        """
        return LunarUtil.NAYIN.get(self.getTime())

    def getTimeShiShenGan(self):
        """
        获取时柱天干十神
        :return: 十神
        """
        return LunarUtil.SHI_SHEN.get(self.getDayGan() + self.getTimeGan())

    def getTimeShiShenZhi(self):
        """
        获取时柱地支十神，由于藏干分主气、余气、杂气，所以返回结果可能为1到3个元素
        :return: 十神
        """
        return self.__getShiShenZhi(self.getTimeZhi())

    def getTimeDiShi(self):
        """
        获取时柱地势（长生十二神）
        :return: 地势
        """
        return self.__getDiShi(self.__lunar.getTimeZhiIndex())

    def getTaiYuan(self):
        """
        获取胎元
        :return: 胎元
        """
        gan_index = self.__lunar.getMonthGanIndexExact() + 1
        if gan_index >= 10:
            gan_index -= 10
        zhi_index = self.__lunar.getMonthZhiIndexExact() + 3
        if zhi_index >= 12:
            zhi_index -= 12
        return LunarUtil.GAN[gan_index + 1] + LunarUtil.ZHI[zhi_index + 1]

    def getTaiYuanNaYin(self):
        """
        获取胎元纳音
        :return: 纳音
        """
        return LunarUtil.NAYIN.get(self.getTaiYuan())

    def getTaiXi(self):
        """
        获取胎息
        :return: 胎息
        """
        gan_index = self.__lunar.getDayGanIndexExact2() if 2 == self.__sect else self.__lunar.getDayGanIndexExact()
        zhi_index = self.__lunar.getDayZhiIndexExact2() if 2 == self.__sect else self.__lunar.getDayZhiIndexExact()
        return LunarUtil.HE_GAN_5[gan_index] + LunarUtil.HE_ZHI_6[zhi_index]

    def getTaiXiNaYin(self):
        """
        获取胎息纳音
        :return: 纳音
        """
        return LunarUtil.NAYIN.get(self.getTaiXi())

    def getMingGong(self):
        """
        获取命宫
        :return: 命宫
        """
        month_zhi_index = 0
        time_zhi_index = 0
        month_zhi = self.getMonthZhi()
        time_zhi = self.getTimeZhi()
        for i in range(0, len(EightChar.MONTH_ZHI)):
            zhi = EightChar.MONTH_ZHI[i]
            if month_zhi == zhi:
                month_zhi_index = i
                break
        for i in range(0, len(EightChar.MONTH_ZHI)):
            zhi = EightChar.MONTH_ZHI[i]
            if time_zhi == zhi:
                time_zhi_index = i
                break
        offset = month_zhi_index + time_zhi_index
        if offset >= 14:
            offset = 26 - offset
        else:
            offset = 14 - offset
        gan_index = (self.__lunar.getYearGanIndexExact() + 1) * 2 + offset
        while gan_index > 10:
            gan_index -= 10
        return LunarUtil.GAN[gan_index] + EightChar.MONTH_ZHI[offset]

    def getMingGongNaYin(self):
        """
        获取命宫纳音
        :return: 纳音
        """
        return LunarUtil.NAYIN.get(self.getMingGong())

    def getShenGong(self):
        """
        获取身宫
        :return: 身宫
        """
        month_zhi_index = 0
        time_zhi_index = 0
        month_zhi = self.getMonthZhi()
        time_zhi = self.getTimeZhi()
        for i in range(0, len(EightChar.MONTH_ZHI)):
            zhi = EightChar.MONTH_ZHI[i]
            if month_zhi == zhi:
                month_zhi_index = i
                break
        for i in range(0, len(LunarUtil.ZHI)):
            zhi = LunarUtil.ZHI[i]
            if time_zhi == zhi:
                time_zhi_index = i
                break
        offset = month_zhi_index + time_zhi_index
        if offset > 12:
            offset -= 12
        gan_index = (self.__lunar.getYearGanIndexExact() + 1) * 2 + offset
        while gan_index > 10:
            gan_index -= 10
        return LunarUtil.GAN[gan_index] + EightChar.MONTH_ZHI[offset]

    def getShenGongNaYin(self):
        """
        获取身宫纳音
        :return: 纳音
        """
        return LunarUtil.NAYIN.get(self.getShenGong())

    def getLunar(self):
        return self.__lunar

    def getYun(self, gender, sect=1):
        """
        获取运
        :param gender: 性别：1男，0女
        :param sect 流派：1按天数和时辰数计算，3天1年，1天4个月，1时辰10天；2按分钟数计算
        :return: 运
        """
        from .eightchar import Yun
        return Yun(self, gender, sect)

    def getYearXun(self):
        """
        获取年柱所在旬
        :return: 旬
        """
        return self.__lunar.getYearXunExact()

    def getYearXunKong(self):
        """
        获取年柱旬空(空亡)
        :return: 旬空(空亡)
        """
        return self.__lunar.getYearXunKongExact()

    def getMonthXun(self):
        """
        获取月柱所在旬
        :return: 旬
        """
        return self.__lunar.getMonthXunExact()

    def getMonthXunKong(self):
        """
        获取月柱旬空(空亡)
        :return: 旬空(空亡)
        """
        return self.__lunar.getMonthXunKongExact()

    def getDayXun(self):
        """
        获取日柱所在旬
        :return: 旬
        """
        return self.__lunar.getDayXunExact2() if 2 == self.__sect else self.__lunar.getDayXunExact()

    def getDayXunKong(self):
        """
        获取日柱旬空(空亡)
        :return: 旬空(空亡)
        """
        return self.__lunar.getDayXunKongExact2() if 2 == self.__sect else self.__lunar.getDayXunKongExact()

    def getTimeXun(self):
        """
        获取时柱所在旬
        :return: 旬
        """
        return self.__lunar.getTimeXun()

    def getTimeXunKong(self):
        """
        获取时柱旬空(空亡)
        :return: 旬空(空亡)
        """
        return self.__lunar.getTimeXunKong()

"""

_sources["Foto"] = """\
# -*- coding: utf-8 -*-
from . import Lunar, LunarMonth
from .util import LunarUtil, FotoUtil


class Foto:
    """
    佛历
    """

    DEAD_YEAR = -543

    def __init__(self, lunar):
        self.__lunar = lunar

    @staticmethod
    def fromLunar(lunar):
        return Foto(lunar)

    @staticmethod
    def fromYmdHms(year, month, day, hour, minute, second):
        return Foto.fromLunar(Lunar.fromYmdHms(year + Foto.DEAD_YEAR - 1, month, day, hour, minute, second))

    @staticmethod
    def fromYmd(year, month, day):
        return Foto.fromYmdHms(year, month, day, 0, 0, 0)

    def getLunar(self):
        return self.__lunar

    def getYear(self):
        sy = self.__lunar.getSolar().getYear()
        y = sy - Foto.DEAD_YEAR
        if sy == self.__lunar.getYear():
            y += 1
        return y

    def getMonth(self):
        return self.__lunar.getMonth()

    def getDay(self):
        return self.__lunar.getDay()

    def getYearInChinese(self):
        y = str(self.getYear())
        s = ""
        for i in range(0, len(y)):
            s += LunarUtil.NUMBER[ord(y[i]) - 48]
        return s

    def getMonthInChinese(self):
        return self.__lunar.getMonthInChinese()

    def getDayInChinese(self):
        return self.__lunar.getDayInChinese()

    def getFestivals(self):
        festivals = []
        md = "%d-%d" % (abs(self.getMonth()), self.getDay())
        if md in FotoUtil.FESTIVAL:
            fs = FotoUtil.FESTIVAL[md]
            for f in fs:
                festivals.append(f)
        return festivals

    def getOtherFestivals(self):
        """
        获取纪念日
        :return: 非正式的节日列表，如中元节
        """
        festivals = []
        key = "%d-%d" % (self.getMonth(), self.getDay())
        if key in FotoUtil.OTHER_FESTIVAL:
            for f in FotoUtil.OTHER_FESTIVAL[key]:
                festivals.append(f)
        return festivals

    def isMonthZhai(self):
        m = self.getMonth()
        return 1 == m or 5 == m or 9 == m

    def isDayYangGong(self):
        for f in self.getFestivals():
            if "杨公忌" == f.getName():
                return True
        return False

    def isDayZhaiShuoWang(self):
        d = self.getDay()
        return 1 == d or 15 == d

    def isDayZhaiSix(self):
        d = self.getDay()
        if 8 == d or 14 == d or 15 == d or 23 == d or 29 == d or 30 == d:
            return True
        elif 28 == d:
            m = LunarMonth.fromYm(self.__lunar.getYear(), self.getMonth())
            return m is not None and 30 != m.getDayCount()
        return False

    def isDayZhaiTen(self):
        d = self.getDay()
        return 1 == d or 8 == d or 14 == d or 15 == d or 18 == d or 23 == d or 24 == d or 28 == d or 29 == d or 30 == d

    def isDayZhaiGuanYin(self):
        k = "%d-%d" % (self.getMonth(), self.getDay())
        for d in FotoUtil.DAY_ZHAI_GUAN_YIN:
            if k == d:
                return True
        return False

    def getXiu(self):
        return FotoUtil.getXiu(self.getMonth(), self.getDay())

    def getXiuLuck(self):
        return LunarUtil.XIU_LUCK[self.getXiu()]

    def getXiuSong(self):
        return LunarUtil.XIU_SONG[self.getXiu()]

    def getZheng(self):
        return LunarUtil.ZHENG[self.getXiu()]

    def getAnimal(self):
        return LunarUtil.ANIMAL[self.getXiu()]

    def getGong(self):
        return LunarUtil.GONG[self.getXiu()]

    def getShou(self):
        return LunarUtil.SHOU[self.getGong()]

    def __str__(self):
        return self.toString()

    def toString(self):
        return "%s年%s月%s" % (self.getYearInChinese(), self.getMonthInChinese(), self.getDayInChinese())

    def toFullString(self):
        s = self.toString()
        for f in self.getFestivals():
            s += " (%s)" % f
        return s

"""

_sources["FotoFestival"] = """\
# -*- coding: utf-8 -*-


class FotoFestival:
    """
    佛历因果犯忌
    """

    def __init__(self, name, result=None, every_month=False, remark=None):
        self.__name = name
        self.__result = "" if result is None else result
        self.__everyMonth = every_month
        self.__remark = "" if remark is None else remark

    def getName(self):
        return self.__name

    def getResult(self):
        return self.__result

    def isEveryMonth(self):
        return self.__everyMonth

    def getRemark(self):
        return self.__remark

    def __str__(self):
        return self.toString()

    def toString(self):
        return self.__name

    def toFullString(self):
        s = self.__name
        if self.__result is not None and len(self.__result) > 0:
            s += " " + self.__result
        if self.__remark is not None and len(self.__remark) > 0:
            s += " " + self.__remark
        return s

"""

_sources["Fu"] = """\
# -*- coding: utf-8 -*-


class Fu:
    """
    三伏
    <p>从夏至后第3个庚日算起，初伏为10天，中伏为10天或20天，末伏为10天。当夏至与立秋之间出现4个庚日时中伏为10天，出现5个庚日则为20天。</p>
    """

    def __init__(self, name, index):
        self.__name = name
        self.__index = index

    def getName(self):
        return self.__name

    def setName(self, name):
        self.__name = name

    def getIndex(self):
        return self.__index

    def setIndex(self, index):
        self.__index = index

    def __str__(self):
        return self.toString()

    def toString(self):
        return self.__name

    def toFullString(self):
        return "%s第%d天" % (self.__name, self.__index)

"""

_sources["Holiday"] = """\
# -*- coding: utf-8 -*-
class Holiday:
    """
    节假日
    """

    def __init__(self, day, name, work, target):
        """
        初始化
        :param day: 日期，YYYY-MM-DD格式
        :param name: 名称，如：国庆
        :param work: 是否调休，即是否要上班
        :param target: 关联的节日，YYYY-MM-DD格式
        """
        self.__day = Holiday.__ymd(day)
        self.__name = name
        self.__work = work
        self.__target = Holiday.__ymd(target)

    @staticmethod
    def __ymd(s):
        return s if "-" in s else (s[0:4] + "-" + s[4:6] + "-" + s[6:])

    def getDay(self):
        return self.__day

    def getName(self):
        return self.__name

    def isWork(self):
        return self.__work

    def getTarget(self):
        return self.__target

    def setDay(self, day):
        self.__day = Holiday.__ymd(day)

    def setName(self, name):
        self.__name = name

    def setWork(self, work):
        self.__work = work

    def setTarget(self, target):
        self.__target = Holiday.__ymd(target)

    def toString(self):
        return "%s %s%s %s" % (self.__day, self.__name, "调休" if self.__work else "", self.__target)

    def __str__(self):
        return self.toString()

"""

_sources["JieQi"] = """\
# -*- coding: utf-8 -*-


class JieQi:
    """
    节气
    """

    def __init__(self, name, solar):
        self.__name = name
        self.__jie = False
        self.__qi = False
        self.__solar = solar
        self.setName(name)

    def getName(self):
        """
        获取名称
        :return: 名称
        """
        return self.__name

    def setName(self, name):
        """
        设置名称
        :param name: 名称
        """
        from . import Lunar
        self.__name = name
        for i in range(0, len(Lunar.JIE_QI)):
            if name == Lunar.JIE_QI[i]:
                if i % 2 == 0:
                    self.__qi = True
                else:
                    self.__jie = True
                return

    def getSolar(self):
        """
        获取阳历日期
        :return: 阳历日期
        """
        return self.__solar

    def setSolar(self, solar):
        """
        设置阳历日期
        :param solar: 阳历日期
        """
        self.__solar = solar

    def isJie(self):
        """
        是否节令
        :return: true/false
        """
        return self.__jie

    def isQi(self):
        """
        是否气令
        :return: true/false
        """
        return self.__qi

    def toString(self):
        return self.__name

    def __str__(self):
        return self.toString()

"""

_sources["Lunar"] = """\
# -*- coding: utf-8 -*-
from . import Solar, NineStar, EightChar, JieQi, ShuJiu, Fu, LunarTime
from .util import LunarUtil, SolarUtil


class Lunar:
    """
    阴历日期
    """
    JIE_QI = ("冬至", "小寒", "大寒", "立春", "雨水", "惊蛰", "春分", "清明", "谷雨", "立夏", "小满", "芒种", "夏至", "小暑", "大暑", "立秋", "处暑", "白露", "秋分", "寒露", "霜降", "立冬", "小雪", "大雪")
    JIE_QI_IN_USE = ("DA_XUE", "冬至", "小寒", "大寒", "立春", "雨水", "惊蛰", "春分", "清明", "谷雨", "立夏", "小满", "芒种", "夏至", "小暑", "大暑", "立秋", "处暑", "白露", "秋分", "寒露", "霜降", "立冬", "小雪", "大雪", "DONG_ZHI", "XIAO_HAN", "DA_HAN", "LI_CHUN", "YU_SHUI", "JING_ZHE")

    def __init__(self, lunar_year: int, lunar_month: int, lunar_day: int, hour: int, minute: int, second: int):
        from . import LunarYear
        y = LunarYear.fromYear(lunar_year)
        m = y.getMonth(lunar_month)
        if m is None:
            raise Exception("wrong lunar year %d  month %d" % (lunar_year, lunar_month))
        if lunar_day < 1:
            raise Exception("lunar day must bigger than 0")
        days = m.getDayCount()
        if lunar_day > days:
            raise Exception("only %d days in lunar year %d month %d" % (days, lunar_year, lunar_month))
        self.__year = lunar_year
        self.__month = lunar_month
        self.__day = lunar_day
        self.__hour = hour
        self.__minute = minute
        self.__second = second
        self.__jieQi = {}
        self.__jieQiList = []
        self.__eightChar = None
        noon = Solar.fromJulianDay(m.getFirstJulianDay() + lunar_day - 1)
        self.__solar = Solar.fromYmdHms(noon.getYear(), noon.getMonth(), noon.getDay(), hour, minute, second)
        if noon.getYear() != lunar_year:
            y = LunarYear.fromYear(noon.getYear())
        self.__compute(y)

    def __compute(self, y):
        self.__computeJieQi(y)
        self.__computeYear()
        self.__computeMonth()
        self.__computeDay()
        self.__computeTime()
        self.__computeWeek()

    def __computeJieQi(self, y):
        julian_days = y.getJieQiJulianDays()
        for i in range(0, len(Lunar.JIE_QI_IN_USE)):
            name = Lunar.JIE_QI_IN_USE[i]
            self.__jieQi[name] = Solar.fromJulianDay(julian_days[i])
            self.__jieQiList.append(name)

    def __computeYear(self):
        # 以正月初一开始
        offset = self.__year - 4
        year_gan_index = offset % 10
        year_zhi_index = offset % 12

        if year_gan_index < 0:
            year_gan_index += 10

        if year_zhi_index < 0:
            year_zhi_index += 12

        # 以立春作为新一年的开始的干支纪年
        g = year_gan_index
        z = year_zhi_index

        # 精确的干支纪年，以立春交接时刻为准
        g_exact = year_gan_index
        z_exact = year_zhi_index

        solar_year = self.__solar.getYear()
        solar_ymd = self.__solar.toYmd()
        solar_ymd_hms = self.__solar.toYmdHms()

        # 获取立春的阳历时刻
        li_chun = self.__jieQi["立春"]
        if li_chun.getYear() != solar_year:
            li_chun = self.__jieQi["LI_CHUN"]
        li_chun_ymd = li_chun.toYmd()
        li_chun_ymd_hms = li_chun.toYmdHms()

        # 阳历和阴历年份相同代表正月初一及以后
        if self.__year == solar_year:
            # 立春日期判断
            if solar_ymd < li_chun_ymd:
                g -= 1
                z -= 1
            # 立春交接时刻判断
            if solar_ymd_hms < li_chun_ymd_hms:
                g_exact -= 1
                z_exact -= 1
        elif self.__year < solar_year:
            if solar_ymd >= li_chun_ymd:
                g += 1
                z += 1
            if solar_ymd_hms >= li_chun_ymd_hms:
                g_exact += 1
                z_exact += 1

        self.__yearGanIndex = year_gan_index
        self.__yearZhiIndex = year_zhi_index

        self.__yearGanIndexByLiChun = (g + 10 if g < 0 else g) % 10
        self.__yearZhiIndexByLiChun = (z + 12 if z < 0 else z) % 12

        self.__yearGanIndexExact = (g_exact + 10 if g_exact < 0 else g_exact) % 10
        self.__yearZhiIndexExact = (z_exact + 12 if z_exact < 0 else z_exact) % 12

    def __computeMonth(self):
        ymd = self.__solar.toYmd()
        time = self.__solar.toYmdHms()
        size = len(Lunar.JIE_QI_IN_USE)

        # 序号：大雪以前-3，大雪到小寒之间-2，小寒到立春之间-1，立春之后0
        index = -3
        start = None
        for i in range(0, size, 2):
            end = self.__jieQi[Lunar.JIE_QI_IN_USE[i]]
            symd = ymd if start is None else start.toYmd()
            if symd <= ymd < end.toYmd():
                break
            start = end
            index += 1
        # 干偏移值（以立春当天起算）
        g_offset = (((self.__yearGanIndexByLiChun + (1 if index < 0 else 0)) % 5 + 1) * 2) % 10
        self.__monthGanIndex = ((index + 10 if index < 0 else index) + g_offset) % 10
        self.__monthZhiIndex = ((index + 12 if index < 0 else index) + LunarUtil.BASE_MONTH_ZHI_INDEX) % 12

        index = -3
        start = None
        for i in range(0, size, 2):
            end = self.__jieQi[Lunar.JIE_QI_IN_USE[i]]
            stime = time if start is None else start.toYmdHms()
            if stime <= time < end.toYmdHms():
                break
            start = end
            index += 1
        # 干偏移值（以立春交接时刻起算）
        g_offset = (((self.__yearGanIndexExact + (1 if index < 0 else 0)) % 5 + 1) * 2) % 10
        self.__monthGanIndexExact = ((index + 10 if index < 0 else index) + g_offset) % 10
        self.__monthZhiIndexExact = ((index + 12 if index < 0 else index) + LunarUtil.BASE_MONTH_ZHI_INDEX) % 12

    def __computeDay(self):
        noon = Solar.fromYmdHms(self.__solar.getYear(), self.__solar.getMonth(), self.__solar.getDay(), 12, 0, 0)
        offset = int(noon.getJulianDay()) - 11
        day_gan_index = offset % 10
        day_zhi_index = offset % 12

        self.__dayGanIndex = day_gan_index
        self.__dayZhiIndex = day_zhi_index

        day_gan_exact = day_gan_index
        day_zhi_exact = day_zhi_index

        # 八字流派2，晚子时（夜子/子夜）日柱算当天
        self.__dayGanIndexExact2 = day_gan_exact
        self.__dayZhiIndexExact2 = day_zhi_exact

        # 八字流派1，晚子时（夜子/子夜）日柱算明天
        hm = ("0" if self.__hour < 10 else "") + str(self.__hour) + ":" + ("0" if self.__minute < 10 else "") + str(self.__minute)
        if "23:00" <= hm <= "23:59":
            day_gan_exact += 1
            if day_gan_exact >= 10:
                day_gan_exact -= 10
            day_zhi_exact += 1
            if day_zhi_exact >= 12:
                day_zhi_exact -= 12
        self.__dayGanIndexExact = day_gan_exact
        self.__dayZhiIndexExact = day_zhi_exact

    def __computeTime(self):
        time_zhi_index = LunarUtil.getTimeZhiIndex(("0" if self.__hour < 10 else "") + str(self.__hour) + ":" + ("0" if self.__minute < 10 else "") + str(self.__minute))
        self.__timeZhiIndex = time_zhi_index
        self.__timeGanIndex = (self.__dayGanIndexExact % 5 * 2 + time_zhi_index) % 10

    def __computeWeek(self):
        self.__weekIndex = self.__solar.getWeek()

    @staticmethod
    def fromYmdHms(lunar_year, lunar_month, lunar_day, hour, minute, second):
        return Lunar(lunar_year, lunar_month, lunar_day, hour, minute, second)

    @staticmethod
    def fromYmd(lunar_year, lunar_month, lunar_day):
        return Lunar(lunar_year, lunar_month, lunar_day, 0, 0, 0)

    @staticmethod
    def fromDate(date):
        return Lunar.fromSolar(Solar.fromDate(date))

    @staticmethod
    def fromSolar(solar):
        from . import LunarYear
        year = 0
        month = 0
        day = 0
        ly = LunarYear.fromYear(solar.getYear())
        for m in ly.getMonths():
            days = solar.subtract(Solar.fromJulianDay(m.getFirstJulianDay()))
            if days < m.getDayCount():
                year = m.getYear()
                month = m.getMonth()
                day = days + 1
                break
        return Lunar(year, month, day, solar.getHour(), solar.getMinute(), solar.getSecond())

    def getYear(self):
        return self.__year

    def getMonth(self):
        return self.__month

    def getDay(self):
        return self.__day

    def getHour(self):
        return self.__hour

    def getMinute(self):
        return self.__minute

    def getSecond(self):
        return self.__second

    def getSolar(self):
        return self.__solar

    def getYearGan(self):
        return LunarUtil.GAN[self.__yearGanIndex + 1]

    def getYearGanByLiChun(self):
        return LunarUtil.GAN[self.__yearGanIndexByLiChun + 1]

    def getYearGanExact(self):
        return LunarUtil.GAN[self.__yearGanIndexExact + 1]

    def getYearZhi(self):
        return LunarUtil.ZHI[self.__yearZhiIndex + 1]

    def getYearZhiByLiChun(self):
        return LunarUtil.ZHI[self.__yearZhiIndexByLiChun + 1]

    def getYearZhiExact(self):
        return LunarUtil.ZHI[self.__yearZhiIndexExact + 1]

    def getYearInGanZhi(self):
        return "%s%s" % (self.getYearGan(), self.getYearZhi())

    def getYearInGanZhiByLiChun(self):
        return "%s%s" % (self.getYearGanByLiChun(), self.getYearZhiByLiChun())

    def getYearInGanZhiExact(self):
        return "%s%s" % (self.getYearGanExact(), self.getYearZhiExact())

    def getMonthGan(self):
        return LunarUtil.GAN[self.__monthGanIndex + 1]

    def getMonthGanExact(self):
        return LunarUtil.GAN[self.__monthGanIndexExact + 1]

    def getMonthZhi(self):
        return LunarUtil.ZHI[self.__monthZhiIndex + 1]

    def getMonthZhiExact(self):
        return LunarUtil.ZHI[self.__monthZhiIndexExact + 1]

    def getMonthInGanZhi(self):
        return "%s%s" % (self.getMonthGan(), self.getMonthZhi())

    def getMonthInGanZhiExact(self):
        return "%s%s" % (self.getMonthGanExact(), self.getMonthZhiExact())

    def getDayGan(self):
        return LunarUtil.GAN[self.__dayGanIndex + 1]

    def getDayGanExact(self):
        return LunarUtil.GAN[self.__dayGanIndexExact + 1]

    def getDayGanExact2(self):
        return LunarUtil.GAN[self.__dayGanIndexExact2 + 1]

    def getDayZhi(self):
        return LunarUtil.ZHI[self.__dayZhiIndex + 1]

    def getDayZhiExact(self):
        return LunarUtil.ZHI[self.__dayZhiIndexExact + 1]

    def getDayZhiExact2(self):
        return LunarUtil.ZHI[self.__dayZhiIndexExact2 + 1]

    def getDayInGanZhi(self):
        return "%s%s" % (self.getDayGan(), self.getDayZhi())

    def getDayInGanZhiExact(self):
        return "%s%s" % (self.getDayGanExact(), self.getDayZhiExact())

    def getDayInGanZhiExact2(self):
        return "%s%s" % (self.getDayGanExact2(), self.getDayZhiExact2())

    def getTimeGan(self):
        return LunarUtil.GAN[self.__timeGanIndex + 1]

    def getTimeZhi(self):
        return LunarUtil.ZHI[self.__timeZhiIndex + 1]

    def getTimeInGanZhi(self):
        return "%s%s" % (self.getTimeGan(), self.getTimeZhi())

    def getYearShengXiao(self):
        return LunarUtil.SHENGXIAO[self.__yearZhiIndex + 1]

    def getYearShengXiaoByLiChun(self):
        return LunarUtil.SHENGXIAO[self.__yearZhiIndexByLiChun + 1]

    def getYearShengXiaoExact(self):
        return LunarUtil.SHENGXIAO[self.__yearZhiIndexExact + 1]

    def getMonthShengXiao(self):
        return LunarUtil.SHENGXIAO[self.__monthZhiIndex + 1]

    def getMonthShengXiaoExact(self):
        return LunarUtil.SHENGXIAO[self.__monthZhiIndexExact + 1]

    def getDayShengXiao(self):
        return LunarUtil.SHENGXIAO[self.__dayZhiIndex + 1]

    def getTimeShengXiao(self):
        return LunarUtil.SHENGXIAO[self.__timeZhiIndex + 1]

    def getYearInChinese(self):
        y = str(self.__year)
        s = ""
        for i in range(0, len(y)):
            s += LunarUtil.NUMBER[ord(y[i]) - 48]
        return s

    def getMonthInChinese(self):
        month = self.__month
        return ("闰" if month < 0 else "") + LunarUtil.MONTH[abs(month)]

    def getDayInChinese(self):
        return LunarUtil.DAY[self.__day]

    def getPengZuGan(self):
        return LunarUtil.PENG_ZU_GAN[self.__dayGanIndex + 1]

    def getPengZuZhi(self):
        return LunarUtil.PENG_ZU_ZHI[self.__dayZhiIndex + 1]

    def getPositionXi(self):
        return self.getDayPositionXi()

    def getPositionXiDesc(self):
        return self.getDayPositionXiDesc()

    def getPositionYangGui(self):
        return self.getDayPositionYangGui()

    def getPositionYangGuiDesc(self):
        return self.getDayPositionYangGuiDesc()

    def getPositionYinGui(self):
        return self.getDayPositionYinGui()

    def getPositionYinGuiDesc(self):
        return self.getDayPositionYinGuiDesc()

    def getPositionFu(self):
        return self.getDayPositionFu()

    def getPositionFuDesc(self):
        return self.getDayPositionFuDesc()

    def getPositionCai(self):
        return self.getDayPositionCai()

    def getPositionCaiDesc(self):
        return self.getDayPositionCaiDesc()

    def getDayPositionXi(self):
        return LunarUtil.POSITION_XI[self.__dayGanIndex + 1]

    def getDayPositionXiDesc(self):
        return LunarUtil.POSITION_DESC[self.getDayPositionXi()]

    def getDayPositionYangGui(self):
        return LunarUtil.POSITION_YANG_GUI[self.__dayGanIndex + 1]

    def getDayPositionYangGuiDesc(self):
        return LunarUtil.POSITION_DESC[self.getDayPositionYangGui()]

    def getDayPositionYinGui(self):
        return LunarUtil.POSITION_YIN_GUI[self.__dayGanIndex + 1]

    def getDayPositionYinGuiDesc(self):
        return LunarUtil.POSITION_DESC[self.getDayPositionYinGui()]

    def getDayPositionFu(self, sect=2):
        return (LunarUtil.POSITION_FU if 1 == sect else LunarUtil.POSITION_FU_2)[self.__dayGanIndex + 1]

    def getDayPositionFuDesc(self, sect=2):
        return LunarUtil.POSITION_DESC[self.getDayPositionFu(sect)]

    def getDayPositionCai(self):
        return LunarUtil.POSITION_CAI[self.__dayGanIndex + 1]

    def getDayPositionCaiDesc(self):
        return LunarUtil.POSITION_DESC[self.getDayPositionCai()]

    def getYearPositionTaiSui(self, sect=2):
        if 1 == sect:
            year_zhi_index = self.__yearZhiIndex
        elif 3 == sect:
            year_zhi_index = self.__yearZhiIndexExact
        else:
            year_zhi_index = self.__yearZhiIndexByLiChun
        return LunarUtil.POSITION_TAI_SUI_YEAR[year_zhi_index]

    def getYearPositionTaiSuiDesc(self, sect=2):
        return LunarUtil.POSITION_DESC[self.getYearPositionTaiSui(sect)]

    def __getMonthPositionTaiSui(self, month_zhi_index, month_gan_index):
        m = month_zhi_index - LunarUtil.BASE_MONTH_ZHI_INDEX
        if m < 0:
            m += 12
        m = m % 4
        if 0 == m:
            p = "艮"
        elif 2 == m:
            p = "坤"
        elif 3 == m:
            p = "巽"
        else:
            p = LunarUtil.POSITION_GAN[month_gan_index]
        return p

    def getMonthPositionTaiSui(self, sect=2):
        if 3 == sect:
            month_zhi_index = self.__monthZhiIndexExact
            month_gan_index = self.__monthGanIndexExact
        else:
            month_zhi_index = self.__monthZhiIndex
            month_gan_index = self.__monthGanIndex
        return self.__getMonthPositionTaiSui(month_zhi_index, month_gan_index)

    def getMonthPositionTaiSuiDesc(self, sect=2):
        return LunarUtil.POSITION_DESC[self.getMonthPositionTaiSui(sect)]

    def __getDayPositionTaiSui(self, day_in_gan_zhi, year_zhi_index):
        if day_in_gan_zhi in "甲子,乙丑,丙寅,丁卯,戊辰,己巳":
            p = "震"
        elif day_in_gan_zhi in "丙子,丁丑,戊寅,己卯,庚辰,辛巳":
            p = "离"
        elif day_in_gan_zhi in "戊子,己丑,庚寅,辛卯,壬辰,癸巳":
            p = "中"
        elif day_in_gan_zhi in "庚子,辛丑,壬寅,癸卯,甲辰,乙巳":
            p = "兑"
        elif day_in_gan_zhi in "壬子,癸丑,甲寅,乙卯,丙辰,丁巳":
            p = "坎"
        else:
            p = LunarUtil.POSITION_TAI_SUI_YEAR[year_zhi_index]
        return p

    def getDayPositionTaiSui(self, sect=2):
        if 1 == sect:
            day_in_gan_zhi = self.getDayInGanZhi()
            year_zhi_index = self.__yearZhiIndex
        elif 3 == sect:
            day_in_gan_zhi = self.getDayInGanZhi()
            year_zhi_index = self.__yearZhiIndexExact
        else:
            day_in_gan_zhi = self.getDayInGanZhiExact2()
            year_zhi_index = self.__yearZhiIndexByLiChun
        return self.__getDayPositionTaiSui(day_in_gan_zhi, year_zhi_index)

    def getDayPositionTaiSuiDesc(self, sect=2):
        return LunarUtil.POSITION_DESC[self.getDayPositionTaiSui(sect)]

    def getTimePositionXi(self):
        return LunarUtil.POSITION_XI[self.__timeGanIndex + 1]

    def getTimePositionXiDesc(self):
        return LunarUtil.POSITION_DESC[self.getTimePositionXi()]

    def getTimePositionYangGui(self):
        return LunarUtil.POSITION_YANG_GUI[self.__timeGanIndex + 1]

    def getTimePositionYangGuiDesc(self):
        return LunarUtil.POSITION_DESC[self.getTimePositionYangGui()]

    def getTimePositionYinGui(self):
        return LunarUtil.POSITION_YIN_GUI[self.__timeGanIndex + 1]

    def getTimePositionYinGuiDesc(self):
        return LunarUtil.POSITION_DESC[self.getTimePositionYinGui()]

    def getTimePositionFu(self, sect=2):
        return (LunarUtil.POSITION_FU if 1 == sect else LunarUtil.POSITION_FU_2)[self.__timeGanIndex + 1]

    def getTimePositionFuDesc(self, sect=2):
        return LunarUtil.POSITION_DESC[self.getTimePositionFu(sect)]

    def getTimePositionCai(self):
        return LunarUtil.POSITION_CAI[self.__timeGanIndex + 1]

    def getTimePositionCaiDesc(self):
        return LunarUtil.POSITION_DESC[self.getTimePositionCai()]

    def getChong(self):
        return self.getDayChong()

    def getDayChong(self):
        return LunarUtil.CHONG[self.__dayZhiIndex]

    def getTimeChong(self):
        return LunarUtil.CHONG[self.__timeZhiIndex]

    def getChongGan(self):
        return self.getDayChongGan()

    def getDayChongGan(self):
        return LunarUtil.CHONG_GAN[self.__dayGanIndex]

    def getTimeChongGan(self):
        return LunarUtil.CHONG_GAN[self.__timeGanIndex]

    def getChongGanTie(self):
        return self.getDayChongGanTie()

    def getDayChongGanTie(self):
        return LunarUtil.CHONG_GAN_TIE[self.__dayGanIndex]

    def getTimeChongGanTie(self):
        return LunarUtil.CHONG_GAN_TIE[self.__timeGanIndex]

    def getChongShengXiao(self):
        return self.getDayChongShengXiao()

    def getDayChongShengXiao(self):
        chong = self.getDayChong()
        for i in range(0, len(LunarUtil.ZHI)):
            if LunarUtil.ZHI[i] == chong:
                return LunarUtil.SHENGXIAO[i]
        return ""

    def getTimeChongShengXiao(self):
        chong = self.getTimeChong()
        for i in range(0, len(LunarUtil.ZHI)):
            if LunarUtil.ZHI[i] == chong:
                return LunarUtil.SHENGXIAO[i]
        return ""

    def getChongDesc(self):
        return self.getDayChongDesc()

    def getDayChongDesc(self):
        return "(" + self.getDayChongGan() + self.getDayChong() + ")" + self.getDayChongShengXiao()

    def getTimeChongDesc(self):
        return "(" + self.getTimeChongGan() + self.getTimeChong() + ")" + self.getTimeChongShengXiao()

    def getSha(self):
        return self.getDaySha()

    def getDaySha(self):
        return LunarUtil.SHA[self.getDayZhi()]

    def getTimeSha(self):
        return LunarUtil.SHA[self.getTimeZhi()]

    def getYearNaYin(self):
        return LunarUtil.NAYIN[self.getYearInGanZhi()]

    def getMonthNaYin(self):
        return LunarUtil.NAYIN[self.getMonthInGanZhi()]

    def getDayNaYin(self):
        return LunarUtil.NAYIN[self.getDayInGanZhi()]

    def getTimeNaYin(self):
        return LunarUtil.NAYIN[self.getTimeInGanZhi()]

    def getSeason(self):
        return LunarUtil.SEASON[abs(self.__month)]

    @staticmethod
    def __convertJieQi(name):
        jq = name
        if "DONG_ZHI" == jq:
            jq = "冬至"
        elif "DA_HAN" == jq:
            jq = "大寒"
        elif "XIAO_HAN" == jq:
            jq = "小寒"
        elif "LI_CHUN" == jq:
            jq = "立春"
        elif "DA_XUE" == jq:
            jq = "大雪"
        elif "YU_SHUI" == jq:
            jq = "雨水"
        elif "JING_ZHE" == jq:
            jq = "惊蛰"
        return jq

    def getJie(self):
        for i in range(0, len(Lunar.JIE_QI_IN_USE), 2):
            key = Lunar.JIE_QI_IN_USE[i]
            d = self.__jieQi[key]
            if d.getYear() == self.__solar.getYear() and d.getMonth() == self.__solar.getMonth() and d.getDay() == self.__solar.getDay():
                return self.__convertJieQi(key)
        return ""

    def getQi(self):
        for i in range(1, len(Lunar.JIE_QI_IN_USE), 2):
            key = Lunar.JIE_QI_IN_USE[i]
            d = self.__jieQi[key]
            if d.getYear() == self.__solar.getYear() and d.getMonth() == self.__solar.getMonth() and d.getDay() == self.__solar.getDay():
                return self.__convertJieQi(key)
        return ""

    def getWeek(self):
        return self.__weekIndex

    def getWeekInChinese(self):
        return SolarUtil.WEEK[self.getWeek()]

    def getXiu(self):
        return LunarUtil.XIU[self.getDayZhi() + str(self.getWeek())]

    def getXiuLuck(self):
        return LunarUtil.XIU_LUCK[self.getXiu()]

    def getXiuSong(self):
        return LunarUtil.XIU_SONG[self.getXiu()]

    def getZheng(self):
        return LunarUtil.ZHENG[self.getXiu()]

    def getAnimal(self):
        return LunarUtil.ANIMAL[self.getXiu()]

    def getGong(self):
        return LunarUtil.GONG[self.getXiu()]

    def getShou(self):
        return LunarUtil.SHOU[self.getGong()]

    def getFestivals(self):
        fs = []
        md = "%d-%d" % (self.__month, self.__day)
        if md in LunarUtil.FESTIVAL:
            fs.append(LunarUtil.FESTIVAL[md])
        if abs(self.__month) == 12 and self.__day >= 29 and self.__year != self.next(1).getYear():
            fs.append("除夕")
        return fs

    def getOtherFestivals(self):
        arr = []
        md = "%d-%d" % (self.__month, self.__day)
        if md in LunarUtil.OTHER_FESTIVAL:
            fs = LunarUtil.OTHER_FESTIVAL[md]
            for f in fs:
                arr.append(f)
        solar_ymd = self.__solar.toYmd()
        if solar_ymd == self.__jieQi["清明"].next(-1).toYmd():
            arr.append("寒食节")

        jq = self.__jieQi["立春"]
        offset = 4 - jq.getLunar().getDayGanIndex()
        if offset < 0:
            offset += 10
        if solar_ymd == jq.next(offset + 40).toYmd():
            arr.append("春社")

        jq = self.__jieQi["立秋"]
        offset = 4 - jq.getLunar().getDayGanIndex()
        if offset < 0:
            offset += 10
        if solar_ymd == jq.next(offset + 40).toYmd():
            arr.append("秋社")
        return arr

    def getEightChar(self):
        if self.__eightChar is None:
            self.__eightChar = EightChar.fromLunar(self)
        return self.__eightChar

    def getBaZi(self):
        ba_zi = self.getEightChar()
        return [ba_zi.getYear(), ba_zi.getMonth(), ba_zi.getDay(), ba_zi.getTime()]

    def getBaZiWuXing(self):
        ba_zi = self.getEightChar()
        return [ba_zi.getYearWuXing(), ba_zi.getMonthWuXing(), ba_zi.getDayWuXing(), ba_zi.getTimeWuXing()]

    def getBaZiNaYin(self):
        ba_zi = self.getEightChar()
        return [ba_zi.getYearNaYin(), ba_zi.getMonthNaYin(), ba_zi.getDayNaYin(), ba_zi.getTimeNaYin()]

    def getBaZiShiShenGan(self):
        ba_zi = self.getEightChar()
        return [ba_zi.getYearShiShenGan(), ba_zi.getMonthShiShenGan(), ba_zi.getDayShiShenGan(), ba_zi.getTimeShiShenGan()]

    def getBaZiShiShenZhi(self):
        ba_zi = self.getEightChar()
        return [ba_zi.getYearShiShenZhi()[0], ba_zi.getMonthShiShenZhi()[0], ba_zi.getDayShiShenZhi()[0], ba_zi.getTimeShiShenZhi()[0]]

    def getBaZiShiShenYearZhi(self):
        return self.getEightChar().getYearShiShenZhi()

    def getBaZiShiShenMonthZhi(self):
        return self.getEightChar().getMonthShiShenZhi()

    def getBaZiShiShenDayZhi(self):
        return self.getEightChar().getDayShiShenZhi()

    def getBaZiShiShenTimeZhi(self):
        return self.getEightChar().getTimeShiShenZhi()

    def getZhiXing(self):
        offset = self.__dayZhiIndex - self.__monthZhiIndex
        if offset < 0:
            offset += 12
        return LunarUtil.ZHI_XING[offset + 1]

    def getDayTianShen(self):
        return LunarUtil.TIAN_SHEN[(self.__dayZhiIndex + LunarUtil.ZHI_TIAN_SHEN_OFFSET[self.getMonthZhi()]) % 12 + 1]

    def getTimeTianShen(self):
        return LunarUtil.TIAN_SHEN[(self.__timeZhiIndex + LunarUtil.ZHI_TIAN_SHEN_OFFSET[self.getDayZhiExact()]) % 12 + 1]

    def getDayTianShenType(self):
        return LunarUtil.TIAN_SHEN_TYPE[self.getDayTianShen()]

    def getTimeTianShenType(self):
        return LunarUtil.TIAN_SHEN_TYPE[self.getTimeTianShen()]

    def getDayTianShenLuck(self):
        return LunarUtil.TIAN_SHEN_TYPE_LUCK[self.getDayTianShenType()]

    def getTimeTianShenLuck(self):
        return LunarUtil.TIAN_SHEN_TYPE_LUCK[self.getTimeTianShenType()]

    def getDayPositionTai(self):
        return LunarUtil.POSITION_TAI_DAY[LunarUtil.getJiaZiIndex(self.getDayInGanZhi())]

    def getMonthPositionTai(self):
        m = self.__month
        if m < 0:
            return ""
        return LunarUtil.POSITION_TAI_MONTH[m - 1]

    def getDayYi(self, sect=1):
        """
        获取每日宜
        :return: 宜
        """
        if 2 == sect:
            month_gan_zhi = self.getMonthInGanZhiExact()
        else:
            month_gan_zhi = self.getMonthInGanZhi()
        return LunarUtil.getDayYi(month_gan_zhi, self.getDayInGanZhi())

    def getDayJi(self, sect=1):
        """
        获取每日忌
        :return: 忌
        """
        if 2 == sect:
            month_gan_zhi = self.getMonthInGanZhiExact()
        else:
            month_gan_zhi = self.getMonthInGanZhi()
        return LunarUtil.getDayJi(month_gan_zhi, self.getDayInGanZhi())

    def getTimeYi(self):
        """
        获取时宜
        :return: 宜
        """
        return LunarUtil.getTimeYi(self.getDayInGanZhiExact(), self.getTimeInGanZhi())

    def getTimeJi(self):
        """
        获取时忌
        :return: 忌
        """
        return LunarUtil.getTimeJi(self.getDayInGanZhiExact(), self.getTimeInGanZhi())

    def getDayJiShen(self):
        """
        获取日吉神（宜趋）
        :return: 日吉神
        """
        return LunarUtil.getDayJiShen(self.getMonthZhiIndex(), self.getDayInGanZhi())

    def getDayXiongSha(self):
        """
        获取日凶煞（宜忌）
        :return: 日凶煞
        """
        return LunarUtil.getDayXiongSha(self.getMonthZhiIndex(), self.getDayInGanZhi())

    def getYueXiang(self):
        """
        获取月相
        :return: 月相
        """
        return LunarUtil.YUE_XIANG[self.__day]

    def __getYearNineStar(self, year_in_gan_zhi):
        index_exact = LunarUtil.getJiaZiIndex(year_in_gan_zhi) + 1
        index = LunarUtil.getJiaZiIndex(self.getYearInGanZhi()) + 1
        year_offset = index_exact - index
        if year_offset > 1:
            year_offset -= 60
        elif year_offset < -1:
            year_offset += 60
        yuan = int((self.__year + year_offset + 2696) / 60) % 3
        offset = (62 + yuan * 3 - index_exact) % 9
        if 0 == offset:
            offset = 9
        return NineStar.fromIndex(offset - 1)

    def getYearNineStar(self, sect=2):
        if 1 == sect:
            year_in_gan_zhi = self.getYearInGanZhi()
        elif 3 == sect:
            year_in_gan_zhi = self.getYearInGanZhiExact()
        else:
            year_in_gan_zhi = self.getYearInGanZhiByLiChun()
        return self.__getYearNineStar(year_in_gan_zhi)

    @staticmethod
    def __getMonthNineStar(year_zhi_index, month_zhi_index):
        index = year_zhi_index % 3
        n = 27 - index * 3
        if month_zhi_index < LunarUtil.BASE_MONTH_ZHI_INDEX:
            n -= 3
        offset = (n - month_zhi_index) % 9
        return NineStar.fromIndex(offset)

    def getMonthNineStar(self, sect=2):
        if 1 == sect:
            year_zhi_index = self.__yearZhiIndex
            month_zhi_index = self.__monthZhiIndex
        elif 3 == sect:
            year_zhi_index = self.__yearZhiIndexExact
            month_zhi_index = self.__monthZhiIndexExact
        else:
            year_zhi_index = self.__yearZhiIndexByLiChun
            month_zhi_index = self.__monthZhiIndex
        return self.__getMonthNineStar(year_zhi_index, month_zhi_index)

    def getDayNineStar(self):
        solar_ymd = self.__solar.toYmd()
        dong_zhi = self.__jieQi["冬至"]
        dong_zhi2 = self.__jieQi["DONG_ZHI"]
        xia_zhi = self.__jieQi["夏至"]

        dong_zhi_index = LunarUtil.getJiaZiIndex(dong_zhi.getLunar().getDayInGanZhi())
        dong_zhi_index2 = LunarUtil.getJiaZiIndex(dong_zhi2.getLunar().getDayInGanZhi())
        xia_zhi_index = LunarUtil.getJiaZiIndex(xia_zhi.getLunar().getDayInGanZhi())

        if dong_zhi_index > 29:
            solar_shun_bai = dong_zhi.next(60 - dong_zhi_index)
        else:
            solar_shun_bai = dong_zhi.next(-dong_zhi_index)
        solar_shun_bai_ymd = solar_shun_bai.toYmd()
        if dong_zhi_index2 > 29:
            solar_shun_bai2 = dong_zhi2.next(60 - dong_zhi_index2)
        else:
            solar_shun_bai2 = dong_zhi2.next(-dong_zhi_index2)
        solar_shun_bai_ymd2 = solar_shun_bai2.toYmd()
        if xia_zhi_index > 29:
            solar_ni_zi = xia_zhi.next(60 - xia_zhi_index)
        else:
            solar_ni_zi = xia_zhi.next(-xia_zhi_index)
        solar_ni_zi_ymd = solar_ni_zi.toYmd()
        offset = 0
        if solar_shun_bai_ymd <= solar_ymd < solar_ni_zi_ymd:
            offset = self.__solar.subtract(solar_shun_bai) % 9
        elif solar_ni_zi_ymd <= solar_ymd < solar_shun_bai_ymd2:
            offset = 8 - (self.__solar.subtract(solar_ni_zi) % 9)
        elif solar_ymd >= solar_shun_bai_ymd2:
            offset = self.__solar.subtract(solar_shun_bai2) % 9
        elif solar_ymd < solar_shun_bai_ymd:
            offset = (8 + solar_shun_bai.subtract(self.__solar)) % 9
        return NineStar.fromIndex(offset)

    def getTimeNineStar(self):
        solar_ymd = self.__solar.toYmd()
        asc = False
        if self.__jieQi["冬至"].toYmd() <= solar_ymd < self.__jieQi["夏至"].toYmd():
            asc = True
        elif solar_ymd >= self.__jieQi["DONG_ZHI"].toYmd():
            asc = True
        start = 6 if asc else 2
        day_zhi = self.getDayZhi()
        if day_zhi in "子午卯酉":
            start = 0 if asc else 8
        elif day_zhi in "辰戌丑未":
            start = 3 if asc else 5
        index = start + self.__timeZhiIndex if asc else start + 9 - self.__timeZhiIndex
        return NineStar.fromIndex(index % 9)

    def getJieQiTable(self):
        return self.__jieQi

    def getJieQiList(self):
        return self.__jieQiList

    def getTimeGanIndex(self):
        return self.__timeGanIndex

    def getTimeZhiIndex(self):
        return self.__timeZhiIndex

    def getDayGanIndex(self):
        return self.__dayGanIndex

    def getDayZhiIndex(self):
        return self.__dayZhiIndex

    def getDayGanIndexExact(self):
        return self.__dayGanIndexExact

    def getDayGanIndexExact2(self):
        return self.__dayGanIndexExact2

    def getDayZhiIndexExact(self):
        return self.__dayZhiIndexExact

    def getDayZhiIndexExact2(self):
        return self.__dayZhiIndexExact2

    def getMonthGanIndex(self):
        return self.__monthGanIndex

    def getMonthZhiIndex(self):
        return self.__monthZhiIndex

    def getMonthGanIndexExact(self):
        return self.__monthGanIndexExact

    def getMonthZhiIndexExact(self):
        return self.__monthZhiIndexExact

    def getYearGanIndex(self):
        return self.__yearGanIndex

    def getYearZhiIndex(self):
        return self.__yearZhiIndex

    def getYearGanIndexByLiChun(self):
        return self.__yearGanIndexByLiChun

    def getYearZhiIndexByLiChun(self):
        return self.__yearZhiIndexByLiChun

    def getYearGanIndexExact(self):
        return self.__yearGanIndexExact

    def getYearZhiIndexExact(self):
        return self.__yearZhiIndexExact

    def getNextJie(self, whole_day=False):
        """
        获取下一节（顺推的第一个节）
        :param whole_day: 是否按天计
        :return: 节气
        """
        conditions = []
        for i in range(0, int(len(Lunar.JIE_QI_IN_USE) / 2)):
            conditions.append(Lunar.JIE_QI_IN_USE[i * 2])
        return self.__getNearJieQi(True, conditions, whole_day)

    def getPrevJie(self, whole_day=False):
        """
        获取上一节（逆推的第一个节）
        :param whole_day: 是否按天计
        :return: 节气
        """
        conditions = []
        for i in range(0, int(len(Lunar.JIE_QI_IN_USE) / 2)):
            conditions.append(Lunar.JIE_QI_IN_USE[i * 2])
        return self.__getNearJieQi(False, conditions, whole_day)

    def getNextQi(self, whole_day=False):
        """
        获取下一气令（顺推的第一个气令）
        :param whole_day: 是否按天计
        :return: 节气
        """
        conditions = []
        for i in range(0, int(len(Lunar.JIE_QI_IN_USE) / 2)):
            conditions.append(Lunar.JIE_QI_IN_USE[i * 2 + 1])
        return self.__getNearJieQi(True, conditions, whole_day)

    def getPrevQi(self, whole_day=False):
        """
        获取上一气令（逆推的第一个气令）
        :param whole_day: 是否按天计
        :return: 节气
        """
        conditions = []
        for i in range(0, int(len(Lunar.JIE_QI_IN_USE) / 2)):
            conditions.append(Lunar.JIE_QI_IN_USE[i * 2 + 1])
        return self.__getNearJieQi(False, conditions, whole_day)

    def getNextJieQi(self, whole_day=False):
        """
        获取下一节气（顺推的第一个节气）
        :param whole_day: 是否按天计
        :return: 节气
        """
        return self.__getNearJieQi(True, None, whole_day)

    def getPrevJieQi(self, whole_day=False):
        """
        获取上一节气（逆推的第一个节气）
        :param whole_day: 是否按天计
        :return: 节气
        """
        return self.__getNearJieQi(False, None, whole_day)

    def __getNearJieQi(self, forward, conditions, whole_day):
        """
        获取最近的节气，如果未找到匹配的，返回null
        :param forward: 是否顺推，true为顺推，false为逆推
        :param conditions: 过滤条件，如果设置过滤条件，仅返回匹配该名称的
        :param whole_day: 是否按天计
        :return: 节气
        """
        name = None
        near = None
        filters = set()
        if conditions is not None:
            for cond in conditions:
                filters.add(cond)
        is_filter = len(filters) > 0
        today = self.__solar.toYmd() if whole_day else self.__solar.toYmdHms()
        for key in self.JIE_QI_IN_USE:
            jq = self.__convertJieQi(key)
            if is_filter and not filters.__contains__(jq):
                continue
            solar = self.__jieQi[key]
            day = solar.toYmd() if whole_day else solar.toYmdHms()
            if forward:
                if day <= today:
                    continue
                if near is None:
                    name = jq
                    near = solar
                else:
                    near_day = near.toYmd() if whole_day else near.toYmdHms()
                    if day < near_day:
                        name = jq
                        near = solar
            else:
                if day > today:
                    continue
                if near is None:
                    name = jq
                    near = solar
                else:
                    near_day = near.toYmd() if whole_day else near.toYmdHms()
                    if day > near_day:
                        name = jq
                        near = solar
        if near is None:
            return None
        return JieQi(name, near)

    def getJieQi(self):
        """
        获取节气名称，如果无节气，返回空字符串
        :return: 节气名称
        """
        for key in self.__jieQi:
            d = self.__jieQi[key]
            if d.getYear() == self.__solar.getYear() and d.getMonth() == self.__solar.getMonth() and d.getDay() == self.__solar.getDay():
                return self.__convertJieQi(key)
        return ""

    def getCurrentJieQi(self):
        """
        获取当天节气对象，如果无节气，返回None
        :return: 节气对象
        """
        for key in self.__jieQi:
            d = self.__jieQi[key]
            if d.getYear() == self.__solar.getYear() and d.getMonth() == self.__solar.getMonth() and d.getDay() == self.__solar.getDay():
                return JieQi(self.__convertJieQi(key), self.__solar)
        return None

    def getCurrentJie(self):
        """
        获取当天节令对象，如果无节令，返回None
        :return: 节气对象
        """
        for i in range(0, len(Lunar.JIE_QI_IN_USE), 2):
            key = Lunar.JIE_QI_IN_USE[i]
            d = self.__jieQi[key]
            if d.getYear() == self.__solar.getYear() and d.getMonth() == self.__solar.getMonth() and d.getDay() == self.__solar.getDay():
                return JieQi(self.__convertJieQi(key), d)
        return None

    def getCurrentQi(self):
        """
        获取当天气令对象，如果无气令，返回None
        :return: 节气对象
        """
        for i in range(1, len(Lunar.JIE_QI_IN_USE), 2):
            key = Lunar.JIE_QI_IN_USE[i]
            d = self.__jieQi[key]
            if d.getYear() == self.__solar.getYear() and d.getMonth() == self.__solar.getMonth() and d.getDay() == self.__solar.getDay():
                return JieQi(self.__convertJieQi(key), d)
        return None

    def next(self, days):
        """
        获取往后推几天的农历日期，如果要往前推，则天数用负数
        :param days: 天数
        :return: 农历日期
        """
        return self.__solar.next(days).getLunar()

    def __str__(self):
        return self.toString()

    def toString(self):
        return "%s年%s月%s" % (self.getYearInChinese(), self.getMonthInChinese(), self.getDayInChinese())

    def toFullString(self):
        s = self.toString()
        s += " " + self.getYearInGanZhi() + "(" + self.getYearShengXiao() + ")年"
        s += " " + self.getMonthInGanZhi() + "(" + self.getMonthShengXiao() + ")月"
        s += " " + self.getDayInGanZhi() + "(" + self.getDayShengXiao() + ")日"
        s += " " + self.getTimeZhi() + "(" + self.getTimeShengXiao() + ")时"
        s += " 纳音[" + self.getYearNaYin() + " " + self.getMonthNaYin() + " " + self.getDayNaYin() + " " + self.getTimeNaYin() + "]"
        s += " 星期" + self.getWeekInChinese()
        for f in self.getFestivals():
            s += " (" + f + ")"
        for f in self.getOtherFestivals():
            s += " (" + f + ")"
        jq = self.getJieQi()
        if len(jq) > 0:
            s += " [" + jq + "]"
        s += " " + self.getGong() + "方" + self.getShou()
        s += " 星宿[" + self.getXiu() + self.getZheng() + self.getAnimal() + "](" + self.getXiuLuck() + ")"
        s += " 彭祖百忌[" + self.getPengZuGan() + " " + self.getPengZuZhi() + "]"
        s += " 喜神方位[" + self.getDayPositionXi() + "](" + self.getDayPositionXiDesc() + ")"
        s += " 阳贵神方位[" + self.getDayPositionYangGui() + "](" + self.getDayPositionYangGuiDesc() + ")"
        s += " 阴贵神方位[" + self.getDayPositionYinGui() + "](" + self.getDayPositionYinGuiDesc() + ")"
        s += " 福神方位[" + self.getDayPositionFu() + "](" + self.getDayPositionFuDesc() + ")"
        s += " 财神方位[" + self.getDayPositionCai() + "](" + self.getDayPositionCaiDesc() + ")"
        s += " 冲[" + self.getChongDesc() + "]"
        s += " 煞[" + self.getSha() + "]"
        return s

    def getYearXun(self):
        """
        获取年所在旬（以正月初一作为新年的开始）
        :return: 旬
        """
        return LunarUtil.getXun(self.getYearInGanZhi())

    def getYearXunByLiChun(self):
        """
        获取年所在旬（以立春当天作为新年的开始）
        :return: 旬
        """
        return LunarUtil.getXun(self.getYearInGanZhiByLiChun())

    def getYearXunExact(self):
        """
        获取年所在旬（以立春交接时刻作为新年的开始）
        :return: 旬
        """
        return LunarUtil.getXun(self.getYearInGanZhiExact())

    def getYearXunKong(self):
        """
        获取值年空亡（以正月初一作为新年的开始）
        :return: 空亡(旬空)
        """
        return LunarUtil.getXunKong(self.getYearInGanZhi())

    def getYearXunKongByLiChun(self):
        """
        获取值年空亡（以立春当天作为新年的开始）
        :return: 空亡(旬空)
        """
        return LunarUtil.getXunKong(self.getYearInGanZhiByLiChun())

    def getYearXunKongExact(self):
        """
        获取值年空亡（以立春交接时刻作为新年的开始）
        :return: 空亡(旬空)
        """
        return LunarUtil.getXunKong(self.getYearInGanZhiExact())

    def getMonthXun(self):
        """
        获取月所在旬（以节交接当天起算）
        :return: 旬
        """
        return LunarUtil.getXun(self.getMonthInGanZhi())

    def getMonthXunExact(self):
        """
        获取月所在旬（以节交接时刻起算）
        :return: 旬
        """
        return LunarUtil.getXun(self.getMonthInGanZhiExact())

    def getMonthXunKong(self):
        """
        获取值月空亡（以节交接当天起算）
        :return: 空亡(旬空)
        """
        return LunarUtil.getXunKong(self.getMonthInGanZhi())

    def getMonthXunKongExact(self):
        """
        获取值月空亡（以节交接时刻起算）
        :return: 空亡(旬空)
        """
        return LunarUtil.getXunKong(self.getMonthInGanZhiExact())

    def getDayXun(self):
        """
        获取日所在旬（以节交接当天起算）
        :return: 旬
        """
        return LunarUtil.getXun(self.getDayInGanZhi())

    def getDayXunExact(self):
        """
        获取日所在旬（晚子时日柱算明天）
        :return: 旬
        """
        return LunarUtil.getXun(self.getDayInGanZhiExact())

    def getDayXunExact2(self):
        """
        获取日所在旬（晚子时日柱算当天）
        :return: 旬
        """
        return LunarUtil.getXun(self.getDayInGanZhiExact2())

    def getDayXunKong(self):
        """
        获取值日空亡
        :return: 空亡(旬空)
        """
        return LunarUtil.getXunKong(self.getDayInGanZhi())

    def getDayXunKongExact(self):
        """
        获取值日空亡（晚子时日柱算明天）
        :return: 空亡(旬空)
        """
        return LunarUtil.getXunKong(self.getDayInGanZhiExact())

    def getDayXunKongExact2(self):
        """
        获取值日空亡（晚子时日柱算当天）
        :return: 空亡(旬空)
        """
        return LunarUtil.getXunKong(self.getDayInGanZhiExact2())

    def getTimeXun(self):
        """
        获取时辰所在旬
        :return: 旬
        """
        return LunarUtil.getXun(self.getTimeInGanZhi())

    def getTimeXunKong(self):
        """
        获取值时空亡
        :return: 空亡(旬空)
        """
        return LunarUtil.getXunKong(self.getTimeInGanZhi())

    def getShuJiu(self):
        """
        获取数九
        :return: 数九，如果不是数九天，返回None
        """
        current = Solar.fromYmd(self.__solar.getYear(), self.__solar.getMonth(), self.__solar.getDay())
        start = self.__jieQi["DONG_ZHI"]
        start = Solar.fromYmd(start.getYear(), start.getMonth(), start.getDay())
        if current.isBefore(start):
            start = self.__jieQi["冬至"]
            start = Solar.fromYmd(start.getYear(), start.getMonth(), start.getDay())
        end = Solar.fromYmd(start.getYear(), start.getMonth(), start.getDay()).next(81)
        if current.isBefore(start) or not current.isBefore(end):
            return None
        days = current.subtract(start)
        return ShuJiu(LunarUtil.NUMBER[int(days / 9) + 1] + "九", days % 9 + 1)

    def getFu(self):
        """
        获取三伏
        :return: 三伏，如果不是伏天，返回None
        """
        current = Solar.fromYmd(self.__solar.getYear(), self.__solar.getMonth(), self.__solar.getDay())
        xia_zhi = self.__jieQi["夏至"]
        li_qiu = self.__jieQi["立秋"]
        start = Solar.fromYmd(xia_zhi.getYear(), xia_zhi.getMonth(), xia_zhi.getDay())
        add = 6 - xia_zhi.getLunar().getDayGanIndex()
        if add < 0:
            add += 10
        add += 20
        start = start.next(add)
        if current.isBefore(start):
            return None
        days = current.subtract(start)
        if days < 10:
            return Fu("初伏", days + 1)
        start = start.next(10)
        days = current.subtract(start)
        if days < 10:
            return Fu("中伏", days + 1)
        start = start.next(10)
        days = current.subtract(start)
        li_qiu_solar = Solar.fromYmd(li_qiu.getYear(), li_qiu.getMonth(), li_qiu.getDay())
        if li_qiu_solar.isAfter(start):
            if days < 10:
                return Fu("中伏", days + 11)
            start = start.next(10)
            days = current.subtract(start)
        if days < 10:
            return Fu("末伏", days + 1)
        return None

    def getLiuYao(self):
        """
        获取六曜
        :return: 六曜
        """
        return LunarUtil.LIU_YAO[(abs(self.__month) + self.__day - 2) % 6]

    def getWuHou(self):
        """
        获取物候
        :return: 物候
        """
        jie_qi = self.getPrevJieQi(True)
        offset = 0
        for i in range(0, len(Lunar.JIE_QI)):
            if jie_qi.getName() == Lunar.JIE_QI[i]:
                offset = i
                break
        index = int(self.__solar.subtract(jie_qi.getSolar()) / 5)
        if index > 2:
            index = 2
        return LunarUtil.WU_HOU[(offset * 3 + index) % len(LunarUtil.WU_HOU)]

    def getHou(self):
        jie_qi = self.getPrevJieQi(True)
        size = len(LunarUtil.HOU) - 1
        offset = int(self.__solar.subtract(jie_qi.getSolar()) / 5)
        if offset > size:
            offset = size
        return "%s %s" % (jie_qi.getName(), LunarUtil.HOU[offset])

    def getDayLu(self):
        """
        获取日禄
        :return: 日禄
        """
        gan = LunarUtil.LU[self.getDayGan()]
        zhi = None
        if self.getDayZhi() in LunarUtil.LU:
            zhi = LunarUtil.LU[self.getDayZhi()]
        lu = gan + "命互禄"
        if zhi is not None:
            lu += " " + zhi + "命进禄"
        return lu

    def getTime(self):
        """
        获取时辰
        :return: 时辰
        """
        return LunarTime.fromYmdHms(self.__year, self.__month, self.__day, self.__hour, self.__minute, self.__second)

    def getTimes(self):
        """
        获取当天的时辰列表
        :return: 时辰列表
        """
        times = [LunarTime.fromYmdHms(self.__year, self.__month, self.__day, 0, 0, 0)]
        for i in range(0, 12):
            times.append(LunarTime.fromYmdHms(self.__year, self.__month, self.__day, (i+1) * 2-1, 0, 0))
        return times

    def getFoto(self):
        """
        获取佛历
        :return: 佛历
        """
        from . import Foto
        return Foto.fromLunar(self)

    def getTao(self):
        """
        获取道历
        :return: 道历
        """
        from . import Tao
        return Tao.fromLunar(self)

"""

_sources["LunarMonth"] = """\
# -*- coding: utf-8 -*-
from . import Solar, LunarYear, NineStar
from .util import LunarUtil


class LunarMonth:
    """
    农历月
    """

    def __init__(self, lunar_year, lunar_month, day_count, first_julian_day, index):
        self.__year = lunar_year
        self.__month = lunar_month
        self.__dayCount = day_count
        self.__firstJulianDay = first_julian_day
        self.__index = index
        self.__zhiIndex = (abs(lunar_month) - 1 + LunarUtil.BASE_MONTH_ZHI_INDEX) % 12

    @staticmethod
    def fromYm(lunar_year, lunar_month):
        from . import LunarYear
        return LunarYear.fromYear(lunar_year).getMonth(lunar_month)

    def getYear(self):
        return self.__year

    def getMonth(self):
        return self.__month

    def getIndex(self):
        return self.__index

    def getZhiIndex(self):
        return self.__zhiIndex

    def getGanIndex(self):
        offset = (LunarYear.fromYear(self.__year).getGanIndex() + 1) % 5 * 2
        return (abs(self.__month) - 1 + offset) % 10

    def getGan(self):
        return LunarUtil.GAN[self.getGanIndex() + 1]

    def getZhi(self):
        return LunarUtil.ZHI[self.getZhiIndex() + 1]

    def getGanZhi(self):
        return "%s%s" % (self.getGan(), self.getZhi())

    def getPositionXi(self):
        return LunarUtil.POSITION_XI[self.getGanIndex() + 1]

    def getPositionXiDesc(self):
        return LunarUtil.POSITION_DESC[self.getPositionXi()]

    def getPositionYangGui(self):
        return LunarUtil.POSITION_YANG_GUI[self.getGanIndex() + 1]

    def getPositionYangGuiDesc(self):
        return LunarUtil.POSITION_DESC[self.getPositionYangGui()]

    def getPositionYinGui(self):
        return LunarUtil.POSITION_YIN_GUI[self.getGanIndex() + 1]

    def getPositionYinGuiDesc(self):
        return LunarUtil.POSITION_DESC[self.getPositionYinGui()]

    def getPositionFu(self, sect=2):
        return (LunarUtil.POSITION_FU if 1 == sect else LunarUtil.POSITION_FU_2)[self.getGanIndex() + 1]

    def getPositionFuDesc(self, sect=2):
        return LunarUtil.POSITION_DESC[self.getPositionFu(sect)]

    def getPositionCai(self):
        return LunarUtil.POSITION_CAI[self.getGanIndex() + 1]

    def getPositionCaiDesc(self):
        return LunarUtil.POSITION_DESC[self.getPositionCai()]

    def isLeap(self):
        return self.__month < 0

    def getDayCount(self):
        return self.__dayCount

    def getFirstJulianDay(self):
        return self.__firstJulianDay

    def getPositionTaiSui(self):
        m = abs(self.__month) % 4
        if 0 == m:
            p = "巽"
        elif 1 == m:
            p = "艮"
        elif 3 == m:
            p = "坤"
        else:
            p = LunarUtil.POSITION_GAN[Solar.fromJulianDay(self.getFirstJulianDay()).getLunar().getMonthGanIndex()]
        return p

    def getPositionTaiSuiDesc(self):
        return LunarUtil.POSITION_DESC[self.getPositionTaiSui()]

    def getNineStar(self):
        index = LunarYear.fromYear(self.__year).getZhiIndex() % 3
        m = abs(self.__month)
        month_zhi_index = (13 + m) % 12
        n = 27 - (index * 3)
        if month_zhi_index < LunarUtil.BASE_MONTH_ZHI_INDEX:
            n -= 3
        offset = (n - month_zhi_index) % 9
        return NineStar.fromIndex(offset)

    def toString(self):
        return "%d年%s%s月(%d天)" % (self.__year, ("闰" if self.isLeap() else ""), LunarUtil.MONTH[abs(self.__month)], self.__dayCount)

    def __str__(self):
        return self.toString()

    def next(self, n):
        """
        获取往后推几个月的阴历月，如果要往前推，则月数用负数
        :param n: 月数
        :return: 阴历月
        """
        if 0 == n:
            return LunarMonth.fromYm(self.__year, self.__month)
        elif n > 0:
            rest = n
            ny = self.__year
            iy = ny
            im = self.__month
            index = 0
            months = LunarYear.fromYear(ny).getMonths()
            while True:
                size = len(months)
                for i in range(0, size):
                    m = months[i]
                    if m.getYear() == iy and m.getMonth() == im:
                        index = i
                        break
                more = size - index - 1
                if rest < more:
                    break
                rest -= more
                last_month = months[size - 1]
                iy = last_month.getYear()
                im = last_month.getMonth()
                ny += 1
                months = LunarYear.fromYear(ny).getMonths()
            return months[index + rest]
        else:
            rest = -n
            ny = self.__year
            iy = ny
            im = self.__month
            index = 0
            months = LunarYear.fromYear(ny).getMonths()
            while True:
                size = len(months)
                for i in range(0, size):
                    m = months[i]
                    if m.getYear() == iy and m.getMonth() == im:
                        index = i
                        break
                if rest <= index:
                    break
                rest -= index
                first_month = months[0]
                iy = first_month.getYear()
                im = first_month.getMonth()
                ny -= 1
                months = LunarYear.fromYear(ny).getMonths()
            return months[index - rest]

"""

_sources["LunarTime"] = """\
# -*- coding: utf-8 -*-
from . import NineStar
from .util import LunarUtil


class LunarTime:
    """
    时辰
    """

    def __init__(self, lunar_year, lunar_month, lunar_day, hour, minute, second):
        from . import Lunar
        self.__lunar = Lunar.fromYmdHms(lunar_year, lunar_month, lunar_day, hour, minute, second)
        self.__zhiIndex = LunarUtil.getTimeZhiIndex("%02d:%02d" % (hour, minute))
        self.__ganIndex = (self.__lunar.getDayGanIndexExact() % 5 * 2 + self.__zhiIndex) % 10

    @staticmethod
    def fromYmdHms(lunar_year, lunar_month, lunar_day, hour, minute, second):
        return LunarTime(lunar_year, lunar_month, lunar_day, hour, minute, second)

    def getGan(self):
        return LunarUtil.GAN[self.__ganIndex + 1]

    def getZhi(self):
        return LunarUtil.ZHI[self.__zhiIndex + 1]

    def getGanZhi(self):
        return "%s%s" % (self.getGan(), self.getZhi())

    def getShengXiao(self):
        return LunarUtil.SHENGXIAO[self.__zhiIndex + 1]

    def getPositionXi(self):
        return LunarUtil.POSITION_XI[self.__ganIndex + 1]

    def getPositionXiDesc(self):
        return LunarUtil.POSITION_DESC[self.getPositionXi()]

    def getPositionYangGui(self):
        return LunarUtil.POSITION_YANG_GUI[self.__ganIndex + 1]

    def getPositionYangGuiDesc(self):
        return LunarUtil.POSITION_DESC[self.getPositionYangGui()]

    def getPositionYinGui(self):
        return LunarUtil.POSITION_YIN_GUI[self.__ganIndex + 1]

    def getPositionYinGuiDesc(self):
        return LunarUtil.POSITION_DESC[self.getPositionYinGui()]

    def getPositionFu(self, sect=2):
        return (LunarUtil.POSITION_FU if 1 == sect else LunarUtil.POSITION_FU_2)[self.__ganIndex + 1]

    def getPositionFuDesc(self, sect=2):
        return LunarUtil.POSITION_DESC[self.getPositionFu(sect)]

    def getPositionCai(self):
        return LunarUtil.POSITION_CAI[self.__ganIndex + 1]

    def getPositionCaiDesc(self):
        return LunarUtil.POSITION_DESC[self.getPositionCai()]

    def getChong(self):
        return LunarUtil.CHONG[self.__zhiIndex]

    def getChongGan(self):
        return LunarUtil.CHONG_GAN[self.__ganIndex]

    def getChongGanTie(self):
        return LunarUtil.CHONG_GAN_TIE[self.__ganIndex]

    def getChongShengXiao(self):
        chong = self.getChong()
        for i in range(0, len(LunarUtil.ZHI)):
            if LunarUtil.ZHI[i] == chong:
                return LunarUtil.SHENGXIAO[i]
        return ""

    def getChongDesc(self):
        return "(" + self.getChongGan() + self.getChong() + ")" + self.getChongShengXiao()

    def getSha(self):
        return LunarUtil.SHA[self.getZhi()]

    def getNaYin(self):
        return LunarUtil.NAYIN[self.getGanZhi()]

    def getTianShen(self):
        return LunarUtil.TIAN_SHEN[(self.__zhiIndex + LunarUtil.ZHI_TIAN_SHEN_OFFSET[self.__lunar.getDayZhiExact()]) % 12 + 1]

    def getTianShenType(self):
        return LunarUtil.TIAN_SHEN_TYPE[self.getTianShen()]

    def getTianShenLuck(self):
        return LunarUtil.TIAN_SHEN_TYPE_LUCK[self.getTianShenType()]

    def getYi(self):
        """
        获取时宜
        :return: 宜
        """
        return LunarUtil.getTimeYi(self.__lunar.getDayInGanZhiExact(), self.getGanZhi())

    def getJi(self):
        """
        获取时忌
        :return: 忌
        """
        return LunarUtil.getTimeJi(self.__lunar.getDayInGanZhiExact(), self.getGanZhi())

    def getNineStar(self):
        solar_ymd = self.__lunar.getSolar().toYmd()
        jie_qi = self.__lunar.getJieQiTable()
        asc = False
        if jie_qi["冬至"] <= solar_ymd < jie_qi["夏至"]:
            asc = True
        start = 7 if asc else 3
        day_zhi = self.__lunar.getDayZhi()
        if day_zhi in "子午卯酉":
            start = 1 if asc else 9
        elif day_zhi in "辰戌丑未":
            start = 4 if asc else 6
        index = start + self.__zhiIndex - 1 if asc else start - self.__zhiIndex - 1

        if index > 8:
            index -= 9
        if index < 0:
            index += 9
        return NineStar.fromIndex(index)

    def getGanIndex(self):
        return self.__ganIndex

    def getZhiIndex(self):
        return self.__zhiIndex

    def __str__(self):
        return self.toString()

    def toString(self):
        return self.getGanZhi()

    def getXun(self):
        """
        获取时辰所在旬
        :return: 旬
        """
        return LunarUtil.getXun(self.getGanZhi())

    def getXunKong(self):
        """
        获取值时空亡
        :return: 空亡(旬空)
        """
        return LunarUtil.getXunKong(self.getGanZhi())

    def getMinHm(self):
        hour = self.__lunar.getHour()
        if hour < 1:
            return "00:00"
        elif hour > 22:
            return "23:00"
        return "%02d:00" % (hour - 1 if hour % 2 == 0 else hour)

    def getMaxHm(self):
        hour = self.__lunar.getHour()
        if hour < 1:
            return "00:59"
        elif hour > 22:
            return "23:59"
        return "%02d:59" % (hour + 1 if hour % 2 != 0 else hour)

"""

_sources["LunarYear"] = """\
# -*- coding: utf-8 -*-
import threading
from math import floor
from . import Solar, NineStar
from .util import ShouXingUtil, LunarUtil


class LunarYear:
    """
    农历年
    """

    YUAN = ("下", "上", "中")

    YUN = ("七", "八", "九", "一", "二", "三", "四", "五", "六")

    __LEAP_11 = (75, 94, 170, 265, 322, 398, 469, 553, 583, 610, 678, 735, 754, 773, 849, 887, 936, 1050, 1069, 1126, 1145, 1164, 1183, 1259, 1278, 1308, 1373, 1403, 1441, 1460, 1498, 1555, 1593, 1612, 1631, 1642, 2033, 2128, 2147, 2242, 2614, 2728, 2910, 3062, 3244, 3339, 3616, 3711, 3730, 3825, 4007, 4159, 4197, 4322, 4341, 4379, 4417, 4531, 4599, 4694, 4713, 4789, 4808, 4971, 5085, 5104, 5161, 5180, 5199, 5294, 5305, 5476, 5677, 5696, 5772, 5791, 5848, 5886, 6049, 6068, 6144, 6163, 6258, 6402, 6440, 6497, 6516, 6630, 6641, 6660, 6679, 6736, 6774, 6850, 6869, 6899, 6918, 6994, 7013, 7032, 7051, 7070, 7089, 7108, 7127, 7146, 7222, 7271, 7290, 7309, 7366, 7385, 7404, 7442, 7461, 7480, 7491, 7499, 7594, 7624, 7643, 7662, 7681, 7719, 7738, 7814, 7863, 7882, 7901, 7939, 7958, 7977, 7996,
                 8034, 8053, 8072, 8091, 8121, 8159, 8186, 8216, 8235, 8254, 8273, 8311, 8330, 8341, 8349, 8368, 8444, 8463, 8474, 8493, 8531, 8569, 8588, 8626, 8664, 8683, 8694, 8702, 8713, 8721, 8751, 8789, 8808, 8816, 8827, 8846, 8884, 8903, 8922, 8941, 8971, 9036, 9066, 9085, 9104, 9123, 9142, 9161, 9180, 9199, 9218, 9256, 9294, 9313, 9324, 9343, 9362, 9381, 9419, 9438, 9476, 9514, 9533, 9544, 9552, 9563, 9571, 9582, 9601, 9639, 9658, 9666, 9677, 9696, 9734, 9753, 9772, 9791, 9802, 9821, 9886, 9897, 9916, 9935, 9954, 9973, 9992)

    __LEAP_12 = (37, 56, 113, 132, 151, 189, 208, 227, 246, 284, 303, 341, 360, 379, 417, 436, 458, 477, 496, 515, 534, 572, 591, 629, 648, 667, 697, 716, 792, 811, 830, 868, 906, 925, 944, 963, 982, 1001, 1020, 1039, 1058, 1088, 1153, 1202, 1221, 1240, 1297, 1335, 1392, 1411, 1422, 1430, 1517, 1525, 1536, 1574, 3358, 3472, 3806, 3988, 4751, 4941, 5066, 5123, 5275, 5343, 5438, 5457, 5495, 5533, 5552, 5715, 5810, 5829, 5905, 5924, 6421, 6535, 6793, 6812, 6888, 6907, 7002, 7184, 7260, 7279, 7374, 7556, 7746, 7757, 7776, 7833, 7852, 7871, 7966, 8015, 8110, 8129, 8148, 8224, 8243, 8338, 8406, 8425, 8482, 8501, 8520, 8558, 8596, 8607, 8615, 8645, 8740, 8778, 8835, 8865, 8930, 8960, 8979, 8998, 9017, 9055, 9074, 9093, 9112, 9150, 9188, 9237, 9275, 9332, 9351, 9370, 9408, 9427, 9446, 9457, 9465,
                 9495, 9560, 9590, 9628, 9647, 9685, 9715, 9742, 9780, 9810, 9818, 9829, 9848, 9867, 9905, 9924, 9943, 9962, 10000)

    __CACHE_YEAR = None

    __lock = threading.Lock()

    def __init__(self, lunar_year):
        self.__year = lunar_year
        offset = lunar_year - 4
        year_gan_index = offset % 10
        year_zhi_index = offset % 12
        if year_gan_index < 0:
            year_gan_index += 10
        if year_zhi_index < 0:
            year_zhi_index += 12
        self.__ganIndex = year_gan_index
        self.__zhiIndex = year_zhi_index
        self.__months = []
        self.__jieQiJulianDays = []
        self.compute()

    @staticmethod
    def fromYear(lunar_year):
        LunarYear.__lock.acquire()
        if LunarYear.__CACHE_YEAR is None or LunarYear.__CACHE_YEAR.getYear() != lunar_year:
            y = LunarYear(lunar_year)
            LunarYear.__CACHE_YEAR = y
        else:
            y = LunarYear.__CACHE_YEAR
        LunarYear.__lock.release()
        return y

    def compute(self):
        from . import Lunar, Solar, LunarMonth
        # 节气
        jq = []
        # 合朔，即每月初一
        hs = []
        # 每月天数，长度15
        day_counts = []
        # 月份
        months = []

        current_year = self.__year
        jd = floor((current_year - 2000) * 365.2422 + 180)
        # 355是2000.12冬至，得到较靠近jd的冬至估计值
        w = floor((jd - 355 + 183) / 365.2422) * 365.2422 + 355
        if ShouXingUtil.calcQi(w) > jd:
            w -= 365.2422
        # 25个节气时刻(北京时间)，从冬至开始到下一个冬至以后
        for i in range(0, 26):
            jq.append(ShouXingUtil.calcQi(w + 15.2184 * i))

        # 从上年的大雪到下年的立春 精确的节气
        for i in range(0, len(Lunar.JIE_QI_IN_USE)):
            if i == 0:
                jd = ShouXingUtil.qiAccurate2(jq[0] - 15.2184)
            elif i <= 26:
                jd = ShouXingUtil.qiAccurate2(jq[i - 1])
            else:
                jd = ShouXingUtil.qiAccurate2(jq[25] + 15.2184 * (i - 26))
            self.__jieQiJulianDays.append(jd + Solar.J2000)

        # 冬至前的初一，今年"首朔"的日月黄经差w
        w = ShouXingUtil.calcShuo(jq[0])
        if w > jq[0]:
            w -= 29.53
        # 递推每月初一
        for i in range(0, 16):
            hs.append(ShouXingUtil.calcShuo(w + 29.5306 * i))
        # 每月
        for i in range(0, 15):
            day_counts.append(int(hs[i + 1] - hs[i]))
            months.append(i)

        prev_year = current_year - 1
        leap_index = 16

        if current_year in LunarYear.__LEAP_11:
            leap_index = 13
        elif current_year in LunarYear.__LEAP_12:
            leap_index = 14
        elif hs[13] <= jq[24]:
            i = 1
            while hs[i + 1] > jq[2 * i] and i < 13:
                i += 1
            leap_index = i
        for j in range(leap_index, 15):
            months[j] -= 1
        ymc = [11, 12, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

        fm = -1
        index = -1
        y = prev_year
        for i in range(0, 15):
            dm = hs[i] + Solar.J2000
            v2 = months[i]
            mc = ymc[v2 % 12]
            if 1724360 <= dm < 1729794:
                mc = ymc[(v2 + 1) % 12]
            elif 1807724 <= dm < 1808699:
                mc = ymc[(v2 + 1) % 12]
            elif dm == 1729794 or dm == 1808699:
                mc = 12
            if fm == -1:
                fm = mc
                index = mc
            if mc < fm:
                y += 1
                index = 1
            fm = mc
            if i == leap_index:
                mc = -mc
            elif dm == 1729794 or dm == 1808699:
                mc = -11
            self.__months.append(LunarMonth(y, mc, day_counts[i], dm, index))
            index += 1

    def getYear(self):
        return self.__year

    def getGanIndex(self):
        return self.__ganIndex

    def getZhiIndex(self):
        return self.__zhiIndex

    def getGan(self):
        return LunarUtil.GAN[self.__ganIndex + 1]

    def getZhi(self):
        return LunarUtil.ZHI[self.__zhiIndex + 1]

    def getGanZhi(self):
        return "%s%s" % (self.getGan(), self.getZhi())

    def toString(self):
        return str(self.__year) + ""

    def toFullString(self):
        return "%d年" % self.__year

    def __str__(self):
        return self.toString()

    def getDayCount(self):
        n = 0
        for m in self.__months:
            if m.getYear() == self.__year:
                n += m.getDayCount()
        return n

    def getMonthsInYear(self):
        months = []
        for m in self.__months:
            if m.getYear() == self.__year:
                months.append(m)
        return months

    def getMonths(self):
        return self.__months

    def getJieQiJulianDays(self):
        return self.__jieQiJulianDays

    def getLeapMonth(self):
        """
        获取闰月
        :return: 闰月数字，1代表闰1月，0代表无闰月
        """
        for m in self.__months:
            if m.getYear() == self.__year and m.isLeap():
                return abs(m.getMonth())
        return 0

    def getMonth(self, lunar_month):
        """
        获取农历月
        :param lunar_month: 闰月数字，1代表闰1月，0代表无闰月
        :return: 农历月
        """
        for m in self.__months:
            if m.getYear() == self.__year and m.getMonth() == lunar_month:
                return m
        return None

    def __getZaoByGan(self, index, name):
        offset = index - Solar.fromJulianDay(self.getMonth(1).getFirstJulianDay()).getLunar().getDayGanIndex()
        if offset < 0:
            offset += 10
        return name.replace("几", LunarUtil.NUMBER[offset + 1], 1)

    def __getZaoByZhi(self, index, name):
        offset = index - Solar.fromJulianDay(self.getMonth(1).getFirstJulianDay()).getLunar().getDayZhiIndex()
        if offset < 0:
            offset += 12
        return name.replace("几", LunarUtil.NUMBER[offset + 1], 1)

    def getTouLiang(self):
        return self.__getZaoByZhi(0, "几鼠偷粮")

    def getCaoZi(self):
        return self.__getZaoByZhi(0, "草子几分")

    def getGengTian(self):
        """
        获取耕田（正月第一个丑日是初几，就是几牛耕田）
        :return: 耕田，如：六牛耕田
        """
        return self.__getZaoByZhi(1, "几牛耕田")

    def getHuaShou(self):
        return self.__getZaoByZhi(3, "花收几分")

    def getZhiShui(self):
        """
        获取治水（正月第一个辰日是初几，就是几龙治水）
        :return: 治水，如：二龙治水
        """
        return self.__getZaoByZhi(4, "几龙治水")

    def getTuoGu(self):
        return self.__getZaoByZhi(6, "几马驮谷")

    def getQiangMi(self):
        return self.__getZaoByZhi(9, "几鸡抢米")

    def getKanCan(self):
        return self.__getZaoByZhi(9, "几姑看蚕")

    def getGongZhu(self):
        return self.__getZaoByZhi(11, "几屠共猪")

    def getJiaTian(self):
        return self.__getZaoByGan(0, "甲田几分")

    def getFenBing(self):
        """
        获取分饼（正月第一个丙日是初几，就是几人分饼）
        :return: 分饼，如：六人分饼
        """
        return self.__getZaoByGan(2, "几人分饼")

    def getDeJin(self):
        """
        获取得金（正月第一个辛日是初几，就是几日得金）
        :return: 得金，如：一日得金
        """
        return self.__getZaoByGan(7, "几日得金")

    def getRenBing(self):
        return self.__getZaoByGan(2, self.__getZaoByZhi(2, "几人几丙"))

    def getRenChu(self):
        return self.__getZaoByGan(3, self.__getZaoByZhi(2, "几人几锄"))

    def getYuan(self):
        return LunarYear.YUAN[int((self.__year + 2696) / 60) % 3] + "元"

    def getYun(self):
        return LunarYear.YUN[int((self.__year + 2696) / 20) % 9] + "运"

    def getNineStar(self):
        index = LunarUtil.getJiaZiIndex(self.getGanZhi()) + 1
        yuan = int((self.__year + 2696) / 60) % 3
        offset = (62 + yuan * 3 - index) % 9
        if 0 == offset:
            offset = 9
        return NineStar.fromIndex(offset - 1)

    def getPositionXi(self):
        return LunarUtil.POSITION_XI[self.__ganIndex + 1]

    def getPositionXiDesc(self):
        return LunarUtil.POSITION_DESC[self.getPositionXi()]

    def getPositionYangGui(self):
        return LunarUtil.POSITION_YANG_GUI[self.__ganIndex + 1]

    def getPositionYangGuiDesc(self):
        return LunarUtil.POSITION_DESC[self.getPositionYangGui()]

    def getPositionYinGui(self):
        return LunarUtil.POSITION_YIN_GUI[self.__ganIndex + 1]

    def getPositionYinGuiDesc(self):
        return LunarUtil.POSITION_DESC[self.getPositionYinGui()]

    def getPositionFu(self, sect=2):
        return (LunarUtil.POSITION_FU if 1 == sect else LunarUtil.POSITION_FU_2)[self.__ganIndex + 1]

    def getPositionFuDesc(self, sect=2):
        return LunarUtil.POSITION_DESC[self.getPositionFu(sect)]

    def getPositionCai(self):
        return LunarUtil.POSITION_CAI[self.__ganIndex + 1]

    def getPositionCaiDesc(self):
        return LunarUtil.POSITION_DESC[self.getPositionCai()]

    def getPositionTaiSui(self):
        return LunarUtil.POSITION_TAI_SUI_YEAR[self.__zhiIndex]

    def getPositionTaiSuiDesc(self):
        return LunarUtil.POSITION_DESC[self.getPositionTaiSui()]

    def next(self, n):
        """
        获取往后推几年的阴历年，如果要往前推，则年数用负数
        :param n: 年数
        :return: 阴历年
        """
        return LunarYear.fromYear(self.__year + n)

"""

_sources["NineStar"] = """\
# -*- coding: utf-8 -*-
from .util import LunarUtil


class NineStar:
    """
    九星
    """

    NUMBER = ("一", "二", "三", "四", "五", "六", "七", "八", "九")
    COLOR = ("白", "黑", "碧", "绿", "黄", "白", "赤", "白", "紫")
    WU_XING = ("水", "土", "木", "木", "土", "金", "金", "土", "火")
    POSITION = ("坎", "坤", "震", "巽", "中", "乾", "兑", "艮", "离")
    NAME_BEI_DOU = ("天枢", "天璇", "天玑", "天权", "玉衡", "开阳", "摇光", "洞明", "隐元")
    NAME_XUAN_KONG = ("贪狼", "巨门", "禄存", "文曲", "廉贞", "武曲", "破军", "左辅", "右弼")
    NAME_QI_MEN = ("天蓬", "天芮", "天冲", "天辅", "天禽", "天心", "天柱", "天任", "天英")
    BA_MEN_QI_MEN = ("休", "死", "伤", "杜", "", "开", "惊", "生", "景")
    NAME_TAI_YI = ("太乙", "摄提", "轩辕", "招摇", "天符", "青龙", "咸池", "太阴", "天乙")
    TYPE_TAI_YI = ("吉神", "凶神", "安神", "安神", "凶神", "吉神", "凶神", "吉神", "吉神")
    SONG_TAI_YI = ("门中太乙明，星官号贪狼，赌彩财喜旺，婚姻大吉昌，出入无阻挡，参谒见贤良，此行三五里，黑衣别阴阳。", "门前见摄提，百事必忧疑，相生犹自可，相克祸必临，死门并相会，老妇哭悲啼，求谋并吉事，尽皆不相宜，只可藏隐遁，若动伤身疾。", "出入会轩辕，凡事必缠牵，相生全不美，相克更忧煎，远行多不利，博彩尽输钱，九天玄女法，句句不虚言。", "招摇号木星，当之事莫行，相克行人阻，阴人口舌迎，梦寐多惊惧，屋响斧自鸣，阴阳消息理，万法弗违情。", "五鬼为天符，当门阴女谋，相克无好事，行路阻中途，走失难寻觅，道逢有尼姑，此星当门值，万事有灾除。", "神光跃青龙，财气喜重重，投入有酒食，赌彩最兴隆，更逢相生旺，休言克破凶，见贵安营寨，万事总吉同。", "吾将为咸池，当之尽不宜，出入多不利，相克有灾情，赌彩全输尽，求财空手回，仙人真妙语，愚人莫与知，动用虚惊退，反复逆风吹。", "坐临太阴星，百祸不相侵，求谋悉成就，知交有觅寻，回风归来路，恐有殃伏起，密语中记取，慎乎莫轻行。", "迎来天乙星，相逢百事兴，运用和合庆，茶酒喜相迎，求谋并嫁娶，好合有天成，祸福如神验，吉凶甚分明。")
    LUCK_XUAN_KONG = ("吉", "凶", "凶", "吉", "凶", "吉", "凶", "吉", "吉")
    LUCK_QI_MEN = ("大凶", "大凶", "小吉", "大吉", "大吉", "大吉", "小凶", "小吉", "小凶")
    YIN_YANG_QI_MEN = ("阳", "阴", "阳", "阳", "阳", "阴", "阴", "阳", "阴")

    def __init__(self, index):
        self.__index = index

    @staticmethod
    def fromIndex(index):
        return NineStar(index)

    def getNumber(self):
        return NineStar.NUMBER[self.__index]

    def getColor(self):
        return NineStar.COLOR[self.__index]

    def getWuXing(self):
        return NineStar.WU_XING[self.__index]

    def getPosition(self):
        return NineStar.POSITION[self.__index]

    def getPositionDesc(self):
        return LunarUtil.POSITION_DESC[self.getPosition()]

    def getNameInXuanKong(self):
        return NineStar.NAME_XUAN_KONG[self.__index]

    def getNameInBeiDou(self):
        return NineStar.NAME_BEI_DOU[self.__index]

    def getNameInQiMen(self):
        return NineStar.NAME_QI_MEN[self.__index]

    def getNameInTaiYi(self):
        return NineStar.NAME_TAI_YI[self.__index]

    def getLuckInQiMen(self):
        return NineStar.LUCK_QI_MEN[self.__index]

    def getLuckInXuanKong(self):
        return NineStar.LUCK_XUAN_KONG[self.__index]

    def getYinYangInQiMen(self):
        return NineStar.YIN_YANG_QI_MEN[self.__index]

    def getTypeInTaiYi(self):
        return NineStar.TYPE_TAI_YI[self.__index]

    def getBaMenInQiMen(self):
        return NineStar.BA_MEN_QI_MEN[self.__index]

    def getSongInTaiYi(self):
        return NineStar.SONG_TAI_YI[self.__index]

    def getIndex(self):
        return self.__index

    def __str__(self):
        return self.toString()

    def toString(self):
        return self.getNumber() + self.getColor() + self.getWuXing() + self.getNameInBeiDou()

    def toFullString(self):
        s = self.getNumber()
        s += self.getColor()
        s += self.getWuXing()
        s += " "
        s += self.getPosition()
        s += "("
        s += self.getPositionDesc()
        s += ") "
        s += self.getNameInBeiDou()
        s += " 玄空["
        s += self.getNameInXuanKong()
        s += " "
        s += self.getLuckInXuanKong()
        s += "] 奇门["
        s += self.getNameInQiMen()
        s += " "
        s += self.getLuckInQiMen()
        if len(self.getBaMenInQiMen()) > 0:
            s += " "
            s += self.getBaMenInQiMen()
            s += "门"
        s += " "
        s += self.getYinYangInQiMen()
        s += "] 太乙["
        s += self.getNameInTaiYi()
        s += " "
        s += self.getTypeInTaiYi()
        s += "]"
        return s

"""

_sources["ShuJiu"] = """\
# -*- coding: utf-8 -*-


class ShuJiu:
    """
    数九
    """

    def __init__(self, name, index):
        self.__name = name
        self.__index = index

    def getName(self):
        return self.__name

    def setName(self, name):
        self.__name = name

    def getIndex(self):
        return self.__index

    def setIndex(self, index):
        self.__index = index

    def __str__(self):
        return self.toString()

    def toString(self):
        return self.__name

    def toFullString(self):
        return "%s第%d天" % (self.__name, self.__index)

"""

_sources["Solar"] = """\
# -*- coding: utf-8 -*-
from datetime import datetime
from math import ceil

from .util import SolarUtil, LunarUtil, HolidayUtil


class Solar:
    """
    阳历日期
    """

    # 2000年儒略日数(2000-1-1 12:00:00 UTC)
    J2000 = 2451545

    def __init__(self, year, month, day, hour, minute, second):
        if year == 1582 and month == 10:
            if 4 < day < 15:
                raise Exception("wrong solar year %d month %d day %d" % (year, month, day))
        if month < 1 or month > 12:
            raise Exception("wrong month %d" % month)
        if day < 1 or month > 31:
            raise Exception("wrong day %d" % day)
        if hour < 0 or hour > 23:
            raise Exception("wrong hour %d" % hour)
        if minute < 0 or minute > 59:
            raise Exception("wrong minute %d" % minute)
        if second < 0 or second > 59:
            raise Exception("wrong second %d" % second)
        self.__year = year
        self.__month = month
        self.__day = day
        self.__hour = hour
        self.__minute = minute
        self.__second = second

    @staticmethod
    def fromDate(date):
        return Solar(date.year, date.month, date.day, date.hour, date.minute, date.second)

    @staticmethod
    def fromJulianDay(julian_day):
        d = int(julian_day + 0.5)
        f = julian_day + 0.5 - d
        if d >= 2299161:
            c = int((d - 1867216.25) / 36524.25)
            d += 1 + c - int(c / 4)
        d += 1524
        year = int((d - 122.1) / 365.25)
        d -= int(365.25 * year)
        month = int(d / 30.601)
        d -= int(30.601 * month)
        day = d
        if month > 13:
            month -= 13
            year -= 4715
        else:
            month -= 1
            year -= 4716
        f *= 24
        hour = int(f)

        f -= hour
        f *= 60
        minute = int(f)

        f -= minute
        f *= 60
        second = int(round(f))
        if second > 59:
            second -= 60
            minute += 1
        if minute > 59:
            minute -= 60
            hour += 1
        if hour > 23:
            hour -= 24
            day += 1
        return Solar(year, month, day, hour, minute, second)

    @staticmethod
    def fromYmdHms(year, month, day, hour, minute, second):
        return Solar(year, month, day, hour, minute, second)

    @staticmethod
    def fromYmd(year, month, day):
        return Solar(year, month, day, 0, 0, 0)

    @staticmethod
    def fromBaZi(year_gan_zhi, month_gan_zhi, day_gan_zhi, time_gan_zhi, sect=2, base_year=1900):
        from . import Lunar
        sect = 1 if 1 == sect else 2
        solar_list = []
        # 月地支距寅月的偏移值
        m = LunarUtil.find(month_gan_zhi[1:], LunarUtil.ZHI, -1) - 2
        if m < 0:
            m += 12
        # 月天干要一致
        if ((LunarUtil.find(year_gan_zhi[:1], LunarUtil.GAN, -1) + 1) * 2 + m) % 10 != LunarUtil.find(month_gan_zhi[:1], LunarUtil.GAN, -1):
            return solar_list
        # 1年的立春是辛酉，序号57
        y = LunarUtil.getJiaZiIndex(year_gan_zhi) - 57
        if y < 0:
            y += 60
        y += 1
        # 节令偏移值
        m *= 2
        # 时辰地支转时刻，子时按零点算
        h = LunarUtil.find(time_gan_zhi[1:], LunarUtil.ZHI, -1) * 2
        hours = [h]
        if 0 == h and 2 == sect:
            hours.append(23)
        start_year = base_year - 1

        # 结束年
        end_year = datetime.now().year

        while y <= end_year:
            if y >= start_year:
                # 立春为寅月的开始
                jie_qi_table = Lunar.fromYmd(y, 1, 1).getJieQiTable()
                # 节令推移，年干支和月干支就都匹配上了
                solar_time = jie_qi_table[Lunar.JIE_QI_IN_USE[4 + m]]
                if solar_time.getYear() >= base_year:
                    # 日干支和节令干支的偏移值
                    d = LunarUtil.getJiaZiIndex(day_gan_zhi) - LunarUtil.getJiaZiIndex(solar_time.getLunar().getDayInGanZhiExact2())
                    if d < 0:
                        d += 60
                    if d > 0:
                        # 从节令推移天数
                        solar_time = solar_time.next(d)
                    for hour in hours:
                        mi = 0
                        s = 0
                        if d == 0 and hour == solar_time.getHour():
                            # 如果正好是节令当天，且小时和节令的小时数相等的极端情况，把分钟和秒钟带上
                            mi = solar_time.getMinute()
                            s = solar_time.getSecond()
                        # 验证一下
                        solar = Solar.fromYmdHms(solar_time.getYear(), solar_time.getMonth(), solar_time.getDay(), hour, mi, s)
                        if d == 30:
                            solar = solar.nextHour(-1)
                        lunar = solar.getLunar()
                        dgz = lunar.getDayInGanZhiExact2() if 2 == sect else lunar.getDayInGanZhiExact()
                        if lunar.getYearInGanZhiExact() == year_gan_zhi and lunar.getMonthInGanZhiExact() == month_gan_zhi and dgz == day_gan_zhi and lunar.getTimeInGanZhi() == time_gan_zhi:
                            solar_list.append(solar)
            y += 60
        return solar_list

    def isLeapYear(self):
        """
        是否闰年
        :return: True/False 闰年/非闰年
        """
        return SolarUtil.isLeapYear(self.__year)

    def getWeek(self):
        """
        获取星期，0代表周日，1代表周一
        :return: 0123456
        """
        return (int(self.getJulianDay() + 0.5) + 7000001) % 7

    def getWeekInChinese(self):
        """
        获取星期的中文
        :return: 日一二三四五六
        """
        return SolarUtil.WEEK[self.getWeek()]

    def getFestivals(self):
        """
        获取节日，有可能一天会有多个节日
        :return: 劳动节等
        """
        festivals = []
        key = "%d-%d" % (self.__month, self.__day)
        if key in SolarUtil.FESTIVAL:
            festivals.append(SolarUtil.FESTIVAL[key])
        week = self.getWeek()
        key = "%d-%d-%d" % (self.__month, int(ceil(self.__day / 7.0)), week)
        if key in SolarUtil.WEEK_FESTIVAL:
            festivals.append(SolarUtil.WEEK_FESTIVAL[key])
        if self.__day + 7 > SolarUtil.getDaysOfMonth(self.__year, self.__month):
            key = "%d-0-%d" % (self.__month, week)
            if key in SolarUtil.WEEK_FESTIVAL:
                festivals.append(SolarUtil.WEEK_FESTIVAL[key])
        return festivals

    def getOtherFestivals(self):
        """
        获取非正式的节日，有可能一天会有多个节日
        :return: 非正式的节日列表，如中元节
        """
        festivals = []
        key = "%d-%d" % (self.__month, self.__day)
        if key in SolarUtil.OTHER_FESTIVAL:
            for f in SolarUtil.OTHER_FESTIVAL[key]:
                festivals.append(f)
        return festivals

    def getXingZuo(self):
        """
        获取星座
        :return: 星座
        """
        index = 11
        y = self.__month * 100 + self.__day
        if 321 <= y <= 419:
            index = 0
        elif 420 <= y <= 520:
            index = 1
        elif 521 <= y <= 621:
            index = 2
        elif 622 <= y <= 722:
            index = 3
        elif 723 <= y <= 822:
            index = 4
        elif 823 <= y <= 922:
            index = 5
        elif 923 <= y <= 1023:
            index = 6
        elif 1024 <= y <= 1122:
            index = 7
        elif 1123 <= y <= 1221:
            index = 8
        elif y >= 1222 or y <= 119:
            index = 9
        elif y <= 218:
            index = 10
        return SolarUtil.XING_ZUO[index]

    def getJulianDay(self):
        """
        获取儒略日
        :return: 儒略日
        """
        y = self.__year
        m = self.__month
        d = self.__day + ((self.__second / 60.0 + self.__minute) / 60 + self.__hour) / 24
        n = 0
        g = False
        if y * 372 + m * 31 + int(d) >= 588829:
            g = True
        if m <= 2:
            m += 12
            y -= 1
        if g:
            n = int(y / 100)
            n = 2 - n + int(n / 4)
        return int(365.25 * (y + 4716)) + int(30.6001 * (m + 1)) + d + n - 1524.5

    def getLunar(self):
        """
        获取农历
        :return: 农历
        """
        from .Lunar import Lunar
        return Lunar.fromSolar(self)

    def nextDay(self, days):
        y = self.__year
        m = self.__month
        d = self.__day
        if 1582 == y and 10 == m:
            if d > 4:
                d -= 10
        if days > 0:
            d += days
            days_in_month = SolarUtil.getDaysOfMonth(y, m)
            while d > days_in_month:
                d -= days_in_month
                m += 1
                if m > 12:
                    m = 1
                    y += 1
                days_in_month = SolarUtil.getDaysOfMonth(y, m)
        elif days < 0:
            while d + days <= 0:
                m -= 1
                if m < 1:
                    m = 12
                    y -= 1
                d += SolarUtil.getDaysOfMonth(y, m)
            d += days
        if 1582 == y and 10 == m:
            if d > 4:
                d += 10
        return Solar.fromYmdHms(y, m, d, self.__hour, self.__minute, self.__second)

    def next(self, days, only_work_day=False):
        """
        获取往后推几天的阳历日期，如果要往前推，则天数用负数
        :param days: 天数
        :param only_work_day: 是否仅工作日
        :return: 阳历日期
        """
        if not only_work_day:
            return self.nextDay(days)
        solar = Solar.fromYmdHms(self.__year, self.__month, self.__day, self.__hour, self.__minute, self.__second)
        if days != 0:
            rest = abs(days)
            add = 1
            if days < 0:
                add = -1
            while rest > 0:
                solar = solar.next(add)
                work = True
                holiday = HolidayUtil.getHoliday(solar.getYear(), solar.getMonth(), solar.getDay())
                if holiday is None:
                    week = solar.getWeek()
                    if 0 == week or 6 == week:
                        work = False
                else:
                    work = holiday.isWork()
                if work:
                    rest -= 1
        return solar

    def getYear(self):
        return self.__year

    def getMonth(self):
        return self.__month

    def getDay(self):
        return self.__day

    def getHour(self):
        return self.__hour

    def getMinute(self):
        return self.__minute

    def getSecond(self):
        return self.__second

    def toYmd(self):
        return "%04d-%02d-%02d" % (self.__year, self.__month, self.__day)

    def toYmdHms(self):
        return "%s %02d:%02d:%02d" % (self.toYmd(), self.__hour, self.__minute, self.__second)

    def toFullString(self):
        s = self.toYmdHms()
        if self.isLeapYear():
            s += " 闰年"
        s += " 星期"
        s += self.getWeekInChinese()
        for f in self.getFestivals():
            s += " (" + f + ")"
        for f in self.getOtherFestivals():
            s += " (" + f + ")"
        s += " "
        s += self.getXingZuo()
        s += "座"
        return s

    def toString(self):
        return self.toYmd()

    def __str__(self):
        return self.toString()

    def subtract(self, solar):
        return SolarUtil.getDaysBetween(solar.getYear(), solar.getMonth(), solar.getDay(), self.__year, self.__month, self.__day)

    def subtractMinute(self, solar):
        days = self.subtract(solar)
        cm = self.__hour * 60 + self.__minute
        sm = solar.getHour() * 60 + solar.getMinute()
        m = cm - sm
        if m < 0:
            m += 1440
            days -= 1
        m += days * 1440
        return m

    def isAfter(self, solar):
        if self.__year > solar.getYear():
            return True
        if self.__year < solar.getYear():
            return False
        if self.__month > solar.getMonth():
            return True
        if self.__month < solar.getMonth():
            return False
        if self.__day > solar.getDay():
            return True
        if self.__day < solar.getDay():
            return False
        if self.__hour > solar.getHour():
            return True
        if self.__hour < solar.getHour():
            return False
        if self.__minute > solar.getMinute():
            return True
        if self.__minute < solar.getMinute():
            return False
        return self.__second > solar.getSecond()

    def isBefore(self, solar):
        if self.__year > solar.getYear():
            return False
        if self.__year < solar.getYear():
            return True
        if self.__month > solar.getMonth():
            return False
        if self.__month < solar.getMonth():
            return True
        if self.__day > solar.getDay():
            return False
        if self.__day < solar.getDay():
            return True
        if self.__hour > solar.getHour():
            return False
        if self.__hour < solar.getHour():
            return True
        if self.__minute > solar.getMinute():
            return False
        if self.__minute < solar.getMinute():
            return True
        return self.__second < solar.getSecond()

    def nextYear(self, years):
        y = self.__year + years
        m = self.__month
        d = self.__day
        if 1582 == y and 10 == m:
            if 4 < d < 15:
                d += 10
        elif 2 == m:
            if d > 28:
                if not SolarUtil.isLeapYear(y):
                    d = 28
        return Solar.fromYmdHms(y, m, d, self.__hour, self.__minute, self.__second)

    def nextMonth(self, months):
        from . import SolarMonth
        month = SolarMonth.fromYm(self.__year, self.__month).next(months)
        y = month.getYear()
        m = month.getMonth()
        d = self.__day
        if 1582 == y and 10 == m:
            if 4 < d < 15:
                d += 10
        else:
            days = SolarUtil.getDaysOfMonth(y, m)
            if d > days:
                d = days
        return Solar.fromYmdHms(y, m, d, self.__hour, self.__minute, self.__second)

    def nextHour(self, hours):
        h = self.__hour + hours
        n = 1
        if h < 0:
            n = -1
        hour = abs(h)
        days = int(hour / 24) * n
        hour = (hour % 24) * n
        if hour < 0:
            hour += 24
            days -= 1
        solar = self.next(days)
        return Solar.fromYmdHms(solar.getYear(), solar.getMonth(), solar.getDay(), hour, solar.getMinute(), solar.getSecond())

"""

_sources["SolarHalfYear"] = """\
# -*- coding: utf-8 -*-
from math import ceil

from . import SolarMonth


class SolarHalfYear:
    """
    阳历半年
    """

    MONTH_COUNT = 6

    def __init__(self, year, month):
        self.__year = year
        self.__month = month

    @staticmethod
    def fromDate(date):
        return SolarHalfYear(date.year, date.month)

    @staticmethod
    def fromYm(year, month):
        return SolarHalfYear(year, month)

    def getYear(self):
        return self.__year

    def getMonth(self):
        return self.__month

    def toString(self):
        return "%d.%d" % (self.__year, self.getIndex())

    def toFullString(self):
        return "%d年%s半年" % (self.__year, ("上" if 1 == self.getIndex() else "下"))

    def __str__(self):
        return self.toString()

    def getIndex(self):
        """
        获取当月是第几半年
        :return: 半年序号，从1开始
        """
        return int(ceil(self.__month * 1.0 / SolarHalfYear.MONTH_COUNT))

    def getMonths(self):
        """
        获取本半年的阳历月列表
        :return: 阳历月列表
        """
        months = []
        index = self.getIndex() - 1
        for i in range(0, SolarHalfYear.MONTH_COUNT):
            months.append(SolarMonth.fromYm(self.__year, SolarHalfYear.MONTH_COUNT * index + i + 1))
        return months

    def next(self, half_years):
        """
        半年推移
        :param half_years: 推移的半年数，负数为倒推
        :return: 推移后的半年
        """
        m = SolarMonth.fromYm(self.__year, self.__month).next(SolarHalfYear.MONTH_COUNT * half_years)
        return SolarHalfYear.fromYm(m.getYear(), m.getMonth())

"""

_sources["SolarMonth"] = """\
# -*- coding: utf-8 -*-

from . import Solar, SolarWeek
from .util import SolarUtil


class SolarMonth:
    """
    阳历月
    """

    def __init__(self, year, month):
        self.__year = year
        self.__month = month

    @staticmethod
    def fromDate(date):
        return SolarMonth(date.year, date.month)

    @staticmethod
    def fromYm(year: int, month: int):
        return SolarMonth(year, month)

    def getYear(self):
        return self.__year

    def getMonth(self):
        return self.__month

    def toString(self):
        return "%d-%d" % (self.__year, self.__month)

    def toFullString(self):
        return "%d年%d月" % (self.__year, self.__month)

    def __str__(self):
        return self.toString()

    def getDays(self):
        """
        获取本月的阳历日期列表
        :return: 阳历日期列表
        """
        days = []
        d = Solar.fromYmd(self.__year, self.__month, 1)
        days.append(d)
        for i in range(1, SolarUtil.getDaysOfMonth(self.__year, self.__month)):
            days.append(d.next(i))
        return days

    def getWeeks(self, start):
        """
        获取本月的阳历日期列表
        :param start: 星期几作为一周的开始，1234560分别代表星期一至星期天
        :return: 阳历日期列表
        """
        weeks = []
        week = SolarWeek.fromYmd(self.__year, self.__month, 1, start)
        while True:
            weeks.append(week)
            week = week.next(1, False)
            first_day = week.getFirstDay()
            if first_day.getYear() > self.__year or first_day.getMonth() > self.__month:
                break
        return weeks

    def next(self, months):
        """
        获取往后推几个月的阳历月，如果要往前推，则月数用负数
        :param months: 月数
        :return: 阳历月
        """
        n = 1
        if months < 0:
            n = -1
        m = abs(months)
        y = self.__year + int(m / 12) * n
        m = self.__month + m % 12 * n
        if m > 12:
            m -= 12
            y += 1
        elif m < 1:
            m += 12
            y -= 1
        return SolarMonth.fromYm(y, m)

"""

_sources["SolarSeason"] = """\
# -*- coding: utf-8 -*-
from math import ceil

from . import SolarMonth


class SolarSeason:
    """
    阳历季度
    """

    MONTH_COUNT = 3

    def __init__(self, year, month):
        self.__year = year
        self.__month = month

    @staticmethod
    def fromDate(date):
        return SolarSeason(date.year, date.month)

    @staticmethod
    def fromYm(year, month):
        return SolarSeason(year, month)

    def getYear(self):
        return self.__year

    def getMonth(self):
        return self.__month

    def toString(self):
        return "%d.%d" % (self.__year, self.getIndex())

    def toFullString(self):
        return "%d年%d季度" % (self.__year, self.getIndex())

    def __str__(self):
        return self.toString()

    def getIndex(self):
        """
        获取当月是第几季度
        :return: 季度序号，从1开始
        """
        return int(ceil(self.__month * 1.0 / SolarSeason.MONTH_COUNT))

    def getMonths(self):
        """
        获取本季度的阳历月列表
        :return: 阳历月列表
        """
        months = []
        index = self.getIndex() - 1
        for i in range(0, SolarSeason.MONTH_COUNT):
            months.append(SolarMonth.fromYm(self.__year, SolarSeason.MONTH_COUNT * index + i + 1))
        return months

    def next(self, seasons):
        """
        季度推移
        :param seasons: 推移的季度数，负数为倒推
        :return: 推移后的季度
        """
        m = SolarMonth.fromYm(self.__year, self.__month).next(SolarSeason.MONTH_COUNT * seasons)
        return SolarSeason.fromYm(m.getYear(), m.getMonth())

"""

_sources["SolarWeek"] = """\
# -*- coding: utf-8 -*-
from math import ceil

from . import Solar
from .util import SolarUtil


class SolarWeek:
    """
    阳历周
    """

    def __init__(self, year, month, day, start):
        """
        通过年月日初始化
        :param year: 年
        :param month: 月，1到12
        :param day: 日，1到31
        :param start: 星期几作为一周的开始，1234560分别代表星期一至星期天
        """
        self.__year = year
        self.__month = month
        self.__day = day
        self.__start = start

    @staticmethod
    def fromDate(date, start):
        return SolarWeek(date.year, date.month, date.day, start)

    @staticmethod
    def fromYmd(year, month, day, start):
        return SolarWeek(year, month, day, start)

    def getYear(self):
        return self.__year

    def getMonth(self):
        return self.__month

    def getDay(self):
        return self.__day

    def getStart(self):
        return self.__start

    def toString(self):
        return "%d.%d.%d" % (self.__year, self.__month, self.getIndex())

    def toFullString(self):
        return "%d年%d月第%d周" % (self.__year, self.__month, self.getIndex())

    def __str__(self):
        return self.toString()

    def getIndex(self):
        """
        获取当前日期是在当月第几周
        :return: 周序号，从1开始
        """
        offset = Solar.fromYmd(self.__year, self.__month, 1).getWeek() - self.__start
        if offset < 0:
            offset += 7
        return int(ceil((self.__day + offset) * 1.0 / 7))

    def getIndexInYear(self):
        """
        获取当前日期是在当年第几周
        :return: 周序号，从1开始
        """
        offset = Solar.fromYmd(self.__year, 1, 1).getWeek() - self.__start
        if offset < 0:
            offset += 7
        return int(ceil((SolarUtil.getDaysInYear(self.__year, self.__month, self.__day) + offset) * 1.0 / 7))

    def getFirstDay(self):
        """
        获取本周第一天的阳历日期（可能跨月）
        :return: 本周第一天的阳历日期
        """
        solar = Solar.fromYmd(self.__year, self.__month, self.__day)
        prev = solar.getWeek() - self.__start
        if prev < 0:
            prev += 7
        return solar.next(-prev)

    def getFirstDayInMonth(self):
        """
        获取本周第一天的阳历日期（仅限当月）
        :return: 本周第一天的阳历日期
        """
        for day in self.getDays():
            if self.__month == day.getMonth():
                return day
        return None

    def getDays(self):
        """
        获取本周的阳历日期列表（可能跨月）
        :return: 本周的阳历日期列表
        """
        days = []
        first = self.getFirstDay()
        days.append(first)
        for i in range(1, 7):
            days.append(first.next(i))
        return days

    def getDaysInMonth(self):
        """
        获取本周的阳历日期列表（仅限当月）
        :return: 本周的阳历日期列表（仅限当月）
        """
        days = []
        for day in self.getDays():
            if self.__month == day.getMonth():
                days.append(day)
        return days

    def next(self, weeks, separate_month):
        """
        周推移
        :param weeks: 推移的周数，负数为倒推
        :param separate_month: 是否按月单独计算
        :return: 推移后的阳历周
        """
        if 0 == weeks:
            return SolarWeek.fromYmd(self.__year, self.__month, self.__day, self.__start)
        solar = Solar.fromYmd(self.__year, self.__month, self.__day)
        if separate_month:
            n = weeks
            week = SolarWeek.fromYmd(solar.getYear(), solar.getMonth(), solar.getDay(), self.__start)
            month = self.__month
            plus = n > 0
            days = 7 if plus else -7
            while 0 != n:
                solar = solar.next(days)
                week = SolarWeek.fromYmd(solar.getYear(), solar.getMonth(), solar.getDay(), self.__start)
                week_month = week.getMonth()
                if month != week_month:
                    index = week.getIndex()
                    if plus:
                        if 1 == index:
                            first_day = week.getFirstDay()
                            week = SolarWeek.fromYmd(first_day.getYear(), first_day.getMonth(), first_day.getDay(), self.__start)
                            week_month = week.getMonth()
                        else:
                            solar = Solar.fromYmd(week.getYear(), week.getMonth(), 1)
                            week = SolarWeek.fromYmd(solar.getYear(), solar.getMonth(), solar.getDay(), self.__start)
                    else:
                        if SolarUtil.getWeeksOfMonth(week.getYear(), week.getMonth(), self.__start) == index:
                            last_day = week.getFirstDay().next(6)
                            week = SolarWeek.fromYmd(last_day.getYear(), last_day.getMonth(), last_day.getDay(), self.__start)
                            week_month = week.getMonth()
                        else:
                            solar = Solar.fromYmd(week.getYear(), week.getMonth(), SolarUtil.getDaysOfMonth(week.getYear(), week.getMonth()))
                            week = SolarWeek.fromYmd(solar.getYear(), solar.getMonth(), solar.getDay(), self.__start)
                    month = week_month
                n -= 1 if plus else -1
            return week
        else:
            solar = solar.next(weeks * 7)
            return SolarWeek.fromYmd(solar.getYear(), solar.getMonth(), solar.getDay(), self.__start)

"""

_sources["SolarYear"] = """\
# -*- coding: utf-8 -*-

from . import SolarMonth


class SolarYear:
    """
    阳历年
    """

    MONTH_COUNT = 12

    def __init__(self, year):
        self.__year = year

    @staticmethod
    def fromDate(date):
        return SolarYear(date.year)

    @staticmethod
    def fromYear(year):
        return SolarYear(year)

    def getYear(self):
        return self.__year

    def toString(self):
        return str(self.__year)

    def toFullString(self):
        return "%d年" % self.__year

    def __str__(self):
        return self.toString()

    def getMonths(self):
        """
        获取本年的阳历月列表
        :return: 阳历月列表
        """
        months = []
        m = SolarMonth.fromYm(self.__year, 1)
        months.append(m)
        for i in range(1, SolarYear.MONTH_COUNT):
            months.append(m.next(i))
        return months

    def next(self, years):
        """
        获取往后推几年的阳历年，如果要往前推，则月数用负数
        :param years: 年数
        :return: 阳历年
        """
        return SolarYear.fromYear(self.__year + years)

"""

_sources["Tao"] = """\
# -*- coding: utf-8 -*-
from . import Lunar, TaoFestival
from .util import LunarUtil, TaoUtil


class Tao:
    """
    道历
    """

    BIRTH_YEAR = -2697

    def __init__(self, lunar):
        self.__lunar = lunar

    @staticmethod
    def fromLunar(lunar):
        return Tao(lunar)

    @staticmethod
    def fromYmdHms(year, month, day, hour, minute, second):
        return Tao.fromLunar(Lunar.fromYmdHms(year + Tao.BIRTH_YEAR, month, day, hour, minute, second))

    @staticmethod
    def fromYmd(year, month, day):
        return Tao.fromYmdHms(year, month, day, 0, 0, 0)

    def getLunar(self):
        return self.__lunar

    def getYear(self):
        return self.__lunar.getYear() - Tao.BIRTH_YEAR

    def getMonth(self):
        return self.__lunar.getMonth()

    def getDay(self):
        return self.__lunar.getDay()

    def getYearInChinese(self):
        y = str(self.getYear())
        s = ""
        for i in range(0, len(y)):
            s += LunarUtil.NUMBER[ord(y[i]) - 48]
        return s

    def getMonthInChinese(self):
        return self.__lunar.getMonthInChinese()

    def getDayInChinese(self):
        return self.__lunar.getDayInChinese()

    def getFestivals(self):
        festivals = []
        md = "%d-%d" % (self.getMonth(), self.getDay())
        if md in TaoUtil.FESTIVAL:
            fs = TaoUtil.FESTIVAL[md]
            for f in fs:
                festivals.append(f)
        jq = self.__lunar.getJieQi()
        if "冬至" == jq:
            festivals.append(TaoFestival("元始天尊圣诞"))
        elif "夏至" == jq:
            festivals.append(TaoFestival("灵宝天尊圣诞"))
        # 八节日
        if jq in TaoUtil.BA_JIE:
            festivals.append(TaoFestival(TaoUtil.BA_JIE[jq]))
        # 八会日
        gz = self.__lunar.getDayInGanZhi()
        if gz in TaoUtil.BA_HUI:
            festivals.append(TaoFestival(TaoUtil.BA_HUI[gz]))
        return festivals

    def __isDayIn(self, days):
        md = "%d-%d" % (self.getMonth(), self.getDay())
        for d in days:
            if md == d:
                return True
        return False

    def isDaySanHui(self):
        return self.__isDayIn(TaoUtil.SAN_HUI)

    def isDaySanYuan(self):
        return self.__isDayIn(TaoUtil.SAN_YUAN)

    def isDayBaJie(self):
        return self.__lunar.getJieQi() in TaoUtil.BA_JIE

    def isDayWuLa(self):
        return self.__isDayIn(TaoUtil.WU_LA)

    def isDayBaHui(self):
        return self.__lunar.getDayInGanZhi() in TaoUtil.BA_HUI

    def isDayMingWu(self):
        return "戊" == self.__lunar.getDayGan()

    def isDayAnWu(self):
        return self.__lunar.getDayZhi() == TaoUtil.AN_WU[abs(self.getMonth()) - 1]

    def isDayWu(self):
        return self.isDayMingWu() or self.isDayAnWu()

    def isDayTianShe(self):
        ret = False
        mz = self.__lunar.getMonthZhi()
        dgz = self.__lunar.getDayInGanZhi()
        if mz in "寅卯辰":
            if "戊寅" == dgz:
                ret = True
        elif mz in "巳午未":
            if "甲午" == dgz:
                ret = True
        elif mz in "申酉戌":
            if "戊申" == dgz:
                ret = True
        elif mz in "亥子丑":
            if "甲子" == dgz:
                ret = True
        return ret

    def __str__(self):
        return self.toString()

    def toString(self):
        return "%s年%s月%s" % (self.getYearInChinese(), self.getMonthInChinese(), self.getDayInChinese())

    def toFullString(self):
        return "道歷%s年，天运%s年，%s月，%s日。%s月%s日，%s時。" % (self.getYearInChinese(), self.__lunar.getYearInGanZhi(), self.__lunar.getMonthInGanZhi(), self.__lunar.getDayInGanZhi(), self.getMonthInChinese(), self.getDayInChinese(), self.__lunar.getTimeZhi())

"""

_sources["TaoFestival"] = """\
# -*- coding: utf-8 -*-


class TaoFestival:
    """
    道历节日
    """

    def __init__(self, name, remark=None):
        self.__name = name
        self.__remark = "" if remark is None else remark

    def getName(self):
        return self.__name

    def getRemark(self):
        return self.__remark

    def __str__(self):
        return self.toString()

    def toString(self):
        return self.__name

    def toFullString(self):
        s = self.__name
        if self.__remark is not None and len(self.__remark) > 0:
            s += "[" + self.__remark + "]"
        return s

"""

_sources["__init__"] = """\
# -*- coding: utf-8 -*-
from JieQi import JieQi
from NineStar import NineStar
from EightChar import EightChar
from ShuJiu import ShuJiu
from Fu import Fu
from Solar import Solar
from SolarWeek import SolarWeek
from SolarMonth import SolarMonth
from SolarSeason import SolarSeason
from SolarHalfYear import SolarHalfYear
from SolarYear import SolarYear
from LunarTime import LunarTime
from Lunar import Lunar
from LunarYear import LunarYear
from LunarMonth import LunarMonth
from Holiday import Holiday
from FotoFestival import FotoFestival
from Foto import Foto
from TaoFestival import TaoFestival
from Tao import Tao

"""

for _mn, _src in _sources.items():
    _mod = _types.ModuleType(_mn)
    _mod.__file__ = os.path.join(_LP_DIR, _mn + ".py")
    exec(_src, _mod.__dict__)
    sys.modules[_mn] = _mod
    sys.modules["lunar_python." + _mn] = _mod

_lp = _types.ModuleType("lunar_python")
_lp.__path__ = [_LP_DIR]
for _mn in _sources:
    setattr(_lp, _mn, sys.modules[_mn])
sys.modules["lunar_python"] = _lp

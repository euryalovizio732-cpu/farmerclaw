"""三农电商合规引擎 — 农产品/农资平台违规话术检测

适配平台：抖音小店 / 拼多多 / 惠农网
合规方向：
  - 食品类极限词拦截（治病、保健功效等）
  - 农资禁用词（包治百病、增产100%等虚假宣传）
  - 平台规则（标题字数、禁止联系方式等）
  - 生鲜包赔话术规范

复用自 CrossClaw ComplianceEngine 架构，三农行业适配版本。
"""

import re
from dataclasses import dataclass, field
from typing import Callable


@dataclass
class ComplianceIssue:
    rule_id: str
    severity: str          # "critical" | "warning" | "info"
    field: str             # 出现问题的字段
    matched_text: str      # 匹配到的违规文本
    suggestion: str        # 修改建议
    auto_fix: str = ""     # 自动修复后的文本（如能自动修复）


# ═══════════════════════════════════════════════════════
#  极限词/禁用词数据库
# ═══════════════════════════════════════════════════════

# 【严禁】食品/农资疗效宣传（critical）
CRITICAL_MEDICAL_CLAIMS = [
    "治病", "治疗", "防治", "预防疾病", "抗癌", "防癌", "消炎", "杀菌治病",
    "降血糖", "降血压", "降血脂", "保肝护肾", "补肾壮阳",
    "减肥瘦身", "美白祛斑", "延缓衰老", "延年益寿",
    "提高免疫力", "增强免疫", "抗病毒",
    "药到病除", "包治", "根治", "彻底治愈",
]

# 【严禁】虚假绝对增产/效果宣传（critical）
CRITICAL_FALSE_EFFICACY = [
    "增产100%", "增产翻倍", "产量翻番", "绝对增产", "保证丰收",
    "万能", "包治百病", "立竿见影", "神奇效果", "神药",
    "绝对有效", "100%有效", "永久有效", "无限增产",
    "虫不敢来", "病菌全灭",
]

# 【严禁】极限词/绝对化表述（critical）
CRITICAL_SUPERLATIVES = [
    "最好", "第一", "唯一", "天下第一", "全国第一", "行业第一",
    "史上最", "有史以来最", "绝对最好", "无可比拟",
    "最优", "最佳", "最高", "最低", "最安全",
    "国家级", "世界级",  # 无证书时禁用
]

# 【严禁】虚假资质声称（critical）
CRITICAL_FALSE_CERT = [
    "无农药残留", "零农残", "农药残留为零",  # 须有检测报告
    "完全有机", "百分百有机",  # 须有认证
    "纯天然无添加",  # 食品类须符合GB标准
    "国家认证",  # 无证书时禁用
    "农业部认证",  # 须真实授权
    "绿色食品认证",  # 须有绿标
]

# 【警告】夸大宣传词（warning）
WARNING_EXAGGERATION = [
    "远近闻名", "口碑爆棚", "全网最火", "卖疯了",
    "超级好吃", "吃了还想吃", "让你欲罢不能",
    "比进口还好", "秒杀大牌", "碾压同类",
    "疯抢", "秒空", "卖断货",
]

# 【警告】诱导联系/违规引流（warning）
WARNING_CONTACT_INFO = [
    r"\d{11}",           # 手机号
    r"微信[号：:]\s*\S+", # 微信号
    r"加我微信",
    r"私信我",
    r"联系我",
    r"wx[号：:]\s*\S+",
    r"V信",
]

# 【提示】可改进的话术（info）
INFO_IMPROVABLE = [
    "便宜", "实惠",   # 建议替换为"产地直供价"
    "质量好",         # 建议替换为具体描述
    "新鲜",           # 建议补充"当日采摘"等具体承诺
]

# 农资专用禁词（化肥/农药）
AGRI_INPUT_FORBIDDEN = [
    "无毒无害", "对人畜完全无毒",
    "不需要用药", "一次用药永久有效",
    "根除病虫害", "彻底消灭",
    "超过农药标准", "违禁农药",
]

# ─── 三农专属黑名单（抖音平台真实封号高危词）────────────
# 来源：抖音三农类目违规案例 + 平台公告 + 商家封号复盘
# 升级方案P0合规防火墙要求
AGRI_DOUYIN_BLACKLIST = [
    # ── 虚假助农类（52.48%投诉首位）──
    # 来源：北京阳光消费大数据研究院《农产品直播电商消费舆情分析报告2023》N=48054
    "卖惨助农", "家里揭不开锅", "滞销求帮助", "爱心助农",
    "偶遇助农",    # 来源：凉山曲布案，公安查处的MCN话术关键词
    "视觉贫困",    # 来源：全国人大代表李君2024两会提案指出的造假手法
    # ── 产地/资质造假 ──
    # 来源：南都2024-03-15《直播间地标农产品标识混乱》公安查处涉案千万案例
    "野生采摘",    # 无野生认证时禁用
    "深山原始",    # 无产地证明时禁用
    "大凉山特产",  # 非大凉山产地禁用（凉山曲布/赵灵儿案已判刑）
    "大凉山原生态", # 来源：凉山案公安查处MCN人设包装词
    "优质原生态",  # 来源：凉山孟阳/凉山阿泽案虚假宣传关键词
    "山区特色农产品", # 来源：凉山案假冒商标关键词
    "无农残",      # 须有检测报告（来源：CRITICAL_FALSE_CERT + 平台规则）
    "纯天然",      # 须符合GB标准
    "特效",        # 药效宣传
    "100%纯正",
    "0添加",       # 来源：东方甄选天萁西梅汁案，虚假标注"0添加"被查处
    # ── 效果夸大 ──
    "增产翻倍", "增产一倍", "产量翻番",
    "100%甜", "绝对好吃", "保证新鲜",
    # ── 虚假营销手段（来源：市场监管总局2024直播电商典型案例）──
    "好评返现",    # 来源：新浪投诉平台多起真实投诉
    "五星好评才退款", # 来源：投诉编号17382572520蓝莓坏果案
    # ── 违反植物常识（10.23%投诉）──
    "菜地里的车厘子", "沙土里的西瓜藤",
]

# ─── 三农白名单（安全可用话术，替换黑名单用）───────────
# 这些词经过实测不触发违规，同时转化效果好
AGRI_SAFE_WHITELIST = [
    "现摘现发",      # 替换"绝对新鲜"
    "坏果包赔",      # 替换"保证质量"
    "产地直发",      # 替换"产地直供"
    "应季新鲜",      # 替换"最新鲜"
    "口感清甜",      # 替换"100%甜"
    "农残检测合格",  # 替换"无农残"
    "实地拍摄",      # 替换虚假宣传类
    "今日采摘",      # 替换"绝对新鲜"
    "果园直发",      # 替换"原产地"
    "当天发货",      # 替换"极速配送"
]

# ═══════════════════════════════════════════════════════
#  自动修复建议映射（黑 → 白）
# ═══════════════════════════════════════════════════════

AUTO_FIX_MAP = {
    # 极限词修复
    "最好": "优质", "第一": "领先", "唯一": "专注",
    "最优": "优质", "最佳": "较佳", "最高": "较高",
    "最安全": "安全可靠",
    # 三农专属修复（黑 → 白）
    "无农药残留": "农残检测合格",
    "无农残": "农残检测合格",
    "纯天然": "应季新鲜",
    "绝对好吃": "口感清甜",
    "保证新鲜": "今日采摘",
    "100%甜": "口感清甜",
    "特效": "效果显著",
    "增产翻倍": "科学施用助力增产",
    "增产一倍": "科学施用助力增产",
    # 新增黑名单修复（来源：真实案例）
    "偶遇助农": "实地溯源",
    "大凉山原生态": "产地实拍",
    "优质原生态": "品质检测合格",
    "山区特色农产品": "当地特色农产品",
    "0添加": "配料表可查",
    "好评返现": "售后保障",
    "五星好评才退款": "坏果包赔无条件退款",
    # 话术优化
    "便宜": "产地直供价",
    "质量好": "品质优良",
    "新鲜": "当日采摘新鲜直发",
    "很甜": "口感清甜",
    "非常甜": "口感清甜",
}


# ═══════════════════════════════════════════════════════
#  规则定义
# ═══════════════════════════════════════════════════════

@dataclass
class ComplianceRule:
    rule_id: str
    name: str
    severity: str
    check_fn: Callable[[str], list[str]]
    suggestion_template: str
    auto_fix_fn: Callable[[str], str] | None = None


def _find_keywords(text: str, keywords: list[str]) -> list[str]:
    found = []
    text_l = text.lower()
    for kw in keywords:
        if kw.lower() in text_l:
            found.append(kw)
    return found


def _find_patterns(text: str, patterns: list[str]) -> list[str]:
    found = []
    for pat in patterns:
        matches = re.findall(pat, text, re.IGNORECASE)
        found.extend(matches)
    return found


def _apply_auto_fix(text: str) -> str:
    for bad, good in AUTO_FIX_MAP.items():
        text = re.sub(re.escape(bad), good, text, flags=re.IGNORECASE)
    return text


RULES: list[ComplianceRule] = [
    ComplianceRule(
        rule_id="AGRI_MEDICAL_CLAIM",
        name="食品/农资疗效宣传禁止",
        severity="critical",
        check_fn=lambda t: _find_keywords(t, CRITICAL_MEDICAL_CLAIMS),
        suggestion_template='删除或替换违规词「{matched}」。食品/农资不得宣传疗效，可替换为功能性描述（如[富含营养]→[含有丰富维C]）',
    ),
    ComplianceRule(
        rule_id="AGRI_FALSE_EFFICACY",
        name="虚假增产/效果宣传",
        severity="critical",
        check_fn=lambda t: _find_keywords(t, CRITICAL_FALSE_EFFICACY),
        suggestion_template='删除「{matched}」。不得承诺绝对增产，改为[助力增产][科学施用可提升产量]等有条件表述',
    ),
    ComplianceRule(
        rule_id="AGRI_SUPERLATIVE",
        name="极限词/绝对化表述",
        severity="critical",
        check_fn=lambda t: _find_keywords(t, CRITICAL_SUPERLATIVES),
        suggestion_template='将「{matched}」替换为非极限化表述，如[最好]→[优质]，[第一]→[领先品牌]',
        auto_fix_fn=_apply_auto_fix,
    ),
    ComplianceRule(
        rule_id="AGRI_FALSE_CERT",
        name="虚假资质/认证声称",
        severity="critical",
        check_fn=lambda t: _find_keywords(t, CRITICAL_FALSE_CERT),
        suggestion_template="删除「{matched}」。如确有认证，请上传证书并使用平台标准认证标签",
    ),
    ComplianceRule(
        rule_id="AGRI_INPUT_FORBIDDEN",
        name="农资违规宣传",
        severity="critical",
        check_fn=lambda t: _find_keywords(t, AGRI_INPUT_FORBIDDEN),
        suggestion_template="删除「{matched}」，农资产品须遵守农业农村部宣传规范",
    ),
    ComplianceRule(
        rule_id="AGRI_EXAGGERATION",
        name="夸大宣传词",
        severity="warning",
        check_fn=lambda t: _find_keywords(t, WARNING_EXAGGERATION),
        suggestion_template="建议将「{matched}」改为有数据支撑的描述，提升可信度",
    ),
    ComplianceRule(
        rule_id="AGRI_CONTACT_INFO",
        name="违规引流/联系方式",
        severity="warning",
        check_fn=lambda t: _find_patterns(t, WARNING_CONTACT_INFO),
        suggestion_template="删除联系方式「{matched}」，平台禁止在商品信息中留联系方式",
    ),
    ComplianceRule(
        rule_id="AGRI_IMPROVABLE",
        name="话术可优化提示",
        severity="info",
        check_fn=lambda t: _find_keywords(t, INFO_IMPROVABLE),
        suggestion_template="建议将「{matched}」替换为更具体的描述，增强转化",
        auto_fix_fn=_apply_auto_fix,
    ),
    ComplianceRule(
        rule_id="AGRI_DOUYIN_BLACKLIST",
        name="抖音三农平台高危词（封号/限流风险）",
        severity="critical",
        check_fn=lambda t: _find_keywords(t, AGRI_DOUYIN_BLACKLIST),
        suggestion_template=(
            "「{matched}」是抖音三农高危词，可能导致限流或封号。"
            f"安全替换词库（白名单）：{', '.join(AGRI_SAFE_WHITELIST[:5])}"
        ),
        auto_fix_fn=_apply_auto_fix,
    ),
]


# ═══════════════════════════════════════════════════════
#  合规引擎
# ═══════════════════════════════════════════════════════

class AgriculturalComplianceEngine:
    """三农电商合规检测引擎

    复用 CrossClaw ComplianceEngine 架构模式，
    全量替换为三农行业规则集。
    """

    def __init__(self, rules: list[ComplianceRule] | None = None):
        self._rules = rules or RULES

    def check(self, text: str, field_name: str = "content") -> list[ComplianceIssue]:
        """检测单段文本，返回所有合规问题"""
        issues: list[ComplianceIssue] = []
        for rule in self._rules:
            matched_list = rule.check_fn(text)
            for matched in matched_list:
                suggestion = rule.suggestion_template.format(matched=matched)
                auto_fix = ""
                if rule.auto_fix_fn:
                    fixed = rule.auto_fix_fn(text)
                    if fixed != text:
                        auto_fix = fixed
                issues.append(ComplianceIssue(
                    rule_id=rule.rule_id,
                    severity=rule.severity,
                    field=field_name,
                    matched_text=matched,
                    suggestion=suggestion,
                    auto_fix=auto_fix,
                ))
        return issues

    def check_listing(
        self,
        *,
        title: str,
        selling_points: list[str] | None = None,
        detail_page: str = "",
        video_script: str = "",
        live_script: str = "",
        platform: str = "douyin",
    ) -> dict:
        """全链路 Listing 合规检测"""
        all_issues: list[ComplianceIssue] = []

        # 标题检测
        all_issues.extend(self.check(title, "标题"))

        # 卖点检测
        for i, sp in enumerate(selling_points or []):
            all_issues.extend(self.check(sp, f"卖点{i + 1}"))

        # 详情页检测
        if detail_page:
            all_issues.extend(self.check(detail_page, "详情页"))

        # 短视频口播检测
        if video_script:
            all_issues.extend(self.check(video_script, "短视频口播"))

        # 直播话术检测
        if live_script:
            all_issues.extend(self.check(live_script, "直播话术"))

        # 标题字数检测
        from app.services.knowledge_base import PLATFORM_TITLE_LIMITS
        limit = PLATFORM_TITLE_LIMITS.get(platform, 60)
        if len(title) > limit:
            all_issues.append(ComplianceIssue(
                rule_id="PLATFORM_TITLE_LENGTH",
                severity="warning",
                field="标题",
                matched_text=title[limit:],
                suggestion=f"{platform}标题建议不超过{limit}字，当前{len(title)}字，请精简",
            ))

        criticals = [i for i in all_issues if i.severity == "critical"]
        warnings = [i for i in all_issues if i.severity == "warning"]
        infos = [i for i in all_issues if i.severity == "info"]

        return {
            "passed": len(criticals) == 0,
            "critical_count": len(criticals),
            "warning_count": len(warnings),
            "info_count": len(infos),
            "issues": [
                {
                    "rule_id": iss.rule_id,
                    "severity": iss.severity,
                    "field": iss.field,
                    "matched_text": iss.matched_text,
                    "suggestion": iss.suggestion,
                    "auto_fix": iss.auto_fix,
                }
                for iss in all_issues
            ],
        }

    def auto_fix_text(self, text: str) -> str:
        """对文本做自动修复（替换可修复违规词）"""
        return _apply_auto_fix(text)


compliance_engine = AgriculturalComplianceEngine()

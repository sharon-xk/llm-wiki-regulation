"""
阶段3: 将违规行为映射到概念页
输入: scripts/tmp/parsed_data.json
输出: scripts/tmp/parsed_data_with_concepts.json
"""
import json
import re

CONCEPT_RULES = {
    "挪用基金财产": [
        r"挪用.*财产", r"侵占.*财产", r"财产.*混同",
        r"将.*基金.*财产.*用于.*借款", r"将.*基金.*财产.*用于.*担保",
        r"将.*基金.*财产.*用于.*质押", r"将.*基金财产.*用于.*(?:借款|担保|质押)",
        r"利用.*基金.*财产.*(?:件|牟|谋)取",
        r"基金.*财产.*(?:件|牟|谋)取",
    ],
    "承诺保本收益": [
        r"保本.*保收益", r"保收益.*保本", r"承诺.*保本", r"承诺.*收益",
        r"承诺.*本金.*不受.*损失", r"保证.*本金", r"保证.*收益",
        r"预期.*收益.*率", r"基准.*年化.*收益", r"固定.*收益",
        r"最低.*收益", r"本金.*不受.*损失", r"差额补足",
        r"承诺.*最低.*收益", r"约定.*预期.*收益",
        r"保证.*投资.*本金", r"保证.*投资.*收益",
        r"约定.*基准.*年化", r"约定.*年化.*收益",
        r"业绩比较基准.*分配.*收益",
        r"按照.*业绩比较基准.*分配",
    ],
    "利益输送": [
        r"利益输送",
        r"利用.*基金.*产品.*进行.*利益",
        r"为.*相关.*主体.*提供.*利益",
        r"利益.*输送.*通道",
    ],
    "关联交易违规": [
        r"关联交易",
        r"未.*建立.*关联交易.*制度",
    ],
    "虚假登记备案": [
        r"虚假.*登记", r"虚假.*备案", r"虚假.*报送", r"虚假.*填报",
        r"登记.*虚假", r"备案.*虚假", r"报送.*虚假",
        r"代持.*份额", r"份额.*代持", r"为.*代持",
        r"挂靠.*资格", r"挂名.*登记", r"挂名.*合规", r"挂靠.*人员",
        r"报送.*虚假.*信息", r"提供.*虚假.*信息", r"提供.*虚假.*材料",
        r"提交.*虚假.*材料", r"提交.*虚假.*意见",
        r"登记信息.*虚假",
        r"学历.*工作履历.*与实际.*不符", r"履历.*与实际.*不",
        r"未.*实际.*履职", r"不.*实际.*履职",
        r"未建立.*劳动关系.*注册.*资格",
        r"为.*未.*建立.*劳动关系.*人员.*注册",
    ],
    "违规募集": [
        r"违规.*[幕募莫慕].*集", r"违规从事[幕募莫慕].*集",
        r"委托.*不[具俱]有.*基金.*销售.*资格.*[幕募莫慕].*集",
        r"委托.*不[具俱]有.*资格.*(?:单位|个人).*[幕募莫慕].*集",
        r"委托.*不[具俱]有.*资格.*(?:单位|个人).*资金",
        r"委托.*不[具俱]有.*基金.*销售.*资格.*(?:单位|个人|机构)",
        r"委托.*不[具俱]备.*基金.*销售.*资格.*[幕募莫慕].*集",
        r"委托.*不[具俱]备.*基金.*销售.*资格.*(?:单位|个人)",
        r"未取得.*基金.*销售.*资格.*[幕募莫慕].*集",
        r"不[具俱]有.*基金.*销售.*资格.*代.*销售",
        r"不[具俱]有.*基金销售.*资格.*销售",
        r"委托.*不[具俱]有.*基金.*销售.*资格.*代.*销",
        r"由.*其他.*私[幕募莫慕].*基金管理人.*代为.*开展.*[幕募莫慕].*集",
        r"不具有.*基金.*销售.*资格.*(?:单位|个人|机构).*[幕募莫慕].*集",
        r"不具备.*基金.*销售.*资格.*(?:单位|个人|机构).*[幕募莫慕].*集",
    ],
    "投资者适当性违规": [
        r"非合格投资者", r"不合格投资者",
        r"向.*合格投资者.*之外.*[幕募莫慕].*集",
        r"未.*合格投资者.*确认", r"未.*合格投资者.*认定",
        r"适当性.*违规", r"适当性.*义务", r"未.*履行.*适当性",
        r"未.*投资者.*适当性", r"投资者.*适当性.*管理",
        r"向.*非.*合格.*投资者.*[幕募莫慕].*集",
        r"投资者.*风险.*测评", r"风险.*匹配",
        r"拼单", r"穿透.*核查.*投资者",
        r"诱导.*投资者.*风险.*测评",
        r"冷静期.*回访", r"回访.*不.*规范",
        r"未.*适当性.*匹配", r"适当性.*管理.*不",
        r"未.*对.*投资者.*进行.*风险", r"适当性.*材料",
    ],
    "信息披露违规": [
        r"信息披露", r"信息.*披露",
        r"未.*[披氢].*[露圳]", r"未.*报告.*信息", r"未.*报告.*重大",
        r"未.*报送", r"信息报送",
        r"未.*按照.*合同.*约定.*(?:[披氢].*[露圳]|报告|告知|报送)",
        r"未.*向.*投资者.*(?:[披氢].*[露圳]|告知|报告)",
        r"未.*履行.*信息.*[披氢].*[露圳].*义务",
        r"未.*确保.*投资者.*获取.*信息",
        r"[披氢].*[露圳].*不.*真实", r"[披氢].*[露圳].*不.*准确",
        r"[披氢].*[露圳].*不.*完整",
        r"未.*向.*协会.*报告.*重大", r"未.*报告.*重大.*事项",
        r"未.*提供.*信息.*[披氢].*[露圳]",
    ],
    "未尽谨慎勤勉义务": [
        r"谨慎勤勉", r"勤勉尽责", r"勤勉义务",
        r"未.*履行.*谨慎", r"未.*履行.*勤勉",
        r"未.*谨慎.*勤勉", r"未尽.*谨慎", r"未尽.*勤勉",
        r"未.*勤勉.*尽责", r"未.*切实.*履行.*管理.*职责",
        r"内控.*缺失", r"内控.*不.*规范", r"内控.*严重",
        r"未.*审慎.*履职", r"未.*审慎.*审查",
        r"出借.*证券.*账户", r"出借.*账户",
        r"不具备.*持续.*运营.*能力",
        r"未.*尽责", r"未.*诚实信用",
        r"接受.*投资人.*指示.*下达.*交易", r"按.*投资.*指令.*交易",
        r"通道.*业务", r"提供.*通道",
        r"未.*妥善.*保管.*(?:基金|相关).*资料",
        r"未.*妥善.*保管.*(?:基金|相关).*材料",
        r"人员.*配置.*不符合.*要求",
        r"未.*建立.*(?:有效|健全).*内[部控]", r"内控制度.*不",
        r"未.*有效.*执行.*内[部控]", r"未.*严格.*执行.*内[部控]",
        r"违反.*合同.*约定.*投资.*限制",
        r"违反.*合同.*约定.*进行.*投资",
        r"经营管理.*失控", r"已不.*符合.*持续",
        r"未.*履行.*托管.*义务", r"未.*进行.*托管",
        r"未.*制定.*风险.*评级", r"未.*对所管理.*基金.*风险评级",
    ],
    "未按规定登记备案": [
        r"未.*备案.*私募", r"未.*私募.*备案", r"未按规定.*备案",
        r"未.*办理.*备案", r"未.*申请.*备案",
        r"未.*履行.*备案.*手续",
        r"管理人.*登记.*信息.*(?:与实际)?\s*不",
        r"登记.*信息.*与实际.*不符", r"登记.*信息.*不实",
        r"未.*变更.*登记", r"未.*更新.*登记",
        r"管理.*未备案.*产品",
        r"未.*及时.*备案", r"未.*办理.*基金.*备案",
        r"未.*申请.*产品.*备案", r"未.*及时.*申请.*备案",
        r"不具备.*基金从业资格", r"从业人员不足",
        r"不符合.*管理人.*登记.*要求", r"不符合.*登记.*要求",
        r"不符合.*登记.*条件",
        r"未.*重大事项.*变更", r"未.*变更.*重大",
        r"管理人.*信息.*与.*事实.*不符", r"填报.*信息.*与.*事实.*不",
        r"高级管理人员.*登记.*信息.*不",
        r"高管.*信息.*与.*实际.*不",
        r"员工.*人.*数.*不.*符合",
        r"未及时.*重大事项.*变更",
    ],
}


def match_concepts(violation_text):
    matched = []
    for concept_name, patterns in CONCEPT_RULES.items():
        for pattern in patterns:
            if re.search(pattern, violation_text):
                matched.append(concept_name)
                break
    return matched


def main():
    with open("/Users/sharon/ai-project/llm-wiki-regulation/scripts/tmp/parsed_data.json") as f:
        data = json.load(f)

    stats = {name: 0 for name in CONCEPT_RULES}
    stats["无匹配(待创建概念页)"] = 0
    stats["多概念匹配"] = 0

    total_violations = 0
    entities_with_unmatched = set()
    unmatched_samples = []

    for record in data:
        violations = record.get("violations", [])
        record["violation_concepts"] = []
        has_unmatched = False

        for v_text in violations:
            concepts = match_concepts(v_text)
            if not concepts:
                stats["无匹配(待创建概念页)"] += 1
                has_unmatched = True
                record["violation_concepts"].append({
                    "text": v_text, "concepts": [], "needs_new": True
                })
                if len(unmatched_samples) < 50:
                    unmatched_samples.append({
                        "entity": record["entity"],
                        "text": v_text[:200],
                    })
            else:
                for c in concepts:
                    stats[c] += 1
                if len(concepts) > 1:
                    stats["多概念匹配"] += 1
                record["violation_concepts"].append({
                    "text": v_text, "concepts": concepts, "needs_new": False
                })
            total_violations += 1

        if has_unmatched:
            entities_with_unmatched.add(record["entity"])

    # 统计每个entity涉及的概念
    entity_concept_map = {}
    for record in data:
        all_concepts = set()
        for vc in record.get("violation_concepts", []):
            for c in vc["concepts"]:
                all_concepts.add(c)
        entity_concept_map[record["entity"]] = sorted(all_concepts)

    # 统计概念共现
    concept_coverage = {}
    for record in data:
        ec = entity_concept_map.get(record["entity"], [])
        for c in ec:
            concept_coverage[c] = concept_coverage.get(c, 0) + 1

    output = "/Users/sharon/ai-project/llm-wiki-regulation/scripts/tmp/parsed_data_with_concepts.json"
    with open(output, 'w') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print("=== 阶段3: 违规行为 → 概念页映射 完成 ===")
    print(f"违规行为总数: {total_violations}")
    print()
    print("概念页匹配统计 (按违规条目数):")
    for name in CONCEPT_RULES:
        count = stats[name]
        pct = count * 100 / total_violations if total_violations > 0 else 0
        print(f"  {name}: {count} 条 ({pct:.1f}%)")

    unmatched = stats["无匹配(待创建概念页)"]
    print(f"  无匹配(待创建概念页): {unmatched} 条 ({unmatched*100/total_violations:.1f}%)")
    print(f"  多概念匹配: {stats['多概念匹配']} 条")

    print(f"\n概念页覆盖entity数:")
    for name in CONCEPT_RULES:
        count = concept_coverage.get(name, 0)
        print(f"  {name}: {count} 个entity")
    print(f"  存在未匹配违规的entity: {len(entities_with_unmatched)} 个")

    print(f"\n输出文件: {output}")

    # 展示未匹配样例
    print(f"\n--- 未匹配违规样例 (前30条) ---")
    for s in unmatched_samples[:30]:
        print(f"  [{s['entity']}]")
        print(f"    {s['text'][:150]}...")
        print()

    # 对未匹配项进行分类统计
    print(f"\n--- 未匹配违规主题分类 ---")
    category_keywords = {
        "非专业化经营/兼营冲突业务": [r"非.?专业化|违反.?专业化|兼营|相冲突|相.?关.?业务|无关.*业务"],
        "办公场所/人员混同": [r"办公场所.*混同|人员.*混同|共用.*办公|共用.*场所|场所.*混同"],
        "不配合自律检查/未完整提供材料": [r"不配合.*检查|未.*完整.*提供.*检查|未.*提供.*检查.*材料|未.*真实.*完整.*提供|未.*按照.*(?:要求|通知).*提供"],
        "人员/场所不符合登记要求": [r"人员.*不符合.*(?:登记|要求)|从业人员.*不足|员工.*不足|无独立.*(?:办公|场所)|办公场所.*不符合|高级管理人员.*不符合.*(?:登记|要求)|从业人员.*不符合"],
        "夸大/片面宣传": [r"夸大|片面宣传|宣传.*与实际.*不符"],
        "违反合同投资限制": [r"违反.*合同.*约定.*投资|违反.*投资.*限制"],
        "基金运作不规范(资金未归集)": [r"资金.*未.*归集|运作.*不规范|未.*归集.*募集.*账户"],
        "经营管理失控/失联": [r"经营管理.*失控|实际控制人.*失联|已不.*符合.*持续|无法.*取得.*联系"],
        "实际控制人以个人名义汇集资金": [r"以个人名义|个人名义.*汇集|使用.*本人.*账户.*投资|使用.*他人.*账户.*投资"],
        "高级管理人员未实际履职": [r"高级管理人员.*未.*实际.*履职|高管.*未.*实际.*履职|未.*实际.*履职|挂名"],
        "违反专业化运营(接受委托操作账户)": [r"委托.*进行.*(?:货币|证券).*交易|委托.*操作.*账户|委托.*(?:货币|证券).*操"],
        "将基金财产用于借款/出借": [r"将.*基金.*(?:财产|资金).*用于.*借|将.*基金.*(?:财产|资金).*出借"],
    }
    unmatched_categories = {cat: 0 for cat in category_keywords}
    unmatched_categorized = set()

    total_unmatched = sum(1 for s in unmatched_samples if True)
    for s in unmatched_samples:
        text = s["text"]
        for cat, patterns in category_keywords.items():
            for pat in patterns:
                if re.search(pat, text):
                    unmatched_categories[cat] += 1
                    unmatched_categorized.add(s["entity"])
                    break

    for cat, count in sorted(unmatched_categories.items(), key=lambda x: -x[1]):
        if count > 0:
            print(f"  {cat}: {count}")

    # Count truly uncategorized in samples
    truly_uncat = sum(1 for s in unmatched_samples if s["entity"] not in unmatched_categorized)
    print(f"\n  (以上为前{min(50, len(unmatched_samples))}条未匹配样例的主题分布)")
    print(f"  全部未匹配条数: {unmatched}")


if __name__ == "__main__":
    main()

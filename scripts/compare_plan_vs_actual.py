#!/usr/bin/env python3
"""
对比 Q2 2026 Tentative Auction Schedule（计划）vs 实际 XML 拍卖结果
"""
import csv
import re
import os

TENTATIVE_FILE = "tentative_full_text.txt"
ACTUAL_CSV = "may2026_auction_results.csv"
OUTPUT_CSV = "may2026_plan_vs_actual.csv"

def parse_tentative_may():
    """解析 Tentative PDF 中5月的所有拍卖计划"""
    plans = []
    with open(TENTATIVE_FILE, "r", encoding="utf-8") as f:
        lines = f.readlines()
    
    in_may = True
    for line in lines:
        line = line.strip()
        if not line or line.startswith("Tentative") or line.startswith("Security Type"):
            continue
        
        # 只取5月数据
        if "June" in line and re.search(r'\bJune\b', line):
            # 包含 June 但检查是否是六月的拍卖日
            dates = re.findall(r'\b\w+, (\w+ \d{1,2}, \d{4})\b', line)
            if dates:
                first_date = dates[0]
                if not first_date.startswith("May"):
                    continue  # 跳过6月及之后
        
        # 判断是否是假日
        if line.startswith("Holiday"):
            plans.append(("HOLIDAY", line, "", "", ""))
            continue
        
        # 解析证券类型和三个日期
        # 格式: "3-Year NOTE Wednesday, May 06, 2026 Monday, May 11, 2026 Friday, May 15, 2026"
        parts = line.split("\t")
        if len(parts) == 1:
            parts = [p.strip() for p in re.split(r'\s{2,}', line)]
        
        # 提取证券类型（第一个空格前的文本）
        type_match = re.match(r'^(\S+.*?\s(?:NOTE|BOND|BILL|TIPS|FRN)(?:\s[RT]+)?)', line)
        if not type_match:
            # 尝试更宽松匹配
            type_match = re.match(r'^([\w\-]+(?:\s[\w\-]+)?(?:\s[\w\-]+)?)', line)
        if not type_match:
            continue
        
        sec_type = type_match.group(1).strip()
        remainder = line[len(sec_type):].strip()
        
        # 提取三个日期
        date_parts = [d.strip() for d in re.split(r'\s+(?=[A-Z][a-z]+day,)', remainder)]
        dates = []
        for dp in date_parts:
            m = re.search(r'(\w+day, \w+ \d{1,2}, \d{4})', dp)
            if m:
                dates.append(m.group(1))
        
        if len(dates) >= 3:
            plans.append((sec_type, dates[0], dates[1], dates[2]))
    
    return plans


def parse_actual():
    """读取批量抓取的实际结果 CSV"""
    actuals = []
    if not os.path.exists(ACTUAL_CSV):
        return actuals
    
    with open(ACTUAL_CSV, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            sec = row.get("证券类型", "")
            term = row.get("期限", "")
            auction_date = row.get("拍卖日", "")
            offering = row.get("发行规模(B)", "")
            btc = row.get("投标倍数", "")
            high_yield = row.get("中标收益率(%)", "")
            high_rate = row.get("高贴现率(%)", "")
            rate = high_yield or high_rate
            pd_acc = row.get("PD中标", "")
            dir_acc = row.get("Direct中标", "")
            ind_acc = row.get("Indirect中标", "")
            total_acc = row.get("中标总额", "")
            
            key = f"{sec} {term}"
            actuals.append({
                "key": key,
                "证券类型": sec,
                "期限": term,
                "拍卖日": auction_date,
                "规模": offering,
                "投标倍数": btc,
                "利率": rate,
                "PD中标": pd_acc,
                "Direct中标": dir_acc,
                "Indirect中标": ind_acc,
                "中标总额": total_acc,
            })
    
    return actuals


def format_date(date_str):
    """格式化日期: 'Monday, May 11, 2026' -> '2026-05-11'"""
    months = {"January": "01", "February": "02", "March": "03", "April": "04",
              "May": "05", "June": "06", "July": "07", "August": "08",
              "September": "09", "October": "10", "November": "11", "December": "12"}
    m = re.search(r'(\w+) (\d{1,2}), (\d{4})', date_str)
    if m:
        month = months.get(m.group(1), "00")
        day = m.group(2).zfill(2)
        year = m.group(3)
        return f"{year}-{month}-{day}"
    return date_str


def grade_auction(btc_str):
    """评级投标倍数"""
    try:
        btc = float(btc_str)
        if btc >= 3.0:
            return "🟢 强"
        elif btc >= 2.5:
            return "🟡 中"
        else:
            return "🔴 弱"
    except:
        return "⚪"


def main():
    plans = parse_tentative_may()
    actuals = parse_actual()
    
    print(f"📋 计划条目: {len(plans)}")
    print(f"📊 实际结果: {len(actuals)}")
    
    # 把实际结果按日期索引
    actual_by_date = {}
    for a in actuals:
        d = a["拍卖日"]
        if d not in actual_by_date:
            actual_by_date[d] = []
        actual_by_date[d].append(a)
    
    # 输出对比表
    script_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(script_dir, OUTPUT_CSV)
    
    with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow([
            "证券类型(计划)", "计划拍卖日", "计划结算日",
            "实际证券", "实际拍卖日", "规模($B)", "利率(%)",
            "投标倍数", "评级", "PD%", "Direct%", "Indirect%",
            "状态"
        ])
        
        matched_count = 0
        
        for p in plans:
            sec_type = p[0]
            plan_auc = p[2]  # auction date
            plan_settle = p[3]  # settlement date
            
            if sec_type == "HOLIDAY":
                writer.writerow([plan_auc, "", "", "", "", "", "", "", "", "", "", "", "🔔 假日"])
                continue
            
            formatted_date = format_date(plan_auc)
            
            # 在当天实际结果中匹配
            found = False
            if formatted_date in actual_by_date:
                candidates = actual_by_date[formatted_date]
                for c in candidates:
                    # 简单关键词匹配
                    c_key = c["key"].lower()
                    p_lower = sec_type.lower()
                    
                    # 匹配逻辑：检查期限或类型
                    term_map = {
                        "3-year": "3-YEAR", "10-year": "10-YEAR", 
                        "30-year": "30-YEAR", "20-year": "20-YEAR",
                        "2-year frn": "1-YEAR", "2-year": "2-YEAR",
                        "5-year": "5-YEAR", "7-year": "7-YEAR",
                        "4-week": "4-WEEK", "8-week": "8-WEEK",
                        "13-week": "13-WEEK", "26-week": "26-WEEK",
                        "52-week": "52-WEEK", "17-week": "17-WEEK",
                        "6-week": "6-WEEK",
                        "10-year tips": "9-YEAR",
                    }
                    
                    match = False
                    c_term = c["期限"].lower()
                    for k, v in term_map.items():
                        if k in p_lower and v.lower() in c_term:
                            match = True
                            break
                    
                    # Also check security type
                    if not match:
                        if "bill" in p_lower and "BILL" in c["证券类型"]:
                            if c_term in p_lower:
                                match = True
                        elif "note" in p_lower and "NOTE" in c["证券类型"]:
                            if c_term in p_lower:
                                match = True
                        elif "bond" in p_lower and "BOND" in c["证券类型"]:
                            if c_term in p_lower:
                                match = True
                        elif "tips" in p_lower.lower() and "NOTE" in c["证券类型"] and "9-year" in c_term:
                            match = True
                        elif "frn" in p_lower.lower() and "NOTE" in c["证券类型"] and "1-year" in c_term:
                            match = True
                    
                    if match:
                        found = True
                        matched_count += 1
                        
                        # 计算投标人占比
                        try:
                            total = float(c["中标总额"])
                            pd_pct = f"{float(c['PD中标'])/total*100:.1f}%" if total > 0 and c['PD中标'] else ""
                            dir_pct = f"{float(c['Direct中标'])/total*100:.1f}%" if total > 0 and c['Direct中标'] else ""
                            ind_pct = f"{float(c['Indirect中标'])/total*100:.1f}%" if total > 0 and c['Indirect中标'] else ""
                        except:
                            pd_pct = dir_pct = ind_pct = ""
                        
                        status = "✅ 按计划" if format_date(plan_auc) == c["拍卖日"] else f"🟡 日期偏差(计划{formatted_date}实际{c['拍卖日']})"
                        
                        writer.writerow([
                            sec_type,
                            plan_auc or format_date(plan_auc),
                            plan_settle or format_date(plan_settle),
                            c["key"],
                            c["拍卖日"],
                            c["规模"],
                            c["利率"],
                            c["投标倍数"],
                            grade_auction(c["投标倍数"]),
                            pd_pct, dir_pct, ind_pct,
                            status
                        ])
                        break
            
            if not found:
                writer.writerow([
                    sec_type, format_date(plan_auc), format_date(plan_settle),
                    "", "", "", "", "", "", "", "", "",
                    "🔍 实际结果未匹配"
                ])
        
        # 查找不在计划中的拍卖（CMB等临时发行）
        for d, items in actual_by_date.items():
            for item in items:
                # 检查是否已经被匹配
                matched = False
                for p in plans:
                    if format_date(p[2]) == d:
                        p_lower = p[0].lower()
                        c_key = item["key"].lower()
                        c_sec = item["证券类型"].lower()
                        
                        term_map = {
                            "3-year": "3-YEAR", "10-year": "10-YEAR",
                            "30-year": "30-YEAR", "20-year": "20-YEAR",
                            "2-year frn": "1-YEAR", "2-year": "2-YEAR",
                            "5-year": "5-YEAR", "7-year": "7-YEAR",
                            "4-week": "4-WEEK", "8-week": "8-WEEK",
                            "13-week": "13-WEEK", "26-week": "26-WEEK",
                            "52-week": "52-WEEK", "17-week": "17-WEEK",
                            "6-week": "6-WEEK",
                            "10-year tips": "9-YEAR",
                        }
                        
                        for k, v in term_map.items():
                            if k in p_lower and v.lower() in c_key:
                                matched = True
                                break
                        if not matched:
                            if "bill" in p_lower and "bill" in c_sec:
                                if item["期限"].lower() in p_lower:
                                    matched = True
                            elif "note" in p_lower and "note" in c_sec:
                                if item["期限"].lower() in p_lower:
                                    matched = True
                
                if not matched:
                    status = "🆕 CMB(临时)" if "0-WEEK" in item["期限"] else "⚠️ 计划外发行"
                    writer.writerow([
                        "—", "—", "—",
                        item["key"], item["拍卖日"], item["规模"], item["利率"],
                        item["投标倍数"], grade_auction(item["投标倍数"]),
                        "", "", "",
                        status
                    ])
    
    print(f"\n{'='*60}")
    print(f"✅ 对比完成")
    print(f"  计划条目:   {len([p for p in plans if p[0] != 'HOLIDAY'])}")
    print(f"  实际记录:   {len(actuals)}")
    print(f"  成功匹配:   {matched_count}")
    print(f"  对比 CSV:   {csv_path}")

if __name__ == "__main__":
    main()

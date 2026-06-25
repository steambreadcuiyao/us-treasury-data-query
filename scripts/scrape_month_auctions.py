#!/usr/bin/env python3
"""
批量抓取 2026年5月 美国财政部拍卖结果（TreasuryDirect XML）
输出 CSV（UTF-8 BOM，含中英文表头）
"""
import csv
import urllib.request
import urllib.error
import xml.etree.ElementTree as ET
import time
import os
from datetime import date, timedelta

BASE_URL = "https://treasurydirect.gov/xml/R_{date}_{seq}.xml"
OUTPUT_CSV = "may2026_auction_results.csv"
MAX_SEQ = 8  # 每天最多尝试 _1 到 _8

# 输出字段：XML 路径 → 中文表头
FIELDS = [
    ("AnnouncementDate", "公告日"),
    ("AuctionDate", "拍卖日"),
    ("IssueDate", "发行日"),
    ("MaturityDate", "到期日"),
    ("SecurityType", "证券类型"),
    ("SecurityTermWeekYear", "期限"),
    ("CUSIP", "CUSIP"),
    ("OfferingAmount", "发行规模(B)"),
    ("InterestRate", "票面利率(%)"),
    ("HighDiscountRate", "高贴现率(%)"),
    ("HighYield", "中标收益率(%)"),
    ("HighDiscountMargin", "中标贴现利差(%)"),
    ("HighPrice", "中标价格"),
    ("BidToCoverRatio", "投标倍数"),
    ("TotalTendered", "投标总额"),
    ("TotalAccepted", "中标总额"),
    ("CompetitiveTendered", "竞争性投标"),
    ("CompetitiveAccepted", "竞争性中标"),
    ("NonCompetitiveAccepted", "非竞争性中标"),
    ("PrimaryDealerTendered", "PD投标"),
    ("PrimaryDealerAccepted", "PD中标"),
    ("DirectBidderTendered", "Direct投标"),
    ("DirectBidderAccepted", "Direct中标"),
    ("IndirectBidderTendered", "Indirect投标"),
    ("IndirectBidderAccepted", "Indirect中标"),
    ("SOMATendered", "SOMA投标"),
    ("SOMAAccepted", "SOMA中标"),
    ("TreasuryRetailAccepted", "零售中标"),
    ("HighAllocationPercentage", "高分配率(%)"),
    ("InvestmentRate", "投资收益率(%)"),
    ("TypeOfAuction", "拍卖方式"),
    ("ReOpeningIndicator", "是否续发"),
    ("ResultsPDFName", "结果PDF"),
    ("FileName", "XML文件名"),
]


def safe_text(elem, tag):
    """安全提取 XML 子元素文本"""
    child = elem.find(f".//{tag}")
    if child is not None and child.text:
        return child.text.strip()
    return ""


def fetch_xml(date_str, seq):
    """下载单个 XML 并解析"""
    url = BASE_URL.format(date=date_str, seq=seq)
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            raw = resp.read()
        # 解析 XML
        root = ET.fromstring(raw)

        # 提取 Announcement 部分
        ann = root.find(".//AuctionAnnouncement")
        # 提取 Results 部分
        res = root.find(".//AuctionResults")

        row = {"FileName": f"R_{date_str}_{seq}.xml"}

        # 从 Announcement 提取
        for tag in ["SecurityType", "SecurityTermWeekYear", "CUSIP",
                     "AnnouncementDate", "AuctionDate", "IssueDate",
                     "MaturityDate", "OfferingAmount", "InterestRate",
                     "ReOpeningIndicator", "TypeOfAuction"]:
            val = safe_text(ann, tag) if ann is not None else ""
            if val:
                row[tag] = val

        # 从 Results 提取
        for tag in ["HighDiscountRate", "HighYield", "HighDiscountMargin",
                     "HighPrice", "BidToCoverRatio", "TotalTendered",
                     "TotalAccepted", "CompetitiveTendered",
                     "CompetitiveAccepted", "NonCompetitiveAccepted",
                     "PrimaryDealerTendered", "PrimaryDealerAccepted",
                     "DirectBidderTendered", "DirectBidderAccepted",
                     "IndirectBidderTendered", "IndirectBidderAccepted",
                     "SOMATendered", "SOMAAccepted",
                     "TreasuryRetailAccepted", "HighAllocationPercentage",
                     "InvestmentRate", "ResultsPDFName"]:
            val = safe_text(res, tag) if res is not None else ""
            if val:
                row[tag] = val

        return row
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None  # 该后缀不存在
        print(f"  HTTP {e.code} on {url}")
        return None
    except Exception as e:
        print(f"  Error on {url}: {e}")
        return None


def main():
    results = []
    total_tried = 0
    total_hit = 0

    # 2026年5月所有日期
    start = date(2026, 5, 1)
    end = date(2026, 5, 31)
    current = start

    while current <= end:
        # 跳过周末
        if current.weekday() >= 5:
            current += timedelta(days=1)
            continue

        date_str = current.strftime("%Y%m%d")
        print(f"\n📅 {date_str} ({current.strftime('%a')})：")

        hit_today = 0
        for seq in range(1, MAX_SEQ + 1):
            total_tried += 1
            row = fetch_xml(date_str, seq)
            if row is not None:
                total_hit += 1
                hit_today += 1
                sec_type = row.get("SecurityType", "?")
                term = row.get("SecurityTermWeekYear", "?")
                offering = row.get("OfferingAmount", "?")
                btc = row.get("BidToCoverRatio", "N/A")
                print(f"  ✅ _ {seq}: {sec_type} {term}  ${offering}B  BTC={btc}")
                results.append(row)
            time.sleep(0.15)  # 礼貌限速

        if hit_today == 0:
            print("  (无拍卖)")
        current += timedelta(days=1)

    # 写入 CSV
    script_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(script_dir, OUTPUT_CSV)
    with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        # 写表头
        writer.writerow([cn for _, cn in FIELDS])
        # 写数据
        for row in results:
            writer.writerow([row.get(en, "") for en, cn in FIELDS])

    print(f"\n{'='*60}")
    print(f"✅ 完成！")
    print(f"  遍历交易日: {sum(1 for d in (start + timedelta(days=i) for i in range((end-start).days+1)) if d.weekday()<6)} 天")
    print(f"  尝试请求:   {total_tried}")
    print(f"  命中拍卖:   {total_hit}")
    print(f"  CSV 输出:   {csv_path}")


if __name__ == "__main__":
    main()

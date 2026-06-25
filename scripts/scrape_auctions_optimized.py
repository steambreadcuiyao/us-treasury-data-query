#!/usr/bin/env python3
"""
最优方案：Tentative Schedule PDF 索引 + 定向 XML 下载

优势：
- 暴力遍历：~168 次请求/月（78% 浪费在 404）
- 本方案：   ~40 次请求/月（仅尝试已知有拍卖的日期）

流程：
1. 解析 Tentative Auction Schedule PDF，提取目标月份的计划拍卖日期
2. 对每个拍卖日期，按证券类型数量试 XML 后缀
3. 下载命中 XML 并解析 bid-to-cover + 投标人分类
4. 输出 CSV（UTF-8 BOM，中文表头）

前置：pip install pdfplumber
"""
import csv
import os
import re
import sys
import time
import urllib.request
import urllib.error
import xml.etree.ElementTree as ET
from datetime import date, datetime

# ─── 配置 ───
TENTATIVE_URL = "https://home.treasury.gov/system/files/221/Tentative-Auction-Schedule.pdf"
XML_BASE = "https://treasurydirect.gov/xml/R_{date}_{seq}.xml"

# Q1 PDF URL pattern (Feb release, covers Feb-Jul)
TENTATIVE_Q_URLS = {
    1: "https://home.treasury.gov/system/files/221/TentativeAuctionScheduleQ12026.pdf",
    2: "https://home.treasury.gov/system/files/221/TentativeAuctionScheduleQ22026.pdf",
}

FIELDS = [
    ("AuctionDate", "拍卖日"), ("SecurityType", "证券类型"),
    ("SecurityTermWeekYear", "期限"), ("CUSIP", "CUSIP"),
    ("OfferingAmount", "规模B"), ("InterestRate", "票面利率%"),
    ("HighDiscountRate", "高贴现率%"), ("HighYield", "中标收益率%"),
    ("HighDiscountMargin", "中标DM%"), ("BidToCoverRatio", "投标倍数"),
    ("TotalTendered", "投标总额"), ("TotalAccepted", "中标总额"),
    ("PrimaryDealerTendered", "PD投标"), ("PrimaryDealerAccepted", "PD中标"),
    ("DirectBidderTendered", "Direct投标"), ("DirectBidderAccepted", "Direct中标"),
    ("IndirectBidderTendered", "Indirect投标"), ("IndirectBidderAccepted", "Indirect中标"),
    ("SOMATendered", "SOMA投标"), ("SOMAAccepted", "SOMA中标"),
    ("NonCompetitiveAccepted", "非竞争性中标"), ("TreasuryRetailAccepted", "零售中标"),
    ("HighAllocationPercentage", "高分配率%"), ("InvestmentRate", "投资收益率%"),
    ("TypeOfAuction", "拍卖方式"), ("ReOpeningIndicator", "是否续发"),
    ("IssueDate", "发行日"), ("MaturityDate", "到期日"),
]

MONTHS = {
    "January": 1, "February": 2, "March": 3, "April": 4,
    "May": 5, "June": 6, "July": 7, "August": 8,
    "September": 9, "October": 10, "November": 11, "December": 12,
}


def safe_text(elem, tag):
    child = elem.find(f".//{tag}") if elem is not None else None
    return child.text.strip() if child is not None and child.text else ""


def download_tentative_pdf(year):
    """下载对应年份季度 Tentative PDF，返回本地文件路径"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    pdf_path = os.path.join(script_dir, f"tentative_{year}.pdf")

    # 先试主 URL
    try:
        req = urllib.request.Request(TENTATIVE_URL, headers={"User-Agent": "Mozilla/5.0"})
        urllib.request.urlretrieve(TENTATIVE_URL, pdf_path)
        return pdf_path
    except Exception:
        pass

    # 试 Q1/Q2 URLs
    for q, url in TENTATIVE_Q_URLS.items():
        try:
            urllib.request.urlretrieve(url, pdf_path)
            return pdf_path
        except Exception:
            continue

    raise RuntimeError(f"无法下载 {year} 年 Tentative Schedule PDF")


def parse_auction_dates(pdf_path, target_year, target_month):
    """从 Tentative PDF 解析指定月份的所有拍卖日期和每日期望拍卖数"""
    import pdfplumber

    auction_days = {}
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if not text:
                continue
            for line in text.split("\n"):
                line = line.strip()
                if not line or line.startswith("Tentative") or line.startswith("Security Type"):
                    continue
                if line.startswith("Holiday"):
                    continue

                # 提取拍卖日期
                m = re.search(r'Auction Date\s+(.+)$', line)
                if not m:
                    # 格式: "3-Year NOTE Wednesday, May 06, 2026 Monday, May 11, 2026 Friday, May 15, 2026"
                    parts = re.split(r'\s{2,}|\t', line)
                    if len(parts) < 2:
                        continue
                    # 找三个日期
                    dates_found = re.findall(
                        r'(\w+day, \w+ \d{1,2}, \d{4})', line
                    )
                    if len(dates_found) < 2:
                        continue
                    auc_date_str = dates_found[1]  # 第二个日期 = 拍卖日
                else:
                    auc_date_str = m.group(1).strip()

                # 解析日期
                parts = auc_date_str.replace(",", "").split()
                if len(parts) < 3:
                    continue
                try:
                    m_num = MONTHS.get(parts[1], 0)
                    d_num = int(parts[2])
                    y_num = int(parts[3])
                    if y_num == target_year and m_num == target_month:
                        day_key = f"{y_num}{m_num:02d}{d_num:02d}"
                        auction_days[day_key] = auction_days.get(day_key, 0) + 1
                except (ValueError, IndexError):
                    continue

    return auction_days


def fetch_xml(date_str, seq):
    """下载并解析单个 XML"""
    url = XML_BASE.format(date=date_str, seq=seq)
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=20) as resp:
            raw = resp.read()
        root = ET.fromstring(raw)
        ann = root.find(".//AuctionAnnouncement")
        res = root.find(".//AuctionResults")

        row = {}
        for tag in [f[0] for f in FIELDS]:
            val = safe_text(ann, tag) or safe_text(res, tag)
            if val:
                row[tag] = val
        return row
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None
        return None
    except Exception:
        return None


def main():
    if len(sys.argv) < 3:
        print("Usage: python scrape_auctions_optimized.py <year> <month> [output_dir]")
        print("Example: python scrape_auctions_optimized.py 2026 4")
        sys.exit(1)

    year = int(sys.argv[1])
    month = int(sys.argv[2])
    output_dir = sys.argv[3] if len(sys.argv) > 3 else os.path.dirname(os.path.abspath(__file__))

    print(f"📥 Step 1: 下载 Tentative Schedule PDF ({year} Q{(month-1)//3+1})...")
    pdf_path = download_tentative_pdf(year)
    print(f"   PDF: {pdf_path}")

    print(f"📋 Step 2: 解析 {year}-{month:02d} 拍卖计划...")
    auction_days = parse_auction_dates(pdf_path, year, month)
    if not auction_days:
        print("   ⚠️ 未找到该月拍卖计划，回退到暴力遍历")
        # Fallback: all weekdays
        d = date(year, month, 1)
        while d.month == month:
            if d.weekday() < 5:
                auction_days[d.strftime("%Y%m%d")] = 4  # 默认期望 4 笔
            d += __import__('datetime').timedelta(days=1)

    print(f"   找到 {len(auction_days)} 个拍卖日，预期 ~{sum(auction_days.values())} 笔拍卖")

    print(f"📊 Step 3: 批量下载 XML...")
    results = []
    total_tried = 0
    total_hit = 0

    for day_key in sorted(auction_days.keys()):
        expected = auction_days[day_key]
        max_seq = max(expected + 2, 6)  # 多试 2 个以防 CMB/补充拍卖
        hit_today = 0

        for seq in range(1, max_seq + 1):
            total_tried += 1
            row = fetch_xml(day_key, seq)
            if row is not None:
                total_hit += 1
                hit_today += 1
                sec = row.get("SecurityType", "?")
                term = row.get("SecurityTermWeekYear", "?")
                btc = row.get("BidToCoverRatio", "N/A")
                size = row.get("OfferingAmount", "?")
                print(f"  ✅ {day_key}_{seq}: {sec} {term}  ${size}B  BTC={btc}")
                results.append(row)
                time.sleep(0.15)
            else:
                break  # 后缀不存在，这一天的拍卖到此为止

    # 保存 CSV
    csv_path = os.path.join(output_dir.replace('\\', '/'), f"auctions_{year}{month:02d}.csv")
    with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow([cn for _, cn in FIELDS])
        for row in results:
            writer.writerow([row.get(en, "") for en, _ in FIELDS])

    efficiency = total_hit / total_tried * 100 if total_tried > 0 else 0
    print(f"\n{'='*60}")
    print(f"✅ 完成！")
    print(f"  拍卖日:     {len(auction_days)} 天")
    print(f"  请求总数:   {total_tried}")
    print(f"  命中拍卖:   {total_hit}")
    print(f"  命中率:     {efficiency:.0f}% (暴力遍历约 22%)")
    print(f"  CSV:        {csv_path}")


if __name__ == "__main__":
    main()

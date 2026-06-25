#!/usr/bin/env python3
"""
TIC Data Query Script
查询美国财政部 TIC (Treasury International Capital) 数据
下载并解析 Table 5: Major Foreign Holders of Treasury Securities

用法：
  python3 query_tic_data.py --output ./data
  python3 query_tic_data.py --output ./data --format csv
"""

import sys
import os
import csv
import argparse
import urllib.request
import ssl
from datetime import datetime

# 禁用 SSL 验证
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

TIC_URL = "https://ticdata.treasury.gov/resource-center/data-chart-center/tic/Documents/slt_table5.txt"


def download_tic_data():
    """下载 TIC 原始文本文件"""
    req = urllib.request.Request(TIC_URL)
    resp = urllib.request.urlopen(req, timeout=30, context=ctx)
    return resp.read().decode('utf-8')


def parse_tic_data(text):
    """
    解析 TIC Table 5 数据
    
    返回:
      - months: ["2026-03", "2026-02", ...]
      - records: [{"国家": "Japan", "最新": 1191.6, "上月": 1239.3, ...}, ...]
      - totals: {grand_total, foreign_official, foreign_official_bills, foreign_official_notes}
    """
    lines = text.strip().split('\n')
    
    # 找数据起始行（以 "Country" 开头的行）
    data_start = None
    for i, line in enumerate(lines):
        if line.startswith('Country\t'):
            data_start = i
            break
    
    if data_start is None:
        raise ValueError("无法找到 TIC 数据表头")
    
    # 解析表头：获取月份列
    header_parts = lines[data_start].split('\t')
    months = [m.strip() for m in header_parts[1:]]  # 跳过 "Country"，去除 \r
    
    # 解析数据行（表头后一直到空行或 Grand Total 之后）
    records = []
    summaries = {}
    
    for i in range(data_start + 1, len(lines)):
        line = lines[i].strip()
        if not line or line.startswith('Notes'):
            break
        
        parts = line.split('\t')
        if len(parts) < 2:
            continue
        
        country = parts[0].strip()
        values = []
        for v in parts[1:]:
            try:
                values.append(float(v))
            except (ValueError, IndexError):
                values.append(0.0)
        
        # 摘要行
        if country == 'Grand Total':
            summaries['grand_total'] = values[0] if values else 0
            continue
        elif country == 'Of Which: Foreign Official':
            summaries['foreign_official'] = values[0] if values else 0
            continue
        elif country == 'Of Which: Foreign Official Treasury Bills':
            summaries['foreign_official_bills'] = values[0] if values else 0
            continue
        elif country == 'Of Which: Foreign Official T-Bonds & Notes':
            summaries['foreign_official_notes'] = values[0] if values else 0
            continue
        
        # 国家数据行
        record = {
            '国家': country,
            '最新': values[0] if len(values) > 0 else 0,
            '上月': values[1] if len(values) > 1 else 0,
            '变化': (values[0] - values[1]) if len(values) >= 2 else 0,
        }
        # 也保存所有月份数据
        for j, month in enumerate(months):
            if j < len(values):
                record[month] = values[j]
        
        records.append(record)
    
    return months, records, summaries


def save_csv(records, summaries, months, output_dir):
    """保存为 CSV 文件（中文表头）"""
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # 主数据文件
    filepath = os.path.join(output_dir, f"tic_foreign_holders_{timestamp}.csv")
    
    with open(filepath, 'w', newline='', encoding='utf-8-sig') as f:
        headers = ['排名', '国家', '最新持仓(十亿)', '上月持仓(十亿)', '月变化(十亿)'] + months
        writer = csv.writer(f)
        writer.writerow(headers)
        
        for rank, rec in enumerate(records, 1):
            # "All Other" 是汇总行，不参与排名，标记为 "-"
            if rec['国家'] == 'All Other':
                rank_str = '-'
            else:
                rank_str = rank
            row = [
                rank_str,
                rec['国家'],
                rec['最新'],
                rec['上月'],
                rec['变化'],
            ]
            for m in months:
                row.append(rec.get(m, ''))
            writer.writerow(row)
        
        # 汇总行
        if summaries:
            writer.writerow([])
            writer.writerow(['', '【汇总】', '', '', '', ''] + [''] * len(months))
            if 'grand_total' in summaries:
                writer.writerow(['', '外国持有总计', summaries['grand_total'], '', '', ''] + [''] * len(months))
            if 'foreign_official' in summaries:
                writer.writerow(['', '  其中: 外国官方', summaries['foreign_official'], '', '', ''] + [''] * len(months))
            if 'foreign_official_bills' in summaries:
                writer.writerow(['', '    短期国库券(Bills)', summaries['foreign_official_bills'], '', '', ''] + [''] * len(months))
            if 'foreign_official_notes' in summaries:
                writer.writerow(['', '    中长期国债(Notes&Bonds)', summaries['foreign_official_notes'], '', '', ''] + [''] * len(months))
    
    return filepath


def main():
    parser = argparse.ArgumentParser(description="查询美国财政部 TIC 外国持有美债数据")
    parser.add_argument("--output", default=".", help="输出目录（默认当前目录）")
    parser.add_argument("--format", default="csv", help="输出格式（默认 csv）")
    parser.add_argument("--top", type=int, default=0, help="只输出前 N 名（默认全部）")
    args = parser.parse_args()
    
    print("[开始] 下载 TIC Table 5 数据...")
    text = download_tic_data()
    
    print("[解析] 解析 TIC 数据...")
    months, records, summaries = parse_tic_data(text)
    
    latest_month = months[0] if months else "?"
    print(f"[信息] 最新数据月份: {latest_month}")
    print(f"[信息] 数据月份数: {len(months)} ({months[-1]} ~ {months[0]})")
    print(f"[信息] 国家/地区数: {len(records)}")
    
    if summaries.get('grand_total'):
        print(f"[信息] 外国持有总计: ${summaries['grand_total']:.1f}B")
    
    # 按最新持仓排序
    records.sort(key=lambda x: x['最新'], reverse=True)
    
    # 保存 CSV
    filepath = save_csv(records, summaries, months, args.output)
    print(f"\n[成功] 已保存: {filepath}")
    
    # 输出摘要（JSON）
    import json
    summary = {
        "source": "TIC Table 5",
        "latest_month": latest_month,
        "countries": len(records),
        "months": months,
        "grand_total": summaries.get('grand_total', 0),
        "foreign_official": summaries.get('foreign_official', 0),
        "filepath": filepath,
        "top10": [
            {"rank": i+1, "country": r['国家'], "holding": r['最新'], "change": r['变化']}
            for i, r in enumerate(r for r in records if r['国家'] != 'All Other')
        ][:10]
    }
    print("\n=== SUMMARY ===")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

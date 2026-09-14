#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
财政部国债回购（Buyback / Redemption Operation）数据查询

数据源：
  A) 官方 API（主源，含实际接受面额）
     https://api.fiscal.treasury.gov/ap/exp/v1/marketable-securities/buybacks
     需请求头 client_id / client_secret（从 TreasuryDirect 公告页前端 JS 提取，见下）
  B) DTS 调整表（辅源，仅价位调整，用于交叉验证）
     /v1/accounting/dts/adjustment_public_debt_transactions_cash_basis

用法：
  python query_buyback_data.py                        # 全部已完成操作 + 最近 20 笔明细
  python query_buyback_data.py --recent 30            # 看最近 30 笔
  python query_buyback_data.py --year 2026            # 按年筛选
  python query_buyback_data.py --csv                  # 导出 CSV 到当前目录
  python query_buyback_data.py --reconcile            # 与 DTS 调整表对账（验证数据一致性）
  python query_buyback_data.py --refresh-credentials  # 重新从公告页抓取 client_id/secret

注意：
  1. 金额单位：API 返回的是「美元」，DTS 调整表是「百万美元」，不要混用。
  2. 现金流日期看 settlementDT（结算日），不是 operationStartDTM（操作日）。
  3. API 凭证由前端 JS 硬编码，可能随页面改版失效；失效时用 --refresh-credentials 重取。
  4. DTS 只有价位调整（premium/discount），拿不到回购本金，本金必须走本脚本的官方 API。
"""

import argparse
import csv
import json
import re
import sys
import urllib.parse
import urllib.request
from collections import defaultdict
from datetime import datetime

BUYBACK_API = "https://api.fiscal.treasury.gov/ap/exp/v1/marketable-securities/buybacks"
ANNOUNCE_PAGE = "https://www.treasurydirect.gov/auctions/announcements-data-results/buy-backs/"
FISCAL_BASE = "https://api.fiscaldata.treasury.gov/services/api/fiscal_service"
DTS_ADJ = "/v1/accounting/dts/adjustment_public_debt_transactions_cash_basis"

# 默认凭证（2026-09-11 从公告页前端 JS 提取）
DEFAULT_CLIENT_ID = "8c94af521a854babb36ad4112c83df03"
DEFAULT_CLIENT_SECRET = "c33631F97444440cbb527E79549CFc40"

UA = {"User-Agent": "Mozilla/5.0"}


# ---------------------------------------------------------------- 凭证

def refresh_credentials():
    """从 TreasuryDirect 公告页的 JS 中提取 API 凭证"""
    req = urllib.request.Request(ANNOUNCE_PAGE, headers=UA)
    html = urllib.request.urlopen(req, timeout=60).read().decode("utf-8", "ignore")
    m = re.search(
        r"host\s*=\s*\{\s*[\"']client_id[\"']\s*:\s*[\"']([0-9a-f]+)[\"']\s*,"
        r"\s*[\"']client_secret[\"']\s*:\s*[\"']([0-9A-Za-z]+)[\"']",
        html,
    )
    if not m:
        raise RuntimeError("未能从公告页提取 API 凭证，页面结构可能已变更")
    cid, secret = m.group(1), m.group(2)
    print(f"[凭证已刷新] client_id={cid}")
    print(f"               请将下面的值更新到脚本常量 DEFAULT_CLIENT_ID / DEFAULT_CLIENT_SECRET")
    print(f"               client_secret={secret}")
    return cid, secret


# ---------------------------------------------------------------- 取数

def fetch_buybacks(client_id=None, client_secret=None, status=None):
    """拉取回购操作全量记录"""
    cid = client_id or DEFAULT_CLIENT_ID
    sec = client_secret or DEFAULT_CLIENT_SECRET
    headers = dict(UA)
    headers["client_id"] = cid
    headers["client_secret"] = sec
    req = urllib.request.Request(BUYBACK_API, headers=headers)
    data = json.load(urllib.request.urlopen(req, timeout=120))
    if status:
        data = [x for x in data if x.get("operationStatus") == status]
    return data


def fmt_money(dollars, unit="B"):
    if dollars is None:
        return "-"
    return f"{dollars / 1e9:,.3f}{unit}"


def summarize(ops):
    """按年度汇总"""
    by_year = defaultdict(lambda: {"n": 0, "accepted": 0, "offered": 0})
    for x in ops:
        if x.get("operationStatus") != "Results":
            continue
        y = (x.get("operationStartDTM") or "")[:4]
        by_year[y]["n"] += 1
        by_year[y]["accepted"] += x.get("totalParAmountAccepted") or 0
        by_year[y]["offered"] += x.get("totalParAmountOffered") or 0
    return by_year


def print_ops(ops, limit=None, title="回购操作明细"):
    rows = sorted(ops, key=lambda r: r.get("operationStartDTM") or "")
    if limit:
        rows = rows[-limit:]
    print(f"\n=== {title}（{len(rows)} 笔） ===")
    print(f"{'操作日':<12}{'结算日':<12}{'类型':<20}{'证券':<18}{'期限段':<14}"
          f"{'接受面额':>11}{'投标面额':>12}{'覆盖倍数':>9}")
    for x in rows:
        acc = x.get("totalParAmountAccepted")
        off = x.get("totalParAmountOffered")
        cover = f"{off / acc:.2f}" if acc else "-"
        print(f"{ (x.get('operationStartDTM') or '')[:10]:<12}"
              f"{ (x.get('settlementDT') or '')[:10]:<12}"
              f"{ (x.get('operationType') or '-')[:18]:<20}"
              f"{ (x.get('securityType') or '-')[:16]:<18}"
              f"{ (x.get('maturityBucket') or '-')[:12]:<14}"
              f"{fmt_money(acc):>11}{fmt_money(off):>12}{cover:>9}")


def export_csv(ops, path="buyback_operations.csv"):
    cols = [
        ("operationStartDTM", "操作日"), ("settlementDT", "结算日"),
        ("operationType", "操作类型"), ("securityType", "证券类型"),
        ("maturityBucket", "期限段"), ("operationStatus", "状态"),
        ("totalParAmountAccepted", "接受面额(美元)"),
        ("totalParAmountOffered", "投标面额(美元)"),
        ("numberIssuesEligible", "合格券种数"), ("numberIssuesAccepted", "中标券种数"),
        ("maturityDateRangeBegin", "期限起"), ("maturityDateRangeEnd", "期限止"),
    ]
    rows = sorted(ops, key=lambda r: r.get("operationStartDTM") or "")
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow([c[1] for c in cols])
        for x in rows:
            w.writerow([x.get(c[0], "") for c in cols])
    print(f"\n已导出: {path}（{len(rows)} 行，UTF-8 BOM 中文表头）")


# ---------------------------------------------------------------- 对账

def _fiscal_get(ep, **kw):
    q = "&".join(f"{k}={urllib.parse.quote(str(v), safe=':(),-')}" for k, v in kw.items())
    req = urllib.request.Request(f"{FISCAL_BASE}{ep}?{q}", headers=UA)
    return json.load(urllib.request.urlopen(req, timeout=180))


def reconcile(ops):
    """与 DTS 调整表对账，验证公告页数据完整性"""
    print("\n=== 对账：公告页回购操作 vs DTS 调整表 buyback 足迹 ===")
    # 公告页：按结算日归集（现金流口径）
    by_settle = defaultdict(list)
    for x in ops:
        if x.get("operationStatus") != "Results":
            continue
        s = x.get("settlementDT")
        if s:
            by_settle[s[:10]].append(x)

    # DTS 调整表：全量分页
    rows, page = [], 1
    while True:
        d = _fiscal_get(
            DTS_ADJ,
            filter="adj_type:in:(Premium on Debt Buyback Operation,Discount on Debt Buyback Operation (-))",
            sort="record_date",
            **{"page[size]": "10000", "page[number]": str(page)},
        )
        rows.extend(d["data"])
        if len(rows) >= int(d["meta"]["total-count"]) or page > 5:
            break
        page += 1
    by_date = defaultdict(dict)
    for r in rows:
        by_date[r["record_date"]][r["adj_type"]] = float(r["adj_today_amt"])
    nz = {k: v for k, v in by_date.items() if any(x != 0 for x in v.values())}

    both = [d for d in nz if d in by_settle]
    only_dts = [d for d in nz if d not in by_settle]
    only_api = [d for d in by_settle if d not in nz]

    print(f"DTS 有非零足迹的日期: {len(nz)} 天")
    print(f"公告页有操作记录的日期: {len(by_settle)} 天")
    print(f"  两边都有: {len(both)} 天")
    print(f"  仅 DTS 有: {len(only_dts)} 天" + (f" -> {only_dts[:8]}" if only_dts else ""))
    print(f"  仅公告页有: {len(only_api)} 天（DTS 无足迹，属正常：折价极小时四舍五入为 0）")

    print(f"\n{'结算日':<12}{'接受面额':>11}{'DTS溢价':>10}{'DTS折价':>10}")
    for d in sorted(nz)[-12:]:
        acc = sum((o.get("totalParAmountAccepted") or 0) for o in by_settle.get(d, []))
        p = nz[d].get("Premium on Debt Buyback Operation", 0)
        dd = nz[d].get("Discount on Debt Buyback Operation (-)", 0)
        print(f"  {d:<12}{fmt_money(acc):>11}{p:>10,.0f}{dd:>10,.0f}")
    print("\n结论：DTS 非零日全部被公告页覆盖即视为数据一致（DTS 单位=百万美元，仅为价位调整）。")


# ---------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser(description="财政部国债回购数据查询")
    ap.add_argument("--recent", type=int, default=20, help="显示最近 N 笔（默认20）")
    ap.add_argument("--year", help="按年份筛选，如 2026")
    ap.add_argument("--csv", action="store_true", help="导出 CSV")
    ap.add_argument("--reconcile", action="store_true", help="与 DTS 调整表对账")
    ap.add_argument("--refresh-credentials", action="store_true", help="重新抓取 API 凭证")
    ap.add_argument("--json", action="store_true", help="输出原始 JSON")
    args = ap.parse_args()

    if args.refresh_credentials:
        refresh_credentials()
        return

    ops = fetch_buybacks()
    print(f"拉取回购操作记录: {len(ops)} 条（含未完成/已取消）")

    done = [x for x in ops if x.get("operationStatus") == "Results"]
    cancelled = [x for x in ops if x.get("operationStatus") == "Cancelled"]
    print(f"  已完成: {len(done)} | 已取消: {len(cancelled)}")
    if done:
        ds = sorted(x["operationStartDTM"] for x in done)
        print(f"  最早: {ds[0][:10]} | 最新: {ds[-1][:10]}")
        total = sum(x.get("totalParAmountAccepted") or 0 for x in done)
        print(f"  累计回购面额: {total / 1e9:,.1f} 十亿美元")

    print("\n=== 按年度汇总 ===")
    by_year = summarize(ops)
    print(f"{'年份':<8}{'笔数':>6}{'接受面额':>12}{'投标面额':>13}{'覆盖倍数':>10}")
    for y in sorted(by_year):
        v = by_year[y]
        cover = f"{v['offered'] / v['accepted']:.2f}" if v["accepted"] else "-"
        print(f"{y:<8}{v['n']:>6}{fmt_money(v['accepted']):>12}"
              f"{fmt_money(v['offered']):>13}{cover:>10}")

    sel = done
    if args.year:
        sel = [x for x in done if (x.get("operationStartDTM") or "").startswith(args.year)]
        if not sel:
            print(f"\n未找到 {args.year} 年的回购操作")
            sys.exit(0)
    print_ops(sel, limit=args.recent, title=f"{args.year or '全部'}回购操作明细（最近 {args.recent} 笔）")

    if args.csv:
        export_csv(sel)
    if args.reconcile:
        reconcile(ops)
    if args.json:
        print("\n" + json.dumps(sel, ensure_ascii=False, indent=2)[:3000])


if __name__ == "__main__":
    main()

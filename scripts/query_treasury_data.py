#!/usr/bin/env python3
"""
US Treasury Data Query Script
查询美国财政部 DTS + MSPD 数据集，保存为 CSV（中文表头）

用法：
  python3 query_treasury_data.py --table operating_cash_balance --filter "record_date:gte:2025-01-01" --output ./data
"""

import sys
import os
import json
import csv
import argparse
import urllib.request
import urllib.parse
import ssl
from datetime import datetime

# ═摘自 conversation
# 禁用 SSL 验证（解决证书问题）
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

BASE_URL = "https://api.fiscaldata.treasury.gov/services/api/fiscal_service"

# 数据表定义（DTS 9张 + MSPD 1张，含中文字段翻译）
TABLES = {
    "operating_cash_balance": {
        "endpoint": "/v1/accounting/dts/operating_cash_balance",
        "name_cn": "运营现金余额",
        "fields_cn": {
            "record_date": "记录日期",
            "account_type": "账户类型",
            "close_today_bal": "当日收盘余额",
            "open_today_bal": "当日开盘余额",
            "open_month_bal": "本月开盘余额",
            "open_fiscal_year_bal": "本财年开盘余额",
            "table_nbr": "表格编号",
            "table_nm": "表格名称",
            "sub_table_name": "子表名称",
            "src_line_nbr": "源数据行号",
            "record_fiscal_year": "记录财年",
            "record_fiscal_quarter": "记录财年季度",
            "record_calendar_year": "记录日历年",
            "record_calendar_quarter": "记录日历季度",
            "record_calendar_month": "记录日历月",
            "record_calendar_day": "记录日历日",
        },
    },
    "deposits_withdrawals": {
        "endpoint": "/v1/accounting/dts/deposits_withdrawals_operating_cash",
        "name_cn": "运营现金存取款",
        "fields_cn": {
            "record_date": "记录日期",
            "account_type": "账户类型",
            "transaction_type": "交易类型",
            "transaction_catg": "交易类别",
            "transaction_catg_desc": "交易类别描述",
            "transaction_today_amt": "当日交易金额",
            "transaction_mtd_amt": "当月累计交易金额",
            "transaction_fytd_amt": "本财年累计交易金额",
            "table_nbr": "表格编号",
            "table_nm": "表格名称",
            "src_line_nbr": "源数据行号",
            "record_fiscal_year": "记录财年",
            "record_fiscal_quarter": "记录财年季度",
            "record_calendar_year": "记录日历年",
            "record_calendar_quarter": "记录日历季度",
            "record_calendar_month": "记录日历月",
            "record_calendar_day": "记录日历日",
        },
    },
    "public_debt_transactions": {
        "endpoint": "/v1/accounting/dts/public_debt_transactions",
        "name_cn": "公共债务交易",
        "fields_cn": {
            "record_date": "记录日期",
            "transaction_type": "交易类型",
            "security_market": "证券市场类型",
            "security_type": "证券类型",
            "security_type_desc": "证券类型描述",
            "transaction_today_amt": "当日交易金额",
            "transaction_mtd_amt": "当月累计交易金额",
            "transaction_fytd_amt": "本财年累计交易金额",
            "table_nbr": "表格编号",
            "table_nm": "表格名称",
            "src_line_nbr": "源数据行号",
            "record_fiscal_year": "记录财年",
            "record_fiscal_quarter": "记录财年季度",
            "record_calendar_year": "记录日历年",
            "record_calendar_quarter": "记录日历季度",
            "record_calendar_month": "记录日历月",
            "record_calendar_day": "记录日历日",
        },
    },
    "adjustment_public_debt": {
        "endpoint": "/v1/accounting/dts/adjustment_public_debt_transactions_cash_basis",
        "name_cn": "公共债务交易现金基础调整",
        "fields_cn": {
            "record_date": "记录日期",
            "transaction_type": "交易类型",
            "adj_type": "调整类型",
            "adj_type_desc": "调整类型描述",
            "adj_today_amt": "当日调整金额",
            "adj_mtd_amt": "当月累计调整金额",
            "adj_fytd_amt": "本财年累计调整金额",
            "table_nbr": "表格编号",
            "table_nm": "表格名称",
            "sub_table_name": "子表名称",
            "src_line_nbr": "源数据行号",
            "record_fiscal_year": "记录财年",
            "record_fiscal_quarter": "记录财年季度",
            "record_calendar_year": "记录日历年",
            "record_calendar_quarter": "记录日历季度",
            "record_calendar_month": "记录日历月",
            "record_calendar_day": "记录日历日",
        },
    },
    "debt_subject_to_limit": {
        "endpoint": "/v1/accounting/dts/debt_subject_to_limit",
        "name_cn": "受限债务",
        "fields_cn": {
            "record_date": "记录日期",
            "debt_catg": "债务类别",
            "debt_catg_desc": "债务类别描述",
            "close_today_bal": "当日收盘余额",
            "open_today_bal": "当日开盘余额",
            "open_month_bal": "本月开盘余额",
            "open_fiscal_year_bal": "本财年开盘余额",
            "table_nbr": "表格编号",
            "table_nm": "表格名称",
            "sub_table_name": "子表名称",
            "src_line_nbr": "源数据行号",
            "record_fiscal_year": "记录财年",
            "record_fiscal_quarter": "记录财年季度",
            "record_calendar_year": "记录日历年",
            "record_calendar_quarter": "记录日历季度",
            "record_calendar_month": "记录日历月",
            "record_calendar_day": "记录日历日",
        },
    },
    "inter_agency_tax": {
        "endpoint": "/v1/accounting/dts/inter_agency_tax_transfers",
        "name_cn": "机构间税收转移",
        "fields_cn": {
            "record_date": "记录日期",
            "transaction_type": "交易类型",
            "agency_name": "机构名称",
            "transfer_today_amt": "当日转移金额",
            "transfer_mtd_amt": "当月累计转移金额",
            "transfer_fytd_amt": "本财年累计转移金额",
            "table_nbr": "表格编号",
            "table_nm": "表格名称",
            "src_line_nbr": "源数据行号",
            "record_fiscal_year": "记录财年",
            "record_fiscal_quarter": "记录财年季度",
            "record_calendar_year": "记录日历年",
            "record_calendar_quarter": "记录日历季度",
            "record_calendar_month": "记录日历月",
            "record_calendar_day": "记录日历日",
        },
    },
    "income_tax_refunds": {
        "endpoint": "/v1/accounting/dts/income_tax_refunds_issued",
        "name_cn": "所得税退税发放",
        "fields_cn": {
            "record_date": "记录日期",
            "refund_type": "退税类型",
            "refund_today_amt": "当日退税金额",
            "refund_mtd_amt": "当月累计退税金额",
            "refund_fytd_amt": "本财年累计退税金额",
            "table_nbr": "表格编号",
            "table_nm": "表格名称",
            "src_line_nbr": "源数据行号",
            "record_fiscal_year": "记录财年",
            "record_fiscal_quarter": "记录财年季度",
            "record_calendar_year": "记录日历年",
            "record_calendar_quarter": "记录日历季度",
            "record_calendar_month": "记录日历月",
            "record_calendar_day": "记录日历日",
        },
    },
    "federal_tax_deposits": {
        "endpoint": "/v1/accounting/dts/federal_tax_deposits",
        "name_cn": "联邦税收存款",
        "fields_cn": {
            "record_date": "记录日期",
            "tax_deposit_type": "税收存款类型",
            "tax_deposit_type_desc": "税收存款类型描述",
            "tax_deposit_today_amt": "当日税收存款金额",
            "tax_deposit_mtd_amt": "当月累计税收存款金额",
            "tax_deposit_fytd_amt": "本财年累计税收存款金额",
            "table_nbr": "表格编号",
            "table_nm": "表格名称",
            "sub_table_name": "子表名称",
            "src_line_nbr": "源数据行号",
            "record_fiscal_year": "记录财年",
            "record_fiscal_quarter": "记录财年季度",
            "record_calendar_year": "记录日历年",
            "record_calendar_quarter": "记录日历季度",
            "record_calendar_month": "记录日历月",
            "record_calendar_day": "记录日历日",
        },
    },
    "short_term_cash": {
        "endpoint": "/v1/accounting/dts/short_term_cash_investments",
        "name_cn": "短期现金投资",
        "fields_cn": {
            "record_date": "记录日期",
            "investment_type": "投资类型",
            "investment_desc": "投资类型描述",
            "par_amount": "票面金额",
            "accrued_interest": "应计利息",
            "table_nbr": "表格编号",
            "table_nm": "表格名称",
            "src_line_nbr": "源数据行号",
            "record_fiscal_year": "记录财年",
            "record_fiscal_quarter": "记录财年季度",
            "record_calendar_year": "记录日历年",
            "record_calendar_quarter": "记录日历季度",
            "record_calendar_month": "记录日历月",
            "record_calendar_day": "记录日历日",
        },
    },
    "mspd_summary": {
        "endpoint": "/v1/debt/mspd/mspd_table_1",
        "name_cn": "国债余额汇总（按证券类型）",
        "fields_cn": {
            "record_date": "记录日期",
            "security_type_desc": "证券大类",
            "security_class_desc": "证券类型",
            "debt_held_public_mil_amt": "公众持有余额",
            "intragov_hold_mil_amt": "政府内部持有余额",
            "total_mil_amt": "总余额",
            "src_line_nbr": "源数据行号",
            "record_fiscal_year": "记录财年",
            "record_fiscal_quarter": "记录财年季度",
            "record_calendar_year": "记录日历年",
            "record_calendar_quarter": "记录日历季度",
            "record_calendar_month": "记录日历月",
            "record_calendar_day": "记录日历日",
        },
    },
    "debt_to_penny": {
        "endpoint": "/v2/accounting/od/debt_to_penny",
        "name_cn": "国债精确余额（Debt to the Penny）",
        "fields_cn": {
            "record_date": "记录日期",
            "debt_held_public_amt": "公众持有金额（美元）",
            "intragov_hold_amt": "政府内部持有金额（美元）",
            "tot_pub_debt_out_amt": "公共债务总余额（美元）",
            "src_line_nbr": "源数据行号",
            "record_fiscal_year": "记录财年",
            "record_fiscal_quarter": "记录财年季度",
            "record_calendar_year": "记录日历年",
            "record_calendar_quarter": "记录日历季度",
            "record_calendar_month": "记录日历月",
            "record_calendar_day": "记录日历日",
        },
    },
    "avg_interest_rates": {
        "endpoint": "/v2/accounting/od/avg_interest_rates",
        "name_cn": "国债平均利率（按证券类型）",
        "fields_cn": {
            "record_date": "记录日期",
            "security_type_desc": "证券大类（Marketable/Nonmarketable）",
            "security_desc": "证券类型",
            "avg_interest_rate_amt": "平均利率（%）",
            "src_line_nbr": "源数据行号",
            "record_fiscal_year": "记录财年",
            "record_fiscal_quarter": "记录财年季度",
            "record_calendar_year": "记录日历年",
            "record_calendar_quarter": "记录日历季度",
            "record_calendar_month": "记录日历月",
            "record_calendar_day": "记录日历日",
        },
    },
    "interest_expense": {
        "endpoint": "/v2/accounting/od/interest_expense",
        "name_cn": "国债利息支出",
        "fields_cn": {
            "record_date": "记录日期",
            "expense_catg_desc": "支出类别",
            "expense_group_desc": "支出分组",
            "expense_type_desc": "证券类型",
            "month_expense_amt": "当月利息支出（美元）",
            "fytd_expense_amt": "本财年累计利息支出（美元）",
            "src_line_nbr": "源数据行号",
            "record_fiscal_year": "记录财年",
            "record_fiscal_quarter": "记录财年季度",
            "record_calendar_year": "记录日历年",
            "record_calendar_quarter": "记录日历季度",
            "record_calendar_month": "记录日历月",
            "record_calendar_day": "记录日历日",
        },
    },
    "schedules_fed_debt": {
        "endpoint": "/v1/accounting/od/schedules_fed_debt",
        "name_cn": "联邦债务明细表",
        "fields_cn": {
            "record_date": "记录日期",
            "debt_holder_type": "持有人类型",
            "security_class1_desc": "证券一级分类",
            "security_class2_desc": "证券二级分类",
            "principal_mil_amt": "本金余额（百万美元）",
            "accrued_int_payable_mil_amt": "已计提未付利息（百万美元）",
            "net_unamortized_mil_amt": "未摊销净额（百万美元）",
            "src_line_nbr": "源数据行号",
            "record_fiscal_year": "记录财年",
            "record_fiscal_quarter": "记录财年季度",
            "record_calendar_year": "记录日历年",
            "record_calendar_quarter": "记录日历季度",
            "record_calendar_month": "记录日历月",
            "record_calendar_day": "记录日历日",
        },
    },
}


def build_filter(filter_conditions):
    """构建 filter 参数字符串"""
    if not filter_conditions:
        return None
    parts = []
    for cond in filter_conditions:
        field, op, value = cond  # format: ("record_date", "gte", "2025-01-01")
        encoded_value = urllib.parse.quote(str(value), safe="")
        parts.append(f"{field}:{op}:{encoded_value}")
    return ",".join(parts)


def download_table(table_key, filter_str=None, sort="-record_date", page_size=10000, max_pages=None):
    """
    下载指定表的数据
    返回: (records, total_count, downloaded_count)
    """
    table = TABLES[table_key]
    endpoint = table["endpoint"]

    all_records = []
    page_num = 1

    while True:
        if max_pages and page_num > max_pages:
            break

        params = []
        if filter_str:
            params.append(f"filter={filter_str}")
        if sort:
            params.append(f"sort={sort}")
        params.append(f"page[size]={page_size}")
        params.append(f"page[number]={page_num}")

        url = f"{BASE_URL}{endpoint}?{'&'.join(params)}"

        try:
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, context=ctx) as resp:
                data = json.loads(resp.read())
        except Exception as e:
            print(f"[错误] 请求失败: {e}", file=sys.stderr)
            break

        batch = data.get("data", [])
        meta = data.get("meta", {})
        total = meta.get("total-count", 0)

        if page_num == 1:
            print(f"[信息] 总记录数: {total}, 每页: {page_size}")

        if not batch:
            break

        all_records.extend(batch)
        print(f"[进度] 第{page_num}页: +{len(batch)}条 (累计:{len(all_records)}/{total})")

        # 检查是否已获取全部
        if len(all_records) >= total or len(batch) < page_size:
            break
        page_num += 1

    return all_records, meta.get("total-count", 0), len(all_records)


def save_csv(table_key, records, output_dir, file_prefix=None):
    """保存为 CSV 文件（中文表头，UTF-8 BOM 编码）"""
    table = TABLES[table_key]
    fields_cn = table["fields_cn"]

    if not records:
        print("[警告] 无数据可保存")
        return None

    os.makedirs(output_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    prefix = file_prefix if file_prefix else table_key
    filename = f"{prefix}_{timestamp}.csv"
    filepath = os.path.join(output_dir, filename)

    with open(filepath, "w", newline="", encoding="utf-8-sig") as f:
        fieldnames = list(records[0].keys())
        chinese_headers = [fields_cn.get(f, f) for f in fieldnames]

        writer = csv.writer(f)
        writer.writerow(chinese_headers)
        for rec in records:
            writer.writerow([rec.get(f, "") for f in fieldnames])

    print(f"[成功] 已保存: {filepath}")
    return filepath


def main():
    parser = argparse.ArgumentParser(description="查询美国财政部 DTS 数据")
    parser.add_argument("--table", required=True, help="表名（见 TABLES 键名）")
    parser.add_argument("--filter", help="筛选条件，格式: field:op:value[,field:op:value]")
    parser.add_argument("--sort", default="-record_date", help="排序字段（默认 -record_date）")
    parser.add_argument("--limit", type=int, default=0, help="最大下载条数（0=全部，默认0）")
    parser.add_argument("--page-size", type=int, default=10000, help="每页条数（默认10000）")
    parser.add_argument("--output", default=".", help="输出目录（默认当前目录）")
    parser.add_argument("--prefix", help="文件名前缀（默认表名）")
    args = parser.parse_args()

    if args.table not in TABLES:
        print(f"[错误] 未知表名: {args.table}")
        print(f"[提示] 可用表: {', '.join(TABLES.keys())}")
        sys.exit(1)

    # 解析 filter 参数
    filter_str = None
    if args.filter:
        # 格式: "record_date:gte:2025-01-01,close_today_bal:gt:1000000"
        conditions = []
        for part in args.filter.split(","):
            f = part.split(":")
            if len(f) == 3:
                conditions.append((f[0], f[1], f[2]))
            else:
                print(f"[警告] 忽略无效 filter 片段: {part}")
        filter_str = build_filter(conditions)

    # 下载数据
    max_pages = None
    if args.limit > 0:
        max_pages = max(1, (args.limit + args.page_size - 1) // args.page_size)

    print(f"[开始] 查询表: {TABLES[args.table]['name_cn']} ({args.table})")
    if filter_str:
        print(f"[筛选] {filter_str}")

    records, total, downloaded = download_table(
        args.table,
        filter_str=filter_str,
        sort=args.sort,
        page_size=args.page_size,
        max_pages=max_pages,
    )

    if not records:
        print("[结果] 未获取到数据")
        sys.exit(0)

    print(f"[完成] 共获取 {len(records)}/{total} 条记录")

    # 保存 CSV
    filepath = save_csv(args.table, records, args.output, file_prefix=args.prefix)
    print(f"\n[输出] {filepath}")

    # 输出 JSON 摘要（供调用方解析）
    summary = {
        "table": args.table,
        "table_cn": TABLES[args.table]["name_cn"],
        "total": total,
        "downloaded": downloaded,
        "filepath": filepath,
    }
    print("\n=== SUMMARY ===")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

# us-treasury-data-query

美国财政部数据查询 WorkBuddy Skill——覆盖四类数据源：

| 数据源 | 类型 | 获取方式 |
|--------|------|---------|
| **DTS**（Daily Treasury Statement） | 9 张表，日度现金流 | FiscalData REST API |
| **MSPD**（Monthly Statement of Public Debt） | 存量余额 + 利率 + 利息支出 | FiscalData REST API |
| **TIC**（Treasury International Capital） | 外国持有美债数据 | 文本文件下载 |
| **TreasuryDirect Auctions** | 拍卖计划 / 结果 / 近期安排 | XML 批量抓取 / PDF 解析 |

## 核心功能

- ✅ DTS 9 张表查询（TGA 余额、存取款、债务交易、税收等）
- ✅ 按证券类型查国债存量余额（Bills/Notes/Bonds/TIPS/FRNs）
- ✅ 外国持有美债国别排名（TIC Table 5）
- ✅ **国债拍卖计划查询**（Tentative Schedule PDF 解析）
- ✅ **拍卖结果批量抓取**（XML，含 bid-to-cover + 投标人分类）
- ✅ **近期拍卖安排**（Upcoming Auctions / PendingAuctions.xml）
- ✅ **计划 vs 实际偏差对比**
- ✅ CSV 导出（UTF-8 BOM，中文表头）
- ✅ 数据分析（描述统计、趋势、同比/环比、异常检测）

## 目录结构

```
├── SKILL.md              # 技能定义（触发条件、数据表详解、API文档）
├── scripts/
│   ├── query_treasury_data.py    # FiscalData API 查询（DTS/MSPD）
│   ├── query_tic_data.py         # TIC 外国持有美债数据
│   ├── scrape_month_auctions.py  # 批量抓取月度拍卖 XML
│   ├── parse_tentative_schedule.py # 解析 Tentative Schedule PDF
│   └── compare_plan_vs_actual.py # 计划 vs 实际对比
├── references/
│   └── api_reference.md   # API 端点参考
└── .gitignore
```

## 快速开始

```bash
# 查询某月拍卖计划
python scripts/parse_tentative_schedule.py

# 批量抓取某月实际拍卖结果
python scripts/scrape_month_auctions.py --year 2026 --month 5

# 查询 TGA 余额
python scripts/query_treasury_data.py --table operating_cash_balance

# 查询国债存量余额（按证券类型）
python scripts/query_treasury_data.py --table mspd_summary

# 查询外国持有美债
python scripts/query_tic_data.py --top 10
```

## 数据源参考

- [FiscalData API](https://api.fiscaldata.treasury.gov/)
- [TreasuryDirect Auctions](https://www.treasurydirect.gov/auctions/)
- [TIC System](https://home.treasury.gov/data/treasury-international-capital-tic-system)

---
name: us-treasury-data-query
description: 查询美国财政部 FiscalData API 的多个数据集——Daily Treasury Statement (DTS, 9表)、Monthly Statement of the Public Debt (MSPD, 1表)、Debt to the Penny、平均利率、利息支出、联邦债务明细表，以及 Treasury International Capital (TIC) 外国持有美债数据；支持查询国债拍卖计划(Tentative Schedule)、拍卖结果(XML批量抓取含bid-to-cover)、近期拍卖安排(Upcoming Auctions)。通过API/XML/文本下载获取数据并以CSV格式保存（中文表头）。支持计划vs实际对比、投标倍数分析。触发词：查询美国财政部数据、Treasury数据、DTS数据、财政部现金流数据、国债余额、MSPD、按证券类型查国债、TIC数据、外国持有美债、美债持有国排名、债务精确余额、国债利率、利息支出、国债拍卖、发债计划、投标倍数、bid-to-cover、拍卖日程、拍卖结果、Tentative Schedule、Upcoming Auctions。
agent_created: true
---

# US Treasury Data Query Skill

通过美国财政部 FiscalData API 查询 Daily Treasury Statement (DTS) 及 Monthly Statement of the Public Debt (MSPD) 数据集，通过 ticdata.treasury.gov 下载 Treasury International Capital (TIC) 外国持有美债数据，以及通过 TreasuryDirect XML 查询国债拍卖计划、实际拍卖结果（含 bid-to-cover）和近期拍卖安排。支持 DTS 9张 + MSPD 1张 + TIC + 拍卖 共四类数据源，CSV导出（中文表头）及数据分析。

## 触发场景

当用户提到以下意图时触发本技能：
- "查询美国财政部数据" / "美国财政部数据"
- "Treasury数据" / "DTS数据"
- "财政部现金流数据" / "美国财政数据"
- 查询债务、现金余额、税收存款等具体指标
- **"国债余额" / "按证券类型查国债" / "MSPD数据"**
- **"Bills/Notes/Bonds/TIPS余额" / "可流通国债分类"**
- **"TIC数据" / "外国持有美债" / "美债持有国排名" / "谁在买美债"**
- **"债务精确余额" / "Debt to the Penny" / "国债总余额"**
- **"国债利率" / "平均发行利率" / "Bills利率"**
- **"利息支出" / "国债利息成本" / "Interest Expense"**
- **"发债计划" / "拍卖日程" / "Tentative Schedule" / "拍卖日历"**
- **"拍卖结果" / "投标倍数" / "bid-to-cover" / "中标利率"**
- **"近期拍卖" / "即将拍卖" / "Upcoming Auctions" / "未来拍卖安排"**
- **"计划vs实际" / "拍卖对比" / "拍卖偏差"**
- **"52周国库券" / "52-Week Bill拍卖" / "CMB拍卖"**

---

## 一、API 基础信息

- **基础 URL**: `https://api.fiscaldata.treasury.gov/services/api/fiscal_service`
- **认证方式**: 无需认证，完全开放
- **请求方法**: 仅支持 GET
- **响应格式**: JSON（默认）/ CSV / XML（通过 `format=` 参数指定）
- **API 文档**: https://fiscaldata.treasury.gov/api-documentation/
- **DTS 数据字典**: https://fiscaldata.treasury.gov/datasets/daily-treasury-statement/
- **MSPD 数据字典**: https://fiscaldata.treasury.gov/datasets/monthly-statement-public-debt/
- **TIC 数据下载**: https://ticdata.treasury.gov/resource-center/data-chart-center/tic/Documents/slt_table5.txt
- **TIC 系统主页**: https://home.treasury.gov/data/treasury-international-capital-tic-system

> ⚠️ **注意**：DTS + MSPD 通过 FiscalData REST API（JSON）查询；**TIC 数据是纯文本文件下载**（tab分隔），无 REST API，需使用 `scripts/query_tic_data.py` 解析。

---

## 二、支持的10张数据表（DTS 9张 + MSPD 1张）

| 表名（中文） | 表名（英文） | API 端点 | 记录数 |
|-------------|-------------|---------|--------|
| 运营现金余额 | Operating Cash Balance | `/v1/accounting/dts/operating_cash_balance` | 16,298 |
| 运营现金存取款 | Deposits and Withdrawals of Operating Cash | `/v1/accounting/dts/deposits_withdrawals_operating_cash` | 468,609 |
| 公共债务交易 | Public Debt Transactions | `/v1/accounting/dts/public_debt_transactions` | 126,284 |
| 公共债务交易现金基础调整 | Adjustment of Public Debt Transactions to Cash Basis | `/v1/accounting/dts/adjustment_public_debt_transactions_cash_basis` | 74,442 |
| 受限债务 | Debt Subject to Limit | `/v1/accounting/dts/debt_subject_to_limit` | 39,543 |
| 机构间税收转移 | Inter-Agency Tax Transfers | `/v1/accounting/dts/inter_agency_tax_transfers` | 3,284 |
| 所得税退税发放 | Income Tax Refunds Issued | `/v1/accounting/dts/income_tax_refunds_issued` | 18,724 |
| 联邦税收存款 | Federal Tax Deposits | `/v1/accounting/dts/federal_tax_deposits` | 47,148 |
| 短期现金投资 | Short-Term Cash Investments | `/v1/accounting/dts/short_term_cash_investments` | 49,516 |
| **★ 国债余额汇总（按证券类型）** | **Summary of Treasury Securities Outstanding** | **`/v1/debt/mspd/mspd_table_1`** | 4,603 |
| **★ 国债精确余额** | **Debt to the Penny** | **`/v2/accounting/od/debt_to_penny`** | 8,316 |
| **★ 国债平均利率** | **Average Interest Rates** | **`/v2/accounting/od/avg_interest_rates`** | 4,945 |
| **★ 国债利息支出** | **Interest Expense on the Public Debt** | **`/v2/accounting/od/interest_expense`** | 7,169 |
| **★ 联邦债务明细表** | **Schedules of Federal Debt** | **`/v1/accounting/od/schedules_fed_debt`** | 4,818 |

> **金额单位**：所有金额字段单位为百万美元（如 `825550` = 8255.50亿美元），数值已四舍五入至最接近的百万位。

---

## 附：数据表详细说明（英文）

> 以下为9张数据表的英文原始描述，用于准确识别用户需求对应的数据表。

### 1. Operating Cash Balance（运营现金余额）

**Table Name**: Operating Cash Balance
**Description**: This table represents the Treasury General Account balance. Additional detail on changes to the Treasury General Account can be found in the Deposits and Withdrawals of Operating Cash table. All figures are rounded to the nearest million.
**Row Description**: Each row represents the closing balance of the Treasury General Account for the record_date and opening balances for the day, month, and fiscal year.
**Row Count**: 16,298

**适用查询场景**：查询国库一般账户(TGA)的日终余额、开盘余额。

---

### 2. Deposits and Withdrawals of Operating Cash（运营现金存取款）

**Table Name**: Deposits and Withdrawals of Operating Cash
**Description**: This table represents deposits and withdrawals from the Treasury General Account. A summary of changes to the Treasury General Account can be found in the Operating Cash Balance table. All figures are rounded to the nearest million.
**Row Description**: Each row represents the amount of deposits and/or withdrawals for the record_date, month-to-date, and year-to-date.
**Row Count**: 468,609

**适用查询场景**：查询国库一般账户(TGA)的存款和取款明细，了解现金流向。

**【重要经验】查询某部门/类别收支的方法：**
- 本表按 `transaction_catg`（交易类别代码）区分收支的部门/类别归属
- 查**支出**：筛选 `transaction_type:eq:Withdrawals`，再按 `transaction_catg` 分组汇总
- 查**收入**：筛选 `transaction_type:eq:Deposits`，再按 `transaction_catg` 分组汇总
- 关键字段：
  - `transaction_catg`：交易类别代码（如 `Dept of Defense (DoD)`、`DoD - Military Active Duty Pay`）
  - `transaction_catg_desc`：交易类别描述（通常为 null）
  - `transaction_today_amt`：当日金额
  - `transaction_mtd_amt`：月度累计金额（Month-To-Date，取最新日期的最大值）
  - `transaction_fytd_amt`：财年累计金额（Fiscal Year-To-Date）
- 常见部门/类别代码示例：
  - `Dept of Defense (DoD)` / `DoD - Military Active Duty Pay` / `DoD - Military Retirement` → 国防部
  - `Dept of Agriculture (USDA)` → 农业部
  - `Dept of Health and Human Services (HHS)` → 卫生与公共服务部
  - `Dept of Veterans Affairs (VA)` → 退伍军人事务部
  - `Dept of Homeland Security (DHS)` → 国土安全部
  - `Individual Income Tax` / `Corporation Income Tax` → 税收收入
  - `Public Debt Cash Issues/Redemptions` → 公共债务

---

### 3. Public Debt Transactions（公共债务交易）

**Table Name**: Public Debt Transactions
**Description**: This table represents the issues and redemption of marketable and nonmarketable securities. All figures are rounded to the nearest million.
**Row Description**: Each row represents the amount of public debt issues and/or redemptions for the record_date, month-to-date, and year-to-date.
**Row Count**: 126,284

**适用查询场景**：查询公共债务的发行和赎回情况，了解国债市场活动。

**【重要经验】"国债"口径说明（写给分析人员）：**
- 当用户提到**"国债"发行/存量/余额**时，默认指**全部可流通国债（Marketable Treasury Securities）**，包含以下所有子类：
  - `Bills`（国库券，≤1年到期）
  - `Notes`（中期票据，2-10年到期）
  - `Bonds`（长期债券，20-30年到期）
  - `Inflation-Protected Securities`（TIPS，通胀保护国债）
  - `Federal Financing Bank`（FFB，规模通常为0）
- **除非用户明确指定**（如"短期国债"/"T-Bills only"），否则不应只取Bills一类
- **常见错误**：把"国债发行量"等同于"T-Bills发行量"——Bills只是国债的一部分，遗漏Notes/Bonds/TIPS会导致严重低估
- **Nonmarketable（不可流通）国债**：包括Government Account Series（GAS，政府账户系列）、Savings Securities等，**不算"市场交易的国债"**，但在计算"总公共债务余额"时需包含
- **数据表选择**：
  - 查**发行/赎回流量（应计制）** → `public_debt_transactions`表（表 III-A），`transaction_type=Issues/Redemptions`
  - 查**发行/赎回现金流量（现金制）** → `adjustment_public_debt_transactions_cash_basis`表（表 III-B），看`adj_today_amt`合计
  - 查**存量余额** → `debt_subject_to_limit`表（含`Debt Held by the Public`等）
  - 注：`public_debt_transactions`是流量表（每日发行/偿还），不是存量；存量余额需查其他表
- **应计制 vs 现金制**：
  - 表 III-A（本表）是**应计制**（Accrual Basis）：债务交易**发生时**记录，不论现金是否收付。例如：折扣发行票据，应计制按**面值**记录发行额
  - 表 III-B（Adjustment表）是**现金制**（Cash Basis）调整：债务交易**产生现金流入/流出时**记录。例如：折扣发行票据，现金制只记录**实际收到的折扣后金额**
  - 两表关系：表 III-B 第一行 `adj_type="Public Debt Issues (Table III-A)"` 的金额 = 表 III-A 当日 Issues 合计。表 III-B 其余行是对表 III-A 的现金制调整项
  - **分析现金净流入/流出**（对TGA的影响）→ 用表 III-B；**分析证券类型结构**（Bills/Notes/Bonds）→ 用表 III-A

---


### 4. Adjustment of Public Debt Transactions to Cash Basis（公共债务交易现金基础调整）

**Table Name**: Adjustment of Public Debt Transactions to Cash Basis
**Description**: This table represents cash basis adjustments to the issues and redemptions of Treasury securities in the Public Debt Transactions table. All figures are rounded to the nearest million.
**Row Description**: Each row represents the adjustment amounts for record_date, month-to-date, and year-to-date.
**Row Count**: 74,442
**API 端点**: `/v1/accounting/dts/adjustment_public_debt_transactions_cash_basis`

**适用查询场景**：查询公共债务交易按现金基础调整的金额，用于现金流量分析（对TGA现金影响）。

**【重要经验】与表 III-A（Public Debt Transactions）的关系：**

| | 表 III-A（Public Debt Transactions） | 表 III-B（本表，Adjustment to Cash Basis） |
|---|---|---|
| **会计基础** | 应计制（Accrual Basis） | 现金制（Cash Basis）调整说明 |
| **记录时机** | 债务交易**发生时**记录（不论现金是否收付） | 债务交易**产生现金流入/流出时**记录 |
| **DTS 表号** | Table III-A | Table III-B |
| **核心问题** | "今天应计了哪些债务交易？" | "今天的债务交易带来多少现金进出？" |
| **一行对应关系** | 当日 Issues 合计 = 表 III-B 第一行 `adj_type="Public Debt Issues (Table III-A)"` 的金额 | 第一行是表 III-A 的复制，其余行是调整项 |

**调整项详解（`adj_type` 字段，以 Issues 为例）：**

| `adj_type` 值 | 含义 | 对现金的影响 | 符号方向 |
|---|---|---|---|
| `Public Debt Issues (Table III-A)` | 表 III-A 发行总额（应计制基数） | 基数，无调整 | 基准 |
| `Premium on New Issues` | 新发行溢价（现金制下多收现金） | 现金流入增加 | + |
| `Bills (-)` | 国库券发行折扣（Sold at discount，现金少收） | 现金流入减少 | - |
| `Bonds and Notes (-)` | 票据/债券发行折扣 | 现金流入减少 | - |
| `Federal Financing Bank (-)` | 联邦融资银行调整 | 通常为零 | - |
| `Government Account Transactions (-)` | **政府账户交易调整**（最大项，GAS应计与现金之差） | GAS无实际现金流动时调整 | - |
| `Interest Increment on US Savings Securities (-)` | 储蓄国债利息增量调整 | 现金流出减少（应计利息未付现） | - |
| `Inflation-Protected Securities Increment (-)` | TIPS 通胀调整增量 | 通胀调整应计但未付现 | - |

> Redemptions（偿还）方向类似，但有 `Premium on Debt Buyback Operation`（回购溢价）和 `Discount on Debt Buyback Operation`（回购折扣）两项。

**现金制净发行计算公式：**
```
现金制净发行 = 表 III-B 所有 Issues 行 adj_today_amt 合计 - 所有 Redemptions 行 adj_today_amt 合计
```
或直接取表 III-B 中 `transaction_type="Public Debt Cash Issues"` 与 `transaction_type="Public Debt Cash Redemptions"` 的净额（如有该 transaction_type）。

**使用建议：**

| 分析目的 | 应使用的表 |
|---|---|
| "财政部今天新发了哪些国债"（证券类型分析，Bills/Notes/Bonds/TIPS 各自多少） | **表 III-A**（`public_debt_transactions`，按 `security_type` 分类） |
| "国债发行/偿还给 TGA 带来了多少现金净流入" | **表 III-B**（本表，`adjustment_..._cash_basis`，看 `adj_today_amt` 合计） |
| "今天财政部净现金发行多少国债" | 表 III-B 的 Issues 行合计 减 Redemptions 行合计 |
| 分析折扣/溢价对现金的影响 | 表 III-B 的 `Bills (-)` / `Bonds and Notes (-)` / `Premium on New Issues` 行 |

**一句话总结**：表 III-A 回答"发了什么债"（应计制），表 III-B 回答"收支了多少现金"（现金制）。表 III-B 是对表 III-A 的现金制重构。

---

### 5. Debt Subject to Limit（受限债务）

**Table Name**: Debt Subject to Limit
**Description**: This table represents the breakdown of total public debt outstanding as it relates to the statutory debt limit. All figures are rounded to the nearest million.
**Row Description**: Each row represents the closing balance of debt subject to the limit for today and opening balances for record_date, month, and fiscal year.
**Row Count**: 39,543

**适用查询场景**：查询受法定债务上限限制的公开债务余额，了解债务上限使用情况。

**【重要经验】Debt Not Subject to Limit 的统计方法：**
- **定义**：Debt Not Subject to Limit = Total Public Debt Outstanding - Debt Subject to Limit
- **组成部分**（3项）：
  1. **Unamortized Discount**（未摊销发行折扣）：规模约 $174B（2026-05-22），数据来源为SLT（Treasury's SLT system）
  2. **Federal Financing Bank (FFB)**（联邦融资银行债务）：规模约 $4B，数据来源为FFB financial reports
  3. **Other**（其他）：规模约 $0.5B，数据来源为Treasury general ledger
- **会计意义**：这3项债务虽然计入Total Public Debt，但依法不受债务上限约束（statutorily excluded from the limit）
- **查询方法**：Debt Not Subject to Limit 不直接存储在表中，需通过计算 `Total Public Debt - Debt Subject to Limit` 获得；或查 `debt_catg` 字段中值为 "Debt Not Subject to Limit" 的记录（如有）

---

### 6. Inter-Agency Tax Transfers（机构间税收转移）

**Table Name**: Inter-Agency Tax Transfers
**Description**: This table represents the breakdown of inter-agency tax transfers within the federal government. All figures are rounded to the nearest million.
**Row Description**: Each row represents the amount of inter-agency tax transfers for record_date, month-to-date, and year-to-date.
**Row Count**: 3,284

**适用查询场景**：查询联邦政府内部机构间的税收转移金额。

---

### 7. Income Tax Refunds Issued（所得税退税发放）

**Table Name**: Income Tax Refunds Issued
**Description**: This table represents the breakdown of tax refunds by recipient (individual vs business) and type (check vs electronic funds transfer). Tax refunds are also represented as withdrawals in the Deposits and Withdrawals of Operating Cash table. All figures are rounded to the nearest million. As of February 14, 2023, Table VI Income Tax Refunds Issued was renamed to Table V Income Tax Refunds Issued within the published report.
**Row Description**: Each row represents the amount of income tax refunds issued for record_date, month-to-date, and year-to-date.
**Row Count**: 18,724

**适用查询场景**：查询所得税退税的发放金额，按收款人类型（个人/企业）和方式（支票/电子转账）分类。

---

### 8. Federal Tax Deposits（联邦税收存款）

**Table Name**: Federal Tax Deposits
**Description**: This table represents the breakdown of taxes that are received by the federal government. Federal taxes received are represented as deposits in the Deposits and Withdrawals of Operating Cash table. All figures are rounded to the nearest million.
**Row Description**: Each row represents the amount of federal tax deposits for record_date, month-to-date, and year-to-date.
**Row Count**: 47,148

**适用查询场景**：查询联邦政府收到的税收存款金额，了解税收收入情况。

**【重要经验】数据更新状态：**
- **数据停止更新时间**：2023年2月13日（record_date = 2023-02-13）
- **原因**：美国财政部从2023年2月14日起停止更新此表（Table V Federal Tax Deposits）
- **最新数据**：查询时 `sort=-record_date&limit=1` 返回的最新记录是 `2023-02-13`
- **替代数据源**：如需2023年2月之后的税收数据，可查 `deposits_withdrawals_operating_cash` 表，筛选 `transaction_catg` 包含 "Tax" 的记录（如 `Individual Income Tax`、`Corporation Income Tax`）

---

### 9. Short-Term Cash Investments（短期现金投资）

**Table Name**: Short-Term Cash Investments
**Description**: This table represents the amount Treasury has in short-term cash investments. Deposits and withdrawals of short-term cash investments are also represented in the Deposits and Withdrawals of Operating Cash table. This program was suspended indefinitely in 2008. All figures are rounded to the nearest million. As of February 14, 2023, Table V Short Term Cash Investments will no longer be updated and removed from the published report. The historical data will remain available.
**Row Description**: Each row represents the deposits and/or withdrawals of short-term cash investments for record_date broken down by type of depository.
**Row Count**: 49,516

**适用查询场景**：查询财政部的短期现金投资金额（历史数据，2008年后已暂停更新）。

---

### 10. MSPD — Summary of Treasury Securities Outstanding（国债余额汇总 · 按证券类型）

**Table Name**: Summary of Treasury Securities Outstanding
**API 端点**: `/v1/debt/mspd/mspd_table_1`
**Row Count**: 4,603
**发布日期**: 每月第四个工作日发布，数据反映上月末情况
**最新数据**: 2026-04-30（发布：2026-05-06）
**金额单位**: 百万美元

> ⚠️ **重要**：本表属于 **MSPD（Monthly Statement of the Public Debt）** 数据集，**不在 DTS 9张表内**。API 路径前缀为 `/v1/debt/mspd/`（不是 `/v1/accounting/dts/`）。

**【核心用途】按证券类型分类的国债存量余额查询**

这是 DTS 数据集中**唯一**能提供按证券类型（Bills/Notes/Bonds/TIPS/FRNs）**存量余额**（Outstanding Balance，而非发行/偿还流量）的数据表。

| 关键字段 | 说明 |
|---------|------|
| `security_type_desc` | 一级分类：**Marketable**（可流通）/ **Nonmarketable**（不可流通） |
| `security_class_desc` | 二级分类：**Bills / Notes / Bonds / TIPS / FRNs / Government Account Series** 等 |
| `debt_held_public_mil_amt` | 公众持有余额（百万美元） |
| `intragov_hold_mil_amt` | 政府内部持有余额（百万美元） |
| `total_mil_amt` | 总计余额（百万美元） |

**常见 security_class_desc 值：**

| 大类 | security_class_desc | 说明 |
|------|---------------------|------|
| Marketable | Bills | 国库券（≤1年） |
| Marketable | Notes | 中期票据（2-10年） |
| Marketable | Bonds | 长期债券（20-30年） |
| Marketable | Treasury Inflation-Protected Securities | TIPS（通胀保值国债） |
| Marketable | Floating Rate Notes | FRNs（浮动利率票据） |
| Marketable | Federal Financing Bank | FFB |
| Nonmarketable | Government Account Series | 政府账户系列（如社保信托基金） |
| Nonmarketable | United States Savings Securities | 储蓄国债 |
| Nonmarketable | State and Local Government Series | SLGS |
| Nonmarketable | Domestic Series | 国内系列 |
| Nonmarketable | Other | 其他 |

**查询示例：**

```bash
# 查询最新一期所有证券类型余额
python scripts/query_treasury_data.py \
  --table mspd_summary \
  --output ./output

# 查询某日期的数据
python scripts/query_treasury_data.py \
  --table mspd_summary \
  --filter "record_date:eq:2026-04-30" \
  --output ./output
```

**与 DTS 其他表的对比：**

| 需求 | DTS `public_debt_transactions` | DTS `debt_subject_to_limit` | **MSPD `mspd_table_1`** |
|------|------|------|------|
| 数据性质 | 流量（发行/偿还） | 存量（Pubic vs Intragovernmental） | **存量 + 证券类型细分** |
| Bills/Notes/Bonds/TIPS分类？ | ✅（但只有流量） | ❌ | **✅** |
| 按证券类型查余额？ | ❌（需自行累计） | ❌ | **✅** |

**【典型数据】** 截至 2026-04-30：
- Total Public Debt: **$38,968B**
- Marketable: $30,677B（78.7%）
  - Notes $15,938B（52.0%）
  - Bills $6,622B（21.6%）
  - Bonds $5,383B（17.5%）
  - TIPS $2,080B（6.8%）
  - FRNs $650B（2.1%）

---

### 11. TIC — Major Foreign Holders of Treasury Securities（外国持有美债数据）

**数据源**: `https://ticdata.treasury.gov/resource-center/data-chart-center/tic/Documents/slt_table5.txt`
**格式**: Tab 分隔的纯文本文件（**非 REST API**，不可用 `query_treasury_data.py`）
**查询脚本**: `scripts/query_tic_data.py`
**更新频率**: 每月中旬发布，数据滞后约 2 个月（例：6月中旬发布4月数据）
**最新数据**: 2026-03（发布：2026-05-15）

> ⚠️ **重要**：TIC 数据**不在 FiscalData API 中**，在 ticdata.treasury.gov 独立发布。数据为固定宽度文本文件，需用 `query_tic_data.py` 解析。

**【核心用途】按国别/地区查询外国持有美国国债的月度数据**

这是了解全球各国央行和投资者对美国国债需求变化的**权威数据源**。

| 关键数据 | 说明 |
|---------|------|
| 各国月度持仓 | 21个国家/地区 + All Other + Grand Total |
| 外国官方 vs 私人 | 区分央行/主权基金 vs 私人投资者 |
| 长期 vs 短期 | Bills（短期国库券）vs Notes & Bonds（中长期国债） |
| 13个月历史 | 每月数据包含最近 13 个月的持仓 |

**数据字段：**

| 字段 | 说明 |
|------|------|
| 国家/地区 | Japan, China Mainland, United Kingdom 等 21 个实体 |
| 最新持仓(十亿) | 最新月份的持仓金额（十亿美元） |
| 上月持仓(十亿) | 上月持仓金额 |
| 月变化(十亿) | 最新 - 上月 |
| 2026-03 ~ 2025-03 | 13 个月的完整时间序列 |

**查询示例：**

```bash
# 下载最新 TIC 数据并导出 CSV
python scripts/query_tic_data.py \
  --output ./output

# 只显示前 5 名
python scripts/query_tic_data.py \
  --top 5 \
  --output ./output
```

**典型数据（2026-03）：**

| 排名 | 国家/地区 | 持仓 | 月变化 |
|:----:|----------|:----:|:-----:|
| 1 | 🇯🇵 日本 | $1,191.6B | -$47.7B |
| 2 | 🇬🇧 英国 | $926.9B | +$29.6B |
| 3 | 🇨🇳 中国内地 | $652.3B | -$41.0B |
| 4 | 🇰🇾 开曼群岛 | $459.4B | +$16.4B |
| 5 | 🇧🇪 比利时 | $454.0B | -$0.7B |

外国持有总计：**$9,348.7B**（其中官方 $3,902.2B）

**关键背景：金融中心托管效应**

排名中的比利时、卢森堡、开曼群岛、爱尔兰、瑞士、新加坡等并非真正的"国家需求"，而是全球金融中心的托管持仓：
- **比利时** = Euroclear（全球最大债券结算所）
- **卢森堡 / 爱尔兰** = 基金注册地
- **开曼群岛** = 对冲基金注册地（基差交易，实际持仓可能接近 $2T，严重低估）

**与 DTS / MSPD 的关系：**

| 需求 | TIC | DTS | MSPD |
|------|:---:|:---:|:---:|
| 谁在买/卖美债？（按国家） | ✅ | ❌ | ❌ |
| 每天发行多少国债？（流量） | ❌ | ✅ | ❌ |
| 总共有多少国债？（按证券类型） | ❌ | ❌ | ✅ |

---

### 12. Debt to the Penny — 国债精确余额（每日）

**API 端点**: `/v2/accounting/od/debt_to_penny`
**Row Count**: 8,316
**更新频率**: 每日
**金额单位**: **美元（精确到分）**

> ⚠️ 与 DTS `debt_subject_to_limit` 的区别：DTS 表的金额单位是**百万美元**（四舍五入），Debt to the Penny 是**美元精确值**（到分）。

| 字段 | 说明 |
|------|------|
| `debt_held_public_amt` | 公众持有债务（美元） |
| `intragov_hold_amt` | 政府内部持有（美元） |
| `tot_pub_debt_out_amt` | 公共债务总余额（美元） |

```bash
python scripts/query_treasury_data.py --table debt_to_penny --filter "record_date:gte:2026-05-01" --output ./output
```

---

### 13. Average Interest Rates — 国债平均发行利率（每月）

**API 端点**: `/v2/accounting/od/avg_interest_rates`
**Row Count**: 4,945
**更新频率**: 每月
**金额单位**: 百分比（%）

| 字段 | 说明 |
|------|------|
| `security_type_desc` | Marketable / Nonmarketable |
| `security_desc` | Treasury Bills / Notes / Bonds / TIPS / FRNs 等 |
| `avg_interest_rate_amt` | 平均利率（%） |

**典型数据（2026-04）**: Bills 3.70%, Notes 3.23%, Bonds 3.40%, TIPS 1.07%, FRNs 3.76%

```bash
python scripts/query_treasury_data.py --table avg_interest_rates --output ./output
```

---

### 14. Interest Expense — 国债利息支出（每月，按证券类型）

**API 端点**: `/v2/accounting/od/interest_expense`
**Row Count**: 7,169
**更新频率**: 每月

| 字段 | 说明 |
|------|------|
| `expense_type_desc` | 证券类型（Treasury Notes / Bonds / TIPS / FRNs） |
| `month_expense_amt` | 当月利息支出（美元） |
| `fytd_expense_amt` | 本财年累计利息支出（美元） |

**典型数据（2026-04）**: Notes 月利息 $41.3B, FYTD $281.7B；全口径月利息 \>$70B

```bash
python scripts/query_treasury_data.py --table interest_expense --filter "record_date:eq:2026-04-30" --output ./output
```

---

### 15. Schedules of Federal Debt — 联邦债务明细表（每月）

**API 端点**: `/v1/accounting/od/schedules_fed_debt`
**Row Count**: 4,818
**更新频率**: 每月

| 字段 | 说明 |
|------|------|
| `debt_holder_type` | 持有人类型（Held by Public / Intragovernmental） |
| `security_class1_desc` | 一级证券分类 |
| `security_class2_desc` | 二级证券分类 |
| `principal_mil_amt` | 本金余额（百万美元） |
| `accrued_int_payable_mil_amt` | 已计提未付利息（百万美元） |
| `net_unamortized_mil_amt` | 未摊销折扣/溢价（百万美元） |

> 比 MSPD 更细：多了已计提利息和未摊销项，且是 holder × security 双维度交叉。

```bash
python scripts/query_treasury_data.py --table schedules_fed_debt --filter "record_date:eq:2026-04-30" --output ./output
```

---

## 三、TreasuryDirect 拍卖数据（三类独立数据源）

> ⚠️ **注意**：以下三类拍卖数据**不在 FiscalData API 中**，均来自 TreasuryDirect 网站。与上述 DTS/MSPD/TIC 是不同的数据体系。

### 四大入口对照表（按用途速查）

| 入口 | 本质 | 数据粒度 | 获取方式 | 类比 |
|------|------|:---:|------|------|
| **General Auction Timing** | 永久性拍卖规则 | 周/月/季模式 | WebFetch | 课表模板——"每周二上数学" |
| **Tentative Auction Schedule** | 季度排期 PDF | 每笔精确到天 + 证券类型 | pdfplumber 解析 PDF | 学期课表——"2月到7月哪天考哪科" |
| **Upcoming Auctions** | 本周已公告拍卖 | 每笔含规模（公告后） | WebFetch / PendingAuctions.xml | 公告栏——"明天考语文，范围3章" |
| **Previous Announcements & Results** | 历史拍卖归档 | 每笔含 bid-to-cover + 投标人分类 | XML 批量抓取 | 档案室——"6月23日数学成绩单" |

### 16. 拍卖计划查询（Tentative Auction Schedule）

**数据源**: `https://home.treasury.gov/system/files/221/Tentative-Auction-Schedule.pdf`
**格式**: PDF（文本可直接用 pdfplumber 解析，无需 OCR）
**更新频率**: 每季度 Refunding 时发布（2月初/5月初/8月初/11月初）
**覆盖期**: 发布后约 6 个月

> ⚠️ **注意**：此 PDF 含 `FlateDecode` 压缩流，**WebFetch 无法读取**，必须用本地 Python + pdfplumber 解析。每次总是当前最新版覆盖旧文件。

**【发布节奏】**

| 季度 | 对应 Refunding 月 | 发布窗口 | 覆盖期 |
|:---:|:---:|------|------|
| Q1 | **2月** | 2月初（2/4~2/10） | 2月 ~ 7月 |
| Q2 | **5月** | 5月初（5/5~5/10） | 5月 ~ 10月 |
| Q3 | **8月** | 8月初（8/4~8/10） | 8月 ~ 次年1月 |
| Q4 | **11月** | 11月初（11/4~11/10） | 11月 ~ 次年4月 |

**【PDF 文本格式】**

每行一条拍卖计划，格式固定：
```
Security Type Announcement Date Auction Date Settlement Date
3-Year NOTE Wednesday, May 06, 2026 Monday, May 11, 2026 Friday, May 15, 2026
10-Year NOTE Wednesday, May 06, 2026 Tuesday, May 12, 2026 Friday, May 15, 2026
...
```

- 假日行以 `Holiday -` 开头
- `R` 后缀 = Reopening（续发），`T` = TIPS，`RT` = TIPS Reopening
- 拍卖计划不含规模——规模由 Refunding Announcement 单独公布

**【查询流程】**

```bash
# Step 1: 下载 PDF
curl -sL -o tentative.pdf "https://home.treasury.gov/system/files/221/Tentative-Auction-Schedule.pdf"

# Step 2: 安装 pdfplumber
pip install pdfplumber

# Step 3: 解析并提取指定月份
python scripts/parse_tentative_schedule.py --month 5 --year 2026 --output ./output
```

**脚本模板**（`parse_tentative_schedule.py`）：
```python
import pdfplumber
with pdfplumber.open("tentative.pdf") as pdf:
    for page in pdf.pages:
        text = page.extract_text()
        for line in text.split('\n'):
            # 按格式: "3-Year NOTE Wednesday, May 06, 2026 Monday, May 11, 2026 Friday, May 15, 2026"
            if re.match(r'^[\w\-]+', line):
                # 解析证券类型和三个日期
                ...
```

---

### 17. 拍卖结果查询（XML 批量抓取）

**数据源**: `https://treasurydirect.gov/xml/R_YYYYMMDD_N.xml`
**格式**: XML（机器直接解析，比 PDF 更优）
**覆盖范围**: 1998 年至今每笔拍卖
**关键字段**: BidToCoverRatio, TotalTendered, TotalAccepted, PrimaryDealerAccepted, DirectBidderAccepted, IndirectBidderAccepted, SOMAAccepted, HighYield, HighDiscountRate, InterestRate

> ⚠️ **重要**：文件名 `_N` 为当天发布序号，**不编码证券类型**。同一天的 `_1` 可能是 Bill，`_2` 可能是 Note——需读取 XML 中的 `<SecurityType>` 判断。

**【XML 与 PDF 对比】**

| 区别 | PDF | XML |
|------|:---:|:---:|
| 可机器解析 | ❌ 需 PDF 解析 | ✅ 直接 parse |
| 公告 + 结果合一 | ❌ 分开 3 个 PDF | ✅ 单个文件 |
| 含投标人分类 | ✅ | ✅ |
| 含 BidToCoverRatio | ✅ | ✅ |
| URL 规律 | `.../preanre/<年份>/R_xxx.pdf` | `xml/R_xxx.xml` |

**【获取 XML 链接的三种方法】**

| 方法 | 覆盖率 | 效率 | 适用场景 |
|------|:---:|:---:|------|
| **A. 暴力遍历**：遍历日期 + 试 `_1`~`_8` | ✅ 100% | 🔴 ~20% 命中率 | 临时小范围查询 |
| **B. Previous Announcements 页面**：选年份 → 提取 XML 链接 | ⚠️ WebFetch 仅返回 Bills 标签 | 🟡 一次页面请求 | 有浏览器时全量最优 |
| **C. Agent Browser 走页面**：打开 JS 页面 → 切 Notes/Bonds/TIPS/FRN 标签 → 提取 | ✅ 100% | 🟢 最精准 | 需要浏览器自动化 |

> ⚠️ **坑**：Previous Announcements 页面（`previous-announcements-and-results/`）使用 JavaScript 多标签页，WebFetch 只能抓到 Bills 标签下的数据。Notes/Bonds/TIPS/FRNs 的结果在 JS 动态加载的其他标签页中——需用 Agent Browser 切标签才能拿到。

**【方法 A：暴力遍历脚本模板】**

```bash
# 遍历某月所有工作日，自动试探 XML
python scripts/scrape_month_auctions.py --year 2026 --month 5 --output ./output
```

核心逻辑：
```python
for date in all_workdays(year, month):
    for seq in range(1, 9):  # 每天最多试 _1 到 _8
        url = f"https://treasurydirect.gov/xml/R_{date}_{seq}.xml"
        try:
            xml = fetch(url)  # HTTP GET
            # 解析 <SecurityType>, <BidToCoverRatio>, etc.
            results.append(parse(xml))
        except HTTP404:
            break  # 该日期此后缀无拍卖
```

**关键字段提取（XML 路径 → 含义）：**

| XML 标签 | 含义 | 单位/格式 |
|---------|------|------|
| `AuctionAnnouncement/SecurityType` | BILL/NOTE/BOND | — |
| `AuctionAnnouncement/SecurityTermWeekYear` | 4-WEEK/3-YEAR/30-YEAR etc. | — |
| `AuctionAnnouncement/OfferingAmount` | 发行规模 | 十亿美元 |
| `AuctionAnnouncement/InterestRate` | 票面利率（Coupon 证券） | % |
| `AuctionResults/BidToCoverRatio` | **投标倍数** | 比率 |
| `AuctionResults/HighDiscountRate` | 高贴现率（Bills） | % |
| `AuctionResults/HighYield` | 中标收益率（Notes/Bonds） | % |
| `AuctionResults/HighDiscountMargin` | 中标贴现利差（FRNs） | % |
| `AuctionResults/TotalTendered` | 投标总额 | 美元 |
| `AuctionResults/TotalAccepted` | 中标总额 | 美元 |
| `AuctionResults/PrimaryDealerAccepted` | PD 中标 | 美元 |
| `AuctionResults/DirectBidderAccepted` | Direct 中标 | 美元 |
| `AuctionResults/IndirectBidderAccepted` | Indirect 中标（含外国央行） | 美元 |
| `AuctionResults/SOMAAccepted` | SOMA（美联储）中标 | 美元 |
| `AuctionResults/HighAllocationPercentage` | 高分配率 | % |

**【投标人占比计算】**
```python
total = float(row['TotalAccepted'])
pd_pct = float(row['PrimaryDealerAccepted']) / total * 100
dir_pct = float(row['DirectBidderAccepted']) / total * 100
ind_pct = float(row['IndirectBidderAccepted']) / total * 100
```

**【网络注意事项】**
- TreasuryDirect 偶发 `WinError 10054`（连接 Reset），需加重试机制
- 建议每次请求间隔 0.15~0.3 秒避免限流
- 单月全量约 30+ 笔拍卖，暴力遍历约 168 次请求（含 404）

---

### 18. 近期拍卖安排查询（Upcoming Auctions）

**数据源**: `https://www.treasurydirect.gov/xml/PendingAuctions.xml`
**格式**: XML（每周五 10:45 ET 更新，含未来已公告拍卖）
**更新频率**: 每周五
**覆盖范围**: 已公告但尚未拍卖的（通常 2~7 天）

> ⚠️ **注意**：Upcoming Auctions 只在 Treasury 公告后才上架，不是预测性的。要看未来 6 个月的"预期"计划 → 用 Tentative Schedule。

**获取方式**：
```bash
# XML 格式（推荐，结构化）
curl -s "https://www.treasurydirect.gov/xml/PendingAuctions.xml"

# 网页版
# https://www.treasurydirect.gov/auctions/upcoming/
```

**XML 包含字段**：SecurityType, SecurityTerm, CUSIP, AuctionDate, IssueDate, OfferingAmount, AnnouncementDate

> ⚠️ **限制**：PendingAuctions.xml 仅含公告字段，**不含拍卖结果**（bid-to-cover 等），因为还没拍。

---

### 19. 计划 vs 实际偏差对比流程

**【完整对比流水线】**

```
Step 1: 解析 Tentative PDF → 计划日程表
        ↓
Step 2: 批量抓取 XML → 实际拍卖结果表
        ↓
Step 3: 按日期 + 证券类型对齐 → 差异表
        ↓
Step 4: 标记偏差类型：
        ✅ 按计划  |  🟡 日期挪移  |  🔴 规模偏差  |  🆕 计划外(CMB)
```

**偏差常见原因**：
- **假日挪移**：阵亡将士纪念日（5月最后一个周一）等 → 周一拍卖挪到周二
- **CMB 临时追加**：Treasury 为满足短期现金需求临时发行，不在季度计划中
- **规模微调**：Bill 规模可能因 Treasury 供需每周调整（但 Q2 2026 起 Treasury 承诺 Coupon 规模"至少几个季度不变"）

**【对比脚本模板】**
```bash
python scripts/compare_plan_vs_actual.py \
  --tentative ./tentative_q2_2026.pdf \
  --actual ./may2026_auction_results.csv \
  --month 5 --year 2026 \
  --output ./may2026_comparison.csv
```

---

## 四、查询参数说明（FiscalData API）

### 通用参数

| 参数 | 作用 | 示例 |
|------|------|------|
| `fields=` | 指定返回字段（逗号分隔） | `fields=record_date,close_today_bal` |
| `filter=` | 筛选数据 | `filter=record_date:gte:2025-01-01` |
| `sort=` | 排序（`-`开头=降序） | `sort=-record_date` |
| `format=` | 响应格式 | `format=csv` |
| `page[number]=` | 页码（从1开始） | `page[number]=2` |
| `page[size]=` | 每页记录数（最大10000） | `page[size]=1000` |

### filter 筛选算子

| 算子 | 含义 | 示例 |
|------|------|------|
| `eq` | 等于 | `record_date:eq:2026-05-22` |
| `in` | 包含在集合中 | `record_fiscal_year:in:(2024,2025,2026)` |
| `gt` | 大于 | `close_today_bal:gt:1000000` |
| `gte` | 大于等于 | `record_date:gte:2025-01-01` |
| `lt` | 小于 | `transaction_today_amt:lt:10000` |
| `lte` | 小于等于 | `record_calendar_month:lte:6` |
| `neq` | 不等于 | `account_type:neq:Depositary` |

### 多条件组合

用逗号分隔多个条件（AND关系）：
```
filter=record_fiscal_year:eq:2026,account_type:eq:Treasury General Account (TGA) Closing Balance
```

---

## 五、执行流程（FiscalData API）

### Step 1：确认查询需求

与用户确认：
1. **查询哪张表**（9张表选一或多选）
2. **日期范围**（如"2025年以来"、"2026-05-22当天"）
3. **其他筛选条件**（如账户类型、金额范围等）
4. **是否需要数据分析/比对**

若用户未明确指定，则查询全量数据（默认取最近100条）。

### Step 2：执行查询

使用 `scripts/query_treasury_data.py` 脚本执行查询。

**基本用法：**
```bash
python3 scripts/query_treasury_data.py \
  --table operating_cash_balance \
  --filter "record_date:gte:2025-01-01" \
  --output "C:/Users/Administrator/WorkBuddy/2026-05-27-21-43-51/us_treasury_data"
```

**参数说明：**
- `--table`: 表名（使用英文表名或缩写，见下方映射）
- `--filter`: 筛选条件（可选）
- `--sort`: 排序（默认 `-record_date`）
- `--limit`: 下载记录数（默认100，设0则下载全量）
- `--output`: 输出目录

**表名映射（--table 参数值）：**
| 参数值 | 对应表 |
|---------|---------|
| `operating_cash_balance` | 运营现金余额 |
| `deposits_withdrawals` | 运营现金存取款 |
| `public_debt_transactions` | 公共债务交易 |
| `adjustment_public_debt` | 公共债务交易现金基础调整 |
| `debt_subject_to_limit` | 受限债务 |
| `inter_agency_tax` | 机构间税收转移 |
| `income_tax_refunds` | 所得税退税发放 |
| `federal_tax_deposits` | 联邦税收存款 |
| `short_term_cash` | 短期现金投资 |
| `mspd_summary` | **国债余额汇总（按证券类型）** |
| `debt_to_penny` | **国债精确余额（Debt to the Penny）** |
| `avg_interest_rates` | **国债平均利率** |
| `interest_expense` | **国债利息支出** |
| `schedules_fed_debt` | **联邦债务明细表** |

### Step 3：保存结果

脚本自动：
1. 调用 API 获取数据（JSON格式）
2. 将字段名翻译为中文
3. 保存为 CSV 文件（UTF-8 BOM 编码，Excel可直接打开）
4. 返回文件路径

**输出文件命名规则：**
`<表名>_<时间戳>.csv`，例如 `operating_cash_balance_20260527_103045.csv`

### Step 4：数据分析（如需要）

若用户有数据分析或比对诉求，基于CSV数据进行：
1. **描述性统计**：最大值、最小值、均值、中位数
2. **趋势分析**：按日期绘制走势图
3. **比对分析**：多表关联、同比/环比
4. **异常检测**：识别异常值

使用 Python（pandas + matplotlib/seaborn）进行分析，生成图表和报告。

---

## 六、字段中英对照表

### 通用字段（所有表）

| 英文字段名 | 中文字段名 |
|-----------|-----------|
| `record_date` | 记录日期 |
| `table_nbr` | 表格编号 |
| `table_nm` | 表格名称 |
| `sub_table_name` | 子表名称 |
| `src_line_nbr` | 源数据行号 |
| `record_fiscal_year` | 记录财年 |
| `record_fiscal_quarter` | 记录财年季度 |
| `record_calendar_year` | 记录日历年 |
| `record_calendar_quarter` | 记录日历季度 |
| `record_calendar_month` | 记录日历月 |
| `record_calendar_day` | 记录日历日 |

### 运营现金余额 (Operating Cash Balance)

| 英文字段名 | 中文字段名 |
|-----------|-----------|
| `account_type` | 账户类型 |
| `close_today_bal` | 当日收盘余额 |
| `open_today_bal` | 当日开盘余额 |
| `open_month_bal` | 本月开盘余额 |
| `open_fiscal_year_bal` | 本财年开盘余额 |

### 运营现金存取款 (Deposits and Withdrawals of Operating Cash)

| 英文字段名 | 中文字段名 |
|-----------|-----------|
| `account_type` | 账户类型 |
| `transaction_type` | 交易类型 |
| `transaction_catg` | 交易类别 |
| `transaction_catg_desc` | 交易类别描述 |
| `transaction_today_amt` | 当日交易金额 |
| `transaction_mtd_amt` | 当月累计交易金额 |
| `transaction_fytd_amt` | 本财年累计交易金额 |

### 公共债务交易 (Public Debt Transactions)

| 英文字段名 | 中文字段名 |
|-----------|-----------|
| `transaction_type` | 交易类型 |
| `security_market` | 证券市场类型 |
| `security_type` | 证券类型 |
| `security_type_desc` | 证券类型描述 |
| `transaction_today_amt` | 当日交易金额 |
| `transaction_mtd_amt` | 当月累计交易金额 |
| `transaction_fytd_amt` | 本财年累计交易金额 |

### 公共债务交易现金基础调整 (Adjustment of Public Debt Transactions to Cash Basis)

| 英文字段名 | 中文字段名 |
|-----------|-----------|
| `transaction_type` | 交易类型 |
| `adj_type` | 调整类型 |
| `adj_type_desc` | 调整类型描述 |
| `adj_today_amt` | 当日调整金额 |
| `adj_mtd_amt` | 当月累计调整金额 |
| `adj_fytd_amt` | 本财年累计调整金额 |

### 受限债务 (Debt Subject to Limit)

| 英文字段名 | 中文字段名 |
|-----------|-----------|
| `debt_catg` | 债务类别 |
| `debt_catg_desc` | 债务类别描述 |
| `close_today_bal` | 当日收盘余额 |
| `open_today_bal` | 当日开盘余额 |
| `open_month_bal` | 本月开盘余额 |
| `open_fiscal_year_bal` | 本财年开盘余额 |

### 联邦税收存款 (Federal Tax Deposits)

| 英文字段名 | 中文字段名 |
|-----------|-----------|
| `tax_deposit_type` | 税收存款类型 |
| `tax_deposit_type_desc` | 税收存款类型描述 |
| `tax_deposit_today_amt` | 当日税收存款金额 |
| `tax_deposit_mtd_amt` | 当月累计税收存款金额 |
| `tax_deposit_fytd_amt` | 本财年累计税收存款金额 |

### 机构间税收转移 (Inter-Agency Tax Transfers)

| 英文字段名 | 中文字段名 |
|-----------|-----------|
| `transaction_type` | 交易类型 |
| `agency_name` | 机构名称 |
| `transfer_today_amt` | 当日转移金额 |
| `transfer_mtd_amt` | 当月累计转移金额 |
| `transfer_fytd_amt` | 本财年累计转移金额 |

### 所得税退税发放 (Income Tax Refunds Issued)

| 英文字段名 | 中文字段名 |
|-----------|-----------|
| `refund_type` | 退税类型 |
| `refund_today_amt` | 当日退税金额 |
| `refund_mtd_amt` | 当月累计退税金额 |
| `refund_fytd_amt` | 本财年累计退税金额 |

### 短期现金投资 (Short-Term Cash Investments)

| 英文字段名 | 中文字段名 |
|-----------|-----------|
| `investment_type` | 投资类型 |
| `investment_desc` | 投资类型描述 |
| `par_amount` | 票面金额 |
| `accrued_interest` | 应计利息 |

### MSPD 国债余额汇总 (Summary of Treasury Securities Outstanding)

| 英文字段名 | 中文字段名 |
|-----------|-----------|
| `security_type_desc` | 证券大类（Marketable/Nonmarketable） |
| `security_class_desc` | 证券类型（Bills/Notes/Bonds/TIPS/FRNs等） |
| `debt_held_public_mil_amt` | 公众持有余额（百万美元） |
| `intragov_hold_mil_amt` | 政府内部持有余额（百万美元） |
| `total_mil_amt` | 总计余额（百万美元） |

### 国债精确余额 (Debt to the Penny)

| 英文字段名 | 中文字段名 |
|-----------|-----------|
| `debt_held_public_amt` | 公众持有金额（美元，精确到分） |
| `intragov_hold_amt` | 政府内部持有金额（美元，精确到分） |
| `tot_pub_debt_out_amt` | 公共债务总余额（美元，精确到分） |

### 国债平均利率 (Average Interest Rates)

| 英文字段名 | 中文字段名 |
|-----------|-----------|
| `security_type_desc` | 证券大类 |
| `security_desc` | 证券类型（Bills/Notes/Bonds/TIPS/FRNs等） |
| `avg_interest_rate_amt` | 平均利率（%） |

### 国债利息支出 (Interest Expense)

| 英文字段名 | 中文字段名 |
|-----------|-----------|
| `expense_catg_desc` | 支出类别 |
| `expense_group_desc` | 支出分组 |
| `expense_type_desc` | 证券类型 |
| `month_expense_amt` | 当月利息支出（美元） |
| `fytd_expense_amt` | 本财年累计利息支出（美元） |

### 联邦债务明细表 (Schedules of Federal Debt)

| 英文字段名 | 中文字段名 |
|-----------|-----------|
| `debt_holder_type` | 持有人类型 |
| `security_class1_desc` | 证券一级分类 |
| `security_class2_desc` | 证券二级分类 |
| `principal_mil_amt` | 本金余额（百万美元） |
| `accrued_int_payable_mil_amt` | 已计提未付利息（百万美元） |
| `net_unamortized_mil_amt` | 未摊销净额（百万美元） |

---

## 七、常见问题处理

### Q1：API请求失败（SSL证书错误）

**解决方案**：在Python脚本中禁用SSL验证：
```python
import ssl
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
# 然后在 urlopen 时传入 context=ctx
```

### Q2：数据量太大，下载慢

**解决方案**：
- 使用 `page[size]` 参数分批下载（每次最多10000条）
- 使用 `filter` 参数缩小数据范围
- 只选择需要的字段（`fields` 参数）

### Q3：中文字段名显示乱码

**解决方案**：保存CSV时使用 `utf-8-sig` 编码（带BOM），Excel可直接识别。

```python
with open(filepath, 'w', newline='', encoding='utf-8-sig') as f:
    writer = csv.writer(f)
    writer.writerow(chinese_headers)
    # ...
```

---

## 八、示例用法

### 示例1：查询某一天的运营现金余额

**用户请求**："查询2026-05-22的运营现金余额"

**执行步骤**：
1. 确认查询表：`operating_cash_balance`
2. 确认筛选条件：`record_date:eq:2026-05-22`
3. 执行查询脚本
4. 返回CSV文件

### 示例2：查询2025年以来的联邦税收存款

**用户请求**："帮我查2025年以来所有的联邦税收存款数据"

**执行步骤**：
1. 确认查询表：`federal_tax_deposits`
2. 确认筛选条件：`record_date:gte:2025-01-01`
3. 执行查询脚本（可能数据量较大，需分批下载）
4. 返回CSV文件

### 示例3：比对两个月的数据

**用户请求**："比对2026年4月和5月的运营现金余额变化情况"

**执行步骤**：
1. 查询2026年4月数据（`record_date:gte:2026-04-01,record_date:lte:2026-04-30`）
2. 查询2026年5月数据（`record_date:gte:2026-05-01,record_date:lte:2026-05-31`）
3. 进行比对分析（计算变化率、绘制对比图）
4. 返回分析报告

### 示例4：查询某部门/类别的收支（如国防部支出）

**用户请求**："帮我查一下美国国防部在5月截止到最新数据，花费了多少钱"

**分析**：
- 用户问"花费了多少钱" → 查**支出** → 筛选 `transaction_type:eq:Withdrawals`
- 用户问"国防部" → 查 `transaction_catg` 包含 "Defense" 或 "DoD" 的记录
- 应使用表：`deposits_withdrawals_operating_cash`

**执行步骤**：
1. 确认查询表：`deposits_withdrawals`
2. 确认筛选条件：
   - `record_date:gte:2026-05-01`（5月1日以来）
   - `record_date:lte:2026-05-22`（最新数据日期，需先查询确认）
   - `transaction_type:eq:Withdrawals`（支出）
   - 先查询获取 `transaction_catg` 字段的所有值，筛选包含 "Defense" 或 "DoD" 或 "Military" 的类别
   - 示例：`transaction_catg:in:(Dept of Defense (DoD) - misc,DoD - Military Active Duty Pay,DoD - Military Retirement,DoD - Health,IAP - Foreign Military Sales)`
3. 执行查询，按 `transaction_catg` 分组，取最新日期的 `transaction_mtd_amt`（月度累计）汇总
4. 返回结果：
   - 5月累计支出（MTD）
   - 财年累计支出（FYTD）
   - 按类别明细

**注意**：
- `transaction_catg` 的具体值需先查询确认（不同部门/类别代码不同）
- 最新数据日期需先查询（如 `sort=-record_date&limit=1` 获取最新 `record_date`）
- 金额字段 `transaction_mtd_amt` 是累计值，取最新日期的最大值即为当月累计

### 示例5：查询按证券类型分类的国债余额

**用户请求**："查询按证券类型分类的最新美国国债余额" / "我要一个分证券类型的最新余额数据"

**执行步骤**：
1. 确认查询表：`mspd_summary`
2. 先获取最新日期：`sort=-record_date&page[size]=1`
3. 按最新日期查询所有证券类型：`filter=record_date:eq:2026-04-30&page[size]=10000`
4. 按 `security_type_desc` + `security_class_desc` 分组汇总
5. 返回分析结果

**返回结果示例**：
- Marketable: $30,677B（Notes 52%, Bills 22%, Bonds 18%, TIPS 7%, FRNs 2%）
- Nonmarketable: $8,291B（Government Account Series 97%）

### 示例7：查询某月拍卖计划

**用户请求**："帮我查5月的国债拍卖计划" / "5月发债日程表"

**执行步骤**：
1. 下载 Tentative Auction Schedule PDF
2. 用 pdfplumber 解析文本
3. 提取目标月份的拍卖条目
4. 返回按日期排序的计划表（证券类型、公告日、拍卖日、结算日）

### 示例8：查询某月实际拍卖结果（含投标倍数）

**用户请求**："查5月实际拍卖结果，特别是投标倍数" / "5月国债拍卖的 bid-to-cover"

**执行步骤**：
1. 确认查询月份（如 2026-05）
2. 运行批量抓取脚本：
   ```bash
   python scripts/scrape_month_auctions.py --year 2026 --month 5 --output ./output
   ```
3. 脚本自动遍历每个工作日，尝试 `R_YYYYMMDD_N.xml`，解析所有命中
4. 输出 CSV（含投标倍数、投标人分类、中标利率等）

### 示例9：对比计划 vs 实际

**用户请求**："5月拍卖计划跟实际结果有偏差吗？" / "对比Tentative Schedule和实际拍卖"

**执行步骤**：
1. 解析 Tentative PDF → 计划表
2. 批量抓取 XML → 实际结果表
3. 按证券类型 + 日期对齐
4. 输出差异表（标注：✅按计划 / 🟡日期挪移 / 🆕计划外CMB）

### 示例10：查询近期（未来几天）拍卖安排

**用户请求**："最近几天有什么国债拍卖？" / "未来一周的拍卖安排"

**执行步骤**：
1. 获取 `https://www.treasurydirect.gov/xml/PendingAuctions.xml`
2. 解析 XML 列出已公告但尚未拍卖的条目
3. 或访问 `https://www.treasurydirect.gov/auctions/upcoming/`

**用户请求**："TIC数据" / "外国持有美债最新情况" / "美债持有国排名"

**执行步骤**：
1. 确认数据源：TIC Table 5（非 API，文本文件下载）
2. 运行脚本：`python scripts/query_tic_data.py --output ./output`
3. 脚本自动下载、解析、保存 CSV
4. 返回排名和汇总数据

**返回结果示例**：
- 总计：$9,348.7B
- Top3：日本 $1,191.6B、英国 $926.9B、中国 $652.3B

---

## 九、注意事项

1. **数据更新频率**：DTS数据每日更新（最新数据通常有1-2天延迟）；**MSPD数据每月更新**（每月第四个工作日发布，数据反映上月末情况）；**拍卖结果 XML** 拍卖当日发布（拍卖结束后几分钟内）；**Upcoming Auctions** 每周五更新；**Tentative Schedule** 每季 Refunding 时发布
2. **金额单位**：DTS/MSPD 金额字段单位为**百万美元**（如 `825550` = 8255.50亿美元）；Debt to the Penny 为**美元精确值**；拍卖 XML 金额为**原始美元值**
3. **财年定义**：美国联邦财年从每年10月1日开始，至次年9月30日结束
4. **API限制**：单次请求最多返回10000条记录，超过需分页获取
5. **数据完整性**：历史数据可能不完整，建议先查看 `total-count` 确认数据量
6. **"国债"口径**：用户说"国债"时，默认指**全部可流通国债（Marketable = Bills + Notes + Bonds + TIPS + FRNs）**，除非用户明确指定只看某一类（如"短期国债"/"T-Bills"）；**不要把"国债发行量"等同于"Bills发行量"**，这是常见错误，会严重低估
7. **MSPD vs DTS**：查存量余额按证券类型分类 → 用 MSPD `mspd_summary`；查每日发行/偿还流量 → 用 DTS `public_debt_transactions`
8. **TIC 数据源**：TIC 是**纯文本文件**（tab分隔），**不是 REST API**——不能用 `query_treasury_data.py`，必须用 `query_tic_data.py`。数据滞后约 2 个月
9. **Debt to the Penny 金额单位**：金额为**美元**（精确到分），不是百万美元——图表展示时需除以 1e12（转万亿）

---

## 十、踩坑经验（深度积累）

> 以下经验来自实际调用中的反复踩坑，每次更新技能后务必同步到此节。

### 坑1：`transaction_catg` 为 `null` 是 Total 汇总行，不是独立分类

**现象**：`deposits_withdrawals_operating_cash` 表中大量行的 `transaction_catg` 为 `null`，初看以为是"无分类"，实际上是**当日汇总行**（Total）。

**验证方法**：检查这些行的 `account_type` 字段，通常包含 `"Total"` 字样，如 `"Total Treasury General Account (TGA)"`。

**正确做法**：
- 计算每日收支明细时，**必须排除 `transaction_catg` 为 `null`（或空字符串）的行**
- 汇总行已包含在分类明细的 MTD differential 合计中，不排除会导致 **double-counting**

```python
# ✅ 正确：只保留有 transaction_catg 的明细行
detail = [r for r in data if r.get('transaction_catg') and r.get('transaction_catg') != '']

# ❌ 错误：包含 null 行，导致汇总值翻倍
detail = [r for r in data if r.get('tran_type_desc') == 'Deposits']
```

**适用于**：`Deposits` 和 `Withdrawals` 两个 `tran_type_desc` 均存在此问题。

---

### 坑2：`transaction_today_amt` 字段全为 null，必须用 MTD differential 计算每日金额

**现象**：API 返回的 `transaction_today_amt` 字段**全部为 null**（至少2026年至今的数据如此），无法直接使用。

**根本原因**：财政部 DTS 报告中，`transaction_today_amt` 某些时期不填充，依赖使用者通过 MTD 累计值差分计算。

**正确做法**：用 `transaction_mtd_amt`（Month-To-Date 累计值）做差分：

```python
# 对每个 account_type + transaction_catg 组合，按日期排序后差分
prev_mtd = {}  # key: catg, value: 前一日 MTD 值

for date in sorted(dates):
    for mtd_val, catg in daily_data[date][acct]:
        if catg in prev_mtd:
            daily_amt = mtd_val - prev_mtd[catg]  # 差分 = 当日MTD - 前日MTD
            if daily_amt > 0:
                result[date][catg] += daily_amt
        prev_mtd[catg] = mtd_val
```

**注意**：
- 只在 `daily_amt > 0` 时记录（避免月末清零导致的负值）
- 月初第一条记录无前日MTD，自动跳过（正确行为）

---

### 坑3：Public Debt Cash Issues / Redemp. 是国债发行/偿还，需单独拎出来

**背景**：`deposits_withdrawals_operating_cash` 表中存在以下关键分类：

| `transaction_catg` 值 | 含义 | 对TGA的影响 |
|---|---|---|
| `Public Debt Cash Issues (Table IIIB)` | 国债发行收入（现金制） | TGA 现金**流入** (+) |
| `Public Debt Cash Redemp. (Table IIIB)` | 国债偿还支出（现金制） | TGA 现金**流出** (-) |

**用户意图识别**：
- 用户说"国债发行收入" → 查 `Public Debt Cash Issues`
- 用户说"国债偿还" → 查 `Public Debt Cash Redemp.`
- 用户说"国债对TGA的影响" → 两个都查，计算净额

**分析建议**：这两项是**现金制**（Table III-B），直接反映对TGA账户的实际现金影响，比应计制（Table III-A）更贴近现金流分析。

---

### 坑4：金额单位是百万美元，图表展示需转十亿

**现象**：CSV 中的原始值如 `247798` 实际表示 **247,798 百万美元 = 247.8 十亿美元**。

**正确做法**：生成图表时统一除以 1000：

```python
# CSV 值单位是百万美元
mtd_val = float(r.get('transaction_mtd_amt'))  # 如 247798 = 247,798 百万美元

# 转十亿：除以 1000
amt_billions = mtd_val / 1000  # → 247.8 十亿美元
```

**图表标注**：务必在图表标题/副标题/坐标轴注明单位：
- ✅ `"支出（十亿美元）"`
- ❌ `"支出（百万美元）"`（会让读者误以为数值是百万级别）

---

### 坑5：MTD differential 计算时需排除 Total 行，否则汇总值翻倍

**现象**：如果不排除 `account_type` 含 `"Total"` 的行，MTD differential 会把明细行和 Total 行**各计算一次**，导致最终汇总值约为正确值的 **2倍**。

**验证方法**：计算完之后，用 API 直接查 `transaction_mtd_amt` 的 Total 行最大值，与计算结果比对，应该吻合。

```python
# 排除 Total 行（通过 account_type 判断）
if 'Total' in str(r.get('account_type', '')):
    continue  # 跳过汇总行
```

**经验**：`transaction_catg` 为 null 的行，其 `account_type` 通常包含 `"Total"`，两个判断可以同时使用，双重保险。

---

### 坑6：Python 生成 HTML/JS 时，f-string 与 JS 模板字符串冲突

**现象**：在 Python 中用 f-string 生成包含 JS 模板字符串（`` ${x} ``) 的 HTML 时，Python 会把 `` ${...} `` 误认为是 f-string 的格式化语法，导致语法错误或输出异常。

**错误示例**：
```python
# ❌ 错误：Python 会把 ${val.toFixed(2)} 当作 f-string 格式化
html = f"""
<script>
    const label = ctx.dataset.label + ': $' + ${val.toFixed(2)} + 'B';
</script>
"""
```

**正确做法**：使用 `%%PLACEHOLDER%%` 模式，先在 Python 中放占位符，最后统一替换：

```python
# ✅ 正确：用占位符，避免 JS/Python 语法冲突
html_template = """
<script>
    const label = ctx.dataset.label + ': $' + %%FORMATTER%% + 'B';
</script>
"""

# 在所有 Python f-string 处理完成后，最后替换占位符
html = html_template.replace('%%FORMATTER%%', '${val.toFixed(2)}')
```

**常用占位符**：
- `%%DATES%%` → JS 数组（日期列表）
- `%%DATASETS%%` → JS 对象数组（Chart.js datasets）
- `%%FORMATTER%%` → JS 模板字符串 `${...}`

---

### 坑7：CSV 文件编码用 `utf-8-sig`（BOM），否则 Excel 中文乱码

**现象**：用 `utf-8` 编码写 CSV，在 Windows 中文版 Excel 中打开时中文表头乱码。

**原因**：Excel 在 Windows 中文 locale 下默认用 GBK 解码 CSV，不加 BOM 无法自动识别 UTF-8。

**正确做法**：
```python
# ✅ 正确：utf-8-sig 会在文件头写入 BOM，Excel 可自动识别
with open(filepath, 'w', newline='', encoding='utf-8-sig') as f:
    writer = csv.writer(f)
    writer.writerow(['记录日期', '账户类型', ...])
```

---

### 坑8：Deposits 和 Withdrawals 的数据结构完全对称

**重要规律**：`deposits_withdrawals_operating_cash` 表中，`Deposits`（收入）和 `Withdrawals`（支出）的处理逻辑**完全对称**：

| 维度 | Deposits（收入） | Withdrawals（支出） |
|---|---|---|
| `tran_type_desc` 值 | `Deposits` | `Withdrawals` |
| NULL 行含义 | 收入汇总（Total） | 支出汇总（Total） |
| 需排除的 NULL 行 | ✅ 是 | ✅ 是 |
| 单独拎出的关键分类 | `Public Debt Cash Issues (Table IIIB)` | `Public Debt Cash Redemp. (Table IIIB)` |
| MTD differential | ✅ 需要（今日收入 = 今日MTD - 昨日MTD） | ✅ 需要（今日支出 = 今日MTD - 昨日MTD） |
| 单位 | 百万美元 | 百万美元 |

**分析模板**：写好 Deposits 的分析脚本后，Withdrawals 只需改 `tran_type_desc` 过滤值和分类名称，其余逻辑完全复用。

---

## 十一、参考资料

### FiscalData API
- **API文档**: https://fiscaldata.treasury.gov/api-documentation/
- **数据字典**: https://fiscaldata.treasury.gov/datasets/daily-treasury-statement/
- **DTS数据集主页**: https://fiscaldata.treasury.gov/datasets/daily-treasury-statement/
- **API基础路径**: https://api.fiscaldata.treasury.gov/services/api/fiscal_service

### TreasuryDirect 拍卖数据
- **Tentative Auction Schedule (PDF)**: https://home.treasury.gov/system/files/221/Tentative-Auction-Schedule.pdf
- **拍卖结果 XML 模板**: `https://treasurydirect.gov/xml/R_YYYYMMDD_N.xml`
- **近期拍卖 XML**: https://www.treasurydirect.gov/xml/PendingAuctions.xml
- **Upcoming Auctions (网页)**: https://www.treasurydirect.gov/auctions/upcoming/
- **拍卖节奏规则**: https://www.treasurydirect.gov/auctions/when-auctions-happen/
- **历史公告与结果**: https://www.treasurydirect.gov/auctions/announcements-data-results/announcement-results-press-releases/previous-announcements-and-results/
- **Auction Query (按CUSIP)**: https://www.treasurydirect.gov/auctions/auction-query/
- **季度 Refunding 公告**: https://home.treasury.gov/policy-issues/financing-the-government/quarterly-refunding/

## 踩坑经验

（以下由 AI 在实际调用中自动积累，请勿手动删除）

- `public_debt_transactions` 表 / `transaction_type` 过滤值：正确值是 `Issues` 和 `Redemptions`（都有尾随 s），不是 `Issue` 或 `Redemption`。这个错误会导致过滤不到数据，API 不会报错但返回空结果。
- `adjustment_public_debt_transactions_cash_basis` 表 / API 端点名称：端点是 `adjustment_public_debt_transactions_cash_basis`（下划线），不是 `adjustment-public-debt-transactions-cash-basis`（ hyphen）。API 路径中的表名用下划线分隔。
- `federal_tax_deposits` 表 / 数据更新状态：数据只更新到 2023-02-13，之后无数据。查询时需先确认时间范围，避免拿到空结果。替代方案是用 `deposits_withdrawals_operating_cash` 表查 `transaction_catg` 包含 "Tax" 的记录。
- **MSPD 数据表** / 端点路径：MSPD 的 API 端点是 `/v1/debt/mspd/mspd_table_1`，前缀为 `/v1/debt/mspd/`，**不在 DTS 的 `/v1/accounting/dts/` 路径下**。这是区别于 DTS 9张表的关键点。MSPD 数据集页面上的 API Quick Guide 表格是 JavaScript 动态加载的，WebFetch 无法获取——需要用浏览器自动化（agent-browser）打开页面，点击 "Show More" 按钮展开才能看到端点信息。MSPD 提供按 `security_type_desc` + `security_class_desc` 两级分类的**存量余额**（Debt Held by the Public + Intragovernmental），是 DTS 9张表中唯一能按证券类型查余额的数据源。
- **TIC 数据**：TIC（Treasury International Capital，外国持有美债数据）**不在** FiscalData API 中，独立于 ticdata.treasury.gov 发布，仅提供 CSV/PDF 下载，无 REST API。
- **TIC 数据格式**：`slt_table5.txt` 是 Tab 分隔的文本文件，共 42 行，表头在第 7 行（`Country\t2026-03\t...`），数据行 21 个国家 + All Other + Grand Total + 3 行 Foreign Official 细分。数据包含最近 13 个月，月份从新到旧排列。解析时需注意：①最后一个月后面有 `\r` 需 strip；②"All Other" 是汇总项，不应参与排名；③金额单位是十亿美元（Billion USD），不是百万美元。
- **Debt to the Penny** / 金额单位：与 DTS/MSPD 的百万美元不同，Debt to the Penny 返回的是**美元精确值**（如 `39163302863182.10` = $39.16T）。分析时需除以 1e12 转万亿，图表标注单位应为"万亿/十亿美元"而非"百万美元"。
- **Tentative Auction Schedule PDF** / 解析方式：PDF 含 `FlateDecode` 压缩流，**WebFetch 无法读取文本**，必须用本地 Python + pdfplumber 解析。直接用 pdfplumber 的 `extract_text()` 即可提取纯文本——格式为 `Security Type Announcement Date Auction Date Settlement Date`，每行一条。假日行以 `Holiday -` 开头。后缀 `R`=Reopening, `T`=TIPS。
- **TreasuryDirect XML** / URL 规律：XML URL 为 `treasurydirect.gov/xml/R_YYYYMMDD_N.xml`，`_N` 是当天发布序号（1~8），**不编码证券类型**。`_1` 可能是 Bill 也可能是 Note，需读取 `<SecurityType>` 判断。比 PDF 更优：公告和结果合一、直接 parse、含 BidToCoverRatio。
- **Previous Announcements 页面** / JS 多标签限制：`previous-announcements-and-results/` 页面用 JavaScript 分标签（Bills / Notes / Bonds / TIPS / FRNs），WebFetch 只抓取初始 HTML 的 Bills 标签。要获取所有证券类型的结果 → 需用 Agent Browser 打开页面并切标签。
- **Upcoming Auctions XML** / 限制：`PendingAuctions.xml` 每周五更新，仅含已公告拍卖的基本字段（SecurityType、CUSIP、日期、规模），**不含 bid-to-cover 等结果数据**（还没拍）。
- **网络连接** / TreasuryDirect 偶发 Reset：批量抓取时偶发 `WinError 10054`（远程主机关闭连接），需加重试机制。请求间隔建议 0.15~0.3 秒。
- **Tentative Schedule 发布节奏** / 规律：Q1(2月初)/Q2(5月初)/Q3(8月初)/Q4(11月初)，覆盖未来约6个月。PDF 文件名 `TentativeAuctionScheduleQ<X><Year>.pdf`，但主页 URL 总是 `Tentative-Auction-Schedule.pdf` 指向最新版。

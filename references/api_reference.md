# US Treasury API Reference

美国财政部财政数据 API 详细参考文档。

---

## Base Information

- **Base URL**: `https://api.fiscaldata.treasury.gov/services/api/fiscal_service`
- **Authentication**: None (fully open)
- **Method**: GET only
- **Response Formats**: JSON (default), CSV, XML
- **API Docs**: https://fiscaldata.treasury.gov/api-documentation/
- **Data Dictionary**: https://fiscaldata.treasury.gov/datasets/daily-treasury-statement/

---

## Daily Treasury Statement (DTS) Tables

The DTS dataset contains 9 data tables. All endpoints under `/v1/accounting/dts/`.

### Table I: Operating Cash Balance

**Endpoint**: `/v1/accounting/dts/operating_cash_balance`

**Description**: Daily Treasury General Account (TGA) closing balances and opening balances.

**Key Fields**:
- `record_date` - Record date (YYYY-MM-DD)
- `account_type` - Account type (TGA Opening/Closing Balance, Total TGA Deposits, Total TGA Withdrawals)
- `close_today_bal` - Closing balance today (millions USD)
- `open_today_bal` - Opening balance today (millions USD)
- `open_month_bal` - Opening balance this month (millions USD)
- `open_fiscal_year_bal` - Opening balance this fiscal year (millions USD)

**Sample Query**:
```
GET /v1/accounting/dts/operating_cash_balance?filter=record_date:eq:2026-05-22&sort=-record_date&page[size]=100
```

---

### Table II: Deposits and Withdrawals of Operating Cash

**Endpoint**: `/v1/accounting/dts/deposits_withdrawals_operating_cash`

**Description**: Daily deposits to and withrawals from the Treasury General Account.

**Key Fields**:
- `record_date` - Record date
- `account_type` - Account type
- `transaction_type` - Transaction type (Deposits/Withdrawals)
- `transaction_catg` - Transaction category code
- `transaction_catg_desc` - Transaction category description
- `transaction_today_amt` - Today's transaction amount (millions USD)
- `transaction_mtd_amt` - Month-to-date transaction amount (millions USD)
- `transaction_fytd_amt` - Fiscal year-to-date transaction amount (millions USD)

**Sample Query**:
```
GET /v1/accounting/dts/deposits_withdrawals_operating_cash?filter=record_date:gte:2026-01-01&sort=-record_date&page[size]=1000
```

---

### Table III-A: Public Debt Transactions

**Endpoint**: `/v1/accounting/dts/public_debt_transactions`

**Description**: Daily public debt cash inflows and outflows.

**Key Fields**:
- `record_date` - Record date
- `transaction_type` - Transaction type (Issuance/Redemption)
- `security_market` - Security market (Bills/Notes/Bonds/FRNs/etc.)
- `security_type` - Security type code
- `security_type_desc` - Security type description
- `transaction_today_amt` - Today's transaction amount (millions USD)
- `transaction_mtd_amt` - Month-to-date amount (millions USD)
- `transaction_fytd_amt` - Fiscal year-to-date amount (millions USD)

---

### Table III-B: Adjustment of Public Debt Transactions to Cash Basis

**Endpoint**: `/v1/accounting/dts/adjustment_public_debt_transactions_cash_basis`

**Description**: Adjustments to convert public debt transactions from accrual to cash basis.

**Key Fields**:
- `record_date` - Record date
- `transaction_type` - Transaction type
- `adj_type` - Adjustment type code
- `adj_type_desc` - Adjustment type description
- `adj_today_amt` - Today's adjustment amount (millions USD)
- `adj_mtd_amt` - Month-to-date adjustment (millions USD)
- `adj_fytd_amt` - Fiscal year-to-date adjustment (millions USD)

---

### Debt Subject to Limit

**Endpoint**: `/v1/accounting/dts/debt_subject_to_limit`

**Description**: Debt subject to the statutory debt limit.

**Key Fields**:
- `record_date` - Record date
- `debt_catg` - Debt category (Public/Intragovernmental)
- `debt_catg_desc` - Debt category description
- `close_today_bal` - Closing balance today (millions USD)
- `open_today_bal` - Opening balance today (millions USD)

---

### Inter-Agency Tax Transfers

**Endpoint**: `/v1/accounting/dts/inter_agency_tax_transfers`

**Description**: Tax transfers between Treasury and federal agencies.

**Key Fields**:
- `record_date` - Record date
- `transaction_type` - Transaction type
- `agency_name` - Agency name
- `transfer_today_amt` - Today's transfer amount (millions USD)
- `transfer_mtd_amt` - Month-to-date transfer (millions USD)
- `transfer_fytd_amt` - Fiscal year-to-date transfer (millions USD)

---

### Income Tax Refunds Issued

**Endpoint**: `/v1/accounting/dts/income_tax_refunds_issued`

**Description**: Daily income tax refunds issued.

**Key Fields**:
- `record_date` - Record date
- `refund_type` - Refund type
- `refund_today_amt` - Today's refund amount (millions USD)
- `refund_mtd_amt` - Month-to-date refund (millions USD)
- `refund_fytd_amt` - Fiscal year-to-date refund (millions USD)

---

### Federal Tax Deposits

**Endpoint**: `/v1/accounting/dts/federal_tax_deposits`

**Description**: Daily federal tax deposits received.

**Key Fields**:
- `record_date` - Record date
- `tax_deposit_type` - Tax deposit type
- `tax_deposit_type_desc` - Tax deposit type description
- `tax_deposit_today_amt` - Today's tax deposit (millions USD)
- `tax_deposit_mtd_amt` - Month-to-date tax deposit (millions USD)
- `tax_deposit_fytd_amt` - Fiscal year-to-date tax deposit (millions USD)

---

### Short-Term Cash Investments

**Endpoint**: `/v1/accounting/dts/short_term_cash_investments`

**Description**: Treasury's short-term cash investment positions.

**Key Fields**:
- `record_date` - Record date
- `investment_type` - Investment type
- `investment_desc` - Investment description
- `par_amount` - Par amount (millions USD)
- `accrued_interest` - Accrued interest (millions USD)

---

## Query Parameters

### Pagination

| Parameter | Description | Default | Max |
|-----------|-------------|---------|-----|
| `page[number]` | Page number (1-based) | 1 | - |
| `page[size]` | Records per page | 100 | 10000 |

### Filtering

Use `filter=` parameter with operator syntax:

```
filter=field_name:operator:value[,field_name:operator:value]...
```

**Operators**:

| Operator | Meaning | Example |
|----------|---------|---------|
| `eq` | Equal | `record_date:eq:2026-05-22` |
| `neq` | Not equal | `account_type:neq:Depositary` |
| `gt` | Greater than | `close_today_bal:gt:1000000` |
| `gte` | Greater than or equal | `record_date:gte:2025-01-01` |
| `lt` | Less than | `transaction_today_amt:lt:5000` |
| `lte` | Less than or equal | `record_calendar_month:lte:6` |
| `in` | In list | `record_fiscal_year:in:(2024,2025,2026)` |

**Multiple conditions** are AND-ed together:
```
filter=record_fiscal_year:eq:2026,account_type:eq:Treasury General Account (TGA) Closing Balance
```

### Sorting

Use `sort=` parameter:

| Value | Meaning |
|-------|---------|
| `record_date` | Ascending by record_date |
| `-record_date` | Descending by record_date |
| `close_today_bal` | Ascending by balance |
| `-close_today_bal` | Descending by balance |

### Field Selection

Use `fields=` to limit returned fields (reduces response size):

```
fields=record_date,account_type,close_today_bal,open_today_bal
```

### Format

Use `format=` to change response format:

| Value | Format |
|-------|--------|
| (omitted) | JSON (default) |
| `csv` | CSV |
| `xml` | XML |

---

## Response Structure (JSON)

```json
{
  "data": [
    {
      "record_date": "2026-05-22",
      "account_type": "Treasury General Account (TGA) Closing Balance",
      "close_today_bal": "825550",
      ...
    }
  ],
  "meta": {
    "count": 100,
    "total-count": 16298,
    "offset": 0
  },
  "links": {
    "self": "https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v1/accounting/dts/operating_cash_balance?...",
    "next": "https://...",
    "last": "https://..."
  }
}
```

- `data` - Array of record objects
- `meta["total-count"]` - Total available records (use for pagination planning)
- `meta["count"]` - Records in this response
- `links["next"]` - URL for next page (null if last page)

---

## Data Notes

1. **Amounts**: All amount fields are in **millions of USD**. Example: `825550` = $825.55 billion.
2. **Dates**: All dates are in `YYYY-MM-DD` format.
3. **Fiscal Year**: US federal fiscal year starts Oct 1 and ends Sep 30. FY2026 = Oct 1, 2025 - Sep 30, 2026.
4. **Update Frequency**: DTS data is updated daily, typically with 1-2 day lag.
5. **Null Values**: Missing data is represented as `null` or empty string.

---

## Error Handling

| HTTP Status | Meaning | Solution |
|--------------|---------|----------|
| 400 | Bad request (invalid filter syntax) | Check filter format |
| 404 | Endpoint not found | Verify endpoint path |
| 500 | Server error | Retry later |
| SSL Error | Certificate verification failed | Disable SSL verification (see SKILL.md) |

---

## Rate Limiting

The API does not publish rate limits. Best practices:
- Use `page[size]=10000` to minimize requests
- Add delays between requests if downloading large datasets
- Use `fields=` to reduce response size

---

## Useful Links

- **API Documentation**: https://fiscaldata.treasury.gov/api-documentation/
- **DTS Dataset Page**: https://fiscaldata.treasury.gov/datasets/daily-treasury-statement/
- **Data Dictionary (DTS)**: https://fiscaldata.treasury.gov/datasets/daily-treasury-statement/deposits-and-withdrawals-of-operating-cash
- **API Base URL**: https://api.fiscaldata.treasury.gov/services/api/fiscal_service

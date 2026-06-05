# Industrial Supply Chain — Automated ETL Pipeline & Analytics Dashboard

> An enterprise-grade Python ETL framework that ingests, cleans, validates, and structures 180,519 rows of global manufacturing logistics data into a relational Star Schema database — feeding a Power BI operational dashboard for delivery performance and carrier risk analysis.

---

## The Problem

In global manufacturing logistics, raw shipping data arrives from multiple sources — freight forwarders, warehouse stock trackers, and order management systems — in inconsistent, messy formats. Pushing this data directly into a dashboard or analytical model produces inaccurate KPIs, breaks reports, and in a factory context, can trigger expensive planning errors.

This project builds an **automated ETL+V pipeline** (Extract, Transform, Validate, Load) that acts as a data quality layer between raw logistics files and the Power BI reporting layer — handling dirty data automatically, quarantining anomalies, and outputting a clean relational database ready for operational analysis.

---

## Dataset

**DataCo Global Supply Chain Dataset**
- **180,519 order transactions** across global shipping operations
- **53 raw columns** covering orders, customers, products, geography, shipment timelines, and delivery performance
- Multi-language source data (Spanish country/region names require translation)
- Known data quality issues: missing zip codes, duplicate columns, mismatched region naming conventions, PII fields requiring removal

---

## System Architecture — ETL+V Pipeline

```
[ Raw CSV Drop Zone: data/raw/ ]
           │
           ▼
    ┌─ 1. EXTRACT ─────────────────────────────────┐
    │  • Scans landing directory for new CSV files  │
    │  • Loads with latin-1 encoding (multilingual) │
    │  • Logs row count and column structure        │
    └──────────────────────────────────────────────┘
           │
           ▼
    ┌─ 2. TRANSFORM ───────────────────────────────┐
    │  • Date standardisation (str → datetime)      │
    │  • PII field removal (email, password, street)│
    │  • Categorical uniformity (160+ country       │
    │    Spanish→English translation map)           │
    │  • Region name normalisation                  │
    │    ("South of USA" → "South US", etc.)        │
    │  • Composite Geography_Key synthesis          │
    │    (sequential surrogate key on unique        │
    │     Market + Region + Country combos)         │
    │  • Lead_Time_Deviation engineered feature     │
    │    (actual days − scheduled days)             │
    │  • Duplicate column removal                   │
    └──────────────────────────────────────────────┘
           │
           ▼
    ┌─ 3. VALIDATE & QUARANTINE ───────────────────┐
    │  • Anomaly detection (zip codes stored as     │
    │    state identifiers, null location fields)   │
    │  • Known bad rows → data/quarantine/          │
    │    (isolated without disrupting runtime)      │
    │  • Clean rows pass through                    │
    └──────────────────────────────────────────────┘
           │
           ▼
    ┌─ 4. LOAD — Star Schema ──────────────────────┐
    │  Dimension tables:                            │
    │    Dim_Geography (Geography_Key FK)           │
    │    Dim_Customer (PII-masked)                  │
    │    Dim_Product                                │
    │    Dim_Product_Category                       │
    │    Dim_Product_Department                     │
    │  Fact tables:                                 │
    │    Fact_Order_Header (logistics & delivery)   │
    │    Fact_Order_LineItem (financial & margin)   │
    │                                               │
    │  Output: SQLite DB + CSV exports for Power BI │
    └──────────────────────────────────────────────┘
           │
           ▼
    ┌─ 5. ARCHIVE ─────────────────────────────────┐
    │  • Processed raw file moved to data/archive/ │
    │  • Idempotent lifecycle — no double-processing│
    └──────────────────────────────────────────────┘
```

---

## Key Engineering Decisions

### 1. Config-Driven Schema (Minimal Hardcoding)
All schema definitions, directory paths, column mappings, and date/string cleaning rules are externalised to `config/settings.json`. The Python execution logic contains no hardcoded column names or file paths — meaning the pipeline adapts to schema changes without modifying `pipeline.py`:

```json
{
  "order_header_cols": ["Order Id", "Geography_Key", "Shipping Mode",
                        "Days for shipping (real)", "Lead_Time_Deviation", ...],
  "cleaning_rules": {
    "region_mapping": { "South of USA": "South US", "West of USA": "West US" }
  }
}
```

> Note: The 160+ country Spanish→English translation map is defined in `src/utils.py` rather than the config file, as embedding a full translation dictionary in JSON is impractical at that scale.

### 2. Composite Geography Key Synthesis
Rather than joining on inconsistent free-text location strings (which fail on whitespace variants and translations), the pipeline generates a surrogate `Geography_Key` from the unique set of `Market + Order Region + Order Country + Order State + Order City` combinations. This creates a stable FK anchor for the geography dimension — the same approach used in production data warehouses to handle multi-source location data.

### 3. Quarantine-Not-Crash Validation
Instead of halting on bad data, the pipeline isolates known anomalies into a decoupled quarantine zone — logging them for manual review without interrupting the main processing run. This is the correct pattern for production pipelines where data quality is imperfect but the run must complete.

### 4. Fact Table Splitting by Analytical Purpose
Rather than one monolithic fact table, execution metrics are split into two targeted tables by analytical granularity:
- **`Fact_Order_Header`** — one row per order: delivery timelines, shipping mode, late delivery risk, lead time deviation → for **logistics and operational efficiency analysis**
- **`Fact_Order_LineItem`** — one row per line item: quantities, prices, discounts, margin → for **financial and profitability analysis**

This prevents row-bloat calculations and avoids many-to-many relationship traps when connecting to the Power BI model.

---

## Exploratory Data Analysis Findings

EDA conducted on the raw 180,519-row dataset (`notebooks/Exploratory Data Analysis.ipynb`):

- Identified **duplicate columns** (`Benefit per order` = `Order Profit Per Order`) → dropped
- Identified **dead columns** (`Product Status` — single value of 0 across all 180,519 rows) → dropped
- Identified **PII fields** requiring removal (Customer Email, Password, Street) → quarantined
- Identified **duplicate relationship columns** (`Customer Id` = `Order Customer Id`, `Product Card Id` = `Order Item Cardprod Id`) → redundant copies dropped
- Discovered **3 records where zip codes were stored as state identifiers** (zip codes `95758` and `91732` found in the `Customer State` field) → state corrected to `CA`, zip restored, city set to `Unknown`, rows quarantined
- Engineered **`Lead_Time_Deviation`** feature: `Days for shipping (real) − Days for shipment (scheduled)` → key metric for delivery performance analysis
- Confirmed **`Late_delivery_risk` flag aligns with `Lead_Time_Deviation > 0`** via cross-tabulation (all risk=1 rows have positive deviation; `Shipping canceled` orders with positive deviation are correctly excluded from the flag)
- Confirmed **86.2% of `Order Zipcode` values are null** — column dropped from fact table

---

## Power BI Dashboard Layer

With the pipeline output stable, the `Fact_Order_Header` table (logistics-focused) is loaded into Power BI for operational analysis. Dashboard KPIs focus on:

- **On-Time Delivery Rate** by shipping mode and market
- **Late Delivery Risk Distribution** by region and carrier
- **Lead Time Deviation Trend** — actual vs. scheduled shipping days over time
- **Order Volume by Market** — geographic distribution of fulfilment operations

Dashboard screenshots are available in `Screenshots/`.

---

## Technical Stack

| Layer | Tools |
|---|---|
| ETL Orchestration | Python 3 (`pipeline.py`) |
| Data Transformation | Pandas (type enforcement, reshaping, feature engineering) |
| Database Layer | SQLite3 (star schema population) |
| Configuration Engine | JSON (`settings.json`) |
| Logging | Python `logging` module (structured pipeline audit trail) |
| EDA | Jupyter Notebook, Matplotlib, Seaborn |
| Visualisation | Power BI Desktop (`Dashboard.pbix`) |
| Dataset | DataCo Global Supply Chain Dataset (180,519 rows × 53 columns) |

---

## Repository Structure

```
supply-chain-analytics-dashboard/
│
├── config/
│   └── settings.json                  # Central config: paths, schemas, cleaning rules
│
├── src/
│   ├── pipeline.py                    # ETL lifecycle orchestrator
│   └── utils.py                       # Transform functions, validation, DB loader,
│                                      #   country/region translation maps
│
├── notebooks/
│   └── Exploratory Data Analysis.ipynb  # EDA: profiling, cleaning decisions, feature engineering
│
├── data/
│   ├── raw/                           # Drop zone for incoming CSV files
│   ├── processed/
│   │   └── SupplyChainOps.db          # Output SQLite database (star schema)
│   ├── archive/                       # Processed source files (idempotent safeguard)
│   └── quarantine/                    # Isolated anomalous rows for review
│
├── Screenshots/                       # Power BI dashboard page exports (4 pages)
├── Dashboard.pbix                     # Power BI report (connects to Fact_Order_Header)
└── requirements.txt
```

---

## Manufacturing Relevance (Industrie 4.0)

This project mirrors the data architecture and operational logic used in **Manufacturing Execution Systems (MES)** and **Supply Chain Management (SCM)** in global manufacturing:

| Pipeline Component | Industrial Equivalent |
|---|---|
| Config-driven schema | MES data model configuration (no hardcoded table structures) |
| ETL + quarantine pattern | Production data integration middleware |
| Star schema output | Data warehouse layer feeding factory BI dashboards |
| Lead Time Deviation feature | OTD (On-Time Delivery) KPI — standard in automotive SCM |
| Late delivery risk flag | Supplier risk scoring in procurement analytics |
| SQLite DB output | Structured data layer for Power BI / Tableau direct query |

---

## Setup & Execution

```bash
git clone https://github.com/YashBarhanpurkar/supply-chain-analytics-dashboard.git
cd supply-chain-analytics-dashboard
pip install -r requirements.txt

# Drop your raw CSV into data/raw/
# Then run from the project root:
python -m src.pipeline

# Outputs:
#  → data/processed/SupplyChainOps.db  (SQLite star schema)
#  → data/quarantine/                  (flagged anomalies)
#  → data/archive/                     (processed source file)
```

---

## Author

**Yash Barhanpurkar**
M.Sc. Global Production Engineering — Technische Universität Berlin
[LinkedIn](https://www.linkedin.com/in/yash-barhanpurkar/) · [GitHub](https://github.com/YashBarhanpurkar)

---

*Topics: `etl-pipeline` `supply-chain` `sqlite` `python` `pandas` `data-engineering` `star-schema` `manufacturing` `power-bi` `logistics-analytics` `industry-4-0`*

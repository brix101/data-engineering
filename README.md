# 🏗️ Data Engineering Practice Project

**E-commerce Data Platform** — a hands-on journey from raw data generation to distributed processing.

## Progress

`1 / 12 phases complete`

---

## Architecture

```text
                    DATA GENERATOR
                         │
                         ▼
                  ┌──────────────┐
                  │ Raw Dataset  │
                  └──────┬───────┘
                         │
                         ▼
                  ┌──────────────┐
                  │  Ingestion   │
                  └──────┬───────┘
                         │
                         ▼
                    ┌─────────┐
                    │  S3 /   │
                    │ MinIO   │
                    └────┬────┘
                         │
                         ▼
                  ┌──────────────┐
                  │   Parquet    │
                  └──────┬───────┘
                         │
                         ▼
                  ┌──────────────┐
                  │  Transform   │
                  │  DuckDB/SQL  │
                  └──────┬───────┘
                         │
                         ▼
                  ┌──────────────┐
                  │    Data      │
                  │  Warehouse   │
                  └──────┬───────┘
                         │
                         ▼
                  ┌──────────────┐
                  │ Data Quality │
                  └──────┬───────┘
                         │
                         ▼
                    ORCHESTRATION
                      (Airflow)
```

---

## Roadmap

### Phase 1 — Data Generation ✅

**Goal:** Generate realistic transactional data.

_You've already done this._

**Checklist**

- [x] Generate customers
- [x] Generate products
- [x] Generate orders
- [x] Generate order items
- [x] Generate payments
- [x] Generate shipments
- [x] Generate returns
- [x] Create relationships between entities
- [x] Generate realistic IDs
- [x] Generate realistic timestamps
- [x] Make payment amounts based on actual order totals
- [x] Add intentionally bad data for later data-quality testing

**Definition of done**

You should be able to run something like:

```bash
python -m generator.main
```

and get a complete dataset.

---

### Phase 2 — Data Ingestion ⭐ NEXT

**Goal:** Build your first proper pipeline.

Instead of manually moving files around, create a Python application that ingests the generated data.

**Tasks**

- [ ] Design your project directory structure
- [ ] Create an ingestion Python package
- [ ] Read raw CSV/JSON files
- [ ] Validate that expected files exist
- [ ] Validate basic schemas
- [ ] Add `ingested_at`
- [ ] Add ingestion logging
- [ ] Handle missing/corrupted files
- [ ] Write ingested data to a destination directory
- [ ] Make the ingestion process repeatable
- [ ] Make it possible to run from the command line

**Challenge**

Make this work:

```bash
python -m pipeline.ingest
```

And produce something like:

```text
data/
├── raw/
│   ├── customers/
│   ├── products/
│   ├── orders/
│   └── ...
│
└── staging/
    ├── customers/
    ├── products/
    ├── orders/
    └── ...
```

**Definition of done**

You understand: `Source → ingestion → staging` and can explain why each layer exists.

---

### Phase 3 — Parquet & Data Lake

**Goal:** Learn how analytical data is stored efficiently.

**Tasks**

- [ ] Convert CSV/JSON → Parquet
- [ ] Learn Parquet schemas
- [ ] Inspect Parquet metadata
- [ ] Use compression
- [ ] Partition data by date
- [ ] Read Parquet using Python
- [ ] Read Parquet using DuckDB
- [ ] Compare CSV vs Parquet
- [ ] Test querying only selected columns
- [ ] Test querying only selected partitions

**Challenge**

Create:

```text
data/lake/
├── customers/
├── products/
└── orders/
    └── year=2026/
        ├── month=08/
        └── month=09/
```

Then query it directly:

```sql
SELECT *
FROM read_parquet('data/lake/orders/**/*.parquet');
```

**Definition of done**

You should understand why data engineers use Parquet instead of just CSV.

---

### Phase 4 — Object Storage / S3

**Goal:** Turn your local data lake into something resembling cloud infrastructure.

Use MinIO locally so you don't need to spend money on AWS.

**Tasks**

- [ ] Add MinIO to Docker Compose
- [ ] Create an S3 bucket
- [ ] Upload raw data
- [ ] Upload Parquet files
- [ ] Download objects
- [ ] List objects
- [ ] Organize objects using prefixes
- [ ] Write Python code to interact with S3
- [ ] Handle failed uploads
- [ ] Make uploads idempotent

**Challenge**

Build:

```text
Python
   ↓
MinIO
   ↓
ecommerce-data/
   ├── raw/
   ├── staging/
   └── processed/
```

**Definition of done**

You can explain the difference between:

- Database
- Data Lake
- Object Storage
- Data Warehouse

---

### Phase 5 — SQL & DuckDB Analytics

**Goal:** Become really comfortable querying large datasets.

**Tasks**

- [ ] Query Parquet with DuckDB
- [ ] JOIN datasets
- [ ] GROUP BY
- [ ] Window functions
- [ ] CTEs
- [ ] Aggregations
- [ ] Date functions
- [ ] Calculate revenue
- [ ] Calculate average order value
- [ ] Calculate customer lifetime value
- [ ] Find repeat customers
- [ ] Find cancelled/returned orders

**Challenge**

Create an analytics query:

```text
Customer → Orders → Order Items → Revenue
```

Then answer:

- Who are the top 10 customers by revenue?
- What is the monthly revenue trend?

**Definition of done**

You can use SQL to turn raw transactional data into useful business information.

---

### Phase 6 — Data Warehouse

**Goal:** Build an analytical database. Use PostgreSQL initially.

**Tasks**

- [ ] Design warehouse schema
- [ ] Identify facts
- [ ] Identify dimensions
- [ ] Create dimension tables
- [ ] Create fact tables
- [ ] Create primary keys
- [ ] Create foreign keys
- [ ] Load transformed data
- [ ] Write analytical queries
- [ ] Add indexes
- [ ] Compare warehouse queries vs raw data queries

You'll probably end up with something like:

```text
Dimensions          Facts
────────────       ───────────────
dim_customer       fact_order
dim_product        fact_order_item
dim_date           fact_payment
                   fact_shipment
                   fact_return
```

**Definition of done**

You understand OLTP vs OLAP and why warehouse schemas are designed differently from application databases.

---

### Phase 7 — Data Transformation & Modeling

**Goal:** Learn how raw data becomes analytics-ready data.

**Tasks**

- [ ] Create staging tables
- [ ] Clean raw data
- [ ] Normalize inconsistent values
- [ ] Handle NULLs
- [ ] Deduplicate records
- [ ] Create dimension tables
- [ ] Create fact tables
- [ ] Create derived metrics
- [ ] Create daily/monthly aggregates
- [ ] Document transformations

**Challenge**

Take:

```text
orders, order_items, customers, products
```

and produce `fact_sales` with:

- `order_id`
- `customer_id`
- `product_id`
- `date_id`
- `quantity`
- `unit_price`
- `discount`
- `total_amount`

**Definition of done**

You can explain: `Raw data → cleaned data → modeled data → analytics.`

---

### Phase 8 — Data Quality 🧪

_This is an important one._

**Goal:** Make the pipeline detect bad data instead of blindly processing everything.

**Introduce intentional problems**

- [ ] NULL customer IDs
- [ ] Duplicate orders
- [ ] Negative quantities
- [ ] Negative prices
- [ ] Invalid dates
- [ ] Unknown customer IDs
- [ ] Payment ≠ order total
- [ ] Shipment without an order
- [ ] Return without an order

**Then create checks**

- [ ] Primary key uniqueness
- [ ] NOT NULL validation
- [ ] Referential integrity
- [ ] Valid ranges
- [ ] Valid dates
- [ ] Business-rule validation

**Challenge**

Your pipeline should fail with something useful:

```text
DATA QUALITY ERROR

orders:
  duplicate order_id: 23
  null customer_id: 7
  negative quantity: 3

Pipeline stopped.
```

**Definition of done**

You understand that data engineering isn't just moving data — it's making sure the data can be trusted.

---

### Phase 9 — Airflow / Orchestration

**Goal:** Automate the entire pipeline.

**Tasks**

- [ ] Add Airflow to Docker Compose
- [ ] Create your first DAG
- [ ] Create ingestion task
- [ ] Create transformation task
- [ ] Create warehouse loading task
- [ ] Create data quality task
- [ ] Define dependencies
- [ ] Add retries
- [ ] Add task logging
- [ ] Configure schedules

**Pipeline**

```text
generate → ingest → upload → transform → warehouse → quality_check
```

**Challenge**

Make the pipeline run automatically every day.

**Definition of done**

You can look at Airflow and understand: what ran, what failed, why it failed, and what runs next.

---

### Phase 10 — Incremental Processing 🚀

_This is where I'd expect you to start thinking more like a production data engineer._

**Tasks**

- [ ] Stop processing the entire dataset every run
- [ ] Add `created_at`
- [ ] Add `updated_at`
- [ ] Track last successful ingestion
- [ ] Process only new records
- [ ] Handle updated records
- [ ] Handle duplicates
- [ ] Implement upserts
- [ ] Handle late-arriving data
- [ ] Make pipeline idempotent

**Example**

```text
Day 1: 10,000 orders  →  process 10,000
Day 2:   +500 orders  →  process ONLY 500
Day 3:   +700 orders  →  process ONLY 700
```

**Definition of done**

You can explain the difference between **full load** and **incremental load**, and implement both.

---

### Phase 11 — Monitoring & Observability

**Goal:** Know when your pipeline is broken.

**Tasks**

- [ ] Add structured logging
- [ ] Track execution time
- [ ] Track rows processed
- [ ] Track rows rejected
- [ ] Track failures
- [ ] Track pipeline status
- [ ] Add retry behavior
- [ ] Create basic metrics
- [ ] Create alerts for failures

**Example output**

```text
Pipeline: daily_orders
Status:   SUCCESS

Rows received:     12,532
Rows processed:    12,421
Rows rejected:        111
Execution time:    34.2 sec
```

**Definition of done**

You can answer _"Did today's pipeline run correctly?"_ without manually checking every table.

---

### Phase 12 — Spark 🔥

_Only after the previous phases._

Now we introduce distributed processing.

**Tasks**

- [ ] Install Spark
- [ ] Understand Spark architecture
- [ ] DataFrame API
- [ ] Read Parquet
- [ ] Write Parquet
- [ ] Filtering
- [ ] Aggregations
- [ ] Joins
- [ ] Partitioning
- [ ] Shuffle
- [ ] Understand lazy evaluation
- [ ] Compare Spark vs DuckDB

**Challenge**

Take your existing transformation:

```text
Raw Parquet → DuckDB → fact_sales
```

and implement it with:

```text
Raw Parquet → Spark → fact_sales
```

Then compare them.

---

## 🏆 Final Project

When everything is finished, your project should look something like:

```text
                ┌──────────────┐
                │   Generator  │
                └──────┬───────┘
                       │
                       ▼
                ┌──────────────┐
                │      Raw     │
                │     Data     │
                └──────┬───────┘
                       │
                       ▼
                ┌──────────────┐
                │   Ingestion  │
                └──────┬───────┘
                       │
                       ▼
                ┌──────────────┐
                │      S3      │
                │    / MinIO   │
                └──────┬───────┘
                       │
                       ▼
                ┌──────────────┐
                │    Parquet   │
                └──────┬───────┘
                       │
                       ▼
                ┌──────────────┐
                │Transformation│
                │ DuckDB/Spark │
                └──────┬───────┘
                       │
                       ▼
                ┌──────────────┐
                │  PostgreSQL  │
                │   Warehouse  │
                └──────┬───────┘
                       │
                ┌──────┴───────┐
                ▼              ▼
          Data Quality     Analytics
                │
                ▼
             Airflow
                │
                ▼
          Monitoring
```

---

## 🎯 How we'll work through it

_(TODO: fill in the working process — cadence, per-phase deliverables, and how to track progress.)_

---

## Legend

- [x] Completed
- [ ] Not started

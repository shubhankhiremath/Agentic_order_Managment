# Dataset Analysis — Agentic Order Management Automation

This report is based on a full inspection of the CSVs in `Dataset/` (Windows also resolves the same folder as `dataset/`). Original CSV files were **not modified**.

Source: **Olist Brazilian E-Commerce Public Dataset** (Kaggle / Olist). All measurements below were computed from the local files, not from assumed documentation.

---

## 1. Repository state (Phase 1) 

The workspace currently contains only the nine CSV files. There is no application code, `docs/` (other than this file), backend, or frontend yet.

---

## 2. Files found

| File | Size (approx.) | Rows | Columns |
|------|----------------|------|---------|
| `olist_orders_dataset.csv` | 16.8 MB | **99,441** | 8 |
| `olist_customers_dataset.csv` | 8.6 MB | **99,441** | 5 |
| `olist_order_items_dataset.csv` | 14.7 MB | **112,650** | 7 |
| `olist_order_payments_dataset.csv` | 5.5 MB | **103,886** | 5 |
| `olist_order_reviews_dataset.csv` | 13.8 MB | **99,224** | 7 |
| `olist_products_dataset.csv` | 2.3 MB | **32,951** | 9 |
| `olist_sellers_dataset.csv` | 171 KB | **3,095** | 4 |
| `olist_geolocation_dataset.csv` | 58.4 MB | **1,000,163** | 5 |
| `product_category_name_translation.csv` | 2.6 KB | **71** | 2 |

**Total:** 9 files, ~1.55 million CSV rows (dominated by geolocation).

---

## 3. Column inventory (actual headers)

### 3.1 `olist_orders_dataset.csv`

| Column | Observed dtype | Role |
|--------|----------------|------|
| `order_id` | string | Primary key (unique, 99,441) |
| `customer_id` | string | FK → customers (1:1 with this table) |
| `order_status` | string | Lifecycle status |
| `order_purchase_timestamp` | datetime string | Purchase time |
| `order_approved_at` | datetime string | Payment/approval time (nullable) |
| `order_delivered_carrier_date` | datetime string | Handoff to carrier (nullable) |
| `order_delivered_customer_date` | datetime string | Actual customer delivery (nullable) |
| `order_estimated_delivery_date` | datetime string | Promised delivery date (never null) |

**`order_status` values (counts):**

| Status | Count |
|--------|------:|
| `delivered` | 96,478 |
| `shipped` | 1,107 |
| `canceled` | 625 |
| `unavailable` | 609 |
| `invoiced` | 314 |
| `processing` | 301 |
| `created` | 5 |
| `approved` | 2 |

**Purchase date range:** 2016-09-04 → 2018-10-17.

### 3.2 `olist_customers_dataset.csv`

| Column | Observed dtype | Role |
|--------|----------------|------|
| `customer_id` | string | PK; one ID per **order** (not per person) |
| `customer_unique_id` | string | Stable person identifier (96,096 unique) |
| `customer_zip_code_prefix` | int | Brazilian CEP prefix |
| `customer_city` | string | City |
| `customer_state` | string | UF (27 values) |

No missing values. 2,997 unique customers placed more than one order (multiple `customer_id` values share a `customer_unique_id`).

### 3.3 `olist_order_items_dataset.csv`

| Column | Observed dtype | Role |
|--------|----------------|------|
| `order_id` | string | FK → orders |
| `order_item_id` | int | Line number within the order (1–21) |
| `product_id` | string | FK → products |
| `seller_id` | string | FK → sellers |
| `shipping_limit_date` | datetime string | Seller ship-by deadline |
| `price` | float | Item price (BRL) |
| `freight_value` | float | Freight (BRL) |

Composite uniqueness: `(order_id, order_item_id)` is unique (0 duplicates). **9,803** orders have more than one item. Max 21 items on one order.

**98,666** distinct orders appear in items → **775 orders have no line items**.

### 3.4 `olist_order_payments_dataset.csv`

| Column | Observed dtype | Role |
|--------|----------------|------|
| `order_id` | string | FK → orders |
| `payment_sequential` | int | Payment installment/split index (1–29) |
| `payment_type` | string | Method |
| `payment_installments` | int | Card installments |
| `payment_value` | float | Amount (BRL) |

Composite uniqueness: `(order_id, payment_sequential)` is unique.

**`payment_type` values:** `credit_card` (76,795), `boleto` (19,784), `voucher` (5,775), `debit_card` (1,529), `not_defined` (3).

**2,961** orders have multiple payment rows. **1 order has no payment:** `bfbd0f9bdef84302105ad712db648a6c` (status `delivered`). Nine rows have `payment_value == 0`.

### 3.5 `olist_order_reviews_dataset.csv`

| Column | Observed dtype | Role |
|--------|----------------|------|
| `review_id` | string | **Not unique** (see notes) |
| `order_id` | string | FK → orders |
| `review_score` | int | 1–5 |
| `review_comment_title` | string | Mostly missing |
| `review_comment_message` | string | Often missing |
| `review_creation_date` | datetime string | Survey created |
| `review_answer_timestamp` | datetime string | Customer answered |

**Review scores:** 5 (57,328), 4 (19,142), 3 (8,179), 2 (3,151), 1 (11,424).

**768** orders have no review. **547** orders have more than one review row (max 3). `review_id` has **814 duplicate occurrences** (789 duplicated IDs); the same `review_id` can appear on **different** `order_id`s with identical comment text. Application PK cannot be `review_id` alone.

### 3.6 `olist_products_dataset.csv`

| Column | Observed dtype | Notes |
|--------|----------------|-------|
| `product_id` | string | PK (32,951 unique) |
| `product_category_name` | string | Portuguese category; 610 null (1.85%) |
| `product_name_lenght` | float | **Source typo:** `lenght` not `length` |
| `product_description_lenght` | float | Same typo |
| `product_photos_qty` | float | Nullable with category |
| `product_weight_g` | float | 2 missing |
| `product_length_cm` | float | 2 missing |
| `product_height_cm` | float | 2 missing |
| `product_width_cm` | float | 2 missing |

The dataset does **not** contain product titles or SKU names — only IDs, Portuguese category, text-length stats, photo count, and physical dimensions.

**73** distinct category names in products vs **71** translation rows. Untranslated categories: `portateis_cozinha_e_preparadores_de_alimentos`, `pc_gamer`.

All products appear in at least one order item (0 orphan products).

### 3.7 `olist_sellers_dataset.csv`

| Column | Observed dtype | Role |
|--------|----------------|------|
| `seller_id` | string | PK (3,095 unique) |
| `seller_zip_code_prefix` | int | CEP prefix |
| `seller_city` | string | |
| `seller_state` | string | 23 states |

No missing values. All sellers appear in items.

### 3.8 `olist_geolocation_dataset.csv`

| Column | Observed dtype | Role |
|--------|----------------|------|
| `geolocation_zip_code_prefix` | int | **Not unique** (19,015 distinct prefixes) |
| `geolocation_lat` | float | |
| `geolocation_lng` | float | |
| `geolocation_city` | string | Spelling variants exist |
| `geolocation_state` | string | 27 UFs |

~1 million rows; median **29** rows per zip prefix (max 1,146). This is a many-rows-per-zip lookup, not a 1:1 dimension table.

**Join coverage:** 157 of 14,994 customer zip prefixes and 7 of 2,246 seller zip prefixes are missing from geolocation.

### 3.9 `product_category_name_translation.csv`

| Column | Observed dtype |
|--------|----------------|
| `product_category_name` | Portuguese (PK, 71) |
| `product_category_name_english` | English label |

Useful for UI/agent responses (English category names).

---

## 4. Relationships (verified)

```
customers.customer_id  1:1  orders.customer_id
orders.order_id        1:N  order_items.order_id
orders.order_id        1:N  order_payments.order_id
orders.order_id        1:N  order_reviews.order_id
order_items.product_id N:1  products.product_id
order_items.seller_id  N:1  sellers.seller_id
products.product_category_name N:1  category_translation (partial)
customers.customer_zip_code_prefix  ~  geolocation.zip (many geo rows)
sellers.seller_zip_code_prefix      ~  geolocation.zip (many geo rows)
```

Integrity checks:

| Check | Result |
|-------|--------|
| Every order has a customer | True (and vice versa) |
| Every item `order_id` exists in orders | True |
| Every payment `order_id` exists in orders | True |
| Every review `order_id` exists in orders | True |
| Every item `product_id` exists in products | True |
| Every item `seller_id` exists in sellers | True |
| Orders without items | **775** (mostly `unavailable` / `canceled`) |
| Orders without payments | **1** |
| Orders without reviews | **768** |

**Important modeling note:** `customer_id` is order-scoped. To list “all orders for a person,” tools should join `customer_unique_id`, not assume `customer_id` is a stable account ID. The required tool `get_customer_orders(customer_id)` should accept either ID and resolve via `customer_unique_id` when possible.

---

## 5. Missing-value observations

| Table | Field | Missing | % | Implication |
|-------|-------|--------:|--:|-------------|
| orders | `order_approved_at` | 160 | 0.16% | Created/canceled/unapproved paths |
| orders | `order_delivered_carrier_date` | 1,783 | 1.79% | Not yet shipped / canceled / unavailable |
| orders | `order_delivered_customer_date` | 2,965 | 2.98% | Not delivered; 8 `delivered` orders still null |
| reviews | `review_comment_title` | 87,656 | 88.34% | Optional text |
| reviews | `review_comment_message` | 58,247 | 58.70% | Score-only reviews common |
| products | category + name/desc/photos lengths | 610 | 1.85% | Unknown category |
| products | weight/dimensions | 2 | 0.01% | Rare |

Status vs timestamps (useful for exception rules):

- `created` (5): all approval/carrier/customer dates null
- `approved` (2): approved set; no carrier/customer dates
- `invoiced` / `processing` / `unavailable`: approved typically set; no carrier dates
- `shipped` (1,107): carrier date always present; customer date always null
- `delivered`: almost complete timestamps; small anomalies (14 missing approval, 2 missing carrier, 8 missing customer date)
- `canceled`: mixed timestamps (some were already in transit)

**Late delivery (deterministic, date-normalized):** of 96,478 `delivered` orders, **6,534** have `order_delivered_customer_date` after `order_estimated_delivery_date`. These are **not** official Olist SLA definitions; they are dataset-derived facts for demo exception detection.

---

## 6. Fields useful to the application

| Domain | Fields to use |
|--------|----------------|
| **Orders** | `order_id`, `customer_id`, `order_status`, all five timestamps |
| **Customers** | `customer_id`, `customer_unique_id`, city, state, zip prefix |
| **Products** | `product_id`, `product_category_name` + English translation, dimensions/weight (optional) |
| **Sellers** | `seller_id`, city, state, zip prefix |
| **Payments** | `payment_type`, `payment_installments`, `payment_value`, `payment_sequential` |
| **Reviews** | `review_score`, comments, timestamps (store with surrogate PK) |
| **Delivery** | estimated vs actual customer date, carrier date, `shipping_limit_date` on items |

Not present in the dataset (must not be fabricated as Olist columns): tracking numbers, carrier names, return requests, refund records, support tickets, product titles, customer names/emails.

Application-owned tables (not from CSVs): `support_tickets`.

---

## 7. How each table will be used

| Source | Application use |
|--------|-----------------|
| orders | Status, timeline, “where is my order,” delivery comparison, dashboard counts |
| customers | Customer lookup, order history via `customer_unique_id` |
| order_items | Line items, prices, freight, sellers, ship-by dates |
| payments | Payment method(s), installments, totals |
| reviews | Satisfaction / complaint context |
| products | Category (EN) and physical attributes on item details |
| sellers | Seller location on item/delivery context |
| category translation | English labels in agent/UI |
| geolocation | Optional lat/lng for city/zip context; **do not query 1M rows per request** |
| support_tickets (app) | `create_support_ticket` tool |

---

## 8. Recommended SQLite schema (Phase 2+)

Preserve real columns. Do not invent Olist fields. Use ORM-mapped names that match the CSV except for documented corrections.

### 8.1 Import all operational tables; treat geolocation as optional aggregated lookup

**Load fully:** customers, orders, order_items, payments, reviews, products, sellers, category_translation.

**Geolocation:** do **not** import 1,000,163 raw rows as-is for v1. If location context is needed, import a **derived** table `geolocation_zip` with one row per `zip_code_prefix` (mean lat/lng, representative city/state). This is a derived lookup, clearly documented, not a fabricated Olist table. Core order tools do not require it.

### 8.2 Proposed tables and keys

**`customers`**

- PK: `customer_id`
- Index: `customer_unique_id`, `customer_zip_code_prefix`
- Columns: as CSV

**`orders`**

- PK: `order_id`
- FK: `customer_id` → `customers.customer_id`
- Indexes: `customer_id`, `order_status`, `order_purchase_timestamp`
- Datetime columns stored as ISO text or SQLite datetime; parse on import

**`order_items`**

- PK: `(order_id, order_item_id)`
- FK: `order_id` → `orders` (nullable FK enforcement: items always valid)
- FK: `product_id` → `products`
- FK: `seller_id` → `sellers`
- Indexes: `order_id`, `product_id`, `seller_id`

**`order_payments`**

- PK: `(order_id, payment_sequential)`
- FK: `order_id` → `orders`
- Index: `order_id`, `payment_type`

**`order_reviews`**

- PK: `id` INTEGER AUTOINCREMENT (surrogate)
- Unique constraint: **none** on `review_id` (not unique in source)
- Index: `order_id`, `review_id`, `review_score`
- FK: `order_id` → `orders`

**`products`**

- PK: `product_id`
- Columns: keep source names `product_name_lenght` / `product_description_lenght` **or** map to `product_name_length` / `product_description_length` in SQLAlchemy with a documented rename. Recommendation: **rename in DB** to correct spelling; document mapping in import script so we do not silently invent new business fields.

**`sellers`**

- PK: `seller_id`
- Index: zip prefix

**`product_category_translations`**

- PK: `product_category_name`
- Column: `product_category_name_english`

**`support_tickets`** (application)

- PK: `ticket_id` (generated, e.g. `TKT-` + ULID/UUID)
- `order_id` (indexed; FK optional so tickets can exist if order later missing)
- `issue`, `description`, `status`, `created_at`

### 8.3 FK policy on import

Use `PRAGMA foreign_keys=ON` after load. Load order: customers → products → sellers → translations → orders → items → payments → reviews.

Do not fail the whole import on the 775 item-less orders or the 1 payment-less order; those are valid parent rows.

### 8.4 Repeatable import

Idempotent script: delete/recreate SQLite file **or** `DELETE` + re-insert in a transaction. Path: `Dataset/*.csv`. Never reload CSVs on API requests.

---

## 9. Sample real order IDs (for later README / tests)

These exist in the local CSVs:

| Scenario | `order_id` |
|----------|------------|
| Delivered on time | `e481f51cbdc54678b7cc49136f2d6af7` |
| Delivered late vs estimate | `203096f03d82e0dffbc41ebc2e2bcfb7` |
| Shipped (not delivered) | `ee64d42b8cf066f35eac1cf57de1aa85` |
| Canceled | `1b9ecfe83cdc259250e1a8aca174f0ad` |
| Unavailable | `8e24261a7e58791d10cb1bf9da94df5c` |
| Invoiced | `136cce7faa42fdb2cefd53fdc79a6098` |
| Processing | `15bed8e2fec7fdbadb186b57c46c92f2` |
| Created | `b5359909123fa03c50bdb0cfed07f098` |
| Approved | `a2e4c44360b4a57bdff22f3a4630c173` |
| No payment row | `bfbd0f9bdef84302105ad712db648a6c` |

---

## 10. Implications for exception detection (preview)

Rules will use **only** these fields and will be documented as **synthetic demo rules**, not official Olist policy:

- Late delivery: `delivered` and actual date > estimated date
- Shipped past estimate: `shipped` and current/reference date > estimated (dataset is historical; use estimated vs last known timestamp / “as-of dataset end” — to be specified in `docs/business_rules.md`)
- Approved/invoiced/processing with no carrier date (stuck pre-ship)
- Delivered status with missing `order_delivered_customer_date`
- Payment `not_defined` or missing payment row
- Long duration: `delivered_customer - purchase` above a documented percentile/threshold

LLM will **not** compute these; `exception_service.py` will.

---

## 11. What we will not invent

- Product names, customer PII, tracking URLs, carrier names
- Official Olist return/refund windows
- Columns not present in the CSVs
- Treating `review_id` as a unique PK
- Treating `customer_id` as a long-lived account ID

# دليل Power BI — لوحة تحكم Olist للتجارة الإلكترونية

هذا الدليل يشرح كيف تعيد بناء لوحة التحكم بنفسك في **Power BI Desktop** على جهازك خلال ~15 دقيقة.
المرجع البصري للشكل النهائي هو ملف **`dashboard.png`** الموجود في نفس المجلد — قارن نتيجتك به.

التصميم المستخدم: بنفسجي غامق **Indigo (#4338CA)** + كهرماني **Amber (#F59E0B)** على خلفية فاتحة.

---

## 0) المتطلبات (قبل كل شيء)

1. ثبّت **Python** من python.org (إصدار 3.10 أو أحدث) على اللابتوب.
2. افتح CMD ونفّذ:
   ```
   pip install pandas matplotlib
   ```
3. في Power BI Desktop: ‏**File ← Options and settings ← Options ← Python scripting** ← اختر مجلد تثبيت Python من القائمة (Detected Python home directories) ← OK.

---

## 1) المسار السريع (موصى به): Python Visuals على صفحتين

### الخطوة 1 — تحميل الملفات

**Get Data ← Text/CSV** وحمّل الملفات الستة من مجلد `data/`:
`orders.csv` ، `customers.csv` ، `order_items.csv` ، `order_payments.csv` ، `products.csv` ، `product_category_name_translation.csv`
ثم **Load**.

### الخطوة 2 — بناء جدول واحد مسطّح (FlatSales) في Power Query

افتح **Transform Data** ونفّذ بالترتيب (Python visual يقبل أعمدة من جدول واحد فقط):

1. في استعلام `order_payments`: رتّب حسب `payment_sequential` تصاعديًا، ثم **Remove Duplicates** على عمود `order_id` (نريد طريقة الدفع الأولى لكل طلب فقط).
2. اختر استعلام `orders` ← **Merge Queries** ← ادمج مع `order_items` على `order_id` ← نوع الدمج **Left Outer** ← وسّع (expand) الأعمدة: `order_item_id` ، `product_id` ، `price` (ألغِ تحديد "Use original column name as prefix").
3. **Merge Queries** ← مع `products` على `product_id` ← Left Outer ← expand: `product_category_name`.
4. **Merge Queries** ← مع `product_category_name_translation` على `product_category_name` ← Left Outer ← expand: `product_category_name_english`.
5. **Merge Queries** ← مع `customers` على `customer_id` ← Left Outer ← expand: `customer_unique_id` ، `customer_state`.
6. **Merge Queries** ← مع `order_payments` على `order_id` ← Left Outer ← expand: `payment_type`.
7. أعد تسمية الاستعلام إلى **`FlatSales`**.
8. اضبط أنواع البيانات: `order_purchase_timestamp` ← Date/Time ، و `price` ← Decimal Number.
9. **Close & Apply**.

> البدء من `orders` مع Left joins مهم: هكذا تبقى كل الطلبات (30,000) حتى التي بلا سطور منتجات، وتتطابق الأرقام مع `dashboard.png`.

### الخطوة 3 — الصفحة 1: Overview (نظرة عامة)

1. أضف صفحة جديدة وسمّها **Overview**.
2. من لوحة Visualizations اختر **Python visual** (أيقونة Py) وكبّر مساحته.
3. اسحب هذه الأعمدة **السبعة بالضبط** من جدول `FlatSales` إلى خانة **Values**:
   `order_id` ، `order_item_id` ، `order_purchase_timestamp` ، `price` ، `payment_type` ، `customer_state` ، `customer_unique_id`
4. انسخ كامل محتوى ملف **`powerbi-page1-overview.py`** والصقه في محرر السكربت ثم اضغط ▶ تشغيل.

النتيجة: بطاقات KPI المستديرة (الطلبات، العملاء، الإيراد، متوسط السلة) + الترند الشهري للطلبات والإيراد + دونات طرق الدفع + أعلى 8 ولايات بالإيراد.

> ملاحظة: Python visual يحذف الصفوف المكررة من الأعمدة المسحوبة، لذلك `order_item_id` موجود في القائمة ليحافظ على مستوى سطر المنتج — بدونه قد تُحسب الإيرادات ناقصة.

### الخطوة 4 — الصفحة 2: Details (التفاصيل)

1. أضف صفحة جديدة وسمّها **Details** وأضف **Python visual** جديد.
2. اسحب هذه الأعمدة **الستة بالضبط** من `FlatSales` إلى **Values**:
   `order_id` ، `order_item_id` ، `order_purchase_timestamp` ، `price` ، `product_category_name_english` ، `customer_unique_id`
3. انسخ كامل محتوى ملف **`powerbi-page2-details.py`** والصقه ثم اضغط ▶ تشغيل.

النتيجة: أعمدة شرائح RFM + معدل الـ Churn حسب الشريحة + أعلى 10 فئات بالإيراد + خريطة الـ Cohort Retention الحرارية.

---

## 2) الـ Slicers (الفلاتر) — تشتغل مع Python visuals

أضف **Slicer** visuals في أي صفحة من `FlatSales`:

| الـ Slicer | العمود | الفائدة |
|---|---|---|
| الولاية | `customer_state` | فلترة حسب ولاية العميل |
| الشهر | `order_purchase_timestamp` (Date hierarchy ← Month) | فلترة زمنية |
| طريقة الدفع | `payment_type` | فلترة حسب طريقة الدفع |

**ملاحظة صادقة:** الـ Slicers **تشتغل** مع Python visuals — Power BI يصفّي الصفوف أولًا ثم يمرّر الـ `dataset` المصفّى للسكربت، فالفلاتر تنعكس على الرسومات مباشرة. لكن انتبه: **التفاعل بالنقر** (cross-highlighting) من رسمة على رسمة أخرى **لا يصل** إلى Python visual — هو يستجيب للـ Slicers والفلاتر فقط، وليس للنقر على أعمدة رسومات أخرى.

---

## 3) المسار البديل: Native Power BI (بدون بايثون — DAX + رسومات جاهزة)

لو تفضّل بناء اللوحة بأدوات Power BI الأصلية:

### الجداول والعلاقات (Model view)

الجداول: `orders` ، `customers` ، `order_items` (جدول الحقائق) ، `order_payments` ، `products` (ادمج معه الترجمة في Power Query).

العلاقات (كلها Many-to-One باتجاه واحد نحو جدول البُعد):

- `order_items[order_id]` ←→ `orders[order_id]`
- `order_items[product_id]` ←→ `products[product_id]`
- `orders[customer_id]` ←→ `customers[customer_id]`
- `order_payments[order_id]` ←→ `orders[order_id]`

### مقاييس DAX (انسخ والصق — Modeling ← New measure)

```dax
Orders Count = COUNTROWS ( 'orders' )

Customers = DISTINCTCOUNT ( 'customers'[customer_unique_id] )

Total Revenue = SUM ( 'order_items'[price] )

Avg Ticket = DIVIDE ( [Total Revenue], [Orders Count] )

Avg Delivery Days =
AVERAGEX (
    FILTER ( 'orders', NOT ISBLANK ( 'orders'[order_delivered_customer_date] ) ),
    DATEDIFF (
        'orders'[order_purchase_timestamp],
        'orders'[order_delivered_customer_date],
        DAY
    )
)

Late Delivery % =
DIVIDE (
    COUNTROWS (
        FILTER (
            'orders',
            NOT ISBLANK ( 'orders'[order_delivered_customer_date] )
                && 'orders'[order_delivered_customer_date]
                    > 'orders'[order_estimated_delivery_date]
        )
    ),
    COUNTROWS (
        FILTER ( 'orders', NOT ISBLANK ( 'orders'[order_delivered_customer_date] ) )
    )
) * 100

Credit Card % =
DIVIDE (
    COUNTROWS (
        FILTER ( 'order_payments', 'order_payments'[payment_type] = "credit_card" )
    ),
    COUNTROWS ( 'order_payments' )
) * 100
```

### جدول RFM (Modeling ← New table)

```dax
RFM_Customers =
VAR RefDate = MAX ( 'orders'[order_purchase_timestamp] )
RETURN
ADDCOLUMNS (
    SUMMARIZE ( 'customers', 'customers'[customer_unique_id] ),
    "RecencyDays", INT ( RefDate - CALCULATE ( MAX ( 'orders'[order_purchase_timestamp] ) ) ),
    "Frequency", CALCULATE ( DISTINCTCOUNT ( 'orders'[order_id] ) ),
    "Monetary", CALCULATE ( SUM ( 'order_items'[price] ) )
)
```

أعمدة محسوبة على `RFM_Customers` (New column):

```dax
Segment =
VAR f = 'RFM_Customers'[Frequency]
VAR r = 'RFM_Customers'[RecencyDays]
VAR m = 'RFM_Customers'[Monetary]
VAR p80 = PERCENTILE.INC ( 'RFM_Customers'[Monetary], 0.8 )
RETURN
SWITCH (
    TRUE (),
    f >= 2 && m >= p80, "Champions",
    f >= 2, "Loyal",
    r <= 90, "New",
    r <= 365, "At-Risk",
    "Lost"
)

Churned = IF ( 'RFM_Customers'[RecencyDays] > 180, 1, 0 )
```

ومقياس:

```dax
Churn Rate % =
DIVIDE ( SUM ( 'RFM_Customers'[Churned] ), COUNTROWS ( 'RFM_Customers' ) ) * 100
```

### الرسومات المقترحة لكل لوحة

- **صف KPIs:** أربع بطاقات **Card** ← `Orders Count` ، `Customers` ، `Total Revenue` (نسّقه R$) ، `Avg Ticket`.
- **الترند الشهري:** **Line and clustered column chart** ← المحور X: `order_purchase_timestamp` (Month) ، أعمدة: `Orders Count` ، خط: `Total Revenue`.
- **شرائح RFM:** **Clustered column chart** ← المحور X: `RFM_Customers[Segment]` ، القيم: Count of `customer_unique_id`.
- **طرق الدفع:** **Donut chart** ← Legend: `order_payments[payment_type]` ، Values: Count of `order_id`.
- **أعلى الفئات:** **Bar chart** ← المحور Y: `products[product_category_name_english]` ، المحور X: `Total Revenue` ، مع فلتر Top N = 10.
- **الـ Churn:** **Clustered column chart** ← المحور X: `Segment` ، القيم: `Churn Rate %`.
- **Cohort Retention:** مصفوفة **Matrix** متقدمة (الأسهل: استخدم صفحة Details من مسار البايثون).

### تنظيف Power Query (مطلوب للمسارين)

- أعمدة الطوابع الزمنية (`order_purchase_timestamp` ، `order_delivered_customer_date` …) ← نوع **Date/Time**.
- `price` ، `freight_value` ، `payment_value` ← **Decimal Number**.
- `customer_zip_code_prefix` ← **Text** (ليس رقمًا).
- قيم `payment_type`: `credit_card` ، `boleto` ، `voucher` ، `debit_card`.

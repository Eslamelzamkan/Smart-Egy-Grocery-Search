# PostgreSQL Database Schema Report: `product_ai_training`

Database: `product_ai_training` on PostgreSQL 18.1 at `localhost:5432`.

## Installed Extensions

| Extension | Version |
|---|---|
| `plpgsql` | `1.0` |

---

## Public Tables Summary

| Table Name | Row Count | Description / Role |
|---|---|---|
| `branches` | 7 | Table `branches` |
| `categories` | 14 | Table `categories` |
| `customers` | 32,045 | Table `customers` |
| `deliveries` | 189,058 | Table `deliveries` |
| `drivers` | 44 | Table `drivers` |
| `favorites` | 83,342 | Table `favorites` |
| `order_items` | 1,428,055 | Table `order_items` |
| `orders` | 209,826 | Table `orders` |
| `products` | 1,093 | Table `products` |
| `promo_codes` | 17 | Table `promo_codes` |
| `special_days` | 67 | Table `special_days` |
| `subcategories` | 47 | Table `subcategories` |
| `trips` | 43,761 | Table `trips` |
| `zones` | 18 | Table `zones` |

---

## Detailed Table Schemas

### Table: `branches` (7 rows)

| Column | Type | Nullable | Default |
|---|---|---|---|
| `id` | `uuid` | NO | - |
| `code` | `text` | NO | - |
| `name` | `text` | NO | - |
| `branch_type` | `text` | NO | - |
| `latitude` | `double precision` | YES | - |
| `longitude` | `double precision` | YES | - |
| `opened_at` | `timestamp without time zone` | NO | - |
| `closed_at` | `timestamp without time zone` | YES | - |

**Sample Row (Keys & Values):**
```json
{
  "id": "b92f5e7c-f6c8-493b-929e-d28196c194bf",
  "code": "HEL",
  "name": "نجمة - مصر الجديدة",
  "branch_type": "Store",
  "latitude": "30.0911",
  "longitude": "31.3236",
  "opened_at": "2022-05-02 23:00:00",
  "closed_at": null
}
```

### Table: `categories` (14 rows)

| Column | Type | Nullable | Default |
|---|---|---|---|
| `id` | `uuid` | NO | - |
| `name_ar` | `text` | NO | - |
| `name_en` | `text` | NO | - |

**Sample Row (Keys & Values):**
```json
{
  "id": "1b9cdb91-0b0b-4d75-aa4d-dca642c3831d",
  "name_ar": "خضروات وفواكه",
  "name_en": "Fruits & Vegetables"
}
```

### Table: `customers` (32,045 rows)

| Column | Type | Nullable | Default |
|---|---|---|---|
| `id` | `uuid` | NO | - |
| `first_name` | `text` | NO | - |
| `last_name` | `text` | YES | - |
| `phone` | `text` | NO | - |
| `email` | `text` | YES | - |
| `created_at` | `timestamp without time zone` | NO | - |

**Sample Row (Keys & Values):**
```json
{
  "id": "d9821b90-39c8-406e-a0b4-e4c159f99e2f",
  "first_name": "فاطمة",
  "last_name": "الشريف",
  "phone": "01099910001",
  "email": "customer100001@example.com",
  "created_at": "2025-06-20 14:23:00"
}
```

### Table: `deliveries` (189,058 rows)

| Column | Type | Nullable | Default |
|---|---|---|---|
| `id` | `uuid` | NO | - |
| `order_id` | `uuid` | NO | - |
| `trip_id` | `uuid` | NO | - |
| `driver_id` | `uuid` | NO | - |
| `stop_number` | `integer` | YES | - |
| `attempt_number` | `integer` | NO | - |
| `trip_started_at` | `timestamp without time zone` | YES | - |
| `ended_at` | `timestamp without time zone` | YES | - |
| `result` | `text` | NO | - |
| `failure_reason` | `text` | YES | - |
| `distance_from_branch_km` | `numeric` | YES | - |
| `driver_distance_from_customer_m` | `integer` | YES | - |
| `cash_to_collect` | `numeric` | YES | - |

**Sample Row (Keys & Values):**
```json
{
  "id": "9d947a82-9ed7-4253-9d98-404270e0d320",
  "order_id": "cb1f4fc3-6835-48cb-bb75-7e7b3b42b227",
  "trip_id": "47b33b83-6db2-447f-9ee7-23bb3b83bd51",
  "driver_id": "30ec9d43-6839-4b81-8ec3-1002e8aa8109",
  "stop_number": "1",
  "attempt_number": "1",
  "trip_started_at": "2024-10-19 09:28:26.171326",
  "ended_at": "2024-10-19 09:51:04.907908",
  "result": "Delivered",
  "failure_reason": null,
  "distance_from_branch_km": "1.60",
  "driver_distance_from_customer_m": "135",
  "cash_to_collect": "444.99"
}
```

### Table: `drivers` (44 rows)

| Column | Type | Nullable | Default |
|---|---|---|---|
| `id` | `uuid` | NO | - |
| `code` | `text` | NO | - |
| `name` | `text` | NO | - |
| `branch_id` | `uuid` | YES | - |
| `vehicle_type` | `text` | YES | - |
| `hired_at` | `timestamp without time zone` | NO | - |

**Sample Row (Keys & Values):**
```json
{
  "id": "ad30ae17-4b44-469c-a7ad-4d441e4c6f44",
  "code": "driver.045",
  "name": "سمر شوقي",
  "branch_id": "b92f5e7c-f6c8-493b-929e-d28196c194bf",
  "vehicle_type": "Motorcycle",
  "hired_at": "2024-08-10 10:00:00"
}
```

### Table: `favorites` (83,342 rows)

| Column | Type | Nullable | Default |
|---|---|---|---|
| `customer_id` | `uuid` | NO | - |
| `product_id` | `uuid` | NO | - |
| `created_at` | `timestamp without time zone` | NO | - |

**Sample Row (Keys & Values):**
```json
{
  "customer_id": "26a15429-034d-4477-b8bf-7894f06a4ee8",
  "product_id": "1bddd5bb-b53f-42d0-904c-989b67ce86b7",
  "created_at": "2026-02-09 08:21:00"
}
```

### Table: `order_items` (1,428,055 rows)

| Column | Type | Nullable | Default |
|---|---|---|---|
| `id` | `uuid` | NO | - |
| `order_id` | `uuid` | NO | - |
| `product_id` | `uuid` | NO | - |
| `quantity` | `numeric` | NO | - |
| `unit_price` | `numeric` | NO | - |
| `regular_price` | `numeric` | YES | - |

**Sample Row (Keys & Values):**
```json
{
  "id": "b401b7ce-fad6-42bd-9566-a8ce9eb3f238",
  "order_id": "8947a175-a50a-4c02-b01e-b17ecbeee1a8",
  "product_id": "9a5c6ffd-88a1-4cbc-9eb4-0e7ce7eb042b",
  "quantity": "2.000",
  "unit_price": "75.07",
  "regular_price": "75.07"
}
```

### Table: `orders` (209,826 rows)

| Column | Type | Nullable | Default |
|---|---|---|---|
| `id` | `uuid` | NO | - |
| `order_number` | `text` | NO | - |
| `customer_id` | `uuid` | NO | - |
| `branch_id` | `uuid` | NO | - |
| `zone_id` | `uuid` | YES | - |
| `created_at` | `timestamp without time zone` | NO | - |
| `channel` | `text` | NO | - |
| `delivery_method` | `text` | NO | - |
| `delivery_slot_start` | `timestamp without time zone` | YES | - |
| `latitude` | `double precision` | YES | - |
| `longitude` | `double precision` | YES | - |
| `location_quality` | `text` | YES | - |
| `payment_method` | `text` | NO | - |
| `promo_code` | `text` | YES | - |
| `subtotal` | `numeric` | NO | - |
| `discount` | `numeric` | NO | - |
| `delivery_fee` | `numeric` | NO | - |
| `total` | `numeric` | NO | - |
| `status` | `text` | NO | - |
| `delivered_at` | `timestamp without time zone` | YES | - |
| `cancelled_at` | `timestamp without time zone` | YES | - |
| `cancelled_by` | `text` | YES | - |
| `cancel_reason` | `text` | YES | - |

**Sample Row (Keys & Values):**
```json
{
  "id": "8947a175-a50a-4c02-b01e-b17ecbeee1a8",
  "order_number": "ORD-20241019-55D90C",
  "customer_id": "15b46c85-a90d-4140-a1de-5d0c36fc2364",
  "branch_id": "b92f5e7c-f6c8-493b-929e-d28196c194bf",
  "zone_id": null,
  "created_at": "2024-10-19 20:22:00",
  "channel": "CallCenter",
  "delivery_method": "Pickup",
  "delivery_slot_start": null,
  "latitude": null,
  "longitude": null,
  "location_quality": null,
  "payment_method": "CashOnDelivery",
  "promo_code": "WELCOME50",
  "subtotal": "666.80",
  "discount": "50.00",
  "delivery_fee": "0.00",
  "total": "616.80",
  "status": "Delivered",
  "delivered_at": "2024-10-19 22:41:21.137235",
  "cancelled_at": null,
  "cancelled_by": null,
  "cancel_reason": null
}
```

### Table: `products` (1,093 rows)

| Column | Type | Nullable | Default |
|---|---|---|---|
| `id` | `uuid` | NO | - |
| `sku` | `text` | NO | - |
| `subcategory_id` | `uuid` | NO | - |
| `name_ar` | `text` | NO | - |
| `name_en` | `text` | NO | - |
| `brand_ar` | `text` | YES | - |
| `brand_en` | `text` | YES | - |
| `size_ar` | `text` | YES | - |
| `size_en` | `text` | YES | - |
| `unit` | `text` | NO | - |
| `price` | `numeric` | YES | - |
| `is_active` | `boolean` | NO | - |
| `created_at` | `timestamp without time zone` | NO | - |

**Sample Row (Keys & Values):**
```json
{
  "id": "b8b32f06-27c0-4941-af90-97927dbcb44b",
  "sku": "P100001",
  "subcategory_id": "e1c932a4-b477-4f44-adea-f5a0160bb616",
  "name_ar": "طماطم 1 كجم",
  "name_en": "Tomatoes 1 kg",
  "brand_ar": null,
  "brand_en": null,
  "size_ar": "1 كجم",
  "size_en": "1 kg",
  "unit": "Kg",
  "price": "21.29",
  "is_active": "True",
  "created_at": "2022-05-02 23:00:00"
}
```

### Table: `promo_codes` (17 rows)

| Column | Type | Nullable | Default |
|---|---|---|---|
| `code` | `text` | NO | - |
| `name` | `text` | NO | - |
| `amount` | `numeric` | NO | - |
| `is_percentage` | `boolean` | NO | - |
| `valid_until` | `timestamp without time zone` | YES | - |
| `usage_limit` | `integer` | YES | - |
| `per_customer_limit` | `integer` | YES | - |

**Sample Row (Keys & Values):**
```json
{
  "code": "WELCOME50",
  "name": "خصم أول طلب",
  "amount": "50.00",
  "is_percentage": "False",
  "valid_until": "2027-12-31 23:59:00",
  "usage_limit": null,
  "per_customer_limit": "1"
}
```

### Table: `special_days` (67 rows)

| Column | Type | Nullable | Default |
|---|---|---|---|
| `day` | `date` | NO | - |
| `name` | `text` | NO | - |
| `shop_closed` | `boolean` | NO | - |

**Sample Row (Keys & Values):**
```json
{
  "day": "2025-03-01",
  "name": "Ramadan",
  "shop_closed": "False"
}
```

### Table: `subcategories` (47 rows)

| Column | Type | Nullable | Default |
|---|---|---|---|
| `id` | `uuid` | NO | - |
| `category_id` | `uuid` | NO | - |
| `name_ar` | `text` | NO | - |
| `name_en` | `text` | NO | - |

**Sample Row (Keys & Values):**
```json
{
  "id": "e1c932a4-b477-4f44-adea-f5a0160bb616",
  "category_id": "1b9cdb91-0b0b-4d75-aa4d-dca642c3831d",
  "name_ar": "خضروات",
  "name_en": "Vegetables"
}
```

### Table: `trips` (43,761 rows)

| Column | Type | Nullable | Default |
|---|---|---|---|
| `id` | `uuid` | NO | - |
| `trip_number` | `text` | NO | - |
| `branch_id` | `uuid` | NO | - |
| `driver_id` | `uuid` | YES | - |
| `vehicle_type` | `text` | YES | - |
| `status` | `text` | NO | - |
| `planned_start_at` | `timestamp without time zone` | YES | - |
| `started_at` | `timestamp without time zone` | YES | - |
| `returned_at` | `timestamp without time zone` | YES | - |
| `cancelled_at` | `timestamp without time zone` | YES | - |
| `cash_status` | `text` | YES | - |
| `expected_cash` | `numeric` | YES | - |
| `handed_over` | `numeric` | YES | - |
| `cash_difference` | `numeric` | YES | - |

**Sample Row (Keys & Values):**
```json
{
  "id": "5e010721-2f79-46bb-a618-c8cc13a3dc02",
  "trip_number": "TR-241019-HEL-000001",
  "branch_id": "b92f5e7c-f6c8-493b-929e-d28196c194bf",
  "driver_id": "ad30ae17-4b44-469c-a7ad-4d441e4c6f44",
  "vehicle_type": "Motorcycle",
  "status": "Closed",
  "planned_start_at": "2024-10-19 09:49:04.504069",
  "started_at": "2024-10-19 09:49:04.504069",
  "returned_at": "2024-10-19 11:33:12.151457",
  "cancelled_at": null,
  "cash_status": "Matched",
  "expected_cash": "1944.24",
  "handed_over": "1944.24",
  "cash_difference": "0.00"
}
```

### Table: `zones` (18 rows)

| Column | Type | Nullable | Default |
|---|---|---|---|
| `id` | `uuid` | NO | - |
| `branch_id` | `uuid` | NO | - |
| `name` | `text` | NO | - |
| `delivery_fee` | `numeric` | NO | - |

**Sample Row (Keys & Values):**
```json
{
  "id": "7eb677a8-9a26-4fb8-96a6-8a1aa3274096",
  "branch_id": "b92f5e7c-f6c8-493b-929e-d28196c194bf",
  "name": "مصر الجديدة - وسط",
  "delivery_fee": "15.00"
}
```

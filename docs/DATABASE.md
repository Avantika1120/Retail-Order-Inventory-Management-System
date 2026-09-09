# Database Design

## PostgreSQL schema

### products
- `id` primary key
- `sku` unique business identifier
- `name`
- `category`
- `price`

### customers
- `id` primary key
- `name`
- `email` unique

### inventory
- `product_id` primary/foreign key to products
- `quantity_on_hand`
- `reorder_level`

### orders
- `id` primary key
- `customer_id` foreign key
- `status`
- `total_amount`
- `created_at`

### order_items
- `id` primary key
- `order_id` foreign key
- `product_id` foreign key
- `quantity`
- `unit_price`
- `line_total`

## Why PostgreSQL for orders and inventory?

The ordering workflow requires consistency across multiple records. A single order can affect an order header, multiple line items, and several inventory rows. These changes should either all succeed or all fail. PostgreSQL transactions and row locks are therefore a better fit than a document store for this part of the system.

## MongoDB collections

### reviews
Example document:

```json
{
  "product_id": 12,
  "customer_id": 42,
  "rating": 4,
  "title": "Good value",
  "body": "Battery life was better than expected.",
  "created_at": "timestamp"
}
```

### audit_events
Example document:

```json
{
  "event_type": "inventory.restocked",
  "payload": {
    "product_id": 12,
    "quantity": 20
  },
  "created_at": "timestamp"
}
```

## Why MongoDB for reviews and audit logs?

Reviews and operational events are append-heavy, document-shaped records whose attributes may evolve. For example, future versions could add moderation metadata, sentiment labels, extracted themes, browser context, or trace IDs without requiring changes to the relational transaction model.

## Consistency boundary

PostgreSQL is the system of record for products, customers, inventory, and orders. MongoDB audit writes happen after successful relational commits, so audit collection failure should not invalidate an already completed customer transaction in a production-hardening version. A real production system could improve this further with an outbox/event queue pattern.
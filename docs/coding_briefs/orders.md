# Latoun Configurator Orders — Coding Agent Brief

## 1. Objective

Update the Latoun configurator to replace the current user-facing **Save Configuration** workflow with an **Order** workflow.

The new system must support:

- One order containing multiple differently configured assemblies
- Quantities for identical assemblies
- Structured relational storage
- No separate global `configurations` table
- No large `configuration_json` blob as the primary order model
- Browser-side draft order state
- Database persistence only when the user submits an order
- Historical price and BOM preservation
- Future support for multi-gang products

Use this core architecture:

```text
Order
  └── Order Items
        ├── structured product configuration
        ├── quantity
        ├── price snapshot
        ├── selected modules
        └── BOM snapshot
```

Do not create one database configuration record for every assembly or every physical product.

---

## 2. Current Behavior

The current Assembly tab includes functionality similar to:

```text
Save Configuration
Export JSON
Saved Configurations
```

A saved configuration represents the current product choices, such as:

```text
1-gang
Rotary Dimmer
Brass
```

This internal prototype behavior should be replaced with an order-oriented workflow.

The configurator should still maintain one current working assembly in frontend state, but ordinary users should not save arbitrary configurations to the database.

---

## 3. Target User Flow

The main configurator flow should become:

```text
Configure assembly
        ↓
Add to Order
        ↓
Review draft order
        ↓
Add another assembly or edit quantities
        ↓
Submit Order
```

Example:

```text
Configure:
1-gang rotary dimmer, brass

Click:
Add to Order

Configure:
1-gang switch, steel

Click:
Add to Order

Draft Order:
2 × Brass Rotary Dimmer
4 × Steel Switch
```

The configurator must support multiple unique assembly types within one order.

---

## 4. Terminology

Use these terms consistently.

### Current Configuration

The assembly currently being edited in the configurator.

It exists only in frontend state until added to the draft order.

Example:

```text
gang count: 1
slot 1: rotary dimmer
finish scheme: brass
```

### Draft Order

A temporary collection of configured assemblies.

For the first implementation, store the draft order in browser `localStorage`.

Do not create a database order merely because the user opens the configurator or changes a product option.

### Order Item

One unique configured assembly with a quantity.

Example:

```text
1-gang rotary dimmer, brass
quantity: 3
```

Three identical physical devices are represented by one order item with `quantity = 3`.

### Submitted Order

A persisted database order containing one or more order items.

After submission, its commercial snapshots must not change automatically when product definitions, materials, or pricing are updated.

---

## 5. Architectural Decisions

Implement the following decisions.

### Use structured order-item configuration

Use relational columns and child rows for the authoritative configuration.

Do not use a large opaque `configuration_json` field as the primary model.

### Do not create a global configurations table

Do not implement:

```text
configurations
orders
order_items
```

where order items reference globally shared configuration records.

Instead, store the product choices directly on each order item and its child records.

### Do not store one row per physical unit

For:

```text
100 × identical brass rotary dimmers
```

store:

```text
one order item
quantity = 100
```

### Persist only meaningful commercial actions

No database writes are required when the user:

```text
changes finish
changes module type
rotates the camera
opens the configurator
abandons the page
```

Create database records when the user submits an order.

### Store commercial snapshots

At order submission, preserve:

```text
unit price
line total
product and option labels
BOM
configuration schema version
```

Do not store temporary rendering details such as camera position or Three.js object state.

---

## 6. Recommended Database Model

Add the following core tables:

```text
orders
order_items
order_item_modules
order_item_bom
```

Reuse existing tables where appropriate:

```text
finish_schemes
module_types
products or product_families
parts
materials
```

Exact foreign-key names may be adjusted to match the existing repository.

---

## 7. `orders` Table

The `orders` table represents the complete customer order.

Recommended fields:

```text
order_id
order_number
status
customer_name
customer_email
customer_phone
shipping_address_line_1
shipping_address_line_2
shipping_city
shipping_state
shipping_postal_code
shipping_country
currency
subtotal
tax
shipping_amount
total
notes
created_at
updated_at
submitted_at
```

Possible statuses:

```text
submitted
quoted
payment_pending
paid
in_production
shipped
completed
cancelled
```

Do not create database orders with an `abandoned` status for every visitor in the initial implementation.

The order should be created when the customer explicitly submits it.

### Order Number

Generate a human-readable order number, for example:

```text
LAT-ORD-000001
```

The database primary key and public order number should be separate fields.

---

## 8. `order_items` Table

Each row represents one unique configured assembly in an order.

Recommended fields:

```text
order_item_id
order_id
product_family_id
gang_count
finish_scheme_id
quantity
unit_price
line_total
configuration_version
product_code_snapshot
product_name_snapshot
finish_scheme_code_snapshot
finish_scheme_name_snapshot
created_at
updated_at
```

Foreign keys:

```text
order_id → orders.order_id
finish_scheme_id → finish_schemes.finish_scheme_id
product_family_id → product_families.product_family_id
```

Use the existing product table if one already exists.

Required rules:

```text
quantity >= 1
gang_count >= 1
unit_price >= 0
line_total = unit_price × quantity
```

Do not rely only on frontend calculations. Recalculate monetary totals on the backend.

---

## 9. `order_item_modules` Table

This table stores slot-by-slot module choices.

Recommended fields:

```text
order_item_module_id
order_item_id
slot_number
module_type_id
module_code_snapshot
module_name_snapshot
created_at
```

Foreign keys:

```text
order_item_id → order_items.order_item_id
module_type_id → module_types.module_type_id
```

Required uniqueness constraint:

```text
UNIQUE(order_item_id, slot_number)
```

Example for one-gang:

```text
order item:
gang_count = 1

module row:
slot_number = 1
module_type = rotary_dimmer
```

Example for two-gang:

```text
order item:
gang_count = 2

module rows:
slot 1 → switch
slot 2 → rotary_dimmer
```

This structure must support future multi-gang configurations without redesigning the order schema.

---

## 10. `order_item_bom` Table

When the order is submitted, store an immutable BOM snapshot for each order item.

Recommended fields:

```text
order_item_bom_id
order_item_id
part_id
part_code_snapshot
part_name_snapshot
quantity_per_assembly
assembly_quantity
total_quantity
unit_cost_snapshot
created_at
```

Foreign key:

```text
order_item_id → order_items.order_item_id
```

Example:

```text
Order item:
3 × 1-gang brass rotary dimmer

BOM:
plate_1gang
quantity_per_assembly = 1
assembly_quantity = 3
total_quantity = 3

screw_set_1gang
quantity_per_assembly = 1
assembly_quantity = 3
total_quantity = 3

rotary_dimmer_module
quantity_per_assembly = 1
assembly_quantity = 3
total_quantity = 3
```

The BOM snapshot should preserve what manufacturing expected when the order was submitted.

Do not resolve historical orders against the current live BOM later.

---

## 11. Optional Audit Snapshot

A small JSON snapshot may be stored for auditing or human-readable export, but it must not be the authoritative configuration model.

Optional field:

```text
configuration_snapshot_json
```

Example content:

```json
{
  "schema_version": 1,
  "gang_count": 1,
  "finish_scheme": {
    "code": "brass",
    "display_name": "Brass"
  },
  "modules": [
    {
      "slot": 1,
      "code": "rotary_dimmer",
      "display_name": "Rotary Dimmer"
    }
  ]
}
```

Do not store:

```text
GLB object trees
Three.js material instances
camera state
UI state
temporary validation messages
full render state
shader source
```

The structured database fields remain authoritative.

---

## 12. Draft Order Storage

For the first public implementation, keep the draft order in browser `localStorage`.

Recommended key:

```text
latoun_draft_order_v1
```

Suggested frontend shape:

```typescript
interface DraftOrder {
  schemaVersion: number;
  items: DraftOrderItem[];
  updatedAt: string;
}

interface DraftOrderItem {
  localId: string;
  configurationHash: string;
  productFamilyCode: string;
  gangCount: number;
  finishSchemeCode: string;
  modules: DraftOrderModule[];
  quantity: number;
  estimatedUnitPrice: number | null;
}

interface DraftOrderModule {
  slotNumber: number;
  moduleTypeCode: string;
}
```

The backend must not trust browser prices during submission.

Draft order data should survive page refreshes.

Provide a clear action to:

```text
Clear Order
```

---

## 13. Configuration Identity and Duplicate Merging

When a user adds the same configured assembly more than once, increase its quantity instead of creating duplicate draft lines.

Create a canonical configuration representation.

Example:

```json
{
  "product_family_code": "electrical_device",
  "gang_count": 1,
  "finish_scheme_code": "brass",
  "modules": [
    {
      "slot_number": 1,
      "module_type_code": "rotary_dimmer"
    }
  ]
}
```

Canonicalization rules:

```text
sort object keys consistently
sort modules by slot_number
normalize codes
exclude quantity
exclude price
exclude timestamps
exclude frontend-only fields
```

Generate:

```text
configuration_hash = SHA-256(canonical representation)
```

When adding to the draft order:

```text
same configuration_hash
→ increase quantity

different configuration_hash
→ add a new order item
```

The hash is for matching and convenience, not security.

---

## 14. Assembly Tab Changes

Remove or hide these user-facing controls:

```text
Save Configuration
Saved Configurations
```

Replace the primary action with:

```text
Add to Order
```

Recommended Assembly tab structure:

```text
Product options
3D preview
Configuration summary
Estimated price
Add to Order
View Order
```

After adding:

```text
Added to Order

1-gang Brass Rotary Dimmer
Quantity in order: 2
```

The current working configuration should remain editable after adding.

Adding to the order must copy the current semantic choices into the draft-order state. Later changes to the current assembly must not mutate an existing order item unless the user explicitly edits that order item.

---

## 15. Order Review UI

Add an Order or Cart view.

Recommended route:

```text
/order
```

or:

```text
/cart
```

Use the user-facing label:

```text
Order
```

The page should display each unique configured assembly.

Example:

| Assembly | Finish | Modules | Quantity | Unit Price | Total |
|---|---|---|---:|---:|---:|
| 1-gang | Brass | Rotary Dimmer | 2 | $285 | $570 |
| 1-gang | Steel | Switch | 4 | $240 | $960 |

Required controls:

```text
increase quantity
decrease quantity
enter quantity
remove item
edit configuration
clear order
submit order
```

When quantity reaches zero, remove the line after confirmation or treat zero as removal.

---

## 16. Editing an Order Item

When the user selects:

```text
Edit
```

load that order item's configuration into the Assembly tab.

Maintain an edit context, for example:

```text
editingDraftOrderItemId
```

The primary action changes from:

```text
Add to Order
```

to:

```text
Update Order Item
```

When saved:

1. Recalculate the canonical configuration hash.
2. If it matches another existing line, merge quantities.
3. Otherwise update the selected line.
4. Return to the Order page or show confirmation.

Do not silently edit another line with the same configuration.

---

## 17. Submit Order API

Add an endpoint such as:

```text
POST /api/orders
```

Example request:

```json
{
  "customer": {
    "name": "John Smith",
    "email": "john@example.com",
    "phone": "+1..."
  },
  "shipping_address": {
    "line_1": "123 Main Street",
    "line_2": null,
    "city": "Chicago",
    "state": "IL",
    "postal_code": "60600",
    "country": "US"
  },
  "notes": null,
  "items": [
    {
      "product_family_code": "electrical_device",
      "gang_count": 1,
      "finish_scheme_code": "brass",
      "quantity": 2,
      "modules": [
        {
          "slot_number": 1,
          "module_type_code": "rotary_dimmer"
        }
      ]
    },
    {
      "product_family_code": "electrical_device",
      "gang_count": 1,
      "finish_scheme_code": "steel",
      "quantity": 4,
      "modules": [
        {
          "slot_number": 1,
          "module_type_code": "switch"
        }
      ]
    }
  ]
}
```

The client must not send authoritative totals.

The backend must resolve and calculate:

```text
product validity
module validity
finish validity
compatibility
unit price
line total
subtotal
tax
shipping
total
BOM
display-name snapshots
product-code snapshots
```

---

## 18. Order Submission Transaction

Create the order in one database transaction.

Required sequence:

```text
1. Validate customer and address data.
2. Validate that at least one item exists.
3. Validate each structured configuration.
4. Resolve live product entities.
5. Resolve current pricing.
6. Resolve current BOM.
7. Create the order row.
8. Create order-item rows.
9. Create order-item-module rows.
10. Create order-item-BOM rows.
11. Calculate and save totals.
12. Commit the transaction.
```

If any item is invalid, roll back the complete order.

Do not partially create an order.

---

## 19. Backend Validation

For every submitted item, validate:

```text
product family exists and is active
gang count is supported
finish scheme exists
finish scheme is active
finish scheme is customer visible
module type exists
module type is active
slot numbers are valid
one module exists for each required slot
no duplicate slot numbers exist
module is compatible with the selected product
semantic material assignments resolve
BOM resolves
pricing resolves
quantity is within allowed range
```

Do not trust configuration hashes supplied by the client.

The backend may generate its own canonical hash for audit and grouping.

---

## 20. Pricing

Use a backend pricing resolver.

Do not accept `estimatedUnitPrice` as authoritative.

At submission:

```text
unit_price = current resolved price
line_total = unit_price × quantity
```

Store:

```text
unit_price
line_total
currency
```

on the order item.

Store order totals on the order.

Historical submitted orders must not change when current product prices change.

### Initial Pricing Fallback

If the existing product model does not yet have complete pricing, implement a clearly isolated pricing service with temporary values.

Do not hard-code price calculations inside React components or API route handlers.

---

## 21. BOM Resolution

Use the existing prototype BOM logic if available, but move authoritative BOM generation to the backend.

The BOM resolver should accept the structured configuration:

```text
product family
gang count
finish scheme
module selections
quantity
```

It should return part rows such as:

```text
plate
plate screws
module internals
actuator
packaging
```

At order submission, copy the resolved BOM into `order_item_bom`.

The preview may continue showing a live derived BOM, but the submitted order must use the backend result.

---

## 22. Semantic Materials and Orders

Orders should store customer product choices, not every resolved render-material assignment.

Store:

```text
finish_scheme_id
finish_scheme_code_snapshot
finish_scheme_name_snapshot
```

Do not store the complete semantic material assignment map as the primary order configuration.

Material assignments remain part of the product-definition system:

```text
finish_scheme + binding_name → render_material
```

Optionally include a resolved material snapshot in an exported order document for debugging, but it is not required in the core order schema.

Manufacturing identity should be represented through product options and BOM parts, not Three.js material instances.

---

## 23. Historical Stability

Submitted orders must remain understandable even if live entities are renamed or disabled.

Store both:

```text
foreign key
snapshot code
snapshot display name
```

Example:

```text
finish_scheme_id = 7
finish_scheme_code_snapshot = "brass"
finish_scheme_name_snapshot = "Brass"
```

Use the snapshot fields when displaying historical orders.

The foreign key may still support internal traceability.

Do not automatically update snapshots when live product names change.

---

## 24. Order Immutability

Before submission, draft order items are editable in browser storage.

After database submission:

```text
commercial configuration
quantity
unit price
line total
BOM snapshot
```

should be treated as immutable for the first implementation.

Later, order changes should use explicit administrative workflows rather than silently editing original rows.

A cancelled order should remain in the database with status:

```text
cancelled
```

Do not hard-delete submitted orders through the normal UI.

---

## 25. Admin Order View

Add a basic internal order-management view if the current app includes admin functionality.

Recommended internal route:

```text
/admin/orders
```

List columns:

```text
order number
submitted date
customer
status
item count
total
```

Order detail should show:

```text
customer information
shipping address
order totals
each order item
item configuration
quantity
price snapshot
module selections
BOM snapshot
```

Administrative status changes may be supported:

```text
submitted
quoted
paid
in_production
shipped
cancelled
```

Do not implement payment processing unless already in scope.

---

## 26. Database Constraints

Recommended constraints:

```text
orders.order_number UNIQUE
order_items.quantity > 0
order_items.gang_count > 0
order_items.unit_price >= 0
order_items.line_total >= 0
UNIQUE(order_item_id, slot_number)
order_item_bom.quantity_per_assembly > 0
order_item_bom.assembly_quantity > 0
order_item_bom.total_quantity > 0
```

Use foreign-key enforcement in SQLite.

Use cascade deletion only for child rows of an unsubmitted test order where deletion is explicitly allowed.

Avoid deleting submitted commercial orders.

---

## 27. Suggested SQLAlchemy Structure

Adapt to repository conventions.

```python
class Order(Base):
    __tablename__ = "orders"

    order_id = Column(Integer, primary_key=True)
    order_number = Column(String, nullable=False, unique=True)
    status = Column(String, nullable=False)

    customer_name = Column(String, nullable=False)
    customer_email = Column(String, nullable=False)
    customer_phone = Column(String, nullable=True)

    shipping_address_line_1 = Column(String, nullable=False)
    shipping_address_line_2 = Column(String, nullable=True)
    shipping_city = Column(String, nullable=False)
    shipping_state = Column(String, nullable=False)
    shipping_postal_code = Column(String, nullable=False)
    shipping_country = Column(String, nullable=False, default="US")

    currency = Column(String, nullable=False, default="USD")
    subtotal = Column(Numeric(12, 2), nullable=False)
    tax = Column(Numeric(12, 2), nullable=False)
    shipping_amount = Column(Numeric(12, 2), nullable=False)
    total = Column(Numeric(12, 2), nullable=False)

    notes = Column(Text, nullable=True)

    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)
    submitted_at = Column(DateTime, nullable=False)
```

```python
class OrderItem(Base):
    __tablename__ = "order_items"

    order_item_id = Column(Integer, primary_key=True)

    order_id = Column(
        Integer,
        ForeignKey("orders.order_id", ondelete="CASCADE"),
        nullable=False,
    )

    product_family_id = Column(
        Integer,
        ForeignKey("product_families.product_family_id"),
        nullable=False,
    )

    finish_scheme_id = Column(
        Integer,
        ForeignKey("finish_schemes.finish_scheme_id"),
        nullable=False,
    )

    gang_count = Column(Integer, nullable=False)
    quantity = Column(Integer, nullable=False)

    unit_price = Column(Numeric(12, 2), nullable=False)
    line_total = Column(Numeric(12, 2), nullable=False)

    configuration_version = Column(Integer, nullable=False, default=1)

    product_code_snapshot = Column(String, nullable=False)
    product_name_snapshot = Column(String, nullable=False)
    finish_scheme_code_snapshot = Column(String, nullable=False)
    finish_scheme_name_snapshot = Column(String, nullable=False)

    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)
```

```python
class OrderItemModule(Base):
    __tablename__ = "order_item_modules"

    order_item_module_id = Column(Integer, primary_key=True)

    order_item_id = Column(
        Integer,
        ForeignKey("order_items.order_item_id", ondelete="CASCADE"),
        nullable=False,
    )

    slot_number = Column(Integer, nullable=False)

    module_type_id = Column(
        Integer,
        ForeignKey("module_types.module_type_id"),
        nullable=False,
    )

    module_code_snapshot = Column(String, nullable=False)
    module_name_snapshot = Column(String, nullable=False)

    created_at = Column(DateTime, nullable=False)

    __table_args__ = (
        UniqueConstraint(
            "order_item_id",
            "slot_number",
            name="uq_order_item_slot",
        ),
    )
```

```python
class OrderItemBom(Base):
    __tablename__ = "order_item_bom"

    order_item_bom_id = Column(Integer, primary_key=True)

    order_item_id = Column(
        Integer,
        ForeignKey("order_items.order_item_id", ondelete="CASCADE"),
        nullable=False,
    )

    part_id = Column(
        Integer,
        ForeignKey("parts.part_id"),
        nullable=True,
    )

    part_code_snapshot = Column(String, nullable=False)
    part_name_snapshot = Column(String, nullable=False)

    quantity_per_assembly = Column(Integer, nullable=False)
    assembly_quantity = Column(Integer, nullable=False)
    total_quantity = Column(Integer, nullable=False)

    unit_cost_snapshot = Column(Numeric(12, 2), nullable=True)
    created_at = Column(DateTime, nullable=False)
```

---

## 28. Frontend Services

Create dedicated frontend modules instead of placing all logic in components.

Suggested responsibilities:

```text
currentConfigurationService
draftOrderService
configurationCanonicalizer
orderApiService
```

### `draftOrderService`

Responsibilities:

```text
load draft order from localStorage
save draft order
add item
merge identical item
update item
remove item
change quantity
clear order
```

### `configurationCanonicalizer`

Responsibilities:

```text
normalize configuration
sort modules
generate canonical string
generate configuration hash
```

### `orderApiService`

Responsibilities:

```text
submit order
load order confirmation
handle API validation errors
```

---

## 29. Order Confirmation

After successful submission:

1. Clear the draft order from `localStorage`.
2. Show an order-confirmation page.
3. Display the public order number.
4. Display submitted items and totals.
5. Prevent accidental resubmission on browser refresh.

Suggested route:

```text
/order-confirmation/{orderNumber}
```

Example:

```text
Thank you.

Your order number is:
LAT-ORD-000124
```

Do not expose internal database IDs.

---

## 30. Concurrency and Idempotency

Prevent duplicate order creation when a user double-clicks Submit or refreshes during submission.

Use an idempotency token.

Frontend:

```text
generate UUID when beginning submission
send as idempotency_key
```

Backend:

```text
store idempotency_key with the order
return the existing order if the same key is submitted again
```

Add a uniqueness constraint:

```text
orders.idempotency_key UNIQUE
```

Disable the submit button while the request is in progress.

---

## 31. Migration From Saved Configurations

Remove the user-facing Saved Configurations feature after the order workflow is working.

Migration steps:

```text
1. Keep the current configuration in React state.
2. Add draft-order localStorage support.
3. Add Add to Order.
4. Add Order review page.
5. Add order database schema.
6. Add order submission API.
7. Add order confirmation.
8. Remove Save Configuration button.
9. Remove Saved Configurations list.
10. Remove obsolete saved-configuration endpoints and tables if unused elsewhere.
```

Before deleting any existing configuration table, inspect whether it contains internal test data that should be exported or migrated.

Do not delete existing data silently during migration.

If the current configuration table is used only by the prototype, document its removal in the migration.

---

## 32. Export JSON

The current Export JSON function may remain as an internal debugging tool, but it should not be presented as the primary customer order action.

Possible internal export:

```json
{
  "order_number": "LAT-ORD-000124",
  "status": "submitted",
  "items": [
    {
      "product_family_code": "electrical_device",
      "gang_count": 1,
      "finish_scheme_code": "brass",
      "quantity": 2,
      "modules": [
        {
          "slot_number": 1,
          "module_type_code": "rotary_dimmer"
        }
      ],
      "unit_price": 285.00,
      "line_total": 570.00
    }
  ]
}
```

The database remains authoritative.

---

## 33. Testing

### Backend Tests

Implement tests for:

```text
create one-item order
create multi-item order
create multi-gang order item
reject empty order
reject quantity below one
reject invalid finish scheme
reject hidden or inactive finish scheme
reject invalid module
reject missing slot
reject duplicate slot
reject unsupported gang count
calculate line total correctly
calculate order subtotal correctly
create BOM snapshot
create display-name snapshots
rollback complete order on item failure
idempotent duplicate submission
generate unique public order number
```

### Frontend Tests

Test:

```text
Add to Order creates one draft item
adding identical configuration increases quantity
adding different finish creates a new item
adding different module creates a new item
draft survives page reload
quantity can be changed
item can be removed
order can be cleared
item can be edited
edited item can merge with an identical item
submit button disables during request
successful submit clears localStorage
failed submit preserves draft order
order confirmation displays order number
```

### Manual Scenarios

Test at least:

```text
1 × Brass Rotary Dimmer
4 × Brass Rotary Dimmer
2 × Steel Switch
one order containing Brass Dimmer and Steel Switch
edit Brass Dimmer into Steel Dimmer
remove one line
reload browser with a draft order
submit order
retry submission after simulated timeout
```

---

## 34. Error Handling

Handle these cases clearly:

```text
localStorage data is invalid
draft-order schema version is unsupported
selected finish became inactive before submission
selected module was removed before submission
pricing cannot resolve
BOM cannot resolve
network request fails
order submission times out
duplicate submission occurs
database transaction fails
```

Example messages:

```text
This finish is no longer available. Please choose another finish.

The Rotary Dimmer is no longer available for slot 1.

We could not calculate the order price. The order was not submitted.

Your draft order is still saved in this browser.
```

Do not clear the draft order after a failed submission.

---

## 35. Non-Goals

Do not implement these unless already present in the repository:

```text
payment processing
user accounts
cross-device cart synchronization
abandoned-cart database tracking
global reusable configuration records
one configuration row per physical unit
full ecommerce inventory reservation
shipping-provider integration
tax-provider integration
discount codes
returns
order editing after submission
automatic manufacturing scheduling
```

Use isolated service interfaces where future integrations are expected.

---

## 36. Acceptance Criteria

The implementation is complete when:

1. `Save Configuration` is removed from the user workflow.
2. `Saved Configurations` is removed from the user workflow.
3. The Assembly tab has `Add to Order`.
4. Draft order items are stored in browser `localStorage`.
5. One draft order supports multiple differently configured assemblies.
6. Identical configurations merge into one line with increased quantity.
7. Different configurations remain separate order items.
8. The Order page supports quantity editing, removal, and configuration editing.
9. Submitted orders are stored in `orders`.
10. Structured assembly data is stored in `order_items` and `order_item_modules`.
11. There is no separate global `configurations` table.
12. Large `configuration_json` blobs are not used as the authoritative model.
13. One order item represents one unique assembly configuration multiplied by quantity.
14. Backend validation rechecks all product choices.
15. Backend pricing is authoritative.
16. Unit-price and line-total snapshots are saved.
17. BOM snapshots are stored in `order_item_bom`.
18. Historical names and codes are stored as snapshots.
19. Order submission is transactional.
20. Duplicate submissions are prevented through idempotency.
21. Successful submission clears the browser draft.
22. Failed submission preserves the browser draft.
23. The order confirmation displays a public order number.
24. Future multi-gang products can be represented through slot rows.
25. No database rows are created merely because a visitor changes configurator options.

---

## 37. Guiding Principles

```text
The configurator edits one current assembly.

The draft order contains one or more configured assemblies.

Draft state lives in the browser.

The database stores submitted commercial intent.

One order item represents one unique configured assembly times quantity.

Product choices are relational and structured.

Do not create a global configuration registry.

Do not store one record per physical device.

Do not treat frontend prices as authoritative.

Preserve price, label, and BOM snapshots at submission.

Keep rendering details separate from order data.

Build for multi-gang products now without overengineering the rest.
```
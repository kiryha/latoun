# Latoun Configurator Orders — Coding Agent Brief

## 1. Objective

Update the Latoun configurator to support a customer-facing **Order** workflow.

The implementation must allow:

- One order containing multiple differently configured assemblies
- Multiple quantities of the same assembly
- Structured relational storage of submitted order items
- Browser-local draft order state
- Database persistence only when the customer submits an order
- Historical price, label, and BOM snapshots
- Future 1-, 2-, 3-, and 4-gang assemblies
- Continued use of the existing admin-only `assignment_states` system

Use this core architecture:

```text
Admin assignment system
    assignment_states
    assignment_state_modules
    used only for viewport/debugging workflows

Customer working assembly
    temporary frontend state

Draft order
    browser localStorage

Submitted order
    orders
    order_items
    order_item_modules
    order_item_bom
```

Do not create a separate global customer `configurations` table.

Do not reuse `assignment_states` for orders.

---

## 2. Read the Repository First

Before implementing:

1. Read the project README.
2. Inspect the existing frontend architecture.
3. Inspect the FastAPI application structure.
4. Inspect current SQLAlchemy models and migrations.
5. Inspect the existing `assignment_states` implementation.
6. Inspect current Assembly and Assignments tabs.
7. Inspect existing product, module, finish, material, asset, and BOM models.
8. Follow existing naming, routing, validation, serialization, and testing conventions.

Do not redesign unrelated parts of the application.

---

## 3. Existing Assignment-State System

The previously used `configurations` admin system has already been replaced by:

```text
assignment_states
assignment_state_modules
```

This system must remain intact.

Assignment States are admin-only viewport presets used by the Assignments tab to determine which geometry to load.

Examples:

```text
1-Gang Switch
1-Gang Rotary Dimmer
2-Gang Switch + Dimmer
3-Gang Switch + Outlet + Dimmer
```

Assignment States are:

- persistent
- reusable
- admin-only
- used for material-assignment debugging
- not customer saved configurations
- not cart items
- not order items
- not priced
- not commercial snapshots

Do not modify their purpose as part of this task.

---

## 4. Separation of Concerns

Keep these concepts strictly separate.

### Assignment State

Determines which geometry is loaded into the admin Assignments viewport.

```text
assignment_states
assignment_state_modules
```

### Current Customer Assembly

The assembly currently being configured by the customer.

Stored in React state.

### Draft Order

A temporary collection of configured assemblies.

Stored in browser `localStorage` for the first implementation.

### Submitted Order

Commercial data persisted in the database after explicit submission.

Stored in:

```text
orders
order_items
order_item_modules
order_item_bom
```

Do not reference `assignment_state_id` from an order item.

An order item must store the customer's structured selections directly.

---

## 5. Target Customer Flow

The public configurator flow should be:

```text
Configure assembly
        ↓
Add to Order
        ↓
Configure another assembly
        ↓
Add to Order
        ↓
Review Order
        ↓
Submit Order
```

Example:

```text
2 × 1-Gang Brass Rotary Dimmer
4 × 1-Gang Steel Switch
1 × 2-Gang Brass Switch + Dimmer
```

This is one order containing three unique order items.

---

## 6. Terminology

Use the following language consistently.

### Current Assembly

The product currently visible and editable in the configurator.

### Add to Order

Copies the current structured assembly choices into the browser-local draft order.

### Draft Order

A browser-local list of unique configured assemblies and quantities.

### Order Item

One unique configured assembly multiplied by quantity.

### Submitted Order

An immutable commercial record persisted in the database.

Do not call public order items “saved configurations.”

---

## 7. Architectural Decisions

Implement the following decisions.

### Use Structured Order-Item Configuration

Store authoritative order configuration as relational columns and child rows.

Do not use one large opaque `configuration_json` blob as the primary model.

### No Global Customer Configuration Table

Do not create:

```text
configurations
```

for customer assemblies.

Do not deduplicate customer configurations globally across orders.

### Preserve Assignment States

Do not remove, rename, or repurpose:

```text
assignment_states
assignment_state_modules
```

### One Row per Unique Order Line

For:

```text
100 × identical brass dimmers
```

store:

```text
one order item
quantity = 100
```

Do not store one configuration or order-item row per physical device.

### Explicit Persistence

Do not write to the database when the customer merely:

- opens the configurator
- changes finish
- changes module
- changes gang count
- rotates the camera
- leaves the page

Persist only when the customer submits the order.

### Backend Authority

The backend must be authoritative for:

- validation
- product compatibility
- pricing
- totals
- BOM generation
- snapshot generation

Do not trust frontend prices or totals.

---

## 8. Recommended Database Model

Create:

```text
orders
order_items
order_item_modules
order_item_bom
```

Reuse existing entities where appropriate:

```text
product_families
module_types
finish_schemes
parts
assets
materials
```

Adapt exact names to the repository.

---

## 9. `orders` Table

The `orders` table represents the complete submitted customer order.

Recommended fields:

```text
order_id
order_number
idempotency_key
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
tax_amount
shipping_amount
total

notes

created_at
updated_at
submitted_at
```

Recommended constraints:

```text
order_number UNIQUE
idempotency_key UNIQUE
```

Recommended initial statuses:

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

Do not create abandoned database orders for visitors in this implementation.

---

## 10. Public Order Number

Use a public human-readable order number separate from the database primary key.

Example:

```text
LAT-ORD-000001
```

Do not expose internal database IDs in public URLs or confirmation messages.

Order-number generation must be safe under concurrent requests.

Follow the project's existing sequence or numbering convention if one exists.

---

## 11. `order_items` Table

Each order-item row represents one unique configured assembly in an order.

Recommended fields:

```text
order_item_id
order_id

product_family_id
gang_count
finish_scheme_id
quantity

configuration_version
configuration_hash

unit_price
line_total

product_code_snapshot
product_name_snapshot
finish_scheme_code_snapshot
finish_scheme_name_snapshot

created_at
updated_at
```

Foreign keys:

```text
order_id
    → orders.order_id

product_family_id
    → product_families.product_family_id

finish_scheme_id
    → finish_schemes.finish_scheme_id
```

Do not add:

```text
assignment_state_id
```

An order item must not depend on an admin Assignment State.

Recommended constraints:

```text
quantity >= 1
gang_count >= 1
unit_price >= 0
line_total >= 0
```

---

## 12. `order_item_modules` Table

Store the module selected for each physical slot.

Recommended fields:

```text
order_item_module_id
order_item_id
slot_number
module_type_id
module_code_snapshot
module_name_snapshot
created_at
updated_at
```

Foreign keys:

```text
order_item_id
    → order_items.order_item_id

module_type_id
    → module_types.module_type_id
```

Required unique constraint:

```text
UNIQUE(order_item_id, slot_number)
```

Examples follow.

### One-Gang Dimmer

```text
order_item:
gang_count = 1

module:
slot 1 → rotary_dimmer
```

### Two-Gang Switch + Dimmer

```text
order_item:
gang_count = 2

modules:
slot 1 → switch
slot 2 → rotary_dimmer
```

### Four-Gang Mixed Assembly

```text
order_item:
gang_count = 4

modules:
slot 1 → switch
slot 2 → switch
slot 3 → outlet
slot 4 → usb_c_outlet
```

This must support future module types without database schema changes.

---

## 13. `order_item_bom` Table

At submission, store an immutable BOM snapshot for every order item.

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
order_item_id
    → order_items.order_item_id
```

`part_id` may be nullable if historical rows must remain valid after a live part is archived or removed.

Example:

```text
Order item:
3 × 2-Gang Brass Switch + Dimmer
```

Possible BOM rows:

```text
2-gang plate:
quantity_per_assembly = 1
assembly_quantity = 3
total_quantity = 3

2-gang screw set:
quantity_per_assembly = 1
assembly_quantity = 3
total_quantity = 3

switch module:
quantity_per_assembly = 1
assembly_quantity = 3
total_quantity = 3

dimmer module:
quantity_per_assembly = 1
assembly_quantity = 3
total_quantity = 3
```

Historical orders must not regenerate their BOM from current product rules.

---

## 14. Optional Compact Audit Snapshot

A small optional JSON snapshot may be stored for audit or export convenience.

Example field:

```text
configuration_snapshot_json
```

Example value:

```json
{
  "schema_version": 1,
  "product_family": {
    "code": "electrical_device",
    "name": "Electrical Device"
  },
  "gang_count": 2,
  "finish_scheme": {
    "code": "brass",
    "name": "Brass"
  },
  "modules": [
    {
      "slot_number": 1,
      "code": "switch",
      "name": "Switch"
    },
    {
      "slot_number": 2,
      "code": "rotary_dimmer",
      "name": "Rotary Dimmer"
    }
  ]
}
```

This JSON must not replace the structured relational fields.

Do not store:

- GLB object trees
- Three.js object state
- camera state
- viewport controls
- temporary UI state
- material instances
- shader source
- admin assignment-state IDs

---

## 15. Configuration Version

Store a configuration schema version on each submitted order item.

Initial value:

```text
configuration_version = 1
```

Increment this only when the meaning or structure of submitted order-item selections changes incompatibly.

Do not use the version for ordinary product-data edits.

---

## 16. Configuration Hash

Generate a canonical hash for each unique structured assembly.

The hash is useful for:

- merging identical draft lines
- detecting duplicates
- diagnostics
- administrative grouping

The canonical representation should include:

```text
product family code
gang count
finish scheme code
module type code for every slot
```

It must exclude:

```text
quantity
price
timestamps
display names
frontend IDs
camera state
assignment-state data
```

Example canonical structure:

```json
{
  "product_family_code": "electrical_device",
  "gang_count": 2,
  "finish_scheme_code": "brass",
  "modules": [
    {
      "slot_number": 1,
      "module_type_code": "switch"
    },
    {
      "slot_number": 2,
      "module_type_code": "rotary_dimmer"
    }
  ]
}
```

Canonicalization rules:

1. Normalize codes consistently.
2. Sort object keys consistently.
3. Sort modules by `slot_number`.
4. Serialize deterministically.
5. Generate SHA-256.

The backend must recalculate the hash and must not trust a client-provided hash.

---

## 17. Draft Order Storage

For the initial implementation, keep the draft order in browser `localStorage`.

Recommended key:

```text
latoun_draft_order_v1
```

Suggested TypeScript structure:

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
  estimatedLineTotal: number | null;
}

interface DraftOrderModule {
  slotNumber: number;
  moduleTypeCode: string;
}
```

Draft state must survive browser refresh.

Do not save draft order items to the database.

---

## 18. Draft Schema Validation

When reading from `localStorage`:

1. Parse safely.
2. Validate the schema version.
3. Validate required fields.
4. Validate positive quantities.
5. Validate slot structure.
6. Reject malformed entries.
7. Preserve valid entries where practical.
8. Show a user-friendly warning if draft data cannot be recovered.

Do not allow malformed local data to crash the configurator.

---

## 19. Add to Order

Replace the customer-facing action:

```text
Save Configuration
```

with:

```text
Add to Order
```

When clicked:

1. Validate the current assembly locally.
2. Create the canonical customer configuration.
3. Generate the draft configuration hash.
4. Search the current draft order for the same hash.
5. If found, increase its quantity.
6. Otherwise add a new draft line.
7. Save the updated draft to `localStorage`.
8. Show a confirmation message.

Example:

```text
Added to Order

2-Gang Brass Switch + Rotary Dimmer
Quantity in order: 2
```

Adding the assembly must copy the current selections.

Later changes to the current viewport assembly must not mutate the added order line.

---

## 20. Assembly Tab Changes

The public Assembly tab should include:

```text
Product family
Gang count
Module selection for each slot
Finish
3D preview
Configuration summary
Estimated price
Add to Order
View Order
```

Remove customer-facing:

```text
Save Configuration
Saved Configurations
```

Do not remove or modify the admin `assignment_states` UI.

The public Assembly tab must not load or save Assignment States.

---

## 21. Assignment Tab Must Remain Independent

The admin Assignments tab continues to use:

```text
Assignment State
Preview Finish Scheme
```

Assignment State determines geometry.

Finish Scheme determines semantic material resolution.

The order implementation must not alter this behavior.

Do not make the public order system depend on the currently selected Assignment State.

---

## 22. Order Review UI

Add a customer-facing Order view.

Suggested route:

```text
/order
```

Display one row or card for each unique draft-order item.

Required information:

```text
assembly type
gang count
finish
slot modules
quantity
estimated unit price
estimated line total
```

Required actions:

```text
increase quantity
decrease quantity
enter quantity
edit assembly
remove item
clear order
submit order
```

Example table:

| Assembly | Finish | Modules | Quantity | Unit Price | Total |
|---|---|---|---:|---:|---:|
| 1-Gang | Brass | Rotary Dimmer | 2 | $285.00 | $570.00 |
| 2-Gang | Steel | Switch + Outlet | 1 | $420.00 | $420.00 |

Frontend prices are estimates only.

Clearly label them as estimated until the backend confirms the order.

---

## 23. Editing a Draft Order Item

When the user selects `Edit`:

1. Load that draft line into the public Assembly tab.
2. Store an editing context such as:

```text
editingDraftOrderItemId
```

3. Change the primary action to:

```text
Update Order Item
```

4. On update, recalculate the canonical configuration and hash.
5. If the updated configuration matches another draft line, merge quantities.
6. Otherwise replace the edited line.
7. Preserve the quantity unless the user changes it explicitly.
8. Return to the Order page or show clear confirmation.

Do not use an Assignment State to edit an order item.

---

## 24. Removing and Clearing Draft Items

Support:

```text
Remove Item
Clear Order
```

Recommended behavior:

- Decreasing quantity from 1 should not silently produce zero.
- Confirm removal or provide an explicit remove action.
- Confirm `Clear Order`.
- Persist every successful change to `localStorage`.

---

## 25. Submit Order Form

Collect at least:

```text
customer name
customer email
customer phone, optional
shipping address
customer notes, optional
```

The initial implementation may use a single US shipping address.

Recommended fields:

```text
address line 1
address line 2
city
state
postal code
country
```

Do not implement payment processing unless already present and explicitly in scope.

---

## 26. Submit Order API

Add an endpoint such as:

```text
POST /api/orders
```

Example request:

```json
{
  "idempotency_key": "03f5e58e-668c-4bb5-a6e6-8d150e26c6ce",
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
      "gang_count": 2,
      "finish_scheme_code": "steel",
      "quantity": 1,
      "modules": [
        {
          "slot_number": 1,
          "module_type_code": "switch"
        },
        {
          "slot_number": 2,
          "module_type_code": "outlet"
        }
      ]
    }
  ]
}
```

The request must not contain authoritative:

```text
unit_price
line_total
subtotal
tax
shipping
total
BOM
```

The backend calculates those values.

---

## 27. Backend Submission Workflow

Create the complete submitted order in one transaction.

Required sequence:

```text
1. Validate request structure.
2. Validate customer data.
3. Validate shipping data.
4. Require at least one item.
5. Validate each product family.
6. Validate gang count.
7. Validate each finish scheme.
8. Validate every module and slot.
9. Validate compatibility.
10. Validate semantic material resolution.
11. Resolve current price.
12. Resolve current BOM.
13. Generate canonical configuration and hash.
14. Generate immutable display/code snapshots.
15. Create order row.
16. Create order-item rows.
17. Create order-item-module rows.
18. Create order-item-BOM rows.
19. Calculate order totals.
20. Commit transaction.
```

If any step fails:

```text
roll back the entire transaction
```

Do not create partial orders.

---

## 28. Backend Validation Rules

Validate each submitted order item.

### Product

```text
product family exists
product family is active
gang count is supported
```

### Finish

```text
finish scheme exists
finish scheme is active
finish scheme is customer-visible
```

Do not accept the internal `init` finish scheme as a customer choice.

### Slots

```text
slot numbers start at 1
slot numbers are unique
slot numbers do not exceed gang count
every required slot is populated
no unexpected additional slot exists
```

For a fully populated plate:

```text
module row count = gang count
```

### Modules

```text
module type exists
module type is active
module is customer-visible where applicable
module is compatible with product family
module is compatible with its slot
module supports the selected gang context
```

### Quantity

```text
quantity >= 1
quantity <= configured maximum
```

### Materials

Verify that all semantic material bindings required by the resolved assembly are resolvable using:

```text
selected finish scheme
        ↓
finish assignment lookup
        ↓
init fallback
        ↓
error if unresolved
```

Reject order submission if required product material assignments are unresolved.

Do not silently order a magenta missing-material assembly.

### Pricing and BOM

```text
price resolves successfully
BOM resolves successfully
all required parts exist or are valid for ordering
```

---

## 29. Pricing Service

Implement or reuse a dedicated backend pricing service.

Suggested interface:

```python
resolve_unit_price(configuration) -> Money
```

Do not place pricing logic directly in:

- React components
- API endpoint handlers
- SQLAlchemy models
- Three.js code

At submission:

```text
unit_price = backend resolved price
line_total = unit_price × quantity
```

Use decimal-safe money types.

Do not use binary floating-point for persisted currency calculations.

---

## 30. Frontend Price Estimates

The frontend may display estimated pricing.

It may obtain estimates through:

```text
client-side cached catalog data
```

or:

```text
backend pricing preview endpoint
```

The backend submission result remains authoritative.

If the submitted price differs from the displayed estimate, return the final totals clearly.

For a later implementation, consider requiring customer confirmation when the difference exceeds a threshold.

---

## 31. BOM Resolver

Implement or reuse a backend BOM resolver.

Suggested input:

```text
product family
gang count
finish scheme
slot modules
quantity
```

Suggested output:

```text
part ID
part code
part name
quantity per assembly
total quantity
unit cost, optional
```

The BOM should resolve product/manufacturing parts, not rendering details.

Possible parts:

```text
plate
plate screws
switch module
dimmer module
outlet module
actuator
insulator
electrical core
packaging
```

Do not use GLB paths as BOM part identifiers.

---

## 32. Materials and Order Data

The order stores customer-facing finish choices:

```text
finish_scheme_id
finish_scheme_code_snapshot
finish_scheme_name_snapshot
```

Do not store the full Three.js material graph or every material assignment on the order item.

The material system remains:

```text
finish scheme + semantic binding
        ↓
render material
```

Material assignment validation is required before submission, but render-material instances are not core commercial order data.

The BOM should contain the manufacturing identity required to produce the chosen finish where applicable.

---

## 33. Historical Snapshots

Submitted orders must remain understandable if live data changes later.

Store both:

```text
foreign key
snapshot code
snapshot display name
```

Examples:

```text
product_family_id = 1
product_code_snapshot = "electrical_device"
product_name_snapshot = "Electrical Device"
```

```text
finish_scheme_id = 4
finish_scheme_code_snapshot = "brass"
finish_scheme_name_snapshot = "Brass"
```

```text
module_type_id = 2
module_code_snapshot = "rotary_dimmer"
module_name_snapshot = "Rotary Dimmer"
```

Historical UI should display snapshots, not current live names.

Do not automatically update order snapshots when catalog names change.

---

## 34. Order Immutability

After submission, treat these as immutable:

```text
product choices
gang count
slot modules
finish
quantity
unit price
line total
BOM snapshot
configuration hash
configuration version
```

For the first implementation, do not support editing submitted order contents.

Administrative status changes are permitted.

Cancellation should update status:

```text
cancelled
```

Do not delete submitted commercial orders from the normal UI.

---

## 35. Idempotency

Prevent duplicate orders caused by:

- double-clicking Submit
- browser retries
- network timeouts
- page refreshes
- repeated API requests

Frontend:

1. Generate a UUID before submission.
2. Store it in submission state.
3. Send it as `idempotency_key`.
4. Disable Submit while the request is in progress.

Backend:

1. Require or accept the idempotency key according to repository conventions.
2. Add a unique database constraint.
3. If the key already exists, return the existing order.
4. Do not create a second order.

The idempotency key must not be reused for a newly edited order.

---

## 36. Order Confirmation

After successful submission:

1. Store the returned public order number.
2. Clear the submitted draft from `localStorage`.
3. Clear edit state.
4. Navigate to an order-confirmation page.
5. Show final backend-calculated totals.
6. Show submitted items.
7. Prevent accidental resubmission.

Suggested route:

```text
/order-confirmation/{orderNumber}
```

Example:

```text
Thank you.

Your order number:
LAT-ORD-000124
```

Do not expose the internal primary key.

---

## 37. Failed Submission

If submission fails:

- do not clear `localStorage`
- preserve all draft items
- preserve entered customer information where safe
- re-enable Submit
- display a clear error
- show item-specific errors where available

Examples:

```text
The Brass finish is no longer available.

Slot 2 contains a module that is not supported by this plate.

Material assignment `brass + actuator_metal` is missing.

We could not calculate the BOM. The order was not submitted.

Your draft order remains saved in this browser.
```

---

## 38. Admin Order List

Add a basic internal order-management view if the application already supports admin routes.

Suggested route:

```text
/admin/orders
```

List columns:

```text
order number
submitted date
customer
status
unique item count
total unit count
order total
```

Distinguish:

```text
unique item count
```

from:

```text
total physical unit count
```

Example:

```text
2 unique items
7 physical assemblies
```

---

## 39. Admin Order Detail

Display:

```text
order number
status
customer information
shipping address
submitted date
currency
subtotal
tax
shipping
total
notes
```

For every order item show:

```text
product snapshot
gang count
finish snapshot
slot modules
quantity
unit price
line total
configuration hash
configuration version
BOM snapshot
```

Do not display or require an Assignment State.

---

## 40. Order Status Updates

Allow internal status changes if consistent with the existing admin system.

Suggested transition set:

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

Centralize transition rules.

Do not let arbitrary frontend strings update status.

Record `updated_at`.

A future audit log may record status history, but it is not required unless already supported.

---

## 41. Recommended SQLAlchemy Models

Adapt names and types to project conventions.

```python
class Order(Base):
    __tablename__ = "orders"

    order_id = Column(Integer, primary_key=True)

    order_number = Column(
        String,
        nullable=False,
        unique=True,
        index=True,
    )

    idempotency_key = Column(
        String,
        nullable=False,
        unique=True,
        index=True,
    )

    status = Column(String, nullable=False, default="submitted")

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
    tax_amount = Column(Numeric(12, 2), nullable=False)
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
        index=True,
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

    configuration_version = Column(Integer, nullable=False, default=1)
    configuration_hash = Column(String, nullable=False, index=True)

    unit_price = Column(Numeric(12, 2), nullable=False)
    line_total = Column(Numeric(12, 2), nullable=False)

    product_code_snapshot = Column(String, nullable=False)
    product_name_snapshot = Column(String, nullable=False)

    finish_scheme_code_snapshot = Column(String, nullable=False)
    finish_scheme_name_snapshot = Column(String, nullable=False)

    configuration_snapshot_json = Column(Text, nullable=True)

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
        index=True,
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
    updated_at = Column(DateTime, nullable=False)

    __table_args__ = (
        UniqueConstraint(
            "order_item_id",
            "slot_number",
            name="uq_order_item_module_slot",
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
        index=True,
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

Use ORM relationships and cascading behavior consistent with the codebase.

---

## 42. API Response

Example successful response:

```json
{
  "order_number": "LAT-ORD-000124",
  "status": "submitted",
  "currency": "USD",
  "subtotal": "990.00",
  "tax_amount": "0.00",
  "shipping_amount": "0.00",
  "total": "990.00",
  "submitted_at": "2026-07-22T20:15:00Z",
  "items": [
    {
      "product_name": "Electrical Device",
      "gang_count": 1,
      "finish_name": "Brass",
      "quantity": 2,
      "unit_price": "285.00",
      "line_total": "570.00",
      "modules": [
        {
          "slot_number": 1,
          "module_name": "Rotary Dimmer"
        }
      ]
    },
    {
      "product_name": "Electrical Device",
      "gang_count": 2,
      "finish_name": "Steel",
      "quantity": 1,
      "unit_price": "420.00",
      "line_total": "420.00",
      "modules": [
        {
          "slot_number": 1,
          "module_name": "Switch"
        },
        {
          "slot_number": 2,
          "module_name": "Outlet"
        }
      ]
    }
  ]
}
```

Return decimal values consistently according to existing API conventions.

---

## 43. Frontend Services

Create dedicated modules rather than putting all logic into page components.

Suggested services:

```text
currentAssemblyService
draftOrderService
configurationCanonicalizer
orderApiService
orderEditService
```

### `draftOrderService`

Responsibilities:

```text
load draft from localStorage
validate draft
save draft
add item
merge identical item
update item
remove item
change quantity
clear order
calculate estimated totals
```

### `configurationCanonicalizer`

Responsibilities:

```text
normalize product code
normalize finish code
sort modules by slot
generate deterministic representation
generate hash
```

### `orderApiService`

Responsibilities:

```text
submit order
load order confirmation
load admin order list, if in scope
load admin order details, if in scope
update status, if in scope
normalize API errors
```

---

## 44. Backend Services

Keep route handlers thin.

Suggested services:

```text
OrderSubmissionService
OrderValidationService
PricingService
BomResolver
ConfigurationCanonicalizer
OrderNumberService
MaterialResolutionValidator
```

Suggested submission entry point:

```python
submit_order(command: SubmitOrderCommand) -> SubmittedOrder
```

The service should own the database transaction.

---

## 45. Migrations

Create migrations for:

```text
orders
order_items
order_item_modules
order_item_bom
```

Do not modify or delete:

```text
assignment_states
assignment_state_modules
```

Do not recreate the old `configurations` table.

If an unused old `configurations` table still exists physically, leave it alone unless the user has explicitly requested database cleanup.

Do not migrate old configuration rows into orders.

Enable SQLite foreign-key enforcement.

Add indexes for:

```text
orders.order_number
orders.idempotency_key
orders.status
orders.submitted_at
order_items.order_id
order_items.configuration_hash
order_item_modules.order_item_id
order_item_bom.order_item_id
```

---

## 46. Existing Configuration Code Cleanup

Remove only public or obsolete references that still treat saved configurations as a customer feature.

Remove or rename:

```text
Save Configuration
Saved Configurations
configuration cart behavior
customer configuration endpoints
```

Do not remove references related to:

```text
Assignment States
Assignments tab
admin viewport presets
assignment-state modules
```

Before deleting code, distinguish whether it belongs to:

```text
old customer configuration prototype
```

or:

```text
current assignment-state admin system
```

---

## 47. Tests — Backend

Implement tests for at least:

```text
create one-item order
create multi-item order
create one-gang item
create two-gang item
create four-gang item
create multiple quantities of one item
reject empty order
reject zero quantity
reject negative quantity
reject unsupported gang count
reject invalid product family
reject inactive product family
reject invalid finish
reject inactive finish
reject non-customer-visible finish
reject init finish as customer selection
reject invalid module type
reject inactive module
reject duplicate slot
reject missing slot
reject slot above gang count
reject incompatible module
reject unresolved semantic material binding
reject unresolved price
reject unresolved BOM
calculate unit price
calculate line total
calculate subtotal
calculate final total
create product snapshots
create finish snapshots
create module snapshots
create BOM snapshots
generate deterministic configuration hash
rollback complete transaction on failure
return existing order for repeated idempotency key
generate unique public order number
```

Also test that order creation does not read from or depend on `assignment_states`.

---

## 48. Tests — Frontend

Implement tests for:

```text
Add to Order creates a draft item
identical configuration increases quantity
different finish creates a separate item
different module creates a separate item
different slot order normalizes correctly
different gang count creates a separate item
draft survives reload
malformed localStorage is handled
quantity can increase
quantity can decrease
item can be removed
order can be cleared
edit loads item into Assembly tab
edit updates item
edit merges with identical existing item
failed submission preserves draft
successful submission clears draft
submit button disables during request
idempotency key is reused during one retry sequence
new edited submission gets a new idempotency key
confirmation shows public order number
```

Ensure public-order tests do not use Assignment States.

---

## 49. Manual Acceptance Scenarios

Test manually:

### Scenario A

```text
Configure 1-Gang Brass Rotary Dimmer
Add to Order
Add the identical assembly again
```

Expected:

```text
one draft line
quantity = 2
```

### Scenario B

```text
Configure 1-Gang Brass Switch
Add to Order

Configure 1-Gang Steel Switch
Add to Order
```

Expected:

```text
two draft lines
```

### Scenario C

```text
Configure 2-Gang Brass:
slot 1 = switch
slot 2 = dimmer
```

Expected:

```text
one order item
two order_item_modules rows
```

### Scenario D

```text
Configure 4-Gang Steel:
slot 1 = switch
slot 2 = switch
slot 3 = outlet
slot 4 = USB-C
quantity = 5
```

Expected:

```text
one order item
quantity = 5
four module rows
BOM quantities multiplied by 5
```

### Scenario E

```text
Open Assignments tab
Select an Assignment State
Change preview finish
```

Expected:

```text
admin assignment workflow behaves exactly as before
no order rows are created
```

### Scenario F

```text
Submit an order
simulate network timeout
retry with the same idempotency key
```

Expected:

```text
one database order
same order returned
```

---

## 50. Non-Goals

Do not implement unless already present and explicitly required:

```text
payment processing
customer accounts
customer saved configurations
global configuration deduplication
database-backed abandoned carts
cross-device cart sync
discount codes
inventory reservation
tax-provider integration
shipping-provider integration
returns
refunds
post-submission item editing
manufacturing scheduling
assignment-state integration with public orders
one database row per physical unit
```

Design service boundaries so these can be added later.

---

## 51. Acceptance Criteria

The implementation is complete when:

1. The customer Assembly tab uses `Add to Order`.
2. Customer-facing `Save Configuration` is removed.
3. Customer-facing `Saved Configurations` is removed.
4. Draft order state is stored in browser `localStorage`.
5. Opening or editing the configurator creates no order database rows.
6. One draft supports multiple different assemblies.
7. Identical assemblies merge by quantity.
8. Different structured assemblies remain separate lines.
9. Draft items support 1–4 gangs.
10. Each slot stores its own module selection.
11. The Order page supports quantity editing.
12. The Order page supports item removal.
13. The Order page supports assembly editing.
14. Submitted orders are stored in `orders`.
15. Structured assembly choices are stored in `order_items`.
16. Slot choices are stored in `order_item_modules`.
17. There is no global customer `configurations` table.
18. The authoritative order configuration is not stored only as JSON.
19. One order item represents one unique assembly multiplied by quantity.
20. Backend validation checks all submitted choices.
21. Backend pricing is authoritative.
22. Backend BOM resolution is authoritative.
23. Price snapshots are stored.
24. Product, finish, and module snapshots are stored.
25. BOM snapshots are stored in `order_item_bom`.
26. Submission is transactional.
27. Failed submission creates no partial order.
28. Duplicate submission is prevented through idempotency.
29. Successful submission clears the draft.
30. Failed submission preserves the draft.
31. Confirmation displays a public order number.
32. Historical order display uses snapshot fields.
33. The order system does not depend on Assignment States.
34. `assignment_states` and `assignment_state_modules` remain intact.
35. The Assignments tab continues using Assignment States for viewport geometry.
36. No order rows are created by admin assignment debugging.
37. No Assignment State is created by customer ordering.
38. Existing material-assignment resolution continues to work.
39. Missing required material assignments block order submission.
40. Tests cover one-, two-, three-, and four-gang assemblies.

---

## 52. Guiding Principles

```text
Assignment States are admin viewport/debug presets.

Customer assemblies are temporary frontend state until added to an order.

Draft orders live in the browser.

Submitted commercial intent lives in the database.

Orders never depend on Assignment States.

One order item represents one unique structured assembly times quantity.

Modules are stored per slot.

Do not create a global customer configuration registry.

Do not store one row per physical device.

Do not trust frontend prices, totals, validation, or hashes.

Preserve historical product, finish, module, price, and BOM snapshots.

Keep Three.js rendering state separate from commercial order data.

Build the relational model for 1–4 gangs now.

Do not disturb the existing assignment-state workflow.
```
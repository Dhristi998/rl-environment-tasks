# Reconcile messy order and return exports

Finance needs net units sold per product. The exports in `/app/data/` are
messy: the same order can appear more than once, product codes have stray
spaces and mixed case, and some returns refer to orders that do not exist.

Create an executable `/app/reconcile` that is used like this:

    /app/reconcile <input_dir> <output_json>

`<input_dir>` contains `orders.csv` and `returns.csv` in the same format as the
files in `/app/data/`. Write a JSON object to `<output_json>` that maps each
product code (upper-case, no surrounding spaces) to its net units: units
ordered minus units returned.

Business rules:
- If an `order_id` appears more than once in `orders.csv`, only its **last** row counts.
- A return only counts if its `order_id` exists in the orders, and it applies to that order's product.
- A return can never take an order below zero units; extra returned units are ignored.
- Leave out products whose net units are zero.

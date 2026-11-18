#!/bin/bash
APP_DIR="${APP_DIR:-/app}"
cat > "$APP_DIR/reconcile" <<'PY'
#!/usr/bin/env python3
import csv, json, os, sys
from collections import defaultdict


def main(input_dir, output_json):
    orders = {}
    with open(os.path.join(input_dir, "orders.csv"), newline="") as f:
        for row in csv.DictReader(f):
            orders[row["order_id"].strip()] = [row["sku"].strip().upper(), int(row["units"])]
    with open(os.path.join(input_dir, "returns.csv"), newline="") as f:
        for row in csv.DictReader(f):
            oid = row["order_id"].strip()
            if oid in orders:
                orders[oid][1] = max(0, orders[oid][1] - int(row["units"]))
    net = defaultdict(int)
    for sku, units in orders.values():
        net[sku] += units
    with open(output_json, "w") as f:
        json.dump({k: v for k, v in sorted(net.items()) if v != 0}, f, indent=2)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
PY
chmod +x "$APP_DIR/reconcile"

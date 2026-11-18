#!/bin/bash
# Reference solution (oracle): Python port of the COBOL control-break report.
APP_DIR="${APP_DIR:-/app}"
cat > "$APP_DIR/salesrpt.py" <<'PY'
def edit(cents, width):
    # COBOL edited picture Z..,ZZ9.99: zero-suppressed, comma-grouped, right-aligned
    return f"{cents // 100:,}.{cents % 100:02d}".rjust(width)


def main():
    lines = []
    prev, reg_tot, reg_cnt, grand = None, 0, 0, 0

    def flush():
        lines.append(prev.ljust(5) + "  " + str(reg_cnt).rjust(5) + "  " + edit(reg_tot, 14))

    with open("sales.dat") as f:
        for raw in f:
            raw = raw.rstrip("\n").rstrip("\r")
            if not raw:
                continue
            region, amount = raw[:5].ljust(5), int(raw[5:14])
            if prev is not None and region != prev:
                flush()
                reg_tot, reg_cnt = 0, 0
            prev = region
            reg_tot += amount
            reg_cnt += 1
            grand += amount
    if prev is not None:
        flush()
    lines.append("GRAND TOTAL".ljust(14) + edit(grand, 17))
    print("\n".join(lines))


if __name__ == "__main__":
    main()
PY

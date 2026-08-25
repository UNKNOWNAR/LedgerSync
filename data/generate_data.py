"""
Synthetic data generator for the transaction reconciliation tool.

Produces two CSV files simulating a real-world reconciliation scenario:
  - payment_gateway.csv  (80 records)
  - bank_settlement.csv  (80 records, some modified)

Scenario breakdown
------------------
 50  clean matches          — identical across both files
 10  settlement delay       — bank date is 1–3 days later
  8  amount variance        — bank amount differs by ~2% (gateway fee)
  5  merchant name variants — slight misspelling / reformatting in bank file
  7  true exceptions        — appear in ONLY ONE of the two files

Usage
-----
  python data/generate_data.py               # writes to data/
  python data/generate_data.py --out /tmp/   # custom output dir
"""

from __future__ import annotations

import argparse
import csv
import datetime
import random
import string
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Seed for reproducibility
# ---------------------------------------------------------------------------
SEED = 42
random.seed(SEED)

# ---------------------------------------------------------------------------
# Realistic Indian merchant names
# ---------------------------------------------------------------------------
MERCHANT_NAMES = [
    "Reliance Fresh",
    "BigBasket",
    "DMart Ready",
    "Swiggy Food Delivery",
    "Zomato",
    "Paytm Mall",
    "Amazon India",
    "Flipkart",
    "Myntra Fashion",
    "Nykaa Beauty",
    "Mamaearth",
    "Boat Lifestyle",
    "Tata CLiQ",
    "Ajio Fashion",
    "JioMart",
    "Healthkart",
    "PharmEasy",
    "1mg Pharmacy",
    "Lenskart",
    "FabIndia",
    "Manyavar",
    "Tanishq Jewellery",
    "Kalyan Jewellers",
    "Vijay Sales",
    "Croma Electronics",
    "Ola Cabs",
    "Uber India",
    "Rapido Bike Taxi",
    "IRCTC Rail",
    "MakeMyTrip",
    "Goibibo Hotels",
    "OYO Rooms",
    "Cleartrip",
    "EaseMyTrip",
    "IndiGo Airlines",
    "Air India",
    "Vistara Airlines",
    "Blinkit Grocery",
    "Zepto Delivery",
    "Dunzo Quick",
    "Urban Company",
    "BookMyShow",
    "PVR Cinemas",
    "INOX Movies",
    "Byju's Learning",
    "Unacademy",
    "Vedantu Classes",
    "Upgrad Education",
    "Policy Bazaar",
    "HDFC Life Insurance",
]

# Merchant name variants (misspellings / reformatting for the 5 variant cases)
MERCHANT_VARIANTS = {
    "Swiggy Food Delivery": "Swiggy Fud Delivery",
    "Kalyan Jewellers": "Kalyan Jwellers",
    "IRCTC Rail": "IRCTC Rail Booking",
    "PVR Cinemas": "PVR Cinema",
    "Blinkit Grocery": "Blinkit Groshery",
}

# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------


def _random_ref() -> str:
    """Generate a realistic reference number."""
    prefix = random.choice(["REF", "TXN", "PAY", "NEFT", "IMPS", "UPI"])
    digits = "".join(random.choices(string.digits, k=12))
    return f"{prefix}{digits}"


def _random_amount() -> float:
    """Generate a realistic INR transaction amount."""
    # Weighted: small (₹100–₹999), medium (₹1000–₹9999), large (₹10000–₹50000)
    tier = random.choices([1, 2, 3], weights=[40, 45, 15])[0]
    if tier == 1:
        return round(random.uniform(100, 999), 2)
    elif tier == 2:
        return round(random.uniform(1000, 9999), 2)
    else:
        return round(random.uniform(10000, 50000), 2)


def _random_date(start: datetime.date, end: datetime.date) -> datetime.date:
    delta = (end - start).days
    return start + datetime.timedelta(days=random.randint(0, delta))


def _tx_id(prefix: str, n: int) -> str:
    return f"{prefix}{n:05d}"


# ---------------------------------------------------------------------------
# Data generation
# ---------------------------------------------------------------------------


def generate_datasets(output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    gw_rows: list[dict] = []
    bank_rows: list[dict] = []

    date_start = datetime.date(2026, 1, 1)
    date_end = datetime.date(2026, 8, 15)

    merchants = MERCHANT_NAMES.copy()
    random.shuffle(merchants)

    ref_counter = 0

    # -----------------------------------------------------------------------
    # Group A — 50 clean matches
    # -----------------------------------------------------------------------
    for i in range(1, 51):
        ref_counter += 1
        ref = _random_ref()
        amount = _random_amount()
        date = _random_date(date_start, date_end)
        merchant = merchants[(i - 1) % len(merchants)]
        gw_id = _tx_id("GW", ref_counter)
        bank_id = _tx_id("BK", ref_counter)

        row = {
            "transaction_id": gw_id,
            "amount": amount,
            "date": date.isoformat(),
            "merchant_name": merchant,
            "reference_number": ref,
        }
        gw_rows.append(row)
        bank_rows.append({**row, "transaction_id": bank_id})

    # -----------------------------------------------------------------------
    # Group B — 10 settlement delay (bank date = gw date + 1..3 days)
    # -----------------------------------------------------------------------
    for i in range(51, 61):
        ref_counter += 1
        ref = _random_ref()
        amount = _random_amount()
        gw_date = _random_date(date_start, date_end - datetime.timedelta(days=3))
        bank_date = gw_date + datetime.timedelta(days=random.randint(1, 3))
        merchant = merchants[(i - 1) % len(merchants)]
        gw_id = _tx_id("GW", ref_counter)
        bank_id = _tx_id("BK", ref_counter)

        gw_rows.append({
            "transaction_id": gw_id,
            "amount": amount,
            "date": gw_date.isoformat(),
            "merchant_name": merchant,
            "reference_number": ref,
        })
        bank_rows.append({
            "transaction_id": bank_id,
            "amount": amount,
            "date": bank_date.isoformat(),
            "merchant_name": merchant,
            "reference_number": ref,
        })

    # -----------------------------------------------------------------------
    # Group C — 8 amount variance (~2% gateway fee deducted by bank)
    # -----------------------------------------------------------------------
    for i in range(61, 69):
        ref_counter += 1
        ref = _random_ref()
        gw_amount = _random_amount()
        # Bank receives ~98% of the gateway amount (2% fee range: 1.5%–2.5%)
        fee_pct = round(random.uniform(1.5, 2.5), 2)
        bank_amount = round(gw_amount * (1 - fee_pct / 100), 2)
        date = _random_date(date_start, date_end)
        merchant = merchants[(i - 1) % len(merchants)]
        gw_id = _tx_id("GW", ref_counter)
        bank_id = _tx_id("BK", ref_counter)

        gw_rows.append({
            "transaction_id": gw_id,
            "amount": gw_amount,
            "date": date.isoformat(),
            "merchant_name": merchant,
            "reference_number": ref,
        })
        bank_rows.append({
            "transaction_id": bank_id,
            "amount": bank_amount,
            "date": date.isoformat(),
            "merchant_name": merchant,
            "reference_number": ref,
        })

    # -----------------------------------------------------------------------
    # Group D — 5 merchant name variants
    # -----------------------------------------------------------------------
    variant_merchants = list(MERCHANT_VARIANTS.keys())
    for i, gw_merchant in enumerate(variant_merchants):
        ref_counter += 1
        ref = _random_ref()
        amount = _random_amount()
        date = _random_date(date_start, date_end)
        bank_merchant = MERCHANT_VARIANTS[gw_merchant]
        gw_id = _tx_id("GW", ref_counter)
        bank_id = _tx_id("BK", ref_counter)

        gw_rows.append({
            "transaction_id": gw_id,
            "amount": amount,
            "date": date.isoformat(),
            "merchant_name": gw_merchant,
            "reference_number": ref,
        })
        bank_rows.append({
            "transaction_id": bank_id,
            "amount": amount,
            "date": date.isoformat(),
            "merchant_name": bank_merchant,
            "reference_number": ref,
        })

    # -----------------------------------------------------------------------
    # Group E — 7 true exceptions (4 gateway-only, 3 bank-only)
    # -----------------------------------------------------------------------
    for i in range(1, 5):   # 4 gateway-only
        ref_counter += 1
        ref = _random_ref()
        amount = _random_amount()
        date = _random_date(date_start, date_end)
        merchant = merchants[(ref_counter - 1) % len(merchants)]
        gw_id = _tx_id("GW", ref_counter)

        gw_rows.append({
            "transaction_id": gw_id,
            "amount": amount,
            "date": date.isoformat(),
            "merchant_name": merchant,
            "reference_number": ref,
        })
        # Not added to bank_rows → true exception

    for i in range(1, 4):   # 3 bank-only
        ref_counter += 1
        ref = _random_ref()
        amount = _random_amount()
        date = _random_date(date_start, date_end)
        merchant = merchants[(ref_counter - 1) % len(merchants)]
        bank_id = _tx_id("BK", ref_counter)

        bank_rows.append({
            "transaction_id": bank_id,
            "amount": amount,
            "date": date.isoformat(),
            "merchant_name": merchant,
            "reference_number": ref,
        })
        # Not added to gw_rows → true exception

    # -----------------------------------------------------------------------
    # Shuffle both files independently so order doesn't hint at matches
    # -----------------------------------------------------------------------
    random.shuffle(gw_rows)
    random.shuffle(bank_rows)

    # -----------------------------------------------------------------------
    # Write CSVs
    # -----------------------------------------------------------------------
    _write_csv(output_dir / "payment_gateway.csv", gw_rows)
    _write_csv(output_dir / "bank_settlement.csv", bank_rows)

    # Summary
    print(f"[OK] Generated payment_gateway.csv  -> {len(gw_rows)} rows")
    print(f"[OK] Generated bank_settlement.csv  -> {len(bank_rows)} rows")
    print(f"\nBreakdown:")
    print(f"  50 clean matches")
    print(f"  10 settlement delay (1-3 day bank lag)")
    print(f"   8 amount variance (~2% gateway fee)")
    print(f"   5 merchant name variants")
    print(f"   7 true exceptions (4 gateway-only, 3 bank-only)")
    print(f"\nFiles written to: {output_dir.resolve()}")


def _write_csv(path: Path, rows: list[dict]) -> None:
    fieldnames = ["transaction_id", "amount", "date", "merchant_name", "reference_number"]
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate synthetic reconciliation test data."
    )
    parser.add_argument(
        "--out",
        default=str(Path(__file__).parent),
        help="Output directory (default: same directory as this script)",
    )
    args = parser.parse_args()
    generate_datasets(Path(args.out))

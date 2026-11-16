import csv
import io
import re
from datetime import datetime
from zoneinfo import ZoneInfo

IST = ZoneInfo("Asia/Kolkata")


def extract_spot_price(text: str) -> float | None:
    """Extracts the numeric spot price after 'NIFTY' and returns it as a float."""
    match = re.search(r"NIFTY\s+([\d,]+(?:\.\d+)?)", text, re.IGNORECASE)
    if not match:
        return None

    # Remove commas (e.g., '25,291.10' -> '25291.10') and convert to float
    return float(match.group(1).replace(",", ""))


def get_days_to_expiry(expiry_str: str, now: datetime | None = None) -> float:
    """
    Calculates exact fractional days remaining until NSE market close (3:30 PM IST)
    on the given expiry date (format: 'DD-Mon-YYYY', e.g., '17-Nov-2026').
    """
    expiry_date = datetime.strptime(expiry_str.strip(), "%d-%b-%Y")
    expiry_dt = expiry_date.replace(
        hour=15, minute=30, second=0, microsecond=0, tzinfo=IST
    )

    current_dt = now.astimezone(IST) if now else datetime.now(IST)

    remaining_seconds = (expiry_dt - current_dt).total_seconds()
    return max(remaining_seconds / 86400.0, 0.0)


def parse_number(value: str):
    """Convert numeric strings to int/float and empty strings to None."""
    val = value.strip().replace(",", "")
    if not val or val == "-":
        return None
    try:
        return int(val) if "." not in val else float(val)
    except ValueError:
        return val


def option_chain_csv_to_json(csv_source: str) -> list[dict]:
    """
    Converts an NSE-style Option Chain CSV string into a list of dicts,
    filtering out any rows that contain '-' on either the CALLS or PUTS side.
    """
    f = io.StringIO(csv_source.strip())

    with f:
        reader = csv.reader(f)

        # Skip the first group-header row ("CALLS,NO TEXT,PUTS")
        next(reader, None)

        # Read the actual column headers
        headers = next(reader, None)
        if not headers:
            return []

        # Clean header names to snake_case for JSON keys
        clean_headers = [h.strip().lower().replace(" ", "_") for h in headers]

        # Column slice indices based on the 23-column layout:
        # [0]: NO TEXT | [1:11]: CALLS | [11]: STRIKE | [12:22]: PUTS | [22]: NO TEXT
        call_keys = clean_headers[1:11]
        put_keys = clean_headers[12:22]

        records = []
        for row in reader:
            if not row or len(row) < 22:
                continue

            call_values = row[1:11]
            put_values = row[12:22]

            # Skip row if '-' appears anywhere in CALLS or PUTS
            if any(v.strip() == "-" for v in call_values + put_values):
                continue

            calls_data = {
                key: parse_number(val) for key, val in zip(call_keys, call_values)
            }
            puts_data = {
                key: parse_number(val) for key, val in zip(put_keys, put_values)
            }

            records.append(
                {
                    "strike": parse_number(row[11]),
                    "calls": calls_data,
                    "puts": puts_data,
                }
            )

    return records


option_chain_csv_js = """id => {
  let csv = [];

  let _id = "#" + id;
  let rows = document.querySelectorAll(_id + " tr");

  if (rows && rows.length > 0) {
    for (let i = 0; i < rows.length; i++) {
      let row = [],
        cols = rows[i].querySelectorAll("td, th");

      for (let j = 0; j < cols.length; j++) {
        row.push(cols[j].innerText.replace(/[,\\r\\n]/g, ""));
      }
      csv.push(row.join(","));
    }
  }

  return csv.join("\\n")
}
"""

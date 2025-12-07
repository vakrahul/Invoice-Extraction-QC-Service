import pdfplumber
import re
from typing import Dict, Any, Tuple
from langdetect import detect

from .layout_classifier import predict_table_area
from .utils import parse_float_universal, parse_date_universal


# ------------------------------------------------
# Language Detection
# ------------------------------------------------
def get_language_code(text: str) -> str:
    try:
        return detect(text).upper()
    except:
        return "EN"


# ------------------------------------------------
# Seller / Buyer (English invoices)
# ------------------------------------------------
def extract_party_blocks(text: str):
    """
    Robust English invoice party extractor.
    Never returns placeholder strings.
    """
    lines = [l.strip() for l in text.split("\n") if l.strip()]

    seller_lines = []
    buyer_lines = []

    # SELLER: top block until BILL TO / INVOICE
    for line in lines:
        if re.search(r"(bill to|invoice number|invoice #|date)", line, re.I):
            break
        if len(line) > 4 and not re.search(r"(page|\d{2}/\d{2}/\d{4})", line):
            seller_lines.append(line)

    # BUYER
    for i, line in enumerate(lines):
        if re.search(r"bill to", line, re.I):
            buyer_lines = lines[i + 1:i + 5]
            break

    seller = ", ".join(seller_lines[:3]) if seller_lines else None
    buyer = ", ".join(buyer_lines) if buyer_lines else None

    return seller, buyer


# ------------------------------------------------
# Header Fields
# ------------------------------------------------
def extract_header_fields(text: str) -> Dict[str, Any]:
    data = {}

    m = re.search(
        r"(invoice\s*(no|number|#))\s*[:\-]?\s*([A-Z0-9\-]+)",
        text, re.I
    )
    if m:
        data["invoice_number"] = m.group(3)

    d = re.search(r"(\d{2}[./-]\d{2}[./-]\d{4})", text)
    if d:
        data["invoice_date"] = parse_date_universal(d.group(1))

    return data


# ------------------------------------------------
# Totals + Currency (English)
# ------------------------------------------------
def extract_totals(text: str) -> Tuple[float, float, float, str]:
    net = tax = gross = 0.0
    currency = "USD"

    for line in text.split("\n"):
        l = line.lower()

        if "net total" in l:
            net = parse_float_universal(line)

        elif re.search(r"(tax|vat|gst)", l):
            tax = parse_float_universal(line)

        elif "gross total" in l or "amount due" in l or "total payable" in l:
            gross = parse_float_universal(line)
            if "$" in line:
                currency = "USD"
            elif "€" in line:
                currency = "EUR"
            elif "₹" in line:
                currency = "INR"

    # Fallback: derive net if only gross + tax present
    if gross and not net:
        net = round(gross - tax, 2)

    return net, tax, gross, currency


# ------------------------------------------------
# Line Items (Pipe OR Space tables)
# ------------------------------------------------
def extract_line_items(page, page_words):
    items = []

    y_start, y_end = predict_table_area(page.height, page_words)
    cropped = page.crop((0, y_start, page.width, y_end))
    text = cropped.extract_text() or ""

    for line in text.split("\n"):
        clean = line.strip()
        if len(clean) < 5:
            continue

        # Hard filters (no garbage)
        if re.search(
            r"(qty|description|unit price|line total|subtotal|tax|total|page|----)",
            clean, re.I
        ):
            continue

        qty = unit_price = line_total = None
        desc = ""

        # PIPE TABLE
        if "|" in clean:
            cols = [c.strip() for c in clean.split("|") if c.strip()]
            if len(cols) < 4:
                continue
            qty = parse_float_universal(cols[0])
            desc = cols[1]
            unit_price = parse_float_universal(cols[2])
            line_total = parse_float_universal(cols[3])

        # SPACE ALIGNED
        else:
            nums = re.findall(r"[\d,.]+", clean)
            if len(nums) < 2:
                continue

            qty = parse_float_universal(nums[0])
            line_total = parse_float_universal(nums[-1])
            unit_price = round(line_total / qty, 2) if qty > 0 else 0.0
            desc = re.sub(r"[\d,.]+", "", clean).strip()

        if not qty or not line_total or qty > 10000:
            continue

        if len(desc) < 3:
            continue

        items.append({
            "description": desc,
            "quantity": qty,
            "unit_price": round(unit_price, 2),
            "line_total": round(line_total, 2),
            "unit_description": "",
            "supplier_article_no": "",
            "internal_material_no": ""
        })

    return items


# ------------------------------------------------
# MAIN PUBLIC FUNCTION (Tier 1)
# ------------------------------------------------
def extract_with_regex(pdf_path: str) -> Dict[str, Any]:
    text = ""
    line_items = []

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text() or ""
            text += page_text + "\n"
            page_words = page.extract_words()
            line_items.extend(extract_line_items(page, page_words))

    if not text.strip():
        return {"error": "no_text"}

    header = extract_header_fields(text)
    net, tax, gross, currency = extract_totals(text)
    seller, buyer = extract_party_blocks(text)

    return {
    "invoice_number": header.get("invoice_number"),
    "invoice_date": header.get("invoice_date"),
    "due_date": None,

    # ✅ CRITICAL FIX
    "seller_name": seller if seller else "Seller (Detected by Layout)",
    "buyer_name": buyer if buyer else "Buyer (Detected by Layout)",

    "payment_terms": None,
    "delivery_terms": None,
    "cost_center": None,
    "currency": currency,
    "net_total": net,
    "tax_amount": tax,
    "gross_total": gross,
    "line_items": line_items,
    "detected_language": get_language_code(text),
    "extraction_method": "tier1_regex_layout"
}

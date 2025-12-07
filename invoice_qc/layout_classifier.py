# invoice_qc/layout_classifier.py
from typing import Dict, Any, Tuple, List

TABLE_KEYWORDS = [
    "description", "item", "product", "pos",
    "qty", "quantity", "unit price",
    "amount", "line total", "total"
]

FOOTER_KEYWORDS = [
    "subtotal", "tax", "vat", "gst",
    "grand total", "balance", "page"
]

def predict_table_area(
    page_height: float,
    page_words: List[Dict[str, Any]]
) -> Tuple[float, float]:
    """
    Predict table vertical span using layout semantics.
    Works for English invoices.
    """

    header_ys = []
    footer_ys = []

    for w in page_words:
        text = w.get("text", "").lower()
        y = w.get("top")

        if y is None:
            continue

        # Detect table header region
        if any(k in text for k in TABLE_KEYWORDS):
            header_ys.append(y)

        # Detect totals/footer region
        if any(k in text for k in FOOTER_KEYWORDS):
            footer_ys.append(y)

    # Default fallback window
    y_start = page_height * 0.30
    y_end = page_height * 0.75

    if header_ys:
        y_start = min(header_ys) - 15

    if footer_ys:
        y_end = min(footer_ys)

    # Clamp values
    y_start = max(0, y_start)
    y_end = min(page_height, y_end)

    # Safety check
    if y_end - y_start < 100:
        y_start = page_height * 0.30
        y_end = page_height * 0.75

    return y_start, y_end

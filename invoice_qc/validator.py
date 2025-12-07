from typing import List, Dict, Any
from collections import defaultdict
import math

def validate_invoice(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Applies strict audit rules and returns the per-invoice validation result.
    This function generates the required list of all missing fields.
    """
    errors = []
    missing_list = []
    
    # Define Schema and Critical Fields
    schema_fields = [
        "invoice_number", "invoice_date", "due_date", "seller_name", "buyer_name", 
        "currency", "net_total", "tax_amount", "gross_total", "payment_terms", 
        "delivery_terms", "cost_center"
    ]
    critical_fields = ["invoice_number", "invoice_date", "seller_name", "gross_total", "currency"]
    
    # --- 1. CHECK TOP-LEVEL FIELDS ---
    for field in schema_fields:
        val = data.get(field)
        is_missing = False
        
        # Check 1: Null, None, or Empty String/Placeholder
        if val is None:
            is_missing = True
        elif isinstance(val, str):
            clean = val.strip().lower()
            if not clean or "unknown" in clean:
                is_missing = True
        # Logic: Gross Total cannot be 0
        elif field == "gross_total" and (val == 0.0 or val == 0):
            is_missing = True

        if is_missing:
            issue = f"missing_field: {field}"
            if field in critical_fields:
                errors.append(issue)
            missing_list.append(issue)

    # --- 2. CHECK LINE ITEMS (Deep Audit) ---
    line_items = data.get("line_items", [])
    if not line_items:
        errors.append("critical_missing: line_items")
    else:
        item_schema = ["description", "quantity", "unit_price", "line_total", 
                       "unit_description", "supplier_article_no", "internal_material_no"]
        missing_cols = set()

        for item in line_items:
            for field in item_schema:
                val = item.get(field)
                if val is None or (isinstance(val, str) and not val.strip()):
                    missing_cols.add(field)
        
        for col in missing_cols:
            missing_list.append(f"missing_field: line_items.{col}")

    # --- 3. BUSINESS RULE: TOTALS MATCH ---
    net = data.get("net_total", 0.0) or 0.0
    tax = data.get("tax_amount", 0.0) or 0.0
    gross = data.get("gross_total", 0.0) or 0.0
    
    if not math.isclose(net + tax, gross, rel_tol=0.001, abs_tol=0.05):
        if gross > 0:
             errors.append(f"business_rule_failed: totals_mismatch")

    # --- 4. COMPILE FINAL REPORT STRUCTURE ---
    all_errors = errors + [m for m in missing_list if m not in errors]
    is_valid = len(errors) == 0
    
    score = 100 - (len(all_errors) * 5)
    if not is_valid: score = 0
    if score < 0: score = 0
    
    # FINAL RETURN STRUCTURE
    return {
        "invoice_id": data.get('invoice_number', 'N/A'),
        "is_valid": is_valid,
        "quality_score": score,
        "errors": all_errors, 
        "missing_values": missing_list 
    }


def compile_validation_report(invoices: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Generates the Aggregated Summary (Part C.4.2) and Per-Invoice Results.
    """
    
    total_invoices = len(invoices)
    valid_invoices = 0
    invalid_invoices = 0
    error_counts = defaultdict(int)
    
    per_invoice_results = []

    for invoice_data in invoices:
        qc_result = validate_invoice(invoice_data)
        
        is_valid = qc_result['is_valid']
        
        if is_valid:
            valid_invoices += 1
        else:
            invalid_invoices += 1
            
        # Update aggregate counts for ALL issues
        for issue in qc_result['errors']:
            error_counts[issue] += 1
            
        # Create the Per-Invoice Structure
        per_invoice_results.append({
            "invoice_id": qc_result['invoice_id'],
            "is_valid": is_valid,
            "quality_score": qc_result['quality_score'],
            "errors": qc_result['errors'],
            "extracted_data": invoice_data 
        })

    summary = {
        "total_invoices": total_invoices,
        "valid_invoices": valid_invoices,
        "invalid_invoices": invalid_invoices,
        "error_counts": dict(error_counts)
    }

    return {
        "summary": summary,
        "results": per_invoice_results
    }
# invoice_qc/pipeline.py
import os
import time
from .regex_extractor import extract_with_regex
from .llm_extractor import extract_with_gemini
from .validator import validate_invoice # Import validation audit

SUPPORTED_LANGUAGES = ["DE", "EN", "ES"]

def validate_tier1_quality(data) -> bool:
    """
    STRICT QUALITY GATE: Checks for critical data integrity issues.
    If the full validation (validate_invoice) returns False, Tier 1 is rejected.
    """
    # Run full validation audit on the Tier 1 result
    qc_result = validate_invoice(data)
    
    # Reject Tier 1 if it is marked as Invalid (missing critical fields like Gross Total)
    if not qc_result['is_valid']:
        print(f"   ❌ Validation Failed on Tier 1 (Missing Critical Data).")
        return False
        
    # Additional Sanity Check: If Line Items were not found, but a gross total was, reject.
    if not data.get('line_items') and data.get('gross_total', 0) > 0:
        print(f"   ❌ Validation Failed (Gross Total Present, but Line Items Missing).")
        return False
        
    # Check 3: Simple Identity Check (to force LLM if names are obviously generic)
    if data.get('seller_name') == "Unknown Seller":
         print(f"   ❌ Identity Check Failed. Cannot reliably identify seller.")
         return False

    return True

def run_invoice_extraction(pdf_path: str):
    start_time = time.time()
    filename = os.path.basename(pdf_path)
    
    # --- STEP 1: RUN TIER 1 (REGEX + TIER 1.5 LAYOUT) ---
    print(f"🔹 Tier 1: Analyzing {filename}...", end=" ", flush=True)
    try:
        tier1_data = extract_with_regex(pdf_path)
    except:
        tier1_data = {"errors": ["Extraction failed in Tier 1 engine"]} # Error on initial load

    # --- STEP 1.5: QUALITY CHECK & ESCALATION LOGIC ---
    
    is_valid_tier1 = validate_tier1_quality(tier1_data)
    lang = tier1_data.get('detected_language', 'UNKNOWN')
    is_supported = lang in SUPPORTED_LANGUAGES
    is_supported = lang.upper() in SUPPORTED_LANGUAGES
    if is_supported and is_valid_tier1:
        print(f"✅ Success (Regex).")
        tier1_data['extraction_method'] = 'tier1_regex'
        tier1_data['processing_time'] = round(time.time() - start_time, 2)
        return tier1_data
    
    # --- STEP 2: HANDOVER TO TIER 2 (GEMINI AI) ---
    
    if not is_supported:
        print(f"🔸 Language '{lang}' unknown. Switching to AI...")
    
    # Execute AI extraction
    tier2_data = extract_with_gemini(pdf_path)
    
    if tier2_data:
        print("   ✅ Gemini Success.")
        tier2_data['extraction_method'] = 'tier2_gemini_hybrid'
        tier2_data['processing_time'] = round(time.time() - start_time, 2)
        return tier2_data
    
    # --- STEP 3: TOTAL FAILURE (Return partial data) ---
    print(f"   ⚠️ Both Tiers failed. Returning partial data.")
    return {
        "invoice_number": tier1_data.get('invoice_number', 'N/A'),
        "errors": ["Total failure in extraction pipeline."],
        "extraction_method": "failed_no_recovery"
    }

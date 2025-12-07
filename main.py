import os
import json
import time

# Import your modules
# Ensure invoice_qc/extractor.py exists from previous steps!
from invoice_qc.regex_extractor import extract_invoice as extract_regex
from invoice_qc.llm_extractor import extract_with_gemini

def process_invoice(pdf_path: str):
    filename = os.path.basename(pdf_path)
    print(f"\n📄 PROCESSING: {filename}")
    print("-" * 30)
    
    start_time = time.time()
    
    # --- TIER 1: REGEX (Fast & Free) ---
    print("🔹 Tier 1: Running Regex Engine...")
    try:
        data = extract_regex(pdf_path)
    except Exception as e:
        print(f"   ⚠️ Regex crashed: {e}")
        data = {"invoice_number": None, "net_total": 0.0}

    # Check Quality of Regex Result
    # We consider it 'failed' if we don't have an Invoice Number OR Total is 0
    is_valid_regex = (
        data.get('invoice_number') and 
        (data.get('gross_total', 0) > 0 or data.get('net_total', 0) > 0)
    )
    
    if is_valid_regex:
        print("✅ Regex Success! (Saved API Cost)")
        data['extraction_method'] = 'regex_engine'
        data['processing_time'] = round(time.time() - start_time, 2)
        return data
    
    # --- TIER 2: GEMINI AI (Smart & Costly) ---
    print("🔸 Regex failed/incomplete. Elevating to Tier 2 (Gemini AI)...")
    
    llm_data = extract_with_gemini(pdf_path)
    
    if llm_data:
        print("✅ Gemini Success!")
        llm_data['extraction_method'] = 'gemini_hybrid'
        llm_data['processing_time'] = round(time.time() - start_time, 2)
        return llm_data
    else:
        print("❌ Both methods failed.")
        data['extraction_method'] = 'failed'
        return data

# --- RUNNER ---
if __name__ == "__main__":
    # Point to your PDFs folder
    PDF_FOLDER = "./pdfs"
    
    if not os.path.exists(PDF_FOLDER):
        print(f"Create a folder named '{PDF_FOLDER}' and put PDFs there.")
        exit()

    files = [f for f in os.listdir(PDF_FOLDER) if f.lower().endswith(".pdf")]
    
    results = []
    
    print(f"🚀 Starting Hybrid Extraction Pipeline on {len(files)} files...\n")
    
    for f in files:
        full_path = os.path.join(PDF_FOLDER, f)
        result = process_invoice(full_path)
        results.append(result)
        
    print("\n" + "="*40)
    print("FINAL RESULTS SUMMARY")
    print("="*40)
    print(json.dumps(results, indent=2))
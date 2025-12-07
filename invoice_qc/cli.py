import argparse
import os
import json
import sys
from typing import List, Dict, Any, Union
from collections import defaultdict
from typing import Any

# CRITICAL IMPORT: We need the regex extractor directly for isolation
from invoice_qc.regex_extractor import extract_with_regex 
from invoice_qc.pipeline import run_invoice_extraction
from invoice_qc.validator import compile_validation_report, validate_invoice

# --- Helper Functions (keep unchanged) ---

def load_invoices(input_path: str) -> List[Dict[str, Any]]:
    # ... (function body) ...
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")
    with open(input_path, 'r') as f:
        return json.load(f)

def save_report(data: Any, output_path: str):
    # ... (function body) ...
    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2)

def print_summary(summary: Dict[str, Any]):
    # ... (function body) ...
    print("\n" + "="*40)
    print("✨ QC VALIDATION SUMMARY")
    print("="*40)
    print(f"Total Invoices Processed: {summary['total_invoices']}")
    print(f"Valid Invoices:           {summary['valid_invoices']}")
    print(f"Invalid Invoices:         {summary['invalid_invoices']}")
    
    if summary['invalid_invoices'] > 0:
        print("\nTop Error Types:")
        sorted_errors = sorted(summary['error_counts'].items(), key=lambda item: item[1], reverse=True)
        for error_type, count in sorted_errors[:3]:
            print(f"- {error_type}: {count}")
    print("="*40 + "\n")
    

# --- Main CLI Logic ---

def main():
    parser = argparse.ArgumentParser(description="Invoice Extraction and Quality Control Service (Hybrid)")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # 1. EXTRACT Command (Runs ONLY the Tier 1 Extractor)
    extract_parser = subparsers.add_parser('extract', help="Extracts data from PDFs only.")
    extract_parser.add_argument('--pdf-dir', required=True, help="Folder containing PDF files.")
    extract_parser.add_argument('--output', required=True, help="Output JSON file for extracted data.")

    # 2. VALIDATE Command
    validate_parser = subparsers.add_parser('validate', help="Validates extracted JSON data against defined rules.")
    validate_parser.add_argument('--input', required=True, help="Input JSON file with extracted invoices.")
    validate_parser.add_argument('--report', required=True, help="Output JSON file for the validation report.")

    # 3. FULL-RUN Command (Runs FULL Hybrid Pipeline)
    full_run_parser = subparsers.add_parser('full-run', help="Runs extraction and validation end-to-end.")
    full_run_parser.add_argument('--pdf-dir', required=True, help="Folder containing PDF files.")
    full_run_parser.add_argument('--report', required=True, help="Output JSON file for the final validation report.")

    args = parser.parse_args()

    # --- EXECUTION FLOW ---
    invoices = []
    
    if args.command in ['extract', 'full-run']:
        pdf_dir = args.pdf_dir
        pdf_files = [os.path.join(pdf_dir, f) for f in os.listdir(pdf_dir) if f.lower().endswith('.pdf')]
        
        print(f"🚀 Running {'Tier 1 (Isolated)' if args.command == 'extract' else 'Hybrid Pipeline'} on {len(pdf_files)} PDFs...")
        
        for pdf_path in pdf_files:
            print(f"   Processing: {os.path.basename(pdf_path)}...", end=" ", flush=True)
            
            if args.command == 'extract':
                # ISOLATION MODE: ONLY call the regex extractor
                invoice_data = extract_with_regex(pdf_path)
            else:
                # FULL-RUN MODE: Call the hybrid pipeline
                invoice_data = run_invoice_extraction(pdf_path)
            
            # Per-invoice Validation for CLI Status (for full-run mode)
            if args.command == 'full-run':
                qc_result = validate_invoice(invoice_data)
                invoice_data["validation_status"] = "VALID" if qc_result["is_valid"] else "INVALID"
                invoice_data["quality_score"] = qc_result["quality_score"]
                invoice_data["missing_values"] = qc_result["errors"]
                print(f"✅ Extracted via {invoice_data.get('extraction_method', 'FAIL')}")
            else:
                 print(f"✅ Extracted (Raw)") # Simple confirmation for extract mode

            invoices.append(invoice_data)
            if not isinstance(invoice_data, dict):
             invoice_data = {
        "invoice_number": "N/A",
        "errors": ["invalid_extraction_output"]
    }

        if args.command == 'extract':
            # In 'extract' mode, save the raw Tier 1 output
            save_report(invoices, args.output)
            print(f"\n✨ Extracted data saved to: {args.output}")
            return
            
    if args.command == 'validate':
        # Load data from input file
        invoices = load_invoices(args.input)
        
    # VALIDATION/REPORTING STEP (Used by 'validate' and 'full-run')
    print("\n🔬 Compiling Validation Report...")
    report_data = compile_validation_report(invoices)
    
    # Save the final report
    save_report(report_data, args.report)
    
    # Print the summary
    print_summary(report_data['summary'])

    if report_data['summary']['invalid_invoices'] > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
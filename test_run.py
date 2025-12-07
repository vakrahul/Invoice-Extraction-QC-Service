import os
import sys

print("--- DEBUG: Script Started ---")
print(f"Current Working Directory: {os.getcwd()}")

# Attempt to verify PDF folder exists
PDF_FOLDER = "./pdfs"
if not os.path.exists(PDF_FOLDER):
    print(f"ERROR: The folder '{PDF_FOLDER}' does not exist here.")
    print("Please create a folder named 'pdfs' and put the PDF files inside.")
    sys.exit(1)

# List files
files = [f for f in os.listdir(PDF_FOLDER) if f.lower().endswith('.pdf')]
print(f"Found {len(files)} PDF files: {files}")

if not files:
    print("ERROR: No .pdf files found in the 'pdfs' folder.")
    sys.exit(1)

# Import logic (Wrapped in try/catch to see import errors)
try:
    print("Attempting to import invoice_qc.extractor...")
    from invoice_qc.regex_extractor import extract_invoice
    print("Import successful!")
except ImportError as e:
    print(f"IMPORT ERROR: {e}")
    print("Make sure 'invoice_qc' folder has an __init__.py file and is in the same directory.")
    sys.exit(1)

# Run Extraction
print("\n--- Starting Extraction ---")
for f in files:
    path = os.path.join(PDF_FOLDER, f)
    print(f"\nProcessing: {f}")
    try:
        data = extract_invoice(path)
        print("✅ SUCCESS! Data Extracted:")
        print(data)
    except Exception as e:
        print(f"❌ FAILED: {e}")
        import traceback
        traceback.print_exc()

print("\n--- Finished ---")
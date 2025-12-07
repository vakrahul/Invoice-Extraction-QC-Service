# invoice_qc/api.py
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import shutil
import os
import uuid
import base64 
from pathlib import Path
from typing import List, Dict, Any

from .pipeline import run_invoice_extraction
from .validator import compile_validation_report

# --- Setup ---
app = FastAPI(title="Invoice QC API", version="1.0")

# CRUCIAL: Allow React frontend to access the API (CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health_check():
    """Returns system status (Part D.2)."""
    return {"status": "ok", "message": "Hybrid Pipeline Operational"}


@app.post("/validate-json")
async def validate_json_endpoint(invoices: List[Dict[str, Any]]):
    """
    POST /validate-json: Validates a pre-extracted list of invoice objects.
    Returns: Summary + Per-invoice validation results (Part D.2).
    """
    if not invoices:
        raise HTTPException(status_code=400, detail="Request body must contain a list of invoices.")
        
    report = compile_validation_report(invoices)
    
    return report

@app.post("/extract-and-validate")
async def extract_and_validate_pdfs_endpoint(file: UploadFile = File(...)):
    """
    POST /extract-and-validate: Accepts a single PDF file, runs extraction, validation, 
    and returns the report, INCLUDING the PDF encoded as Base64 for preview.
    """
    
    # 1. Create a secure temporary path
    temp_dir = Path("temp_uploads")
    temp_dir.mkdir(exist_ok=True)
    unique_id = uuid.uuid4()
    temp_filepath = temp_dir / f"{unique_id}_{file.filename}"
    
    pdf_base64_data = None # Initialize variable

    try:
        # 2. Save uploaded file to disk
        with open(temp_filepath, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # 3. Encode the PDF for Frontend Preview (CRITICAL FOR UX BONUS)
        with open(temp_filepath, "rb") as pdf_file:
            pdf_base64_data = base64.b64encode(pdf_file.read()).decode('utf-8')
            
        # 4. Run the Hybrid Pipeline (extracts + applies validation rules internally)
        extracted_data = run_invoice_extraction(temp_filepath)
        
        # 5. Compile the report
        report = compile_validation_report([extracted_data])
        
        # 6. ATTACH BASE64 TO THE REPORT
        if report['results'] and pdf_base64_data:
            report['results'][0]['original_pdf_base64'] = pdf_base64_data
        
        return report

    except Exception as e:
        # Note: If the error is an unhandled exception during extraction, this catches it.
        raise HTTPException(status_code=500, detail=f"Internal Processing Error: {str(e)}")
    finally:
        # 7. Cleanup
        if temp_filepath.exists():
            os.remove(temp_filepath)
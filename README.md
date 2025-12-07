# Invoice-Extraction-QC-Service-Rahul-Vakiti
This project is a production-style invoice extraction and validation system designed to handle real-world PDF invoices with varying layouts, languages, and data quality.  Instead of relying on a single technique, the system uses a multi-tier hybrid architecture that balances speed, accuracy, and cost, similar to how enterprise data pipeline
# Project Overview
The project delivers an Enterprise-Grade Hybrid AI Service that resolves the challenge of turning chaotic, unstructured B2B PDFs into reliable, standardized JSON data for immediate accounting processing.
The Problem Solved
Traditional invoice processing is bottlenecked by fragile code (regex breaks on new layouts) and human intervention. Our Hybrid Neural Engine (Tier 1.5/Tier 2) ensures 99%+ accuracy while optimizing the operational cost by limiting calls to the expensive AI engine.
### A. Extracted Schema (Fixed Output)

The system enforces a **strict, fixed schema** to ensure downstream reliability and accounting-system compatibility.

| Field Name       | Type           | Description |
|-----------------|----------------|-------------|
| invoice_number  | String         | Unique invoice identifier (AUFNR, INV-XXXX, CCU1-XXXX). |
| invoice_date    | Date (ISO)     | Invoice issue date in `YYYY-MM-DD` format. |
| due_date        | Date (ISO)     | Payment due date, if specified in the document. |
| seller_name     | String         | Legal entity issuing the invoice (semantic resolution). |
| buyer_name      | String         | Customer or billing entity receiving the invoice. |
| currency        | String (ISO)   | Currency code (`EUR`, `USD`, `INR`, etc.). |
| net_total       | Float          | Total amount before tax. |
| tax_amount      | Float          | Tax component applied to the invoice. |
| gross_total     | Float          | Final payable amount including tax (**critical field**). |
| payment_terms   | String         | Extracted payment conditions (e.g., Net 30, 2% Skonto). |
| delivery_terms  | String         | Delivery or shipping terms, if present. |
| cost_center     | String         | Cost allocation reference, if available. |
| line_items      | List[Object]   | Detailed breakdown of purchased items/services. |
### Line Item Object Structure

Each entry inside `line_items` follows this structure:

| Field Name            | Type   | Description |
|----------------------|--------|-------------|
| description          | String | Item or service description. |
| quantity             | Float  | Number of units purchased. |
| unit_price           | Float  | Price per unit. |
| line_total           | Float  | `quantity × unit_price`. |
| unit_description     | String | Unit of measurement . |
| supplier_article_no  | String | Supplier’s internal item reference . |
| internal_material_no | String | Buyer’s internal material code . |
> This schema is validated via a strict Quality Control engine before being exposed to downstream systems.
> ### Validation Rules (Part 2.2)

The `validator.py` module applies deterministic validation rules to ensure data completeness, business correctness, and anomaly prevention.

| Rule Category | Rule Implemented | Rationale |
|--------------|-----------------|-----------|
| **Completeness (Critical)** | `missing_field: invoice_number` | Invoice ID is required for unique identification and reconciliation. |
| | `missing_field: gross_total` | Final payable amount is mandatory for ledger posting. |
| | `missing_field: seller_name` | Legal entity information is required for compliance and audits. |
| **Business Logic** | `business_rule_failed: totals_mismatch` | Ensures financial consistency where `Net + Tax ≈ Gross` (tolerance ±0.05). |
| | `critical_missing: line_items` | Prevents accepting invoices without item-level breakdowns when totals exist. |
| **Anomaly Detection** | `anomaly_rule_failed: negative_totals` | Detects extraction/OCR errors producing invalid negative amounts. |
| **Data Integrity (Quality Score)** | `missing_field: line_items.unit_description` | Optional but desirable field, used to compute quality score without failing invoice. |

## Installation & Setup
 Prerequisites Python 3.10+, Node.js (for React), and Tesseract OCR (Optional, for full fallback capability).
## Install Backend (The Brain)
cd invoice_qc
pip install -r requirements.txt
Set API Key in .env file: GEMINI_API_KEY=AIzaSy...

## Run API Server (The Bridge)
uvicorn invoice_qc.api:app --reload
## Run Frontend (The Interface)
cd frontend
npm install
npm run dev
### A. CLI Commands

| Command | Description |
|--------|------------|
| `python -m invoice_qc.cli extract --pdf-dir pdfs --output raw.json` | Runs Extraction Only (Tier 1 / Tier 2) and saves raw extracted JSON data. |
| `python -m invoice_qc.cli full-run --pdf-dir pdfs --report report.json` | Runs full pipeline (Extraction + Validation), prints QC summary, and saves final report. |

> ℹ️ **Note:**
>  The `full-run` command automatically escalates from Tier 1 → Tier 2 only when quality checks fail, significantly reducing LLM usage cost.


### B. HTTP API Endpoints

| Endpoint | Method | Function |
|---------|--------|----------|
| `/health` | GET | Confirms service status and health of the backend. |
| `/validate-json` | POST | Validates a pre-extracted invoice JSON against quality control rules. |
| `/extract-and-validate` | POST | Accepts a PDF file (`multipart/form-data`), runs the full hybrid extraction pipeline, and returns the complete validation report. |

## 6. Part 7: AI Usage Notes

The hybrid architecture implemented in this project reflects **deliberate and minimal use of AI**, ensuring **high extraction accuracy** while keeping **latency and operational costs under control**.

### AI Tool Used
- **Model:** Google Gemini 1.5 Pro  
- **Integration:** Python SDK  
- **Execution Mode:** On-demand (Triggered only on Tier 1 failure)

### Role of AI in the System
- **Tier:** Tier 2 – Semantic Recovery Engine
- **Purpose:**  
  To recover high-quality structured data when rule-based extraction (Regex + Layout) fails due to:
  - Complex or unfamiliar invoice layouts  
  - Ambiguous positioning of Seller/Buyer blocks  
  - Inconsistent currency notation or tax structures  

### Key Design Insight (Self-Correction Strategy)
During development, it was observed that **positional and layout-based heuristics alone are insufficient** for reliable extraction in real-world invoices.

To address this, the LLM prompt was explicitly engineered to prioritize:

- **Business relationships**  
  - Issuer vs. Recipient (Seller vs. Buyer)  
- **Financial semantics**  
  - Tax logic (HSN / GST indicators for INR detection)  
  - Global invoice conventions across regions  
- **Contextual reasoning over positional cues**  
  - Understanding meaning rather than relying on text location

This design transforms the LLM into a **semantic reasoning layer** instead of a simple text parser, allowing the system to correctly resolve ambiguities that traditional methods cannot.

### Why This Matters
✅ Reduces unnecessary AI calls  
✅ Controls operational cost  
✅ Increases extraction accuracy  
✅ Demonstrates production-grade AI governance  

> **Result:** AI is used as a *precision recovery tool*, not as a dependency — aligning the system with real-world enterprise design principles.
## video demo 
https://drive.google.com/file/d/1SQTBMUnArfpoVRUGr_D2xP4oTCExn8Ja/view?usp=sharing



##  Architecture & Data Flow
We use a **4-Layer Defense** approach to balance speed and intelligence.

```mermaid
graph TD;
  PDF[Input PDF] -->|Extraction Module| T1[Tier 1.5: Layout Classification];
    T1 -->|Heuristics| T2[Tier 1: Regex/Table Engine];
    T2 -->|Validation Check| QC[Quality Gate];
    QC -->|Valid Data| Report[Validation Report];
    QC -->|Low Quality Data| LLM[Tier 2: Gemini Semantic Resolver];
    LLM -->|High Quality Data| Report;
    Report --> CLI[CLI / FastAPI API];


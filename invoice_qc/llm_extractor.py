import os
import json
import pdfplumber
import google.generativeai as genai
from pathlib import Path
from dotenv import load_dotenv

# --- SETUP ---
current_file = Path(__file__).resolve()
env_path = current_file.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

api_key = os.getenv("GEMINI_API_KEY")
if api_key:
    genai.configure(api_key=api_key)

# Using Pro for best reasoning
CANDIDATE_MODELS = ['gemini-1.5-pro', 'gemini-pro', 'gemini-2.5-flash']

def extract_with_gemini(pdf_path: str):
    if not api_key: return None

    # 1. Read PDF
    text_content = ""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                text_content += (page.extract_text() or "") + "\n"
    except Exception: return None

    if not text_content.strip(): return None

    # 2. THE "HEADER PRIORITY" PROMPT
    prompt = f"""
    You are an expert Document Analyst. Extract data into strict JSON.
    
    ### 1. IDENTITY IDENTIFICATION (CRITICAL):
    * **SELLER (Issuer):** * Look at the **Top-Left** or **Top-Right** of the page. The **Logo** or **Bold Header** is the Seller (e.g. "JKL Corporation", "Medical Equipment").
        * **Double Check:** Who owns the Bank Details/IBAN in the footer? That is the Seller.
        * *Negative Rule:* Do NOT pick the tiny text line inside the address box as the Seller name.
    
    * **BUYER (Recipient):** * Look for the **Address Block** (usually left side). 
        * **Window Envelope Rule:** The box contains [Tiny Sender Line] -> [Main Buyer Name]. 
        * **Ignore the tiny top line.** Extract the LARGE text block below it as the Buyer.
        * Look for "Kundenanschrift" (Customer Address).

    ### 2. DATA EXTRACTION:
    * **Invoice Number:** Extract "AUFNR...", "Rechnung Nr", "Bestellung Nr".
    * **Dates:** Format YYYY-MM-DD.
    * **Payment Terms:** Look for "0 Tage 2,0% Skonto" or similar.
    * **Delivery Terms:** Look for "Lieferbedingungen" (e.g. "Keine Angabe").

    ### 3. LINE ITEMS (TABLE):
    * Extract products cleanly. 
    * **Sanity Check:** Quantity is usually a small integer (1, 2, 4, 10). If you see a phone number or ID like '11223344', DO NOT put it in Quantity.
    * **Math:** Qty * Unit Price ≈ Total.
    4. **PAYMENT TERMS (Fixing the Missing Value):**
       - **Instruction:** Look specifically for conditions like "Paid in Full", "Credit Card", "UPI", or "Net 30".
       - Prioritize text near the keywords: "Payment Mode", "Terms", or "Total Amount".
       2. **DELIVERY/COST CENTER (Specific Fix):**
       - **Delivery Terms:** If not explicitly stated, check the general context for terms like 'Delivered', 'Shipped', or extract the most relevant status text near the address block. (The document likely contains text implying a local standard delivery).
       - **Cost Center:** This is often not present. If you cannot find a "Kostenstelle" or similar label, set to null. (The existing null is likely correct, but we check one last time).
    
    5. **LINE ITEM METADATA (Internal IDs):**
       - **Internal Material No (HSN):** Look for 'HSN:', 'Item Code', or 'Internal ID' in the line item description/text. Extract the number/code immediately following this.
       - **Unit Description:** If not explicitly 'pcs' or 'VE', use the general unit of sale (e.g., 'Unit' or 'Item'). Since this is an iPhone sale, it is one 'Unit'.
       - **Invoice ID/Dates:** Ensure they are extracted precisely.

    ### OUTPUT SCHEMA:
    {{
        "invoice_number": "string",
        "invoice_date": "YYYY-MM-DD",
        "due_date": "YYYY-MM-DD (null if not found)",
        "seller_name": "string (The Logo/Header Company)",
        "buyer_name": "string (The Recipient in the address box)",
        "currency": "Find the 3-letter code (e.g. EUR, USD, INR)",
        "net_total": float,
        "tax_amount": float,
        "gross_total": float,
        "payment_terms": "string",
        "delivery_terms": "string",
        "cost_center": "string",
        "line_items": [
            {{
                "description": "string",
                "quantity": float,
                "unit_price": float,
                "line_total": float,
                "unit_description": "string",
                "supplier_article_no": "string",
                "internal_material_no": "string"
            }}
        ]
    }}

    INVOICE TEXT:
    {text_content}
    """

    # 3. Call AI
    for model_name in CANDIDATE_MODELS:
        try:
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(prompt)
            clean_text = response.text.replace("```json", "").replace("```", "").strip()
            
            # Parse & Clean
            data = json.loads(clean_text)
            
            # Remove Duplicates/Negatives
            if "line_items" in data and isinstance(data["line_items"], list):
                cleaned_items = []
                seen = set()
                for item in data["line_items"]:
                    qty = item.get('quantity', 0)
                    total = item.get('line_total', 0)
                    if qty < 0 or total < 0: continue
                    
                    key = (str(item.get('description')).strip(), total)
                    if key in seen: continue
                    seen.add(key)
                    cleaned_items.append(item)
                data["line_items"] = cleaned_items

            return data
        except:
            continue

    return None
import React, { useState } from 'react';
import { Upload, FileText, AlertCircle, Loader2, DollarSign, CheckCircle, Download, Eye, X } from 'lucide-react';
import './App.scss';
// Assuming ModelViewer.jsx is created and imported separately
import ModelViewer from './ModelViewer'; 


// Component to display individual detail rows
const DetailItem = ({ label, value, color }) => (
  <div className="qc-detail-item">
    <span className="qc-detail-label">{label}</span>
    <span className={`qc-detail-value ${color || ''}`}>
      {value || 'N/A'}
    </span>
  </div>
);

// Component to render the validation badges
const StatusBadge = ({ status, errorCount }) => {
  const isInvalid = status === 'INVALID' || errorCount > 0;
  return (
    <span className={`qc-status-badge ${isInvalid ? 'qc-status-invalid' : 'qc-status-valid'}`}>
      {isInvalid ? `INVALID (${errorCount} Error${errorCount > 1 ? 's' : ''})` : 'VALID'}
    </span>
  );
};

// --- NEW HELPER: DOWNLOAD LOGIC ---
const handleDownload = (data, filename) => {
    const jsonString = JSON.stringify(data, null, 2);
    const blob = new Blob([jsonString], { type: 'application/json' });
    const href = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = href;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
};

// --- PDF PREVIEW MODAL COMPONENT (Uses iframe for proper PDF rendering) ---
const PdfPreviewModal = ({ base64Data, onClose }) => {
    if (!base64Data) return null;

    // Use 'application/pdf' MIME type to embed the PDF content
    const pdfSrc = `data:application/pdf;base64,${base64Data}`;

    return (
        <div className="qc-modal-overlay" onClick={onClose}>
            <div className="qc-modal-content" onClick={e => e.stopPropagation()}>
                <button className="qc-modal-close" onClick={onClose}>
                    <X className="w-6 h-6"/>
                </button>
                <h3 className="qc-modal-title">Original Document Preview (PDF)</h3>
                <div className="qc-modal-viewer">
                    {/* CRITICAL: Use iframe for reliable PDF embedding */}
                    <iframe
                        src={pdfSrc} 
                        title="Invoice Preview"
                        className="qc-pdf-iframe" 
                        style={{ width: '100%', height: '70vh', border: 'none' }}
                    />
                </div>
                <p className="text-sm text-gray-500 mt-4">Note: This is the actual PDF rendered by the browser.</p>
            </div>
        </div>
    );
};


function InvoiceQCConsole() {
    const [file, setFile] = useState(null);
    const [loading, setLoading] = useState(false);
    const [report, setReport] = useState(null);
    const [error, setError] = useState(null);
    const [showModal, setShowModal] = useState(false); // State for modal visibility

    // Safely calculates the number of critical errors.
    const criticalErrors = report?.results?.[0]?.errors?.filter(m => m.includes('critical_missing:')).length || 0;

    const handleFileChange = (e) => {
        if (e.target.files) {
            setFile(e.target.files[0]);
            setReport(null);
            setError(null);
            setShowModal(false); // Reset modal state
        }
    };

    const handleUpload = async () => {
        if (!file) return;

        setLoading(true);
        setError(null);
        setReport(null);

        const formData = new FormData();
        formData.append("file", file);

        try {
            const response = await fetch("http://127.0.0.1:8000/extract-and-validate", {
                method: "POST",
                body: formData,
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.detail || "Server failed to process the PDF.");
            }
            
            setReport(data);

        } catch (err) {
            setError(`Extraction Failed: ${err.message || 'Check backend connection.'}`);
        } finally {
            setLoading(false);
        }
    };
    
    // Safely access the single invoice result data
    const invoiceResult = report?.results?.[0];
    const extractedData = invoiceResult?.extracted_data;
    const pdfBase64 = invoiceResult?.original_pdf_base64; 
    
    // Logic to control the 3D model visualization (Visible during loading or initial state)
    const showModelViewer = loading || !report;


    return (
        <>
            {/* 1. PDF Preview Modal (Appears above everything else) */}
            {showModal && pdfBase64 && (
                <PdfPreviewModal 
                    base64Data={pdfBase64} 
                    onClose={() => setShowModal(false)}
                />
            )}

            <div className="qc-container">
                {/* Header */}
                <header className="qc-header">
                    <h1 className="qc-title">
                        <DollarSign className="qc-title-icon"/> Invoice QC Console
                    </h1>
                    <p className="qc-subtitle">Representation</p>
                </header>

                {/* Upload/Action Section */}
                <div className="qc-card qc-action-section">
                    <div className="qc-input-group">
                        
                        <div className="qc-file-input">
                            <input 
                                type="file" 
                                accept=".pdf"
                                onChange={handleFileChange} 
                                className="qc-file-input-field"
                                id="file-upload"
                            />
                            <label htmlFor="file-upload" className="qc-file-input-label">
                                <FileText className="qc-file-input-icon" />
                            </label>
                            {file && <p className="qc-file-name">File selected: <strong>{file.name}</strong></p>}
                        </div>

                        <button
                            onClick={handleUpload}
                            disabled={loading || !file}
                            className="qc-button"
                        >
                            {loading ? <Loader2 className="qc-loader" /> : <Upload className="qc-button-icon" />}
                            {loading ? 'Processing...' : 'Run Extraction'}
                        </button>
                    </div>

                    {error && (
                        <div className="qc-error-message">
                            <AlertCircle className="qc-error-icon" />
                            <span className="qc-error-text">Extraction Failed:</span> {error}
                        </div>
                    )}
                </div>
                
                {/* 2. 3D Model Viewer Section (The Animation Layer) */}
                <div className="mb-8 border border-gray-100 rounded-lg overflow-hidden shadow-inner">
                    <ModelViewer isLoading={loading} isVisible={showModelViewer} />
                </div>


                {/* 3. Results Section */}
                {invoiceResult && extractedData && (
                    <div className="qc-card qc-results-section">
                        
                        {/* TOP ACTION BAR: PREVIEW & DOWNLOAD */}
                        <div className="flex justify-between items-center border-b pb-4 mb-4">
                            <h2 className="qc-results-title m-0 p-0 border-0">QC Validation Report</h2>
                            <div className="flex gap-3">
                                {/* PREVIEW BUTTON (Opens Modal) */}
                                {pdfBase64 && (
                                    <button 
                                        onClick={() => setShowModal(true)} 
                                        className="qc-small-button bg-gray-100 hover:bg-gray-200 text-gray-700"
                                    >
                                        <Eye className="w-5 h-5"/> Show PDF Preview
                                    </button>
                                )}
                                {/* DOWNLOAD BUTTON */}
                                <button 
                                    onClick={() => handleDownload(extractedData, `QC_Report_${invoiceResult.invoice_id || 'UNKNOWN'}.json`)}
                                    className="qc-small-button bg-green-100 hover:bg-green-200 text-green-700"
                                >
                                    <Download className="w-5 h-5"/> Download JSON
                                </button>
                            </div>
                        </div>


                        {/* Data Display Content */}
                        <div className="qc-details-grid">
                            <DetailItem label="Invoice ID" value={invoiceResult.invoice_id} color="color-blue" />
                            <DetailItem label="Extraction Method" value={extractedData.extraction_method} />
                            <DetailItem 
                                label="Validation Status" 
                                value={<StatusBadge status={invoiceResult.is_valid ? 'VALID' : 'INVALID'} errorCount={criticalErrors} />}
                            />
                            <DetailItem label="Quality Score" value={`${invoiceResult.quality_score}%`} />
                        </div>

                        {/* Core Invoice Data */}
                        <div className="qc-details-grid border-t pt-4">
                            <DetailItem label="Seller Name" value={extractedData.seller_name} />
                            <DetailItem label="Buyer Name" value={extractedData.buyer_name} />
                            <DetailItem label="Gross Total" value={`${extractedData.currency} ${extractedData.gross_total?.toFixed(2)}`} color="color-green" />
                            <DetailItem label="Payment Terms" value={extractedData.payment_terms || 'N/A'} />
                            <DetailItem label="Date" value={extractedData.invoice_date} />
                            <DetailItem label="Net Total" value={extractedData.net_total?.toFixed(2)} />
                        </div>

                        {/* Missing Values & Errors */}
                        {invoiceResult.errors.length > 0 && (
                            <div className="qc-missing-section">
                                <h3 className="qc-missing-title">
                                    <AlertCircle className="qc-error-icon" /> Missing/Inaccurate Fields:
                                </h3>
                                <ul className="qc-missing-list">
                                    {invoiceResult.errors.map((msg, index) => (
                                        <li key={index} className={msg.includes('critical') ? 'qc-critical-error' : ''}>
                                            {msg.replace('missing_field: ', '').replace('critical_missing: ', '')}
                                        </li>
                                    ))}
                                </ul>
                            </div>
                        )}

                        {/* Line Items Table */}
                        {extractedData.line_items && extractedData.line_items.length > 0 && (
                            <div className="qc-table-section">
                                <h3 className="qc-table-title">
                                    <CheckCircle className="qc-table-icon" /> Line Items ({extractedData.line_items.length})
                                </h3>
                                <div className="qc-table-container">
                                    <table className="qc-table">
                                        <thead className="qc-table-head">
                                            <tr>
                                                <th className="qc-table-th">Description</th>
                                                <th className="qc-table-th text-right">Qty</th>
                                                <th className="qc-table-th text-right">Unit Price</th>
                                                <th className="qc-table-th text-right">Line Total</th>
                                                <th className="qc-table-th">Details</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {extractedData.line_items.map((item, index) => (
                                                <tr key={index} className="qc-table-tr">
                                                    <td className="qc-table-td font-medium">{item.description}</td>
                                                    <td className="qc-table-td text-right">{item.quantity}</td>
                                                    <td className="qc-table-td text-right">{item.unit_price?.toFixed(2)}</td>
                                                    <td className="qc-table-td text-right font-semibold">{item.line_total?.toFixed(2)}</td>
                                                    <td className="qc-table-td text-gray-500 text-xs">
                                                        {item.internal_material_no && `Int Mat: ${item.internal_material_no}`}
                                                    </td>
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                </div>
                            </div>
                        )}
                    </div>
                )}
            </div>
        </>
    );
}

export default InvoiceQCConsole;
import logging
import time
from sqlalchemy.orm import Session
from app.models import Document
from modules.invoice_automation.models import Invoice, PayrollRecord
from modules.invoice_automation.invoice_service import process_invoice
from modules.invoice_automation.payroll_service import process_payroll
from app.services.extractor import extract_structured_data
from app.services.rag_pipeline import ask_question_rag
from app.services.embeddings import get_embedding
from app.services.vector_store import search_similar_chunks
from openai import OpenAI
from app.config import settings

logger = logging.getLogger(__name__)

# Central registry of tool functions
class ToolRegistry:
    def __init__(self):
        self._tools = {}
        self._register_default_tools()

    def register_tool(self, name: str, func, description: str):
        self._tools[name] = {
            "func": func,
            "description": description
        }

    def get_tool(self, name: str):
        return self._tools.get(name)

    def list_tools(self):
        return [
            {"name": name, "description": info["description"]}
            for name, info in self._tools.items()
        ]

    def execute_tool(self, name: str, db: Session, context: dict, **kwargs):
        tool = self.get_tool(name)
        if not tool:
            raise ValueError(f"Tool '{name}' not found in registry.")
        logger.info(f"Executing tool '{name}' with kwargs: {kwargs}")
        return tool["func"](db, context, **kwargs)

    def _register_default_tools(self):
        self.register_tool(
            "extract_document",
            extract_document_tool,
            "Extracts structured schema from raw document content. Input: document_id."
        )
        self.register_tool(
            "search_vector_db",
            search_vector_db_tool,
            "Performs semantic vector search on ingested chunks. Input: query, limit (optional)."
        )
        self.register_tool(
            "summarize_document",
            summarize_document_tool,
            "Summarizes a document's raw content using LLM. Input: document_id."
        )
        self.register_tool(
            "detect_anomalies",
            detect_anomalies_tool,
            "Performs compliance and anomaly auditing check on document data. Input: document_id."
        )
        self.register_tool(
            "send_email",
            send_email_tool,
            "Simulates sending notification email/slack alert to teams. Input: recipient, subject, body."
        )
        self.register_tool(
            "generate_report",
            generate_report_tool,
            "Compiles multiple findings and outputs a finalized text summary or file. Input: content, title."
        )

# Tool Implementations

def extract_document_tool(db: Session, context: dict, **kwargs):
    document_id = kwargs.get("document_id") or context.get("document_id")
    if not document_id:
        raise ValueError("extract_document tool requires 'document_id'")
    
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise ValueError(f"Document {document_id} not found in database.")
    
    extracted_data = extract_structured_data(document.content)
    document.extracted_json = extracted_data
    db.commit()

    # Trigger invoice/payroll processing
    doc_type = extracted_data.get("document_type")
    if doc_type == "invoice":
        process_invoice(db, str(document.id), extracted_data)
    elif doc_type == "payroll":
        process_payroll(db, str(document.id), extracted_data)
    
    return {
        "status": "success",
        "document_type": doc_type,
        "extracted_data": extracted_data
    }

def search_vector_db_tool(db: Session, context: dict, **kwargs):
    query = kwargs.get("query") or context.get("query")
    if not query:
        raise ValueError("search_vector_db tool requires 'query'")
    
    limit = kwargs.get("limit", context.get("limit", 5))
    
    # Try asking via RAG pipeline
    try:
        rag_res = ask_question_rag(db, query)
        return {
            "status": "success",
            "answer": rag_res.get("answer"),
            "sources": [
                {"filename": s["filename"], "score": s["score"]}
                for s in rag_res.get("sources", [])
            ]
        }
    except Exception as e:
        logger.warning(f"RAG search failed, falling back to raw similarity: {str(e)}")
        query_vector = get_embedding(query)
        chunks = search_similar_chunks(db, query_vector, limit=limit)
        return {
            "status": "success",
            "chunks": [
                {"filename": c["filename"], "content": c["content"], "similarity": c["similarity"]}
                for c in chunks
            ]
        }

def summarize_document_tool(db: Session, context: dict, **kwargs):
    document_id = kwargs.get("document_id") or context.get("document_id")
    if not document_id:
        raise ValueError("summarize_document tool requires 'document_id'")
    
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise ValueError(f"Document {document_id} not found in database.")
    
    summary_prompt = f"Summarize the following document content in 2-3 concise sentences. Focus on the core actors, amounts, dates, and intent:\n\n{document.content[:3000]}"
    
    if settings.OPENAI_API_KEY:
        try:
            client = OpenAI(
                api_key=settings.OPENAI_API_KEY,
                base_url=settings.OPENAI_API_BASE
            )
            response = client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "You are a helpful, precise operational summarizer."},
                    {"role": "user", "content": summary_prompt}
                ],
                temperature=0.0
            )
            summary = response.choices[0].message.content.strip()
        except Exception as e:
            logger.warning(f"Live OpenAI summarization failed: {str(e)}. Using fallback.")
            summary = f"FALLBACK SUMMARY: Document contains text of size {len(document.content)} characters. Filename is {document.filename}."
    else:
        # Mock summarizer
        sentences = [s.strip() for s in document.content.split(".") if len(s.strip()) > 15]
        summary = " ".join(sentences[:3]) if sentences else f"Document summary for {document.filename}."

    return {
        "status": "success",
        "summary": summary
    }

def detect_anomalies_tool(db: Session, context: dict, **kwargs):
    document_id = kwargs.get("document_id") or context.get("document_id")
    if not document_id:
        raise ValueError("detect_anomalies tool requires 'document_id'")
    
    # Check if invoice or payroll anomaly exists
    from modules.invoice_automation.models import Anomaly
    anomalies = db.query(Anomaly).filter(Anomaly.document_id == document_id).all()
    
    return {
        "status": "success",
        "anomalies_found": len(anomalies),
        "anomalies": [a.to_dict() for a in anomalies]
    }

def send_email_tool(db: Session, context: dict, **kwargs):
    recipient = kwargs.get("recipient") or context.get("recipient") or "admin@syntra.os"
    subject = kwargs.get("subject") or context.get("subject") or "Syntra OS Notification"
    body = kwargs.get("body") or context.get("body") or "This is an automated workflow notification."
    
    logger.info(f"MOCK EMAIL SENT to {recipient} with subject '{subject}'")
    return {
        "status": "success",
        "recipient": recipient,
        "subject": subject,
        "message": "Email sent successfully (mocked)."
    }

def generate_report_tool(db: Session, context: dict, **kwargs):
    content = kwargs.get("content") or context.get("content") or "No findings provided."
    title = kwargs.get("title") or context.get("title") or "Syntra OS Operational Audit Report"
    
    report_text = f"=== {title} ===\nRun Time: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\nFindings Summary:\n{content}\n\nReport verified by Syntra OS Agent Engine."
    return {
        "status": "success",
        "report_title": title,
        "report_text": report_text
    }

# Create a global instance
tool_registry = ToolRegistry()

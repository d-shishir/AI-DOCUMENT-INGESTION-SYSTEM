from sqlalchemy.orm import Session
from sqlalchemy import func, case
from typing import Dict, Any
from .models import AITrace, TraceStep, SystemErrorLog, RAGQualityMetric, ToolCallMetric, SystemMetric

class MetricsCollector:
    """
    Utility to aggregate system-wide operational and performance metrics.
    Queries database tables directly to compute real-time averages, counts, and ratios.
    """
    @staticmethod
    def get_system_metrics(db: Session) -> Dict[str, Any]:
        # 1. General counts
        total_requests = db.query(AITrace).count()
        success_requests = db.query(AITrace).filter(AITrace.status == "success").count()
        failed_requests = db.query(AITrace).filter(AITrace.status == "failed").count()
        running_requests = db.query(AITrace).filter(AITrace.status == "running").count()
        
        error_rate = 0.0
        if total_requests > 0:
            error_rate = round(failed_requests / total_requests, 4)

        # 2. Latencies
        avg_latency = db.query(func.avg(AITrace.total_latency_ms)).filter(AITrace.status != "running").scalar() or 0.0
        avg_latency = round(float(avg_latency), 2)

        # 3. Module Breakdown (average latency and counts per module)
        module_metrics = {}
        modules = ["workflow", "agent", "rag", "crm", "finance", "document_ingestion"]
        for mod in modules:
            mod_count = db.query(AITrace).filter(AITrace.module == mod).count()
            mod_success = db.query(AITrace).filter(AITrace.module == mod, AITrace.status == "success").count()
            mod_failed = db.query(AITrace).filter(AITrace.module == mod, AITrace.status == "failed").count()
            
            mod_avg_lat = db.query(func.avg(AITrace.total_latency_ms)).filter(AITrace.module == mod, AITrace.status != "running").scalar() or 0.0
            mod_success_rate = 1.0
            if mod_count > 0:
                mod_success_rate = round(mod_success / mod_count, 4)

            module_metrics[mod] = {
                "count": mod_count,
                "avg_latency_ms": round(float(mod_avg_lat), 2),
                "success_rate": mod_success_rate,
                "failed_count": mod_failed
            }

        # 4. RAG Quality Averages
        rag_metrics = db.query(
            func.avg(RAGQualityMetric.context_relevance),
            func.avg(RAGQualityMetric.hallucination_score),
            func.avg(RAGQualityMetric.answer_confidence)
        ).first()

        context_relevance = round(float(rag_metrics[0] or 1.0), 3)
        hallucination_score = round(float(rag_metrics[1] or 0.0), 3)
        answer_confidence = round(float(rag_metrics[2] or 1.0), 3)

        # 5. Tool Call Metrics
        tools_summary = {}
        tool_rows = db.query(
            ToolCallMetric.tool_name,
            func.count(ToolCallMetric.id),
            func.avg(ToolCallMetric.latency_ms),
            func.sum(case((ToolCallMetric.status == "failed", 1), else_=0))
        ).group_by(ToolCallMetric.tool_name).all()

        for t_name, count, avg_lat, failed in tool_rows:
            tools_summary[t_name] = {
                "invocations": count,
                "avg_latency_ms": round(float(avg_lat or 0.0), 2),
                "failures": int(failed or 0)
            }

        # 6. LLM Token metrics
        total_tokens = db.query(func.sum(SystemMetric.metric_value))\
            .filter(SystemMetric.metric_name == "token_usage")\
            .scalar() or 0.0

        return {
            "total_requests": total_requests,
            "success_requests": success_requests,
            "failed_requests": failed_requests,
            "running_requests": running_requests,
            "error_rate": error_rate,
            "average_latency_ms": avg_latency,
            "modules": module_metrics,
            "rag": {
                "context_relevance": context_relevance,
                "hallucination_score": hallucination_score,
                "answer_confidence": answer_confidence
            },
            "tools": tools_summary,
            "total_tokens_used": int(total_tokens)
        }

metrics_collector = MetricsCollector()

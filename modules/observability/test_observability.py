import sys
import os
import uuid

# Ensure workspace root and backend root are in sys.path
dir_path = os.path.dirname(os.path.abspath(__file__))
root_path = os.path.abspath(os.path.join(dir_path, "..", ".."))
backend_path = os.path.abspath(os.path.join(dir_path, "..", "..", "backend"))

if root_path not in sys.path:
    sys.path.insert(0, root_path)
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from app.database import SessionLocal, engine, Base
import modules.observability.models

# Auto-create tables for testing
Base.metadata.create_all(bind=engine)

from modules.observability import trace_manager, TraceSession, logger, track_latency
from modules.observability.error_tracker import error_tracker
from modules.observability.metrics_collector import metrics_collector
from modules.observability.models import AITrace, TraceStep, ToolCallMetric, SystemErrorLog, RAGQualityMetric

# A test function to check latency tracking decorator
@track_latency("test_decorated_step", module="test_module")
def sample_timed_function(db):
    import time
    time.sleep(0.1)
    return "Done"

def test_observability_pipeline():
    print("🧪 Running Observability, Monitoring & Debugging Tests...")
    db = SessionLocal()
    try:
        # Test 1: Start a trace session
        print("1. Testing TraceSession context manager...")
        goal = "Audit payroll discrepancies"
        with TraceSession(module="agent", input_data=goal, db=db) as sess:
            t_id = sess.trace_id
            assert t_id is not None, "TraceSession did not generate a trace_id"
            
            # Verify the trace exists in the database
            trace = db.query(AITrace).filter(AITrace.trace_id == t_id).first()
            assert trace is not None, "Trace not found in DB"
            assert trace.module == "agent", f"Expected module 'agent', got '{trace.module}'"
            assert trace.status == "running", "Trace status should be 'running' inside context"

            # Test 2: Add step within trace session
            print("2. Testing trace steps adding...")
            step_id = trace_manager.add_step(
                trace_id=t_id,
                step_name="parse_payroll_excel",
                status="success",
                latency_ms=250,
                metadata={"rows": 100},
                db=db
            )
            assert step_id is not None, "Failed to write step log"
            
            step = db.query(TraceStep).filter(TraceStep.id == step_id).first()
            assert step is not None, "Step not found in DB"
            assert step.step_name == "parse_payroll_excel"

            # Test 3: Track latency decorator
            print("3. Testing @track_latency decorator...")
            val = sample_timed_function(db=db)
            assert val == "Done"
            
            # Verify decorator step was recorded
            dec_step = db.query(TraceStep).filter(
                TraceStep.trace_id == t_id, 
                TraceStep.step_name == "test_decorated_step"
            ).first()
            assert dec_step is not None, "Decorated latency step was not saved to DB"
            assert dec_step.latency_ms >= 100, f"Expected timing >= 100ms, got {dec_step.latency_ms}"

            # Test 4: Tool call tracking
            print("4. Testing tool call tracking...")
            tool_id = trace_manager.add_tool_call(
                trace_id=t_id,
                tool_name="detect_anomalies",
                input_params={"limit": 10},
                output_result={"anomalies_found": 3},
                latency_ms=85,
                status="success",
                db=db
            )
            assert tool_id is not None, "Failed to write tool call log"
            
            tool_call = db.query(ToolCallMetric).filter(ToolCallMetric.id == tool_id).first()
            assert tool_call is not None, "Tool call not found in DB"
            assert tool_call.tool_name == "detect_anomalies"

            # Test 5: Error logging
            print("5. Testing error traceback recording...")
            error_tracker.capture_error(
                module="agent",
                error_message="Mock JSON parse failure",
                stack_trace="Traceback: line 42 inside agent_manager.py",
                input_context={"raw_payload": "{invalid_json}"},
                trace_id=t_id,
                db=db
            )
            
            err = db.query(SystemErrorLog).filter(SystemErrorLog.trace_id == t_id).first()
            assert err is not None, "Error record not written to database"
            assert "JSON parse" in err.error_message

        # Verify trace closed successfully and updated total latency
        trace = db.query(AITrace).filter(AITrace.trace_id == t_id).first()
        assert trace.status == "success", f"Expected trace status 'success', got '{trace.status}'"
        assert trace.total_latency_ms >= 100, f"Expected total latency >= 100ms, got {trace.total_latency_ms}"
        print("✔ TraceSession ended correctly and closed stats.")

        # Test 6: RAG metrics
        print("6. Testing RAG Quality metrics persistence...")
        rag_trace_id = trace_manager.start_trace(module="rag", input_data="Mock query", db=db)
        
        rag_id = trace_manager.add_rag_metric(
            trace_id=rag_trace_id,
            query="Who is the CFO?",
            top_k=2,
            similarity_scores=[0.88, 0.72],
            context_relevance=1.0,
            hallucination_score=0.0,
            answer_confidence=0.98,
            retrieved_chunks=[{"content": "CFO is John."}],
            db=db
        )
        assert rag_id is not None
        trace_manager.end_trace(rag_trace_id, final_output="CFO is John.", status="success", db=db, latency_ms=120)

        rag_metric = db.query(RAGQualityMetric).filter(RAGQualityMetric.id == rag_id).first()
        assert rag_metric is not None
        assert rag_metric.answer_confidence == 0.98
        print("✔ RAG quality analytics verified.")

        # Test 7: Metrics Collector Aggregates
        print("7. Testing MetricsCollector summary calculations...")
        metrics = metrics_collector.get_system_metrics(db)
        assert metrics["total_requests"] >= 2, f"Expected >= 2 requests, got {metrics['total_requests']}"
        assert metrics["rag"]["answer_confidence"] > 0.0, "Expected answer confidence aggregated value"
        assert "detect_anomalies" in metrics["tools"], "Expected detect_anomalies tool metrics summarized"
        print("✔ Metrics collector summary verification complete.")

        print("\n🎉 ALL OBSERVABILITY SYSTEM TESTS PASSED SUCCESSFULLY! 🎉")
    except Exception as e:
        print(f"❌ TEST FAILED: {str(e)}")
        raise e
    finally:
        db.close()

if __name__ == "__main__":
    test_observability_pipeline()

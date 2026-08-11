from app.core.observability import metrics, TraceContext

def test_metrics_registry_counters_and_gauges():
    metrics.increment("deployments_total", 1)
    metrics.set_gauge("last_qa_score", 94.5)
    
    summary = metrics.get_metrics_summary()
    assert summary["counters"]["deployments_total"] >= 1
    assert summary["gauges"]["last_qa_score"] == 94.5

def test_trace_context_span_lifecycle():
    with TraceContext(
        operation_name="test_operation",
        project_id="test_proj",
        task_id="test_task",
        agent_name="TestAgent"
    ) as trace:
        assert trace.trace_id.startswith("trace_")
        assert trace.span_id.startswith("span_")
    
    assert trace.duration_ms >= 0.0

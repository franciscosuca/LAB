from httpbench.bench.metrics import RequestResult, ScenarioSummary, percentile


def test_percentile_basic():
    values = [10, 20, 30, 40, 50]
    assert percentile(values, 50) == 30
    assert percentile(values, 0) == 10
    assert percentile(values, 100) == 50


def test_percentile_empty():
    assert percentile([], 50) == 0.0


def test_percentile_single_value():
    assert percentile([42.0], 90) == 42.0


def test_request_result_ok_property():
    ok = RequestResult(
        protocol="HTTP/2", scenario="s", path="/x", status=200, bytes_received=10, ttfb=0.01, total_time=0.02
    )
    assert ok.ok is True

    server_error = RequestResult(
        protocol="HTTP/2", scenario="s", path="/x", status=500, bytes_received=0, ttfb=0.01, total_time=0.02
    )
    assert server_error.ok is False

    transport_error = RequestResult(
        protocol="HTTP/2",
        scenario="s",
        path="/x",
        status=None,
        bytes_received=0,
        ttfb=None,
        total_time=0.02,
        error="ConnectError: boom",
    )
    assert transport_error.ok is False


def test_scenario_summary_from_results():
    results = [
        RequestResult(protocol="HTTP/2", scenario="s", path="/x", status=200, bytes_received=100, ttfb=0.01, total_time=0.02),
        RequestResult(protocol="HTTP/2", scenario="s", path="/x", status=200, bytes_received=100, ttfb=0.02, total_time=0.03),
        RequestResult(protocol="HTTP/2", scenario="s", path="/x", status=500, bytes_received=0, ttfb=0.01, total_time=0.05),
    ]
    summary = ScenarioSummary.from_results("HTTP/2", "s", results, duration_s=1.0)

    assert summary.count == 3
    assert summary.errors == 1
    assert summary.total_bytes == 200  # only the 2 ok results count
    assert summary.total_ms.p50 > 0
    assert summary.throughput_rps == 2.0  # 2 ok results / 1.0s

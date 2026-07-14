from api_client import iter_sse_events


def test_iter_sse_events_parses_stream():
    lines = [
        "event: metadata",
        'data: {"thread_id": "thread-1"}',
        "",
        "event: token",
        'data: {"content": "Olá"}',
        "",
        "event: final",
        'data: {"finished": false}',
        "",
    ]

    events = list(iter_sse_events(lines))

    assert events == [
        ("metadata", {"thread_id": "thread-1"}),
        ("token", {"content": "Olá"}),
        ("final", {"finished": False}),
    ]

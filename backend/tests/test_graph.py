from backend.app.graph import build_graph


def test_graph_is_scaffolded():
    graph = build_graph()
    assert graph["steps"] == 8

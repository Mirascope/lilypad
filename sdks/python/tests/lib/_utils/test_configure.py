from lilypad import configure
from lilypad.lib._configure import lilypad_config
from lilypad.lib._utils.settings import get_settings


def test_configure_and_ctx():
    configure(api_key="A", project_id="P1")
    s = get_settings()
    assert (s.api_key, s.project_id) == ("A", "P1")

    with lilypad_config(api_key="B", project_id="P2"):
        inner = get_settings()
        assert (inner.api_key, inner.project_id) == ("B", "P2")

    outer = get_settings()
    assert (outer.api_key, outer.project_id) == ("A", "P1")

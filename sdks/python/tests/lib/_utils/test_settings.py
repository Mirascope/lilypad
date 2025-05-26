from lilypad import configure
from lilypad.lib._configure import lilypad_config
from lilypad.lib._utils.settings import get_settings


def test_configure_updates_settings():
    configure(api_key="KEY_A", project_id="PROJ_A")
    s = get_settings()
    assert s.api_key == "KEY_A" and s.project_id == "PROJ_A"


def test_context_manager_override():
    configure(api_key="KEY_A", project_id="PROJ_A")
    with lilypad_config(api_key="KEY_B", project_id="PROJ_B"):
        s_inside = get_settings()
        assert s_inside.api_key == "KEY_B"
        assert s_inside.project_id == "PROJ_B"
    # Back to the original
    s_outside = get_settings()
    assert s_outside.api_key == "KEY_A"
    assert s_outside.project_id == "PROJ_A"

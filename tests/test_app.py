import app


def test_app_globals_are_set_after_successful_setup() -> None:
    assert app.settings is None
    assert app.registry is None

    # After setup, globals should be not None.
    app.setup()

    assert app.settings is not None
    assert app.registry is not None

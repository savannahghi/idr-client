import app
from app.__main__ import main_pipeline_factory


def test_main() -> None:
    pipeline = main_pipeline_factory()
    assert pipeline is not None

    app.setup()
    pipeline.execute(None)

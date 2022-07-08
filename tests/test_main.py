"""Tests in the app.__main__ module."""
from app.__main__ import argparse_factory, main_pipeline_factory
from tests.core.factories import FakeTransportFactory


def test_argparse_factory() -> None:
    parser = argparse_factory()
    assert parser is not None


def test_main_pipeline_factory() -> None:
    pipeline = main_pipeline_factory(transport=FakeTransportFactory())
    assert pipeline is not None

from typing import Optional
from unittest import TestCase

import pytest

from app.core import AbstractDomainObject, IdentifiableDomainObject

from .factories import FakeDataSource, FakeDataSourceType, FakeExtractMetadata


class _SimpleDomainObject(AbstractDomainObject):
    """
    A simple concrete domain object implementation for testing methods on the
    ``AbstractDomainObject`` class.
    """

    first_name: str
    last_name: str
    middle_name: Optional[str]


class _SomeDomainObject(IdentifiableDomainObject):
    """
    A domain object that inherits from another domain object. The goal is to
    check whether annotations defined in base class are also inherited.
    """

    name: str
    description: Optional[str]


class TestAbstractDomainObject(TestCase):
    """Tests for the ``AbstractDomainObject`` base class."""

    def test_domain_object_initialization_with_all_params(self) -> None:
        """
        Assert that when given all parameters, a domain object should be
        initialized correctly and should not raise any errors.
        """

        domain_object1 = _SimpleDomainObject(
            first_name="Juha", last_name="Kalulu"
        )
        domain_object2 = _SimpleDomainObject(
            first_name="Juha", last_name="Kalulu", middle_name="Kijiko"
        )

        assert domain_object1 is not None
        assert domain_object1.first_name == "Juha"
        assert domain_object1.last_name == "Kalulu"
        assert domain_object1.middle_name is None
        assert domain_object2 is not None
        assert domain_object2.first_name == "Juha"
        assert domain_object2.last_name == "Kalulu"
        assert domain_object2.middle_name == "Kijiko"

    def test_domain_object_initialization_with_missing_params(self) -> None:
        """
        Assert that trying to initializer a domain object with missing params
        results in the expected exceptions being raised.
        """
        with pytest.raises(ValueError, match="last_name"):
            _SimpleDomainObject(first_name="Juha")

        with pytest.raises(ValueError, match="first_name"):
            _SimpleDomainObject(last_name="Kalulu")

        with pytest.raises(ValueError, match="id"):
            _SomeDomainObject(name="xyz", description="A good description.")

    def test_get_required_fields_class_method(self) -> None:
        """
        Assert that the ``AbstractDomainObject.get_required_fields()`` method
        returns the expected value.
        """

        self.assertListEqual(
            list(_SimpleDomainObject.get_required_fields()),
            ["first_name", "last_name"],
        )
        self.assertListEqual(
            list(_SomeDomainObject.get_required_fields()), ["name", "id"]
        )


class TestFakeDataSourceInterface(TestCase):
    """Tests for the ``DataSource`` interface default implementations."""

    def test_string_representation(self) -> None:
        """
        Assert that the default ``DataSource.__str__()`` implementation
        returns the expected value.
        """
        data_source = FakeDataSource(id="1", name="Some data source")
        assert str(data_source) == "1::Some data source"

    def test_of_mapping_class_method(self) -> None:
        """
        Assert that the ``DataSource.of_mapping()`` class method returns
        the expected value.
        """

        data_source1 = FakeDataSource.of_mapping(
            {
                "id": "1",
                "name": "Some data source",
                "description": "A very good description.",
            }
        )
        data_source2 = FakeDataSource.of_mapping(
            {
                "id": "2",
                "name": "Some other data source",
                "preferred_uploads_name": "some_data",
            }
        )

        assert data_source1 is not None
        assert data_source1.id == "1"
        assert data_source1.name == "Some data source"
        assert data_source1.description == "A very good description."
        assert data_source2 is not None
        assert data_source2.id == "2"
        assert data_source2.name == "Some other data source"
        assert data_source2.description is None


class TestFakeDataSourceTypeInterface(TestCase):
    """Tests for the ``DataSourceType`` interface default implementations."""

    def test_string_representation(self) -> None:
        """
        Assert that the default ``DataSourceType.__str__()`` implementation
        returns the expected value.
        """
        data_source = FakeDataSourceType(name="Some data source type")
        assert str(data_source) == "mock_data::Some data source type"


class TestExtractMetadataInterface(TestCase):
    """Tests for the ``ExtractMetadata`` interface default implementations."""

    def test_string_representation(self) -> None:
        """
        Assert that the default ``ExtractMetadata.__str__()`` implementation
        returns the expected value.
        """
        extract = FakeExtractMetadata(id="1", name="Some data")
        assert str(extract) == "1::Some data"

    def test_of_mapping_class_method(self) -> None:
        """
        Assert that the ``ExtractMetadata.of_mapping()`` class method returns
        the expected value.
        """

        extract1 = FakeExtractMetadata.of_mapping(
            {
                "id": "1",
                "name": "Some data",
                "description": "A very good description.",
            }
        )
        extract2 = FakeExtractMetadata.of_mapping(
            {
                "id": "2",
                "name": "Some other data",
                "preferred_uploads_name": "some_data",
            }
        )

        assert extract1 is not None
        assert extract1.id == "1"
        assert extract1.name == "Some data"
        assert extract1.description == "A very good description."
        assert extract1.preferred_uploads_name is None
        assert extract2 is not None
        assert extract2.id == "2"
        assert extract2.name == "Some other data"
        assert extract2.description is None
        assert extract2.preferred_uploads_name == "some_data"

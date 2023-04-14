from app.core import IDRClientException
from tests import TestCase


class TestIDRClientException(TestCase):
    """Tests for the ``IDRClientException`` class."""

    def test_accessors(self) -> None:
        """Assert ``IDRClientException`` accessors return expected values."""

        client_error1 = IDRClientException(message="Fatal error.")
        client_error2 = IDRClientException()

        assert client_error1.message == "Fatal error."
        assert client_error2.message is None

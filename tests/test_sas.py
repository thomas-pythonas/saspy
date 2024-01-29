import pytest
from unittest.mock import MagicMock, patch

from sas import Sas
from error_handler import *


@pytest.fixture
def sas_instance():
    with patch("serial.Serial"), patch("time.sleep"):
        sas = Sas(port="/dev/ttyUSB0")
        yield sas


@patch("serial.Serial")
def test_start_method(mock_serial):
    mock_serial_instance = mock_serial.return_value
    mock_serial_instance.read.return_value = b"\x01"

    with patch.object(mock_serial_instance, "isOpen", return_value=False):
        result = mock_serial_instance.start()

    assert result is not None
    assert mock_serial_instance.isOpen.called_once()
    assert mock_serial_instance.open.called_once()
    assert mock_serial_instance.flushOutput.called_once()
    assert mock_serial_instance.flushInput.called_once()
    assert mock_serial_instance.read.called_once_with(1)


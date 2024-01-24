import pytest
from unittest.mock import MagicMock, patch
from sas import Sas

@pytest.fixture
def sas_instance():
    # Mocking the serial class and some methods to avoid actual communication
    with patch('serial.Serial') as mock_serial:
        mock_serial_instance = mock_serial.return_value
        mock_serial_instance.read.return_value = b'\x01'  # I'm pretty that this is not enough
        sas = Sas(port="/dev/ttyUSB0")
        yield sas

def test_sas_init(sas_instance):
    assert sas_instance.address is None
    assert sas_instance.machine_n is None
    assert sas_instance.aft_get_last_transaction is True
    assert sas_instance.transaction is None

def test_start_method(sas_instance):
    # Mocking is_open
    sas_instance.is_open = MagicMock(return_value=False)

    # Mocking open
    sas_instance.open = MagicMock()

    # Mocking flushOutput, flushInput, and read methods
    sas_instance.connection.flushOutput.return_value = None
    sas_instance.connection.flushInput.return_value = None
    sas_instance.connection.read.return_value = b'\x01'  # Should be same as above

    # Mocking time.sleep to avoid actual sleep
    with patch('time.sleep'):
        result = sas_instance.start()

    assert result is None
    assert sas_instance.is_open.called_once()
    assert sas_instance.open.called_once()
    assert sas_instance.connection.flushOutput.called_once()
    assert sas_instance.connection.flushInput.called_once()
    assert sas_instance.connection.read.called_once_with(1)

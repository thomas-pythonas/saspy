from sas import Sas
from config_handler import *

# Let's init the configuration file
config_handler = ConfigHandler()
config_handler.read_config_file()


sas = Sas(
    port=config_handler.get_config_value("connection", "serial_port"),
    timeout=config_handler.get_config_value("connection", "timeout"),
    poll_address=config_handler.get_config_value("events", "poll_address"),
    denom=config_handler.get_config_value("machine", "denomination"),
    asset_number=config_handler.get_config_value("machine", "asset_number"),
    reg_key=config_handler.get_config_value("machine", "reg_key"),
    pos_id=config_handler.get_config_value("machine", "pos_id"),
    key=config_handler.get_config_value("security", "key"),
    debug_level="DEBUG",
    perpetual=config_handler.get_config_value("connection", "infinite"),
)

print(sas.start())
print(sas.sas_version_gaming_machine_serial_id())
print(sas.gaming_machine_id())
print(sas.aft_in(15.00))
print(sas.aft_clean_transaction_poll())
print(sas.current_credits())

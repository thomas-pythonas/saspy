import yaml


class ConfigHandler:
    def __init__(self, file_path="config.yml"):
        self.config_file_path = file_path
        self.config = None

    def read_config_file(self):
        with open(self.config_file_path, "r") as yaml_file:
            self.config = yaml.safe_load(yaml_file)

    def get_config_value(self, section, key):
        if self.config:
            return self.config.get(section, {}).get(key)
        else:
            raise ValueError("Configuration not loaded. Call read_config_file first.")

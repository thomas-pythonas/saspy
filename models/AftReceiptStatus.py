class AftReceiptStatus:
    """Class representing the receipt status for AFT"""

    STATUS_MAP = {
        "00": "Receipt printed",
        "20": "Receipt printing in progress (not complete)",
        "40": "Receipt pending (not complete)",
        "ff": "No receipt requested or receipt not printed",
    }

    @classmethod
    def get_status(cls, key):
        """Get the status value for the given key.

        Args:
            key (str): The key for the status.

        Returns:
            str: The corresponding status value or an error message if the key is not found.
        """
        # Use get() method to retrieve the value, or return an error message.
        return cls.STATUS_MAP.get(key, f"Unknown key: {key}")

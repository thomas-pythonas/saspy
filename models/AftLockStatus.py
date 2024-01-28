class AftLockStatus:
    """Class representing the lock status for AFT"""

    STATUS_MAP = {
        "00": "Game locked",
        "40": "Game lock pending",
        "ff": "Game not locked",
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

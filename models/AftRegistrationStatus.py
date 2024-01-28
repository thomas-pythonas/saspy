class AftRegistrationStatus:
    """Class representing the registration status for AFT"""

    STATUS_MAP = {
        "00": "Gaming machine registration ready",
        "01": "Gaming machine registered",
        "40": "Gaming machine registration pending",
        "80": "Gaming machine not registered",
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

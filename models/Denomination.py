class Denomination:
    """Class representing the Denominations"""

    STATUS_MAP = {
        "00": None,
        "01": 0.01,
        "17": 0.02,
        "02": 0.05,
        "03": 0.10,
        "04": 0.25,
        "05": 0.50,
        "06": 1.00,
        "07": 5.00,
        "08": 10.00,
        "09": 20.00,
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

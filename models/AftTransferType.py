class AftTransferType:
    """Class representing the transfer type for AFT"""

    STATUS_MAP = {
        "00": "Transfer in-house amount from host to gaming machine",
        "10": "Transfer bonus coin out win amount from host to gaming machine",
        "11": "Transfer bonus jackpot win amount from host to gaming machine (force attendant pay lockup)",
        "20": "Transfer in-house amount from host to ticket (only one amount type allowed per transfer)",
        "40": "Transfer debit amount from host to gaming machine",
        "60": "Transfer debit amount from host to ticket",
        "80": "Transfer in-house amount from gaming machine to host",
        "90": "Transfer win amount (in-house) from gaming machine to host",
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

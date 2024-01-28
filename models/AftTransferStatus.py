class AftTransferStatus:
    """Class representing the transfer status for AFT"""

    STATUS_MAP = {
        "00": "Full transfer successful",
        "01": "Partial transfer successful Binary codes 010xxxxx indicate transfer pending",
        "40": "Transfer pending (not complete)",
        "80": "Transfer cancelled by host",
        "81": "Transaction ID not unique (same as last successful transfer logged in history)",
        "82": "Not a valid transfer function (unsupported type, amount, index, etc.)",
        "83": "Not a valid transfer amount or expiration (non-BCD, etc.)",
        "84": "Transfer amount exceeds the gaming machine transfer limit",
        "85": "Transfer amount not an even multiple of gaming machine denomination",
        "86": "Gaming machine unable to perform partial transfers to the host",
        "87": "Gaming machine unable to perform transfers at this time (door open, tilt, disabled, cashout in progress, etc.)",
        "88": "Gaming machine not registered (required for debit transfers)",
        "89": "Registration key does not match",
        "8a": "No POS ID (required for debit transfers)",
        "8b": "No won credits available for cashout",
        "8c": "No gaming machine denomination set (unable to perform cents to credits conversion)",
        "8d": "Expiration not valid for transfer to ticket (already expired)",
        "8e": "Transfer to ticket device not available",
        "8f": "Unable to accept transfer due to existing restricted amounts from different pool",
        "90": "Unable to print transaction receipt (receipt device not currently available)",
        "91": "Insufficient data to print transaction receipt (required fields missing)",
        "92": "Transaction receipt not allowed for specified transfer type",
        "93": "Asset number zero or does not match",
        "94": "Gaming machine not locked (transfer specified lock required)",
        "95": "Transaction ID not valid",
        "9f": "Unexpected error Binary codes 110xxxxx indicate incompatible or unsupported poll",
        "c0": "Not compatible with current transfer in progress",
        "c1": "Unsupported transfer code Binary codes 111xxxxx indicate no transfer information available",
        "ff": "No transfer information available",
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

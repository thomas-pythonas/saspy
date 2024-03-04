class AftStatements:
    """Class representing the statements for AFT"""

    STATUS_MAP = {
        "registration_status": [],
        "asset_number": [],
        "registration_key": [],
        "POS_ID": [],
        "transaction_buffer_position": [],
        "transfer_status": [],
        "receipt_status": [],
        "transfer_type": [],
        "cashable_amount": [],
        "restricted_amount": [],
        "nonrestricted_amount": [],
        "transfer_flags": [],
        "transaction_ID_lenght": [],
        "transaction_ID": [],
        "transaction_date": [],
        "transaction_time": [],
        "expiration": [],
        "pool_ID": [],
        "cumulative_casable_amount_meter_size": [],
        "cumulative_casable_amount_meter": [],
        "cumulative_restricted_amount_meter_size": [],
        "cumulative_restricted_amount_meter": [],
        "cumulative_nonrestricted_amount_meter_size": [],
        "cumulative_nonrestricted_amount_meter": [],
        "game_lock_status": [],
        "avilable_transfers": [],
        "host_cashout_status": [],
        "AFT_status": [],
        "max_buffer_index": [],
        "current_cashable_amount": [],
        "current_restricted_amount": [],
        "current_non_restricted_amount": [],
        "restricted_expiration": [],
        "restricted_pool_ID": [],
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

    @classmethod
    def get_non_empty_status_map(cls):
        """Return a dictionary containing only keys with non-empty values."""
        non_empty_map = {key: value for key, value in cls.STATUS_MAP.items() if value}
        return non_empty_map

class Tito:
    """Class representing the TITO"""

    STATUS_MAP = {
        "asset_number": [],
        "status_bits": [],
        "cashable_ticket_receipt_exp": [],
        "restricted_ticket_exp": [],
        "cashout_ticket_number": [],
        "cashout_amount_in_cents": [],
        "machine_ID": [],
        "sequence_numbercashout_type": [],
        "cashout_amount": [],
        "validation_type": [],
        "index_number": [],
        "date_validation_operation": [],
        "time_validation_operation": [],
        "validation_number": [],
        "ticket_amount": [],
        "ticket_number": [],
        "validation_system_ID": [],
        "expiration_date_printed_on_ticketpool_id": [],
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

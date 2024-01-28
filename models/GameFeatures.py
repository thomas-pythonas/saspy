class GameFeatures:
    """Class representing the Game Features"""

    STATUS_MAP = {
        "game_number": [],
        "jackpot_multiplier": [],
        "AFT_bonus_awards": [],
        "legacy_bonus_awards": [],
        "tournament": [],
        "validation_extensions": [],
        "validation_style": [],
        "ticket_redemption": [],
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

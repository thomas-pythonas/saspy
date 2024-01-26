from dataclasses import dataclass


@dataclass
class GameFeatures:
    game_number: str
    jackpot_multiplier: str
    AFT_bonus_awards: str
    legacy_bonus_awards: str
    tournament: str
    validation_extensions: str
    validation_style: str
    ticket_redemption: str


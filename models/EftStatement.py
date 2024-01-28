from dataclasses import dataclass


@dataclass
class EftStatement:
    eft_status: str
    promo_amount: str
    cashable_amount: str
    eft_transfer_counter: str

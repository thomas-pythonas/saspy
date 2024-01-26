from dataclasses import dataclass


@dataclass
class TitoStatement:
    asset_number: str
    status_bits: str
    cashable_ticket_receipt_exp: str
    restricted_ticket_exp: str
    cashout_ticket_number: str
    cashout_amount_in_cents: str
    machine_id: str
    sequence_numbercashout_type: str
    cashout_amount: str
    validation_type: str
    index_number: str
    date_validation_operation: str
    time_validation_operation: str
    validation_number: str
    ticket_amount: str
    ticket_number: str
    validation_system_id: str
    expiration_date_printed_on_ticketpool_id: str
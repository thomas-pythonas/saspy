from dataclasses import dataclass


@dataclass
class AftStatement:
    registration_status: str
    asset_number: str
    registration_key: str
    pos_id: str
    transaction_buffer_position: str
    transfer_status: str
    receipt_status: str
    transfer_type: str
    cashable_amount: str
    restricted_amount: str
    nonrestricted_amount: str
    transfer_flags: str
    transaction_ID_length: str
    transaction_ID: str
    transaction_date: str
    transaction_time: str
    expiration: str
    pool_id: str
    cumulative_cashable_amount_meter_size: str
    cumulative_cashable_amount_meter: str
    cumulative_restricted_amount_meter_size: str
    cumulative_restricted_amount_meter: str
    cumulative_nonrestricted_amount_meter_size: str
    cumulative_nonrestricted_amount_meter: str
    game_lock_status: str
    available_transfers: str
    host_cashout_status: str
    aft_status: str
    max_buffer_index: str
    current_cashable_amount: str
    current_restricted_amount: str
    current_non_restricted_amount: str
    restricted_expiration: str
    restricted_pool_id: str
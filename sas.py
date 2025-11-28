#!/usr/bin/env python3
# -*- coding: utf8 -*-
# import bcd
import serial
import time
import binascii
import os
# import string
from PyCRC.CRC16Kermit import CRC16Kermit
from array import array

# ser = serial.Serial('/dev/ttyS3','19200', timeout=1)  # open first serial port
data_to_sent = [0x01, 0x21, 0x00, 0x00]
# adress=1
# print "OK"
from multiprocessing import log_to_stderr
import logging
import datetime

EVENTS_POLL_TIMEOUT = 0.2
# SLEEP_IF_FORMAT_TRANSACTION = 0
AFT_LOCK_STATUS = {'00': 'Game locked', '40': 'Game lock pending', 'ff': 'Game not locked'}
AFT_REGISTRACION_STATUS = {'00': 'Gaming machine registration ready', '01': 'Gaming machine registered',
                           '40': 'Gaming machine registration pending', '80': 'Gaming machine not registered'}
AFT_TRANSFER_STATUS = {
    '00': 'Full transfer successful',
    '01': 'Partial transfer successful Binary codes 010xxxxx indicate transfer pending',
    '40': 'Transfer pending (not complete)',
    '80': 'Transfer cancelled by host',
    '81': 'Transaction ID not unique (same as last successful transfer logged in history)',
    '82': 'Not a valid transfer function (unsupported type, amount, index, etc.)',
    '83': 'Not a valid transfer amount or expiration (non-BCD, etc.)',
    '84': 'Transfer amount exceeds the gaming machine transfer limit',
    '85': 'Transfer amount not an even multiple of gaming machine denomination',
    '86': 'Gaming machine unable to perform partial transfers to the host',
    '87': 'Gaming machine unable to perform transfers at this time (door open, tilt, disabled, cashout in progress, etc.)',
    '88': 'Gaming machine not registered (required for debit transfers)',
    '89': 'Registration key does not match',
    '8a': 'No POS ID (required for debit transfers)',
    '8b': 'No won credits available for cashout',
    '8c': 'No gaming machine denomination set (unable to perform cents to credits conversion)',
    '8d': 'Expiration not valid for transfer to ticket (already expired)',
    '8e': 'Transfer to ticket device not available',
    '8f': 'Unable to accept transfer due to existing restricted amounts from different pool',
    '90': 'Unable to print transaction receipt (receipt device not currently available)',
    '91': 'Insufficient data to print transaction receipt (required fields missing)',
    '92': 'Transaction receipt not allowed for specified transfer type',
    '93': 'Asset number zero or does not match',
    '94': 'Gaming machine not locked (transfer specified lock required)',
    '95': 'Transaction ID not valid',
    '9f': 'Unexpected error Binary codes 110xxxxx indicate incompatible or unsupported poll',
    'c0': 'Not compatible with current transfer in progress',
    'c1': 'Unsupported transfer code Binary codes 111xxxxx indicate no transfer information available',
    'ff': 'No transfer information available',
    # ' ': 'No response',
}

AFT_RECEIPT_STATUS = {
    '00': 'Receipt printed',
    '20': 'Receipt printing in progress (not complete)',
    '40': 'Receipt pending (not complete)',
    'ff': 'No receipt requested or receipt not printed',
}

AFT_TRANSFER_TYPE = {
    '00': 'Transfer in-house amount from host to gaming machine',
    '10': 'Transfer bonus coin out win amount from host to gaming machine',
    '11': 'Transfer bonus jackpot win amount from host to gaming machine (force attendant pay lockup)',
    '20': 'Transfer in-house amount from host to ticket (only one amount type allowed per transfer)',
    '40': 'Transfer debit amount from host to gaming machine',
    '60': 'Transfer debit amount from host to ticket',
    '80': 'Transfer in-house amount from gaming machine to host',
    '90': 'Transfer win amount (in-house) from gaming machine to host',

}
DENOMINATION = {
    '00': None,
    '01': 0.01,
    '17': 0.02,
    '02': 0.05,
    '03': 0.10,
    '04': 0.25,
    '05': 0.50,
    '06': 1.00,
    '07': 5.00,
    '08': 10.00,
    '09': 20.00,
}

GPOLL = {
    '00': 'No activity',
    '01': 'No Response',
    '11': 'Slot door was opened',
    '12': 'Slot door was closed',
    '13': 'Drop door was opened',
    '14': 'Drop door was closed',
    '15': 'Card cage was opened',
    '16': 'Card cage was closed',
    '17': 'AC power was applied to gaming machine',
    '18': 'AC power was lost from gaming machine',
    '19': 'Cashbox door was opened',
    '1a': 'Cashbox door was closed',
    '1b': 'Cashbox was removed',
    '1c': 'Cashbox was installed',
    '1d': 'Belly door was opened',
    '1e': 'Belly door was closed',
    '1f': 'No activity and waiting for player input (obsolete)',
    '20': '''General tilt (Use this tilt when other exception tilt codes do not apply or 
          when the tilt condition cannot be determined.)''',
    '21': 'Coin in tilt',
    '22': 'Coin out tilt',
    '23': 'Hopper empty detected',
    '24': 'Extra coin paid',
    '25': 'Diverter malfunction (controls coins to drop or hopper)',
    '27': 'Cashbox full detected',
    '28': 'Bill jam',
    '29': 'Bill acceptor hardware failure',
    '2a': 'Reverse bill detected',
    '2b': 'Bill rejected',
    '2c': 'Counterfeit bill detected',
    '2d': 'Reverse coin in detected',
    '2e': 'Cashbox near full detected',
    '31': 'CMOS RAM error (data recovered from EEPROM)',
    '32': 'CMOS RAM error (no data recovered from EEPROM)',
    '33': 'CMOS RAM error (bad device)',
    '34': 'EEPROM error (data error)',
    '35': 'EEPROM error (bad device)',
    '36': 'EPROM error (different checksum – version changed)',
    '37': 'EPROM error (bad checksum compare)',
    '38': 'Partitioned EPROM error (checksum – version changed)',
    '39': 'Partitioned EPROM error (bad checksum compare)',
    '3a': 'Memory error reset (operator used self test switch)',
    '3b': 'Low backup battery detected',
    '3c': '''Operator changed options (This is sent whenever the operator changes
          configuration options. This includes, but is not limited to, denomination,
          gaming machine address, or any option that affects the response to long polls
          1F, 53, 54, 56, A0, B2, B3, B4, or B5.)''',
    '3d': 'A cash out ticket has been printed',
    '3e': 'A handpay has been validated',
    '3f': 'Validation ID not configured',
    '40': 'Reel Tilt (Which reel is not specified.)',
    '41': 'Reel 1 tilt',
    '42': 'Reel 2 tilt',
    '43': 'Reel 3 tilt',
    '44': 'Reel 4 tilt',
    '45': 'Reel 5 tilt',
    '46': 'Reel mechanism disconnected',
    '47': '$1.00 bill accepted (non-RTE only)',
    '48': '$5.00 bill accepted (non-RTE only)',
    '49': '$10.00 bill accepted (non-RTE only)',
    '4a': '$20.00 bill accepted (non-RTE only)',
    '4b': '$50.00 bill accepted (non-RTE only)',
    '4c': '$100.00 bill accepted (non-RTE only)',
    '4d': '$2.00 bill accepted (non-RTE only)',
    '4e': '$500.00 bill accepted (non-RTE only)',
    '4f': 'Bill accepted (In non-RTE mode, use this exception for all bills without a specific exception. In RTE mode, use for all bill denominations.)',
    '50': '$200.00 bill accepted (non-RTE only)',
    '51': 'Handpay is pending (Progressive, non-progressive or cancelled credits)',
    '52': 'Handpay was reset (Jackpot reset switch activated)',
    '53': 'No progressive information has been received for 5 seconds',
    '54': 'Progressive win (cashout device/credit paid)',
    '55': 'Player has cancelled the handpay request',
    '56': 'SAS progressive level hit',
    '57': 'System validation request',
    '60': 'Printer communication error',
    '61': 'Printer paper out error',
    '66': 'Cash out button pressed',
    '67': 'Ticket has been inserted',
    '68': 'Ticket transfer complete',
    '69': 'AFT transfer complete',
    '6a': 'AFT request for host cashout',
    '6b': 'AFT request for host to cash out win',
    '6c': 'AFT request to register',
    '6d': 'AFT registration acknowledged',
    '6e': 'AFT registration cancelled',
    '6f': 'Game locked',
    '70': 'Exception buffer overflow',
    '71': 'Change lamp on',
    '72': 'Change lamp off',
    '74': 'Printer paper low',
    '75': 'Printer power off',
    '76': 'Printer power on',
    '77': 'Replace printer ribbon',
    '78': 'Printer carriage jammed',
    '79': 'Coin in lockout malfunction (coin accepted while coin mech disabled)',
    '7a': 'Gaming machine soft (lifetime-to-date) meters reset to zero',
    '7b': 'Bill validator (period) totals have been reset by an attendant/operator',
    '7c': 'A legacy bonus pay awarded and/or a multiplied jackpot occurred',
    '7e': 'Game has started',
    '7f': 'Game has ended',
    '80': 'Hopper full detected',
    '81': 'Hopper level low detected',
    '82': 'Display meters or attendant menu has been entered',
    '83': 'Display meters or attendant menu has been exited',
    '84': 'Self test or operator menu has been entered',
    '85': 'Self test or operator menu has been exited',
    '86': 'Gaming machine is out of service (by attendant)',
    '87': 'Player has requested draw cards (only send when in RTE mode)',
    '88': 'Reel N has stopped (only send when in RTE mode)',
    '89': '''Coin/credit wagered (only send when in RTE mode, and only send if the
          configured max bet is 10 or less)''',
    '8a': 'Game recall entry has been displayed',
    '8b': 'Card held/not held (only send when in RTE mode)',
    '8c': 'Game selected',
    '8e': 'Component list changed',
    '8f': 'Authentication complete',
    '98': 'Power off card cage access',
    '99': 'Power off slot door access',
    '9a': 'Power off cashbox door access',
    '9b': 'Power off drop door access'
}
meters = dict.fromkeys(('total_cancelled_credits_meter',
                        'total_in_meter',
                        'total_out_meter',
                        'total_in_meter',
                        'total_jackpot_meter',
                        'games_played_meter',
                        'games_won_meter',
                        'games_lost_meter',
                        'games_last_power_up',
                        'games_last_slot_door_close',
                        'slot_door_opened_meter',
                        'power_reset_meter',
                        's1_bills_accepted_meter',
                        's5_bills_accepted_meter',
                        's10_bills_accepted_meter',
                        's20_bills_accepted_meter',
                        's50_bills_accepted_meter',
                        's100_bills_accepted_meter',
                        's500_bills_accepted_meter',
                        's1000_bills_accepted_meter',
                        's200_bills_accepted_meter',
                        's25_bills_accepted_meter',
                        's2000_bills_accepted_meter',
                        's2500_bills_accepted_meter',
                        's5000_bills_accepted_meter',
                        's10000_bills_accepted_meter',
                        's20000_bills_accepted_meter',
                        's25000_bills_accepted_meter',
                        's50000_bills_accepted_meter',
                        's100000_bills_accepted_meter',
                        's250_bills_accepted_meter',
                        'cashout_ticket_number',
                        'cashout_amount_in_cents',
                        'ASCII_game_ID',
                        'ASCII_additional_ID',
                        'bin_denomination',
                        'bin_max_bet',
                        'bin_progressive_mode',
                        'bin_game_options',
                        'ASCII_paytable_ID',
                        'ASCII_base_percentage',
                        'bill_meter_in_dollars',
                        'ROM_signature',
                        'current_credits',
                        'bin_level',
                        'amount',
                        'partial_pay_amount',
                        'bin_reset_ID',
                        'bill_meter_in_dollars',
                        'true_coin_in',
                        'true_coin_out',
                        'current_hopper_level',
                        'credit_amount_of_all_bills_accepted',
                        'coin_amount_accepted_from_external_coin_acceptor',
                        'country_code',
                        'bill_denomination',
                        'meter_for_accepted_bills',
                        'number_bills_in_stacker',
                        'credits_SAS_in_stacker',
                        'machine_ID',
                        'sequence_number',
                        'validation_type',
                        'index_number',
                        'date_validation_operation',
                        'time_validation_operation',
                        'validation_number',
                        'ticket_amount',
                        'ticket_number',
                        'validation_system_ID',
                        'expiration_date_printed_on_ticket',
                        'pool_id',
                        'current_hopper_lenght',
                        'current_hopper_ststus',
                        'current_hopper_percent_full',
                        'current_hopper_level',
                        'bin_validation_type',
                        'total_validations',
                        'cumulative_amount',
                        'total_number_of_games_impemented',
                        'game_n_number',
                        'game_n_coin_in_meter',
                        'game_n_coin_out_meter',
                        'game_n_jackpot_meter',
                        'geme_n_games_played_meter',
                        'game_n_number_config',
                        'game_n_ASCII_game_ID',
                        'game_n_ASCII_additional_id',
                        'game_n_bin_denomination',
                        'game_n_bin_max_bet',
                        'game_n_bin_progressive_group',
                        'game_n_bin_game_options',
                        'game_n_ASCII_paytable_ID',
                        'game_n_ASCII_base_percentage',
                        'ASCII_SAS_version',
                        'ASCII_serial_number',
                        'selected_game_number',
                        'number_of_enabled_games',
                        'enabled_games_numbers',
                        'cashout_type',
                        'cashout_amount',
                        'ticket_status',
                        'ticket_amount',
                        'parsing_code',
                        'validation_data',
                        'registration_status',
                        'asset_number',
                        'registration_key',
                        'POS_ID',
                        'game_lock_status',
                        'avilable_transfers',
                        'host_cashout_status',
                        'AFT_ststus',
                        'max_buffer_index',
                        'current_cashable_amount',
                        'current_restricted_amount',
                        'current_non_restricted_amount',
                        'restricted_expiration',
                        'restricted_pool_ID',
                        'game_number',
                        'features_1',
                        'features_2',
                        'features_3'

                        ), [])
aft_statement = dict.fromkeys((
    'registration_status',
    'asset_number',
    'registration_key',
    'POS_ID',
    'transaction_buffer_position',
    'transfer_status',
    'receipt_status',
    'transfer_type',
    'cashable_amount',
    'restricted_amount',
    'nonrestricted_amount',
    'transfer_flags',
    'asset_number',
    'transaction_ID_lenght',
    'transaction_ID',
    'transaction_date',
    'transaction_time',
    'expiration',
    'pool_ID',
    'cumulative_casable_amount_meter_size',
    'cumulative_casable_amount_meter',
    'cumulative_restricted_amount_meter_size',
    'cumulative_restricted_amount_meter',
    'cumulative_nonrestricted_amount_meter_size',
    'cumulative_nonrestricted_amount_meter',
    'asset_number',
    'game_lock_status',
    'avilable_transfers',
    'host_cashout_status',
    'AFT_status',
    'max_buffer_index',
    'current_cashable_amount',
    'current_restricted_amount',
    'current_non_restricted_amount',
    'restricted_expiration',
    'restricted_pool_ID',

), [])
tito_statement = dict.fromkeys((
    'asset_number',
    'status_bits',
    'cashable_ticket_reciept_exp',
    'restricted_ticket_exp',
    'cashout_ticket_number',
    'cashout_amount_in_cents',
    'machine_ID',
    'sequence_number'
    'cashout_type',
    'cashout_amount',
    'validation_type',
    'index_number',
    'date_validation_operation',
    'time_validation_operation',
    'validation_number',
    'ticket_amount',
    'ticket_number',
    'validation_system_ID',
    'expiration_date_printed_on_ticket'
    'pool_id'
), [])

eft_statement = dict.fromkeys((
    'eft_status',
    'promo_amount',
    'cashable_amount',
    'eft_transfer_counter'

), [])
game_features = dict.fromkeys((
    'game_number',
    'jackpot_multiplier',
    'AFT_bonus_avards',
    'legacy_bonus_awards',
    'tournament',
    'validation_extensions',
    'validation_style',
    'ticket_redemption'
), [])


class BadCRC(Exception):
    pass


class BadCommand(Exception):
    pass


class AFTBadAmount(Exception):
    pass


class BadTransactionID(Exception):
    pass


class NoSasConnection(Exception):
    pass


class SASOpenError(Exception):
    pass


class EMGGpollBadResponse(Exception):
    pass


class Sas():

    def __init__(self, port, timeout=2, log=None, sleep_time=0.02, poll_adress=0x82, aft_check_last_transaction=True, sas_dump=False, denom=0.01, lock_time=0, get_aft_transaction_from_EMG=False,):
        # self.poll_adres = '82'
        self.adress = None
        self.mashin_n = None
        self.sleep_time = sleep_time
        self.lock_time = lock_time
        self.aft_check_last_transaction = aft_check_last_transaction
        # self.last_transaction_n = None
        self.asset_number = '01000000'
        self.reg_key = '0000000000000000000000000000000000000000'
        self.POS_ID = 'B374A402'
        self.transaction = None
        # self.my_key = '44'
        self.poll_adress = poll_adress
        self.denom = denom
        self.sas_dump = sas_dump
        self.event = None
        self.last_AFT_lock_status = False
        self.get_aft_transaction_from_EMG = get_aft_transaction_from_EMG
        if self.sas_dump:
            os.system('sudo touch /var/log/sas_dump.log')
            os.system('sudo chown colibri:colibri /var/log/sas_dump.log')
            self.my_log = open('/var/log/sas_dump.log', 'a')
            self.my_log.close()
        if log == None:
            self.log = log_to_stderr()
            self.log.setLevel(logging.INFO)
        else:
            self.log = log
        while 1:
            try:
                # print 1
                self.connection = serial.Serial(port=port, baudrate=19200, timeout=timeout)
                self.close()
                self.timeout = timeout
                self.log.info('SAS Port OK!')
                break
            except:
                self.log.critical("SAS Port error")
                time.sleep(1)
        return

    def is_open(self):
        return self.connection.isOpen()

    def clean_buffer(self):
        try:
            if self.is_open() == False:
                self.open()
            self.connection.reset_output_buffer()
            self.connection.reset_output_buffer()
        except Exception as e:
            self.log.error(e, exc_info=True)
        self.close()

    def flush(self):
        try:
            if self.is_open() == False:
                self.open()
            self.connection.flush()
        except Exception as e:
            self.log.error(e, exc_info=True)
        self.close()

    def start(self):
        self.log.info('Connecting SAS...')
        while True:
            if self.is_open() == False:
                # self.log.error('Port not open')
                try:
                    self.open()
                    if self.is_open() == False:
                        self.log.error('Port not open')
                except SASOpenError:
                    self.log.critical('No SAS Port')
                except Exception as e:
                    self.log.critical(e, exc_info=True)
            else:
                self.connection.flush()
                response = self.connection.read(1)
                if response == None:
                    self.log.error('No SAS Connection')
                    time.sleep(1)
                if response:
                    self.adress = int(binascii.hexlify(response))
                    # if self.adress >= 1:
                    self.mashin_n = response.hex()
                    self.log.info('adress recognised ' + str(self.adress))
                    break
                else:
                    self.log.error('No SAS Connection')
                    time.sleep(1)

        self.close()
        return self.mashin_n

    def close(self):
        self.connection.close()

    def open(self):
        try:
            self.connection.open()
        except:
            raise SASOpenError

    def _conf_event_port(self):
        self.close()
        self.connection.timeout = EVENTS_POLL_TIMEOUT
        self.connection.parity = serial.PARITY_NONE
        self.connection.stopbits = serial.STOPBITS_TWO
        self.open()


    def _conf_port(self):
        self.close()
        self.connection.timeout = self.timeout
        self.connection.parity = serial.PARITY_MARK
        self.connection.stopbits = serial.STOPBITS_ONE
        self.open()
        # self.clean_buffer()

    def crc(self, response, chk=False, seed=0):
        c = ''
        if chk != False:
            crc = response[-4:]
            response = response[:-4]

        for x in response:
            c = c + x
            if len(c) == 2:
                q = (seed ^ int(c, 16)) & 0o17
                seed = (seed >> 4) ^ (q * 0o010201)
                q = (seed ^ (int(c, 16) >> 4)) & 0o17
                seed = (seed >> 4) ^ (q * 0o010201)
                c = ''
        data = hex(seed)
        tmp = []
        if len(data) == 5:
            data = data[0:2] + '0' + data[2:]
        elif len(data) == 4:
            data = data[0:2] + '00' + data[2:]
        elif len(data) == 3:
            data = data[0:2] + '000' + data[2:]
        elif len(data) == 2:
            data = data[0:2] + '0000'
        if chk == False:
            data = data[4:] + data[2:-2]
        #            pass
        else:
            data = data[4:] + data[2:-2]
            if data == crc:
                return True
            else:
                raise BadCRC(response)
        return data

    def _send_command(self, command, no_response=False, timeout=None, crc_need=True, size=1):

        # if timeout == None:
        #     timeout = self.timeout + 1
        # time.sleep(0.04)
        busy = True
        response = b''
        # self.my_log.flush()
        try:
            # if self.poll_adres == '82':
            #     self.poll_adres = '80'
            # else:
            #     self.poll_adres = '82'

            buf_header = [self.adress]
            self._conf_port()
            # self.connection.flushInput()
            # self.connection.write(('80' + self.mashin_n).decode("hex"))
            # self.close()
            # self.connection.parity = serial.PARITY_SPACE
            # self.open()

            buf_header.extend(command)
            buf_count = len(command)
            # buf_header[2]=buf_count+2
            if (crc_need == True):
                crc = CRC16Kermit().calculate(bytes(buf_header))
                buf_header.extend([((crc >> 8) & 0xFF), (crc & 0xFF)])
            self.log.debug(buf_header)
            # time.sleep(0.04)
            self.connection.write([self.poll_adress, self.adress])
            time.sleep(self.sleep_time)
            self.close()
            self.connection.parity = serial.PARITY_SPACE
            self.open()
            # self.connection.flushInput()
            # my_log = open('/home/colibri/dump.log', 'w')
            if self.sas_dump:
                self.my_log = open('/var/log/sas_dump.log', 'a')
                self.my_log.write('TX %s: %s\n' % (time.time(), binascii.hexlify(bytearray(buf_header))))
                self.my_log.close()
            # print self.connection.portstr
            # self.connection.write([0x31, 0x32,0x33,0x34,0x35])
            self.connection.write(buf_header[1:])

        except Exception as e:
            self.log.error(e, exc_info=True)

        try:
            buffer = []
            # t = time.time()
            # while time.time() - t < self.timeout:
            #     tmp = self.connection.read(1)
            #     if not tmp:
            #         pass
            #     elif binascii.hexlify(tmp) == bytes(self.mashin_n.encode('utf-8')) and not response:
            #         response += tmp
            #     elif len(response) == 1 and no_response is False and binascii.hexlify(tmp) == binascii.hexlify(
            #             bytearray([buf_header[1]])):
            #         response += tmp
            #     elif len(response) == 1 and no_response is False and binascii.hexlify(tmp) != binascii.hexlify(
            #             bytearray([buf_header[1]])):
            #         response = b''
            #     elif response:
            #         response += tmp
            #     if len(response) == size:
            #         break
            response = self.connection.read(size)
            if no_response == True:
                try:
                    # raise KeyError(response)
                    return int(binascii.hexlify(response))
                except ValueError as e:
                    self.log.warning("wrong ardess or NACK")
                    return None
            #     else:
            #         # response += self.connection.read(size)
            #         if (self.checkResponse(response, size) is False):
            #             break
            #
            # if time.time() - t >= timeout:
            #     self.log.warning("sas timeout")
            #     # buffer.append(response)
            #     # print response))
            #     return None

            busy = False
            response = self.checkResponse(response)
            self.log.debug('sas response %s', binascii.hexlify(response))
                # self.log.info('no sas response')
            return response
            # return None
        except Exception as e:
            self.log.error(e, exc_info=True)

        busy = False
        return None

    def checkResponse(self, rsp):
        if not rsp:
            # self.flush()
            # self.close()
            raise NoSasConnection('NoSasConnection')
        # if self.crc(rsp.hex(), True):
        #    return rsp[1:-2]
        # raise BadCRC(rsp)
        resp = rsp
        # print resp
        # if (resp[0] is self.adress):
        #     self.log.error("wrong ardess or NACK")
        #     raise BadCRC

        CRC = resp.hex()[-4:]

        command = resp[0:-2]

        crc1 = CRC16Kermit().calculate(bytes(command))

        data = resp[1:-2]

        crc1 = hex(crc1).split('x')[-1]

        while len(crc1) < 4:
            crc1 = "0" + crc1

        # print crc1
        # print CRC
        # raise KeyError(crc1, CRC)
        if (CRC != crc1):
            # print "Wrong response command hash " + str(CRC)
            # print    "////" + str(hex(crc1).split('x')[-1])
            # print    "////" + str(self.hexlify(command))
            raise BadCRC(self.hexlify(self.bytearray(resp)))
        # return False
        elif CRC == crc1:
            if self.sas_dump:
                self.my_log = open('/var/log/sas_dump.log', 'a')
                self.my_log.write('RX %s: %s\n' % (time.time(), binascii.hexlify(resp)))
                self.my_log.close()
            return data
        # raise BadCRC(self.hexlify(resp))

    ##    def check_crc(self):
    ##        cmd=[0x01, 0x50, 0x81]
    ##        cmd=self.bytearray(cmd)
    ##        #print self.sas_CRC([0x01, 0x50, 0x81])
    ##        #print ('\\'+'\\'.join(hex(e)[1:] for e in cmd))
    ##
    ##        print (CRC16Kermit().calculate(str(cmd)))
    ##        return

    def events_poll(self, timeout=EVENTS_POLL_TIMEOUT, **kwargs):
        self._conf_event_port()
        event = ''
        # self.my_log.write('TX %s: %s\n' % (time.time(), '8281'))
        # time.sleep(0.04)
        cmd = [0x80 + self.adress]
        self.connection.write([self.poll_adress])
        try:
            self.connection.write(cmd)
            # t = time.time()
            # while time.time() - t < timeout:
            # print "time"+ str(time.time()-t)
            event = self.connection.read(1)
            # if event != '':
            #     break
            if event == '':
                raise NoSasConnection('NoSasConnection')
                # event = None
                # return None
            # self.my_log.write('RX %s: %s\n' % (time.time(), event.encode('hex')))
            # self.my_log.flush()
            event = GPOLL[event.hex()]
            if event != self.event:
                self.event = event
            else:
                event = 'No activity'
        except KeyError as e:
            raise EMGGpollBadResponse
        except Exception as e:
            raise e
        # self._conf_port()
        return event

    def shutdown(self, **kwargs):
        # 01
        # print "1"

        if (self._send_command([0x01], True, crc_need=True) == self.adress):
            return True
        else:
            return False
        return None

    def startup(self, **kwargs):
        # 02
        # cmd=[0x02]
        if (self._send_command([0x02], True, crc_need=True) == self.adress):
            return True
        else:
            return False
        return None

    def sound_off(self, **kwargs):
        # 03
        if (self._send_command([0x03], True, crc_need=True) == self.adress):
            return True
        else:
            return False
        return None

    def sound_on(self, **kwargs):
        # 04
        if (self._send_command([0x04], True, crc_need=True) == self.adress):
            return True
        else:
            return False
        return None

    def reel_spin_game_sounds_disabled(self, **kwargs):
        # 05
        if (self._send_command([0x05], True, crc_need=True) == self.adress):
            return True
        else:
            return None
        return None

    def enable_bill_acceptor(self, **kwargs):
        # 06
        if (self._send_command([0x06], True, crc_need=True) == self.adress):
            return True
        else:
            return False
        return None

    def disable_bill_acceptor(self, **kwargs):
        # 07
        if (self._send_command([0x07], True, crc_need=True) == self.adress):
            return True
        else:
            return False
        return None

    def configure_bill_denom(self, bill_denom=[0xFF, 0xFF, 0xFF], action_flag=[0xff], **kwargs):
        # 08
        cmd = [0x08, 0x00]
        ##print str(hex(bill_denom))
        s = '00ffffff'
        # print bytes.fromhex(((s)))
        cmd.extend(bill_denom)
        cmd.extend(action_flag)
        if (self._send_command(cmd, True, crc_need=True) == self.adress):
            return True
        # else:
        return None
        # return None

    def en_dis_game(self, game_number=None, en_dis=False, **kwargs):
        if game_number == None:
            game_number = self.selected_game_number()
        game = int(game_number, 16)
        if en_dis == True:
            en_dis = [0]
        else:
            en_dis = [1]
        cmd = [0x09]

        cmd.extend([((game >> 8) & 0xFF), (game & 0xFF)])
        cmd.extend(en_dis)
        if (self._send_command(cmd, True, crc_need=True) == self.adress):
            return game_number
        # else:
        return None
        # return None

    def enter_maintenance_mode(self, **kwargs):
        # 0A
        if (self._send_command([0x0A], True, crc_need=True) == self.adress):
            return True
        else:
            return None
        # return None

    def exit_maintanance_mode(self, **kwargs):
        # 0B
        if (self._send_command([0x0B], True, crc_need=True) == self.adress):
            return True
        else:
            return False
        return None

    def en_dis_rt_event_reporting(self, enable=False, **kwargs):
        # 0E
        if enable == False:
            enable = [0]
        else:
            enable = [1]
        cmd = [0x0E]
        cmd.extend(self.bytearray(enable))
        if (self._send_command(cmd, True, crc_need=True) == self.adress):
            return True
        # else:
        return None
        # return None

    def send_meters_10_15(self, denom=True, **kwargs):
        cmd = [0x0f]
        data = self._send_command(cmd, crc_need=False, size=28)
        if (data is not None):
            meters = {}
            if denom == True:
                meters['total_cancelled_credits_meter'] = round(int((self.hexlify(self.bytearray(data[1:5])))) * self.denom, 2)
                meters['total_in_meter'] = round(int(self.hexlify(self.bytearray(data[5:9]))) * self.denom, 2)
                meters['total_out_meter'] = round(int(self.hexlify(self.bytearray(data[9:13]))) * self.denom, 2)
                meters['total_droup_meter'] = round(int(self.hexlify(self.bytearray(data[13:17]))) * self.denom, 2)
                meters['total_jackpot_meter'] = round(int(self.hexlify(self.bytearray(data[17:21]))) * self.denom, 2)
                meters['games_played_meter'] = int(self.hexlify(self.bytearray(data[21:25])))
            else:
                meters['total_cancelled_credits_meter'] = int((self.hexlify(self.bytearray(data[1:5]))))
                meters['total_in_meter'] = int(self.hexlify(self.bytearray(data[5:9])))
                meters['total_out_meter'] = int(self.hexlify(self.bytearray(data[9:13])))
                meters['total_droup_meter'] = int(self.hexlify(self.bytearray(data[13:17])))
                meters['total_jackpot_meter'] = int(self.hexlify(self.bytearray(data[17:21])))
                meters['games_played_meter'] = int(self.hexlify(self.bytearray(data[21:25])))
            return meters
        return None

    def total_cancelled_credits(self, denom=True, **kwargs):
        # 10
        cmd = [0x10]
        data = self._send_command(cmd, crc_need=False, size=8)
        if (data is not None):
            if denom == True:
                return round(int(self.hexlify(self.bytearray(data[1:5]))) * self.denom, 2)
            else:
                return int(self.hexlify(self.bytearray(data[1:5])))
        return None

    def total_bet_meter(self, denom=True, **kwargs):
        # 11
        cmd = [0x11]
        data = self._send_command(cmd, crc_need=False, size=8)
        if (data is not None):
            if denom == True:
                return round(int(self.hexlify(self.bytearray(data[1:5]))) * self.denom, 2)
            else:
                return int(self.hexlify(self.bytearray(data[1:5])))
        return None

    def total_win_meter(self, denom=True, **kwargs):
        # 12
        cmd = [0x12]
        data = self._send_command(cmd, crc_need=False, size=8)
        if (data is not None):
            if denom == True:
                return round(int(self.hexlify(self.bytearray(data[1:5]))) * self.denom, 2)
            else:
                return int(self.hexlify(self.bytearray(data[1:5])))
        return None

    def total_in_meter(self, denom=True, **kwargs):
        # 13
        cmd = [0x13]
        data = self._send_command(cmd, crc_need=False, size=8)
        if (data is not None):
            if denom == True:
                return round(int(self.hexlify(self.bytearray(data[1:5]))) * self.denom, 2)
            else:
                return int(self.hexlify(self.bytearray(data[1:5])))
        return None

    def total_jackpot_meter(self, denom=True, **kwargs):
        # 14
        cmd = [0x14]
        data = self._send_command(cmd, crc_need=False, size=8)
        if (data is not None):
            if denom == True:
                return round(int(self.hexlify(self.bytearray(data[1:5]))) * self.denom, 2)
            else:
                return int(self.hexlify(self.bytearray(data[1:5])))
        return None

    def games_played_meter(self, **kwargs):
        # 15
        cmd = [0x15]
        data = self._send_command(cmd, crc_need=False, size=8)
        if (data is not None):
            return int(self.hexlify(self.bytearray(data[1:5])))
        return None

    def games_won_meter(self, denom=True, **kwargs):
        # 16
        cmd = [0x16]
        data = self._send_command(cmd, crc_need=False, size=8)
        if (data is not None):
            if denom == True:
                return round(int(self.hexlify(self.bytearray(data[1:5]))) * self.denom, 2)
            else:
                return int(self.hexlify(self.bytearray(data[1:5])))
        return None

    def games_lost_meter(self, **kwargs):
        # 17
        cmd = [0x17]
        data = self._send_command(cmd, crc_need=False, size=8)
        if (data is not None):
            return int(self.hexlify(self.bytearray(data[1:5])))
        return None

    def games_powerup_door_opened(self, **kwargs):
        # 18
        cmd = [0x18]
        data = self._send_command(cmd, crc_need=False, size=8)
        if (data is not None):
            meters = {}
            meters['games_last_power_up'] = int(self.hexlify(self.bytearray(data[1:3])))
            meters['games_last_slot_door_close'] = int(self.hexlify(self.bytearray(data[1:5])))

            return data
        return None

    def meters_11_15(self, denom=True, **kwargs):
        # 19
        cmd = [0x19]
        data = self._send_command(cmd, crc_need=False, size=24)
        if (data is not None):
            meters = {}
            if denom == False:
                meters['total_bet_meter'] = int(self.hexlify(self.bytearray(data[1:5])))
                meters['total_win_meter'] = int(self.hexlify(self.bytearray(data[5:9])))
                meters['total_in_meter'] = int(self.hexlify(self.bytearray(data[9:13])))
                meters['total_jackpot_meter'] = int(self.hexlify(self.bytearray(data[13:17])))
                meters['games_played_meter'] = int(self.hexlify(self.bytearray(data[17:21])))
            else:
                meters['total_bet_meter'] = round(int(self.hexlify(self.bytearray(data[1:5]))) * self.denom, 2)
                meters['total_win_meter'] = round(int(self.hexlify(self.bytearray(data[5:9]))) * self.denom, 2)
                meters['total_in_meter'] = round(int(self.hexlify(self.bytearray(data[9:13]))) * self.denom, 2)
                meters['total_jackpot_meter'] = round(int(self.hexlify(self.bytearray(data[13:17]))) * self.denom, 2)
                meters['games_played_meter'] = int(self.hexlify(self.bytearray(data[17:21])))
            return meters
        return None

    def current_credits(self, denom=True, **kwargs):
        # 1A
        cmd = [0x1A]
        data = self._send_command(cmd, crc_need=False, size=8)
        if (data is not None):
            if denom == True:
                return round(int(self.hexlify(self.bytearray(data[1:5]))) * self.denom, 2)
            else:
                return int(self.hexlify(self.bytearray(data[1:5])))
        return None

    def handpay_info(self, **kwargs):
        # 1B
        cmd = [0x1B]
        data = self._send_command(cmd, crc_need=False)
        if (data is not None):
            meters = {}
            meters['bin_progressive_group'] = int(self.hexlify(self.bytearray(data[1:2])))
            meters['bin_level'] = int(self.hexlify(self.bytearray(data[2:3])))
            meters['amount'] = int(self.hexlify(self.bytearray(data[3:8])))
            meters['bin_reset_ID'] = int(self.hexlify(self.bytearray(data[8:])))
            return meters
        return None

    def meters(self, denom=True, **kwargs):
        # 1C
        cmd = [0x1C]
        data = self._send_command(cmd, crc_need=False, size=36)
        if (data is not None):
            meters = {}
            if denom == False:
                meters['total_bet_meter'] = int(self.hexlify(self.bytearray(data[1:5])))
                meters['total_win_meter'] = int(self.hexlify(self.bytearray(data[5:9])))
                meters['total_in_meter'] = int(self.hexlify(self.bytearray(data[9:13])))
                meters['total_jackpot_meter'] = int(self.hexlify(self.bytearray(data[13:17])))
                meters['games_played_meter'] = int(self.hexlify(self.bytearray(data[17:21])))
                meters['games_won_meter'] = int(self.hexlify(self.bytearray(data[21:25])))
                meters['slot_door_opened_meter'] = int(self.hexlify(self.bytearray(data[25:29])))
                meters['power_reset_meter'] = int(self.hexlify(self.bytearray(data[29:33])))
            else:
                meters['total_bet_meter'] = round(int(self.hexlify(self.bytearray(data[1:5]))) * self.denom, 2)
                meters['total_win_meter'] = round(int(self.hexlify(self.bytearray(data[5:9]))) * self.denom, 2)
                meters['total_in_meter'] = round(int(self.hexlify(self.bytearray(data[9:13]))) * self.denom, 2)
                meters['total_jackpot_meter'] = round(int(self.hexlify(self.bytearray(data[13:17]))) * self.denom, 2)
                meters['games_played_meter'] = int(self.hexlify(self.bytearray(data[17:21])))
                meters['games_won_meter'] = round(int(self.hexlify(self.bytearray(data[21:25]))) * self.denom, 2)
                meters['slot_door_opened_meter'] = int(self.hexlify(self.bytearray(data[25:29])))
                meters['power_reset_meter'] = int(self.hexlify(self.bytearray(data[29:33])))

            return meters
        return None

    def total_bill_meters(self, **kwargs):
        # 1E
        cmd = [0x1E]
        data = self._send_command(cmd, crc_need=False, size=28)
        if (data is not None):
            meters = {}
            meters['s1_bills_accepted_meter'] = int(self.hexlify(self.bytearray(data[1:5])))
            meters['s5_bills_accepted_meter'] = int(self.hexlify(self.bytearray(data[5:9])))
            meters['s10_bills_accepted_meter'] = int(self.hexlify(self.bytearray(data[9:13])))
            meters['s20_bills_accepted_meter'] = int(self.hexlify(self.bytearray(data[13:17])))
            meters['s50_bills_accepted_meter'] = int(self.hexlify(self.bytearray(data[17:21])))
            meters['s100_bills_accepted_meter'] = int(self.hexlify(self.bytearray(data[21:25])))

            return meters
        return None

    def gaming_machine_ID(self, **kwargs):
        # 1F
        cmd = [0x1F]
        data = self._send_command(cmd, crc_need=False, size=24)
        if (data is not None):
            denom = DENOMINATION[self.hexlify(self.bytearray(data[6:7]))]
            self.log.info('addenomination recognised ' + str(denom))
            self.denom = denom
            return denom
            # meters['ASCII_game_ID']=(((data[1:3])))
            # meters['ASCII_additional_ID']=(((data[3:6])))
            # meters['bin_denomination']=int(self.hexlify(self.bytearray(data[4:5])))
            # meters['bin_max_bet']=(self.hexlify(self.bytearray(data[7:8])))
            # meters['bin_progressive_mode']=int(self.hexlify(self.bytearray(data[8:9])))
            # meters['bin_game_options']=(self.hexlify(self.bytearray(data[9:11])))
            # meters['ASCII_paytable_ID']=(((data[11:17])))
            # meters['ASCII_base_percentage']=(((data[17:21])))

            # return data
        return None

    def total_dollar_value_of_bills_meter(self, **kwargs):
        # 20

        cmd = [0x20]
        data = self._send_command(cmd, crc_need=False, size=8)

        if (data is not None):
            return int(self.hexlify(self.bytearray(data[1:])))

        return None

    def ROM_signature_verification(self, **kwargs):
        # 21

        cmd = [0x21, 0x00, 0x00]
        data = self._send_command(cmd, crc_need=True)
        if (data is not None):
            return int(self.hexlify(self.bytearray(data[1:3])))
        return None

    def eft_button_pressed(self, state=0, **kwargs):
        # 24
        cmd = [0x24, 0x03]
        cmd.append(state)

        data = self._send_command(cmd, crc_need=True)
        if (data is not None):
            return data
        return None

    def true_coin_in(self, denom=True, **kwargs):
        # 2A
        cmd = [0x2A]
        data = self._send_command(cmd, crc_need=False)
        if (data is not None):
            if denom == False:
                return int(self.hexlify(self.bytearray(data[1:5])))
            else:
                return round(int(self.hexlify(self.bytearray(data[1:5]))) * self.denom, 2)
        return None

    def true_coin_out(self, denom=True, **kwargs):
        # 2B
        cmd = [0x2B]
        data = self._send_command(cmd, crc_need=False)
        if (data is not None):
            if denom == False:
                return int(self.hexlify(self.bytearray(data[1:5])))
            else:
                return round(int(self.hexlify(self.bytearray(data[1:5]))) * self.denom, 2)
        return None

    def curr_hopper_level(self, **kwargs):
        # 2C
        cmd = [0x2C]
        data = self._send_command(cmd, crc_need=False)
        if (data is not None):
            return int(self.hexlify(self.bytearray(data[1:5])))
        return None

    def total_hand_paid_cancelled_credit(self, **kwargs):
        # 2D
        cmd = [0x2D]
        data = self._send_command(cmd, crc_need=False, size=8)
        if (data is not None):
            return int(self.hexlify(self.bytearray(data[1:5])))
        return None

    def delay_game(self, delay_time=100, **kwargs):
        # 2E
        tmp = []
        delay_time = self.mony_to_hex(delay_time, 2, False)
        # delay_time = str(delay_time)
        # delay = '' + ('0' * (4 - len(delay_time)) + delay_time)
        cmd = '2E' + delay_time
        cmd = self.cmd_to_list(cmd)
        # count = 0
        # for i in range(int(len(delay) / 2)):
        #     cmd.append(int(delay[count:count + 2], 16))
        #     count += 2
        if self._send_command(cmd, True, crc_need=True) == self.adress:
            return True
        else:
            return False

        return None

    def selected_meters_for_game(self, **kwargs):
        # 2F
        # FIXME: selected_meters_for_game
        return None

    def send_1_bills_in_meters(self, **kwargs):
        # 31
        cmd = [0x31]
        data = self._send_command(cmd, crc_need=False, size=8)
        if (data is not None):
            return int(self.hexlify(self.bytearray(data[1:5])))
        return None

    def send_2_bills_in_meters(self, **kwargs):
        # 32
        cmd = [0x32]
        data = self._send_command(cmd, crc_need=False, size=8)
        if (data is not None):
            return int(self.hexlify(self.bytearray(data[1:5])))
        return None

    def send_5_bills_in_meters(self, **kwargs):
        # 33
        cmd = [0x33]
        data = self._send_command(cmd, crc_need=False, size=8)
        if (data is not None):
            return int(self.hexlify(self.bytearray(data[1:5])))
        return None

    def send_10_bills_in_meters(self, **kwargs):
        # 34
        cmd = [0x34]
        data = self._send_command(cmd, crc_need=False, size=8)
        if (data is not None):
            return int(self.hexlify(self.bytearray(data[1:5])))
        return None

    def send_20_bills_in_meters(self, **kwargs):
        # 35
        cmd = [0x35]
        data = self._send_command(cmd, crc_need=False, size=8)
        if (data is not None):
            return int(self.hexlify(self.bytearray(data[1:5])))
        return None

    def send_50_bills_in_meters(self, **kwargs):
        # 36
        cmd = [0x36]
        data = self._send_command(cmd, crc_need=False, size=8)
        if (data is not None):
            return int(self.hexlify(self.bytearray(data[1:5])))
        return None

    def send_100_bills_in_meters(self, **kwargs):
        # 37
        cmd = [0x37]
        data = self._send_command(cmd, crc_need=False, size=8)
        if (data is not None):
            return int(self.hexlify(self.bytearray(data[1:5])))
        return None

    def send_500_bills_in_meters(self, **kwargs):
        # 38
        cmd = [0x38]
        data = self._send_command(cmd, crc_need=False, size=8)
        if (data is not None):
            return int(self.hexlify(self.bytearray(data[1:5])))
        return None

    def send_1000_bills_in_meters(self, **kwargs):
        # 39
        cmd = [0x39]
        data = self._send_command(cmd, crc_need=False, size=8)
        if (data is not None):
            return int(self.hexlify(self.bytearray(data[1:5])))
        return None

    def send_200_bills_in_meters(self, **kwargs):
        # 3A
        cmd = [0x3a]
        data = self._send_command(cmd, crc_need=False, size=8)
        if (data is not None):
            return int(self.hexlify(self.bytearray(data[1:5])))
        return None

    def send_25_bills_in_meters(self, **kwargs):
        # 3B
        cmd = [0x3B]
        data = self._send_command(cmd, crc_need=False, size=8)
        if (data is not None):
            return int(self.hexlify(self.bytearray(data[1:5])))
        return None

    def send_2000_bills_in_meters(self, **kwargs):
        # 3C
        cmd = [0x3C]
        data = self._send_command(cmd, crc_need=False, size=8)
        if (data is not None):
            return int(self.hexlify(self.bytearray(data[1:5])))
        return None

    def cash_out_ticket_info(self, **kwargs):
        # 3D
        cmd = [0x3D]
        data = self._send_command(cmd, crc_need=False)
        if (data is not None):
            tito_statement = {}
            tito_statement['cashout_ticket_number'] = int(self.hexlify(self.bytearray(data[1:3])))
            tito_statement['cashout_amount_in_cents'] = int(self.hexlify(self.bytearray(data[3:])))
            return tito_statement
        return None

    def send_2500_bills_in_meters(self, **kwargs):
        # 3E
        cmd = [0x3E]
        data = self._send_command(cmd, crc_need=False, size=8)
        if (data is not None):
            return int(self.hexlify(self.bytearray(data[1:5])))
        return None

    def send_5000_bills_in_meters(self, **kwargs):
        # 3F
        cmd = [0x3F]
        data = self._send_command(cmd, crc_need=False, size=8)
        if (data is not None):
            return int(self.hexlify(self.bytearray(data[1:5])))
        return None

    def send_10000_bills_in_meters(self, **kwargs):
        # 40
        cmd = [0x40]
        data = self._send_command(cmd, crc_need=False, size=8)
        if (data is not None):
            return int(self.hexlify(self.bytearray(data[1:5])))
        return None

    def send_20000_bills_in_meters(self, **kwargs):
        # 41
        cmd = [0x41]
        data = self._send_command(cmd, crc_need=False, size=8)
        if (data is not None):
            return int(self.hexlify(self.bytearray(data[1:5])))
        return None

    def send_25000_bills_in_meters(self, **kwargs):
        # 42
        cmd = [0x42]
        data = self._send_command(cmd, crc_need=False, size=8)
        if (data is not None):
            return int(self.hexlify(self.bytearray(data[1:5])))
        return None

    def send_50000_bills_in_meters(self, **kwargs):
        # 43
        cmd = [0x43]
        data = self._send_command(cmd, crc_need=False, size=8)
        if (data is not None):
            return int(self.hexlify(self.bytearray(data[1:5])))
        return None

    def send_100000_bills_in_meters(self, **kwargs):
        # 44
        cmd = [0x44]
        data = self._send_command(cmd, crc_need=False, size=8)
        if (data is not None):
            return int(self.hexlify(self.bytearray(data[1:5])))
        return None

    def send_250_bills_in_meters(self, **kwargs):
        # 45
        cmd = [0x45]
        data = self._send_command(cmd, crc_need=False, size=8)
        if (data is not None):
            return int(self.hexlify(self.bytearray(data[1:5])))
        return None

    def credit_amount_of_all_bills_accepted(self, **kwargs):
        # 46
        cmd = [0x46]
        data = self._send_command(cmd, crc_need=False, size=8)
        if (data is not None):
            return int(self.hexlify(self.bytearray(data[1:5])))
        return None

    def coin_amount_accepted_from_external_coin_acceptor(self, **kwargs):
        # 47
        cmd = [0x47]
        data = self._send_command(cmd, crc_need=False, size=8)
        if (data is not None):
            return int(self.hexlify(self.bytearray(data[1:5])))
        return None

    def last_accepted_bill_info(self, **kwargs):
        # 48
        cmd = [0x48]
        data = self._send_command(cmd, crc_need=False)
        if (data is not None):
            meters = {}
            meters['country_code'] = int(self.hexlify(self.bytearray(data[1:2])))
            meters['bill_denomination'] = int(self.hexlify(self.bytearray(data[2:3])))
            meters['meter_for_accepted_bills'] = int(self.hexlify(self.bytearray(data[3:6])))
            return meters
        return None

    def number_of_bills_currently_in_stacker(self, **kwargs):
        # 49
        cmd = [0x49]
        data = self._send_command(cmd, crc_need=False, size=8)
        if (data is not None):
            return int(self.hexlify(self.bytearray(data[1:5])))
        return None

    def total_credit_amount_of_all_bills_in_stacker(self, **kwargs):
        # 4A
        cmd = [0x49]
        data = self._send_command(cmd, crc_need=False, size=8)
        if (data is not None):
            return int(self.hexlify(self.bytearray(data[1:5])))
        return None

    def set_secure_enhanced_validation_ID(self, MachineID=[0x01, 0x01, 0x01], seq_num=[0x00, 0x00, 0x01], **kwargs):
        # 4C
        # FIXME: set_secure_enhanced_validation_ID
        cmd = [0x4C]

        cmd.extend(MachineID)
        cmd.extend(seq_num)
        cmd = self.bytearray(cmd)
        # print str(self.hexlify((cmd)))
        data = self._send_command(cmd, True, crc_need=True)
        if (data is not None):
            tito_statement['machine_ID'] = int(self.hexlify(self.bytearray(data[1:4])))
            tito_statement['sequence_number'] = int(self.hexlify(self.bytearray(data[4:8])))

            return data
        return None

    def enhanced_validation_information(self, curr_validation_info=0, **kwargs):
        # 4D
        # FIXME: enhanced_validation_information
        cmd = [0x4D]

        # cmd.append(transfer_code)
        # cmd=cmd.extend(0)
        # rint str(self.hexlify(self.bytearray(cmd)))
        cmd.append((curr_validation_info))
        data = self._send_command(cmd, True, crc_need=True)
        if (data is not None):
            tito_statement['validation_type'] = int(self.hexlify(self.bytearray(data[1:2])))
            tito_statement['index_number'] = int(self.hexlify(self.bytearray(data[2:3])))
            tito_statement['date_validation_operation'] = str(self.hexlify(self.bytearray(data[3:7])))
            tito_statement['time_validation_operation'] = str(self.hexlify(self.bytearray(data[7:10])))
            tito_statement['validation_number'] = str(self.hexlify(self.bytearray(data[10:18])))
            tito_statement['ticket_amount'] = int(self.hexlify(self.bytearray(data[18:23])))
            tito_statement['ticket_number'] = int(self.hexlify(self.bytearray(data[23:25])))
            tito_statement['validation_system_ID'] = int(self.hexlify(self.bytearray(data[25:26])))
            tito_statement['expiration_date_printed_on_ticket'] = str(self.hexlify(self.bytearray(data[26:30])))
            tito_statement['pool_id'] = int(self.hexlify(self.bytearray(data[30:32])))

            return data
        return None

    def current_hopper_status(self, **kwargs):
        # 4F
        # FIXME: current_hopper_status

        cmd = [0x4F]

        data = self._send_command(cmd, True, crc_need=False)
        if (data is not None):
            meters['current_hopper_lenght'] = int(self.hexlify(self.bytearray(data[1:2])))
            meters['current_hopper_ststus'] = int(self.hexlify(self.bytearray(data[2:3])))
            meters['current_hopper_percent_full'] = int(self.hexlify(self.bytearray(data[3:4])))
            meters['current_hopper_level'] = int(self.hexlify(self.bytearray(data[4:])))
            return data
        return None

    def validation_meters(self, type_of_validation=0x00, **kwargs):
        # 50
        # FIXME: validation_meters
        cmd = [0x50]
        cmd.append(type_of_validation)
        data = self._send_command(cmd, True, crc_need=True)
        if (data is not None):
            meters['bin_validation_type'] = int(self.hexlify(self.bytearray(data[1])))
            meters['total_validations'] = int(self.hexlify(self.bytearray(data[2:6])))
            meters['cumulative_amount'] = str(self.hexlify(self.bytearray(data[6:])))

            return data
        return None

    def total_number_of_games_impimented(self, **kwargs):
        # 51
        cmd = [0x51]
        # cmd.extend(type_of_validation)
        data = self._send_command(cmd, crc_need=False, size=6)
        if (data is not None):
            return str(self.hexlify(self.bytearray(data[1:])))
        return None

    def game_meters(self, game_number=None, denom=True, **kwargs):
        # 52
        cmd = [0x52]
        if game_number == None:
            game_number == self.selected_game_number(in_hex=False)
        else:
            game_number = int(game_number, 16)
        cmd.extend([((game_number >> 8) & 0xFF), (game_number & 0xFF)])

        data = self._send_command(cmd, crc_need=True, size=22)
        if (data is not None):
            meters = {}
            if denom == False:
                meters['game_n_number'] = str(self.hexlify(self.bytearray(data[1:3])))
                meters['game_n_coin_in_meter'] = int(self.hexlify(self.bytearray(data[3:7])))
                meters['game_n_coin_out_meter'] = int(self.hexlify(self.bytearray(data[7:11])))
                meters['game_n_jackpot_meter'] = int(self.hexlify(self.bytearray(data[11:15])))
                meters['geme_n_games_played_meter'] = int(self.hexlify(self.bytearray(data[15:])))
            else:
                meters['game_n_number'] = str(self.hexlify(self.bytearray(data[1:3])))
                meters['game_n_coin_in_meter'] = round(int(self.hexlify(self.bytearray(data[3:7]))) * self.denom, 2)
                meters['game_n_coin_out_meter'] = round(int(self.hexlify(self.bytearray(data[7:11]))) * self.denom, 2)
                meters['game_n_jackpot_meter'] = round(int(self.hexlify(self.bytearray(data[11:15]))) * self.denom, 2)
                meters['geme_n_games_played_meter'] = int(self.hexlify(self.bytearray(data[15:])))
            return meters
        return None

    def game_configuration(self, game_number=None, **kwargs):
        # 53
        # FIXME: game_configuration
        if game_number == None:
            game_number = self.selected_game_number(in_hex=False)
        else:
            game_number = int(game_number, 16)
        cmd = [0x53]
        cmd.extend([(game_number & 0xFF), ((game_number >> 8) & 0xFF)])

        data = self._send_command(cmd, True, crc_need=True)
        if (data is not None):
            meters['game_n_number_config'] = int(self.hexlify(self.bytearray(data[1:3])))
            meters['game_n_ASCII_game_ID'] = str(self.hexlify(self.bytearray(data[3:5])))
            meters['game_n_ASCII_additional_id'] = str(self.hexlify(self.bytearray(data[5:7])))
            meters['game_n_bin_denomination'] = str(self.hexlify(self.bytearray(data[7])))
            meters['game_n_bin_progressive_group'] = str(self.hexlify(self.bytearray(data[8])))
            meters['game_n_bin_game_options'] = str(self.hexlify(self.bytearray(data[9:11])))
            meters['game_n_ASCII_paytable_ID'] = str(self.hexlify(self.bytearray(data[11:17])))
            meters['game_n_ASCII_base_percentage'] = str(self.hexlify(self.bytearray(data[17:])))

            return data
        return None

    def SAS_version_gaming_machine_serial_ID(self, **kwargs):
        # 54
        cmd = [0x54, 0x00]

        data = self._send_command(cmd, crc_need=False, size=20)
        if (data is not None):
            meters = {}
            meters['ASCII_SAS_version'] = int(self.hexlify(self.bytearray(data[2:5]))) * 0.01
            meters['ASCII_serial_number'] = str(self.bytearray(data[5:]))
            return meters
        return None

    def selected_game_number(self, in_hex=True, **kwargs):
        # 55
        cmd = [0x55]

        data = self._send_command(cmd, crc_need=False, size=6)
        if (data is not None):
            # meters['selected_game_number']=int(self.hexlify(self.bytearray(data[1:])))
            if in_hex == False:
                return int(self.hexlify(self.bytearray(data[1:])))
            else:
                return self.hexlify(self.bytearray(data[1:]))
        return None

    def enabled_game_numbers(self, **kwargs):
        # 56

        cmd = [0x56]

        data = self._send_command(cmd, crc_need=False)
        if (data is not None):
            meters = {}
            meters['number_of_enabled_games'] = int(self.hexlify(self.bytearray(data[2])))
            meters['enabled_games_numbers'] = int(self.hexlify(self.bytearray(data[3:])))

            return meters
        return None

    def pending_cashout_info(self, **kwargs):
        # 57

        cmd = [0x57]

        data = self._send_command(cmd, crc_need=False)
        if (data is not None):
            tito_statement = {}
            tito_statement['cashout_type'] = int(self.hexlify(self.bytearray(data[1:2])))
            tito_statement['cashout_amount'] = str(self.hexlify(self.bytearray(data[2:])))

            return tito_statement
        return None

    def validation_number(self, validationID=1, valid_number=0, **kwargs):
        # 58

        cmd = [0x58]
        cmd.append(validationID)
        cmd.extend(self.bcd_coder_array(valid_number, 8))
        # print cmd
        data = self._send_command(cmd, crc_need=True)
        if (data is not None):
            return str(self.hexlify(self.bytearray(data[1])))
        return None

    def eft_send_promo_to_machine(self, amount=0, count=1, status=0, **kwargs):
        # 63
        # FIXME: eft_send_promo_to_machine
        cmd = [0x63, count, ]
        # status 0-init 1-end
        cmd.append(status)
        cmd.extend(self.bcd_coder_array(amount, 4))
        data = self._send_command(cmd, crc_need=True)
        if (data is not None):
            eft_statement = {}
            eft_statement['eft_status'] = str(self.hexlify(self.bytearray(data[1:])))
            eft_statement['promo_amount'] = str(self.hexlify(self.bytearray(data[4:])))
            # eft_statement['eft_transfer_counter']=int(self.hexlify(self.bytearray(data[3:4])))

            return eft_statement
        return None

    def eft_load_cashable_credits(self, amount=0, count=1, status=0, **kwargs):
        # 69
        # FIXME: eft_load_cashable_credits
        cmd = [0x69, count, ]
        cmd.append(status)
        cmd.extend(self.bcd_coder_array(amount, 4))
        data = self._send_command(cmd, True, crc_need=True)

        if (data is not None):
            meters['eft_status'] = str(self.hexlify(self.bytearray(data[1:2])))
            meters['cashable_amount'] = str(self.hexlify(self.bytearray(data[2:5])))

            return data[3]
        return None

    def eft_avilable_transfers(self, **kwargs):
        # 6A
        # FIXME: eft_load_cashable_credits
        cmd = [0x6A]
        data = self._send_command(cmd, True, crc_need=False)
        if (data is not None):
            # meters['number_bills_in_stacker']=int(self.hexlify(self.bytearray(data[1:5])))
            return data
        return None

    def autentification_info(self, action=0, adressing_mode=0, component_name='', auth_method=b'\x00\x00\x00\x00',
                             seed_lenght=0, seed='', offset_lenght=0, offset='', **kwargs):
        # 6E
        # FIXME: autentification_info
        cmd = [0x6E, 0x00]
        cmd.append(action)
        if action == 0:
            # cmd.append(action)
            cmd[1] = 1
        else:
            if (action == 1 or action == 3):
                cmd.append(adressing_mode)
                cmd.append(len(self.bytearray(component_name)))
                cmd.append(self.bytearray(component_name))
                cmd[1] = len(self.bytearray(component_name)) + 3
            else:
                if action == 2:
                    cmd.append(adressing_mode)
                    cmd.append(len(self.bytearray(component_name)))
                    cmd.append(self.bytearray(component_name))
                    cmd.append(auth_method)
                    cmd.append(seed_lenght)
                    cmd.append(self.bytearray(seed))
                    cmd.append(offset_lenght)
                    cmd.append(self.bytearray(offset))

                    cmd[1] = len(self.bytearray(offset)) + len(self.bytearray(seed)) + len(
                        self.bytearray(component_name)) + 6

        data = self._send_command(cmd, True, crc_need=True)
        if (data is not None):
            return data[1]
        return None

    def extended_meters_for_game(self, n=1, **kwargs):
        # TODO: extended_meters_for_game
        # 6F
        return None

    def ticket_validation_data(self, **kwargs):
        # 70
        # FIXME: ticket_validation_data
        cmd = [0x70]

        data = self._send_command(cmd, True, crc_need=False)
        if (data is not None):
            meters['ticket_status'] = int(self.hexlify(self.bytearray(data[2:3])))
            meters['ticket_amount'] = str(self.hexlify(self.bytearray(data[3:8])))
            meters['parsing_code'] = int(self.hexlify(self.bytearray(data[8:9])))
            meters['validation_data'] = str(self.hexlify(self.bytearray(data[9:])))

            return data[1]
        return None

    def redeem_ticket(self, transfer_code=0, transfer_amount=0, parsing_code=0, validation_data=0,
                      rescticted_expiration=0, pool_ID=0, **kwargs):
        # 71
        # FIXME: redeem_ticket
        cmd = [0x71, 0x00]
        cmd.append(transfer_code)
        cmd.extend(self.bcd_coder_array(transfer_amount, 5))
        cmd.append(parsing_code)

        cmd.extend(self.bcd_coder_array(validation_data, 8))
        cmd.extend(self.bcd_coder_array(rescticted_expiration, 4))
        cmd.extend(self.bcd_coder_array(pool_ID, 2))
        cmd[1] = 8 + 13

        data = self._send_command(cmd, True, crc_need=True)
        if (data is not None):
            meters['ticket_status'] = int(self.hexlify(self.bytearray(data[2:3])))
            meters['ticket_amount'] = int(self.hexlify(self.bytearray(data[3:8])))
            meters['parsing_code'] = int(self.hexlify(self.bytearray(data[8:9])))
            meters['validation_data'] = str(self.hexlify(self.bytearray(data[9:])))

            return data[1]
        return None

    def AFT_change_transaction(self, transaction='2020202020202020202020202020202021'):
        self.transaction = int(transaction, 16)
        return True

    def AFT_jp(self, mony, amount=1, lock_timeout=None, games=None, **kwargs):
        # self.lock_emg(lock_time=500, condition=1)
        if self.denom > 0.01:
            return None
        if games == None:
            for i in range(3):
                try:
                    game_selected = self.selected_game_number(in_hex=False)
                except:
                    game_selected = None
                if game_selected == None:
                    time.sleep(0.04)
                else:
                    break
        else:
            game_selected = games
        if game_selected == 0:
            return 'NoGame'
        elif game_selected == None:
            return 'NoGame'
        elif game_selected < 1:
            return 'NoGame'
        my_time = datetime.datetime.now()
        my_time = datetime.datetime.strftime(my_time, '%m%d%Y')
        if mony == None:
            mony = self.current_credits(denom=True)
        mony_1 = mony_2 = mony_3 = self.mony_to_hex(0, 5)
        if amount == 1:
            mony_1 = self.mony_to_hex(mony, 5)
        elif amount == 2:
            mony_2 = self.mony_to_hex(mony, 5)
        elif amount == 3:
            mony_3 = self.mony_to_hex(mony, 5)
        else:
            raise AFTBadAmount
        self.AFT_register()
        if lock_timeout is None:
            lock_timeout = self.lock_time
        self.last_AFT_lock_status = False
        if lock_timeout > 0:
            lock_data = self.AFT_game_lock_and_status_request(lock_timeout=lock_timeout)
            if lock_data == None or lock_data == False:
                self.log.warning('EMG is not locked')
                self.last_AFT_lock_status = True
                data = self.AFT_clean_transaction_poll()
                return False
            if lock_data['game_lock_status'] != '00':
                self.log.warning('EMG is not locked')
                self.last_AFT_lock_status = True
                data = self.AFT_clean_transaction_poll()
                return False
        last_transaction = self.AFT_format_transaction()
        len_transaction_id = hex(len(last_transaction) // 2)[2:]
        if len(len_transaction_id) < 2:
            len_transaction_id = '0' + len_transaction_id
        elif len(len_transaction_id) % 2 == 1:
            len_transaction_id = '0' + len_transaction_id
        cmd = '{index}00{transfer_code}{mony_1}{mony_2}{mony_3}{transfer_flag}{asett}{key}{len_transaction}{transaction}{times}0C0000'.format(
            transfer_code='11', index='00', mony_1=mony_1, mony_2=mony_2, mony_3=mony_3,
            asett=self.asset_number, key=self.reg_key, len_transaction=len_transaction_id, transaction=last_transaction,
            times=my_time, transfer_flag='00')
        cmd = '72' + hex(int(len(cmd) // 2))[2:] + cmd
        new_cmd = self.cmd_to_list(cmd)
        # count = 0
        # for i in range(int(len(cmd) / 2)):
        #     new_cmd.append(int(cmd[count:count + 2], 16))
        #     count += 2

        response = None
        # self.AFT_register()
        # if lock_timeout == 0:
        #     lock_timeout = self.lock_time
        # if lock_timeout > 0:
        #     lock_data = self.AFT_game_lock_and_status_request(lock_timeout=lock_timeout)
        #     if lock_data['game_lock_status'] != '00':
        #         self.log.warning('EMG is not locked')
        #         return None
        data = self._send_command(new_cmd, crc_need=True, size=82)
        if (data is not None):
            a = int(self.hexlify(self.bytearray(data[26:27])), 16)
            response = {
                'Length': int(self.hexlify(self.bytearray(data[26:27])), 16),
                'Transaction buffer position': int(self.hexlify(self.bytearray(data[2:3])), 16),
                'Transfer status': AFT_TRANSFER_STATUS[self.hexlify(self.bytearray(data[3:4]))],
                'Receipt status': AFT_RECEIPT_STATUS[self.hexlify(self.bytearray(data[4:5]))],
                'Transfer type': AFT_TRANSFER_TYPE[self.hexlify(self.bytearray(data[5:6]))],
                'Cashable amount': round(int(self.hexlify(self.bytearray(data[6:11]))) * self.denom, 2),
                'Restricted amount': round(int(self.hexlify(self.bytearray(data[11:16]))) * self.denom, 2),
                'Nonrestricted amount': round(int(self.hexlify(self.bytearray(data[16:21]))) * self.denom, 2),
                'Transfer flags': self.hexlify(self.bytearray(data[21:22])),
                'Asset number': self.hexlify(self.bytearray(data[22:26])),
                'Transaction ID length': self.hexlify(self.bytearray(data[26:27])),
                'Transaction ID': self.hexlify(self.bytearray(data[27:(27 + a)]))
            }
        # try:
        self.AFT_unregister()
        # except:
        #     self.log.warning('AFT UNREGISTER ERROR: won to host')
        return response

    def AFT_initial_out(self, mony=None, amount=1, lock_timeout=None, **kwargs):
        # self.lock_emg(lock_time=500, condition=1)
        if self.denom > 0.01:
            return None
        my_time = datetime.datetime.now()
        my_time = datetime.datetime.strftime(my_time, '%m%d%Y')
        if mony == None:
            mony = self.current_credits(denom=True)
        mony_1 = mony_2 = mony_3 = self.mony_to_hex(0, 5)
        if amount == 1:
            mony_1 = self.mony_to_hex(mony, 5)
        elif amount == 2:
            mony_2 = self.mony_to_hex(mony, 5)
        elif amount == 3:
            mony_3 = self.mony_to_hex(mony, 5)
        else:
            raise AFTBadAmount
        self.AFT_register()
        if lock_timeout is None:
            lock_timeout = self.lock_time
        self.last_AFT_lock_status = False
        if lock_timeout > 0:
            lock_data = self.AFT_game_lock_and_status_request(lock_timeout=lock_timeout)
            if lock_data == None or lock_data == False:
                self.log.warning('EMG is not locked')
                self.last_AFT_lock_status = True
                data = self.AFT_clean_transaction_poll()
                return False
            if lock_data['game_lock_status'] != '00':
                self.log.warning('EMG is not locked')
                self.last_AFT_lock_status = True
                data = self.AFT_clean_transaction_poll()
                return False
        last_transaction = self.AFT_format_transaction()
        len_transaction_id = hex(len(last_transaction) // 2)[2:]
        if len(len_transaction_id) < 2:
            len_transaction_id = '0' + len_transaction_id
        elif len(len_transaction_id) % 2 == 1:
            len_transaction_id = '0' + len_transaction_id
        cmd = '{index}00{transfer_code}{mony_1}{mony_2}{mony_3}{transfer_flag}{asett}{key}{len_transaction}{transaction}{times}0C0000'.format(
            transfer_code='00', index='00', mony_1=mony_1, mony_2=mony_2, mony_3=mony_3,
            asett=self.asset_number, key=self.reg_key, len_transaction=len_transaction_id, transaction=last_transaction,
            times=my_time, transfer_flag='0a')
        cmd = '72' + hex(int(len(cmd) // 2))[2:] + cmd
        new_cmd = self.cmd_to_list(cmd)

        response = None
        # self.AFT_register()
        # if lock_timeout == 0:
        #     lock_timeout = self.lock_time
        # if lock_timeout > 0:
        #     lock_data = self.AFT_game_lock_and_status_request(lock_timeout=lock_timeout)
        #     if lock_data['game_lock_status'] != '00':
        #         self.log.warning('EMG is not locked')
        #         return None
        try:
            data = self._send_command(new_cmd, crc_need=True, size=82)
            if (data is not None):
                a = int(self.hexlify(self.bytearray(data[26:27])), 16)
                response = {
                    'Length': int(self.hexlify(self.bytearray(data[26:27])), 16),
                    'Transaction buffer position': int(self.hexlify(self.bytearray(data[2:3])), 16),
                    'Transfer status': AFT_TRANSFER_STATUS[self.hexlify(self.bytearray(data[3:4]))],
                    'Receipt status': AFT_RECEIPT_STATUS[self.hexlify(self.bytearray(data[4:5]))],
                    'Transfer type': AFT_TRANSFER_TYPE[self.hexlify(self.bytearray(data[5:6]))],
                    'Cashable amount': round(int(self.hexlify(self.bytearray(data[6:11]))) * self.denom, 2),
                    'Restricted amount': round(int(self.hexlify(self.bytearray(data[11:16]))) * self.denom, 2),
                    'Nonrestricted amount': round(int(self.hexlify(self.bytearray(data[16:21]))) * self.denom, 2),
                    'Transfer flags': self.hexlify(self.bytearray(data[21:22])),
                    'Asset number': self.hexlify(self.bytearray(data[22:26])),
                    'Transaction ID length': self.hexlify(self.bytearray(data[26:27])),
                    'Transaction ID': self.hexlify(self.bytearray(data[27:(27 + a)]))
                }
        except Exception as e:
            self.log.error(e, exc_info=True)
        # try:
        self.AFT_unregister()
        # except:
        #     self.log.warning('AFT UNREGISTER ERROR: out')
        return response

    def AFT_out(self, mony=None, amount=1, lock_timeout=None, **kwargs):
        # self.lock_emg(lock_time=500, condition=1)
        if self.denom > 0.01:
            return None
        my_time = datetime.datetime.now()
        my_time = datetime.datetime.strftime(my_time, '%m%d%Y')
        if mony == None:
            mony = self.current_credits(denom=True)
        mony_1 = mony_2 = mony_3 = self.mony_to_hex(0, 5)
        if amount == 1:
            mony_1 = self.mony_to_hex(mony, 5)
        elif amount == 2:
            mony_2 = self.mony_to_hex(mony, 5)
        elif amount == 3:
            mony_3 = self.mony_to_hex(mony, 5)
        else:
            raise AFTBadAmount
        self.AFT_register()
        if lock_timeout is None:
            lock_timeout = self.lock_time
        self.last_AFT_lock_status = False
        if lock_timeout > 0:
            lock_data = self.AFT_game_lock_and_status_request(lock_timeout=lock_timeout)
            if lock_data == None or lock_data == False:
                self.log.warning('EMG is not locked')
                self.last_AFT_lock_status = True
                data = self.AFT_clean_transaction_poll()
                return False
            if lock_data['game_lock_status'] != '00':
                self.log.warning('EMG is not locked')
                self.last_AFT_lock_status = True
                data = self.AFT_clean_transaction_poll()
                return False
        last_transaction = self.AFT_format_transaction()
        len_transaction_id = hex(len(last_transaction) // 2)[2:]
        if len(len_transaction_id) < 2:
            len_transaction_id = '0' + len_transaction_id
        elif len(len_transaction_id) % 2 == 1:
            len_transaction_id = '0' + len_transaction_id
        cmd = '{index}00{transfer_code}{mony_1}{mony_2}{mony_3}{transfer_flag}{asett}{key}{len_transaction}{transaction}{times}0C0000'.format(
            transfer_code='80', index='00', mony_1=mony_1, mony_2=mony_2, mony_3=mony_3,
            asett=self.asset_number, key=self.reg_key, len_transaction=len_transaction_id, transaction=last_transaction,
            times=my_time, transfer_flag='00')
        cmd = '72' + hex(int(len(cmd) // 2))[2:] + cmd
        new_cmd = self.cmd_to_list(cmd)

        response = None
        # self.AFT_register()
        # if lock_timeout == 0:
        #     lock_timeout = self.lock_time
        # if lock_timeout > 0:
        #     lock_data = self.AFT_game_lock_and_status_request(lock_timeout=lock_timeout)
        #     if lock_data['game_lock_status'] != '00':
        #         self.log.warning('EMG is not locked')
        #         return None
        try:
            data = self._send_command(new_cmd, crc_need=True, size=82)
            if (data is not None):
                a = int(self.hexlify(self.bytearray(data[26:27])), 16)
                response = {
                    'Length': int(self.hexlify(self.bytearray(data[26:27])), 16),
                    'Transaction buffer position': int(self.hexlify(self.bytearray(data[2:3])), 16),
                    'Transfer status': AFT_TRANSFER_STATUS[self.hexlify(self.bytearray(data[3:4]))],
                    'Receipt status': AFT_RECEIPT_STATUS[self.hexlify(self.bytearray(data[4:5]))],
                    'Transfer type': AFT_TRANSFER_TYPE[self.hexlify(self.bytearray(data[5:6]))],
                    'Cashable amount': round(int(self.hexlify(self.bytearray(data[6:11]))) * self.denom, 2),
                    'Restricted amount': round(int(self.hexlify(self.bytearray(data[11:16]))) * self.denom, 2),
                    'Nonrestricted amount': round(int(self.hexlify(self.bytearray(data[16:21]))) * self.denom, 2),
                    'Transfer flags': self.hexlify(self.bytearray(data[21:22])),
                    'Asset number': self.hexlify(self.bytearray(data[22:26])),
                    'Transaction ID length': self.hexlify(self.bytearray(data[26:27])),
                    'Transaction ID': self.hexlify(self.bytearray(data[27:(27 + a)]))
                }
        except Exception as e:
            self.log.error(e, exc_info=True)
        # try:
        self.AFT_unregister()
        # except:
        #     self.log.warning('AFT UNREGISTER ERROR: out')
        return response

    def AFT_cashout_enable(self, amount=1, **kwargs):

        my_time = datetime.datetime.now()
        my_time = datetime.datetime.strftime(my_time, '%m%d%Y')
        mony_1 = mony_2 = mony_3 = self.mony_to_hex(0, 5)
        last_transaction = self.AFT_format_transaction()
        len_transaction_id = hex(len(last_transaction) // 2)[2:]
        if len(len_transaction_id) < 2:
            len_transaction_id = '0' + len_transaction_id
        elif len(len_transaction_id) % 2 == 1:
            len_transaction_id = '0' + len_transaction_id

        cmd = '00{index}{transfer_code}{mony_1}{mony_2}{mony_3}{transfer_flag}{asett}{key}{len_transaction}{transaction}{times}0C0000'.format(
            transfer_code='80', index='00', mony_1=mony_1, mony_2=mony_2, mony_3=mony_3,
            asett=self.asset_number, key=self.reg_key, len_transaction=len_transaction_id, transaction=last_transaction,
            times=my_time, transfer_flag='02')
        cmd = '72' + hex(int(len(cmd) // 2))[2:] + cmd
        new_cmd = self.cmd_to_list(cmd)
        self.AFT_register()

        response = None
        try:
            data = self._send_command(new_cmd, crc_need=True, size=82)
            if (data is not None):
                a = int(self.hexlify(self.bytearray(data[26:27])), 16)
                response = {
                    'Length': int(self.hexlify(self.bytearray(data[26:27])), 16),
                    'Transaction buffer position': int(self.hexlify(self.bytearray(data[2:3])), 16),
                    'Transfer status': AFT_TRANSFER_STATUS[self.hexlify(self.bytearray(data[3:4]))],
                    'Receipt status': AFT_RECEIPT_STATUS[self.hexlify(self.bytearray(data[4:5]))],
                    'Transfer type': AFT_TRANSFER_TYPE[self.hexlify(self.bytearray(data[5:6]))],
                    'Cashable amount': round(int(self.hexlify(self.bytearray(data[6:11]))) * self.denom, 2),
                    'Restricted amount': round(int(self.hexlify(self.bytearray(data[11:16]))) * self.denom, 2),
                    'Nonrestricted amount': round(int(self.hexlify(self.bytearray(data[16:21]))) * self.denom, 2),
                    'Transfer flags': self.hexlify(self.bytearray(data[21:22])),
                    'Asset number': self.hexlify(self.bytearray(data[22:26])),
                    'Transaction ID length': self.hexlify(self.bytearray(data[26:27])),
                    'Transaction ID': self.hexlify(self.bytearray(data[27:(27 + a)]))
                }
        except Exception as e:
            self.log.info(e, exc_info=True)
        # try:
        self.AFT_unregister()
        # except:
        # try:
        #     time.sleep(0.04)
        #     self.AFT_clean_transaction_poll()
        # except Exception as e:
        #     pass
        try:
            self.AFT_clean_transaction_poll()
        except:
            pass
        return True

    def AFT_won(self, mony, amount=1, games=None, lock_timeout=None, **kwargs):

        if self.denom > 0.01:
            return None
        if games == None:
            for i in range(3):
                try:
                    game_selected = self.selected_game_number(in_hex=False)
                except:
                    game_selected = None
                if game_selected == None:
                    time.sleep(0.04)
                else:
                    break
        else:
            game_selected = games
        if game_selected == 0:
            return 'NoGame'
        elif game_selected == None:
            return 'NoGame'
        elif game_selected < 1:
            return 'NoGame'
        elif not game_selected:
            return 'NoGame'

        my_time = datetime.datetime.now()
        my_time = datetime.datetime.strftime(my_time, '%m%d%Y')
        mony_1 = mony_2 = mony_3 = self.mony_to_hex(0, 5)
        if amount == 1:
            mony_1 = self.mony_to_hex(mony, 5)
        elif amount == 2:
            mony_2 = self.mony_to_hex(mony, 5)
        elif amount == 3:
            mony_3 = self.mony_to_hex(mony, 5)
        else:
            raise AFTBadAmount
        self.AFT_register()
        if lock_timeout is None:
            lock_timeout = self.lock_time
        self.last_AFT_lock_status = False
        if lock_timeout > 0:
            lock_data = self.AFT_game_lock_and_status_request(lock_timeout=lock_timeout)
            if lock_data == None or lock_data == False:
                self.log.warning('EMG is not locked')
                self.last_AFT_lock_status = True
                data = self.AFT_clean_transaction_poll()
                return False
            if lock_data['game_lock_status'] != '00':
                self.log.warning('EMG is not locked')
                self.last_AFT_lock_status = True
                data = self.AFT_clean_transaction_poll()
                return False
        last_transaction = self.AFT_format_transaction()
        len_transaction_id = hex(int(len(last_transaction) // 2))[2:]

        if len(len_transaction_id) < 2:
            len_transaction_id = '0' + len_transaction_id
        elif len(len_transaction_id) % 2 == 1:
            len_transaction_id = '0' + len_transaction_id

        cmd = '{transfer_code}{index}{mony_1}{mony_2}{mony_3}{transfer_flag}{asett}{key}{len_transaction}{transaction}{times}0C0000'.format(
            transfer_code='0000', index='10', mony_1=mony_1, mony_2=mony_2, mony_3=mony_3,
            asett=self.asset_number, key=self.reg_key, len_transaction=len_transaction_id, transaction=last_transaction,
            times=my_time, transfer_flag='00')
        cmd = '72' + hex(int(len(cmd) // 2))[2:] + cmd

        new_cmd = self.cmd_to_list(cmd)

        response = None
        try:
            data = self._send_command(new_cmd, crc_need=True, size=82)
            if (data is not None):
                a = int(self.hexlify(self.bytearray(data[26:27])), 16)
                response = {
                    'Length': int(self.hexlify(self.bytearray(data[26:27])), 16),
                    'Transaction buffer position': int(self.hexlify(self.bytearray(data[2:3])), 16),
                    'Transfer status': AFT_TRANSFER_STATUS[self.hexlify(self.bytearray(data[3:4]))],
                    'Receipt status': AFT_RECEIPT_STATUS[self.hexlify(self.bytearray(data[4:5]))],
                    'Transfer type': AFT_TRANSFER_TYPE[self.hexlify(self.bytearray(data[5:6]))],
                    'Cashable amount': round(int(self.hexlify(self.bytearray(data[6:11]))) * self.denom, 2),
                    'Restricted amount': round(int(self.hexlify(self.bytearray(data[11:16]))) * self.denom, 2),
                    'Nonrestricted amount': round(int(self.hexlify(self.bytearray(data[16:21]))) * self.denom, 2),
                    'Transfer flags': self.hexlify(self.bytearray(data[21:22])),
                    'Asset number': self.hexlify(self.bytearray(data[22:26])),
                    'Transaction ID length': self.hexlify(self.bytearray(data[26:27])),
                    'Transaction ID': self.hexlify(self.bytearray(data[27:(27 + a)]))
                }
        except Exception as e:
            self.log.error(e, exc_info=True)
        self.AFT_unregister()
        # except:
        #     self.log.warning('AFT UNREGISTER ERROR: won')
        return response

    def AFT_in(self, mony, amount=1, lock_timeout=None, **kwargs):
        if self.denom > 0.01:
            return None
        my_time = datetime.datetime.now()
        my_time = datetime.datetime.strftime(my_time, '%m%d%Y')
        mony_1 = mony_2 = mony_3 = self.mony_to_hex(0, 5)
        if amount == 1:
            mony_1 = self.mony_to_hex(mony, 5)
        elif amount == 2:
            mony_2 = self.mony_to_hex(mony, 5)
        elif amount == 3:
            mony_3 = self.mony_to_hex(mony, 5)
        else:
            raise AFTBadAmount
        self.AFT_register()
        if lock_timeout is None:
            lock_timeout = self.lock_time
        self.last_AFT_lock_status = False
        if lock_timeout > 0:
            lock_data = self.AFT_game_lock_and_status_request(lock_timeout=lock_timeout)
            if lock_data == None or lock_data == False:
                self.log.warning('EMG is not locked')
                self.last_AFT_lock_status = True
                data = self.AFT_clean_transaction_poll()
                return False
            if lock_data['game_lock_status'] != '00':
                self.log.warning('EMG is not locked')
                self.last_AFT_lock_status = True
                data = self.AFT_clean_transaction_poll()
                return False
        last_transaction = self.AFT_format_transaction()
        len_transaction_id = hex(int(len(last_transaction) // 2))[2:]
        # raise KeyError(last_transaction, len_transaction_id)
        if len(len_transaction_id) < 2:
            len_transaction_id = '0' + len_transaction_id
        elif len(len_transaction_id) % 2 == 1:
            len_transaction_id = '0' + len_transaction_id
        cmd = '{transfer_code}{index}00{mony_1}{mony_2}{mony_3}{transfer_flag}{asett}{key}{len_transaction}{transaction}{times}0C0000'.format(
            transfer_code='00', index='00', mony_1=mony_1, mony_2=mony_2, mony_3=mony_3,
            asett=self.asset_number, key=self.reg_key, len_transaction=len_transaction_id, transaction=last_transaction,
            times=my_time, transfer_flag='00')
        cmd = '72' + hex(int(len(cmd) // 2))[2:] + cmd
        new_cmd = self.cmd_to_list(cmd)
        response = None
        # self.AFT_register()
        # if lock_timeout == 0:
        #     lock_timeout = self.lock_time
        # if lock_timeout > 0:
        #     lock_data = self.AFT_game_lock_and_status_request(lock_timeout=lock_timeout)
        #     if lock_data['game_lock_status'] != '00':
        #         self.log.warning('EMG is not locked')
        #         return None
        try:
            data = self._send_command(new_cmd, crc_need=True, size=82)
            if (data is not None):
                a = int(self.hexlify(self.bytearray(data[26:27])), 16)
                response = {
                    'Length': int(self.hexlify(self.bytearray(data[26:27])), 16),
                    'Transaction buffer position': int(self.hexlify(self.bytearray(data[2:3])), 16),
                    'Transfer status': AFT_TRANSFER_STATUS[self.hexlify(self.bytearray(data[3:4]))],
                    'Receipt status': AFT_RECEIPT_STATUS[self.hexlify(self.bytearray(data[4:5]))],
                    'Transfer type': AFT_TRANSFER_TYPE[self.hexlify(self.bytearray(data[5:6]))],
                    'Cashable amount': round(int(self.hexlify(self.bytearray(data[6:11]))) * self.denom, 2),
                    'Restricted amount': round(int(self.hexlify(self.bytearray(data[11:16]))) * self.denom, 2),
                    'Nonrestricted amount': round(int(self.hexlify(self.bytearray(data[16:21]))) * self.denom, 2),
                    'Transfer flags': self.hexlify(self.bytearray(data[21:22])),
                    'Asset number': self.hexlify(self.bytearray(data[22:26])),
                    'Transaction ID length': self.hexlify(self.bytearray(data[26:27])),
                    'Transaction ID': self.hexlify(self.bytearray(data[27:(27 + a)]))
                }
        except Exception as e:
            self.log.error(e, exc_info=True)
        # try:
        self.AFT_unregister()
        # except:
        # self.log.warning('AFT UNREGISTER ERROR: in')
        return response

    def AFT_clean_transaction_poll(self, register=False, **kwargs):
        # try:
        if register == True:
            self.AFT_register()
        # except Exception as e:
        #     self.log.error(e, exc_info = True)
        if self.transaction == None:
            self.AFT_get_last_transaction()
        # time.sleep(0.7)
        cmd = '7202FF00'
        count = 0
        new_cmd = self.cmd_to_list(cmd)
        response = None
        try:
            data = self._send_command(new_cmd, crc_need=True, size=90)
            if (data is not None):
                # print self.hexlify(self.bytearray(data))
                a = int(self.hexlify(self.bytearray(data[26:27])), 16)
                response = {
                    'Length': int(self.hexlify(self.bytearray(data[26:27])), 16),
                    'Transfer status': AFT_TRANSFER_STATUS[self.hexlify(self.bytearray(data[3:4]))],
                    'Receipt status': AFT_RECEIPT_STATUS[self.hexlify(self.bytearray(data[4:5]))],
                    'Transfer type': AFT_TRANSFER_TYPE[self.hexlify(self.bytearray(data[5:6]))],
                    'Cashable amount': round(int(self.hexlify(self.bytearray(data[6:11]))) * self.denom, 2),
                    'Restricted amount': round(int(self.hexlify(self.bytearray(data[11:16]))) * self.denom, 2),
                    'Nonrestricted amount': round(int(self.hexlify(self.bytearray(data[16:21]))) * self.denom, 2),
                    'Transfer flags': self.hexlify(self.bytearray(data[21:22])),
                    'Asset number': self.hexlify(self.bytearray(data[22:26])),
                    'Transaction ID length': self.hexlify(self.bytearray(data[26:27])),
                    'Transaction ID': self.hexlify(self.bytearray(data[27:(27 + a)]))
                }
            if self.last_AFT_lock_status == True:
                response['Transfer status'] = 'Gaming machine not locked (transfer specified lock required)'
                return response
            if register == True:
                # try:
                self.AFT_unregister()
            if response == None:
                pass
            elif hex(self.transaction)[2:] == response['Transaction ID']:
                return response
            else:
                if self.aft_check_last_transaction == True:
                    raise BadTransactionID('last: %s, new:%s ' % (
                        hex(self.transaction)[2:], response['Transaction ID']))
                else:
                    self.log.info('last: %s, new:%s ' % (
                        hex(self.transaction)[2:], response['Transaction ID']))
        except BadCRC:
            pass
        if self.last_AFT_lock_status:
            self.last_AFT_lock_status = False
        return False

    def AFT_transfer_funds(self, security_code=44, transfer_code=00, transaction_index=00, transfer_type=00, cashable_amount=0,
                           restricted_amount=0, non_restricted_amount=0, transfer_flags=00,
                           asset_number=b'0000000000', registration_key=0, transaction_ID_lenght=0x00,
                           transaction_ID='', expiration=0, pool_ID=0, reciept_data='', lock_timeout=0, **kwargs):
        # 72
        cmd = [0x72, security_code]
        cmd.append(transfer_code)
        cmd.append(transaction_index)
        cmd.append(transfer_type)
        cmd.extend(self.bcd_coder_array(cashable_amount, 5))
        cmd.extend(self.bcd_coder_array(restricted_amount, 5))
        cmd.extend(self.bcd_coder_array(non_restricted_amount, 5))
        cmd.append(transfer_flags)
        cmd.extend((asset_number))
        cmd.extend(self.bcd_coder_array(registration_key, 20))
        cmd.append(len(transaction_ID))
        cmd.extend(transaction_ID)
        cmd.extend(self.bcd_coder_array(expiration, 4))
        cmd.extend(self.bcd_coder_array(pool_ID, 2))

        cmd.append(len(reciept_data))
        cmd.extend(reciept_data)
        cmd.extend(self.bcd_coder_array(lock_timeout, 2))

        cmd[1] = len(transaction_ID) + len(transaction_ID) + 53
        new_cmd = self.cmd_to_list(cmd)
        cmd = new_cmd
        data = self._send_command(cmd, crc_need=True)
        if (data is not None):
            aft_statement['transaction_buffer_position'] = int(self.hexlify(self.bytearray(data[2:3])), 16)
            aft_statement['transfer_status'] = int(self.hexlify(self.bytearray(data[3:4])))
            aft_statement['receipt_status'] = int(self.hexlify(self.bytearray(data[4:5])))
            aft_statement['transfer_type'] = int(self.hexlify(self.bytearray(data[5:6])))
            aft_statement['cashable_amount'] = int(self.hexlify(self.bytearray(data[6:11])))
            aft_statement['restricted_amount'] = int(self.hexlify(self.bytearray(data[11:16])))
            aft_statement['nonrestricted_amount'] = int(self.hexlify(self.bytearray(data[16:21])))
            aft_statement['transfer_flags'] = int(self.hexlify(self.bytearray(data[21:22])))
            aft_statement['asset_number'] = (self.hexlify(self.bytearray(data[22:26])))
            aft_statement['transaction_ID_lenght'] = int(self.hexlify(self.bytearray(data[26:27])))
            a = int(self.hexlify(self.bytearray(data[26:27])))
            aft_statement['transaction_ID'] = str(self.hexlify(self.bytearray(data[27:(27 + a + 1)])))
            a = 27 + a + 1
            aft_statement['transaction_date'] = str(self.hexlify(self.bytearray(data[a:a + 5])))
            a = a + 5
            aft_statement['transaction_time'] = str(self.hexlify(self.bytearray(data[a:a + 4])))
            aft_statement['expiration'] = str(self.hexlify(self.bytearray(data[a + 4:a + 9])))
            aft_statement['pool_ID'] = str(self.hexlify(self.bytearray(data[a + 9:a + 11])))
            aft_statement['cumulative_casable_amount_meter_size'] = (self.hexlify(self.bytearray(data[a + 11:a + 12])))
            b = a + int(self.hexlify(self.bytearray(data[a + 11:a + 12])))
            aft_statement['cumulative_casable_amount_meter'] = (self.hexlify(self.bytearray(data[a + 12:b + 1])))
            aft_statement['cumulative_restricted_amount_meter_size'] = (self.hexlify(self.bytearray(data[b + 1:b + 2])))
            c = b + 2 + int(self.hexlify(self.bytearray(data[b + 1:b + 2])))
            aft_statement['cumulative_restricted_amount_meter'] = (self.hexlify(self.bytearray(data[b + 2:c])))
            aft_statement['cumulative_nonrestricted_amount_meter_size'] = (self.hexlify(self.bytearray(data[c:c + 1])))
            b = int(self.hexlify(self.bytearray(data[c:c + 1]))) + c
            aft_statement['cumulative_nonrestricted_amount_meter'] = (self.hexlify(self.bytearray(data[c + 1:])))

            return data[1]
        return None

    def AFT_get_last_transaction(self, **kwargs):
        cmd = [0x72, 0x02, 0xFF, 0x00]
        transaction = None
        try:
            data = self._send_command(cmd, crc_need=True, size=90)
        except Exception as e:
            self.log.error(e, exc_info=True)
            transaction = int('2020202020202020202020202020202021', 16)
            self.log.warning('AFT no transaction')
        if (data is not None):
            try:
                # if self.aft_check_last_transaction == False:
                #     raise ValueError

                count = int(self.hexlify(self.bytearray(data[26:27])), 16)
                if count > 1:
                    pass
                else:
                    raise ValueError
                # raise KeyError(self.hexlify(self.bytearray(data[27:27 + count])))
                transaction = self.hexlify(self.bytearray(data[27:27 + count]))
                if int(transaction, 16) < 10931737842416972128203783466984490934305:
                    raise ValueError
                # raise KeyError(self.hexlify(self.bytearray(data[26:])))
                if transaction == '2121212121212121212121212121212121':
                    transaction = '2020202020202020202020202020202021'
                # self.transaction = int(transaction, 16)
                return int(transaction, 16)
            except ValueError as e:
                self.log.warning(e, exc_info=True)
                transaction = int('2020202020202020202020202020202021', 16)
                self.log.warning('AFT no transaction')
            except Exception as e:
                self.log.error(e, exc_info=True)
                transaction = int('2020202020202020202020202020202021', 16)
                self.log.warning('AFT no transaction')
        else:
            #if not self.transaction:
            transaction = int('2020202020202020202020202020202021', 16)
            self.log.warning('AFT no transaction')
        self.transaction = transaction
        return transaction

    def AFT_format_transaction(self, get_from_emg=None, **kwargs):
        if get_from_emg is None:
            get_from_emg = self.get_aft_transaction_from_EMG
        if get_from_emg == True:
            self.transaction = self.AFT_get_last_transaction()
        self.transaction += 1
        transaction = hex(self.transaction)[2:]
        count = 0
        tmp = []
        for i in range(int(len(transaction) / 2)):
            tmp.append(transaction[count:count + 2])
            count += 2
        tmp.reverse()
        for i in range(len(tmp)):
            if int(tmp[i], 16) >= 126:
                tmp[i] = '20'
                if int(tmp[i + 1], 16) + 1 <= 32:
                    tmp[i + 1] = '20'
                else:
                    tmp[i + 1] = hex(int(tmp[i + 1], 16) + 1)[2:]
        tmp.reverse()
        response = ''
        for i in tmp:
            response += i
        if response == '2121212121212121212121212121212121':
            response = '2020202020202020202020202020202021'
        self.transaction = int(response, 16)
        return response

    def AFT_register_initial(self, **kwargs):
        try:
            return self.AFT_register_gaming_machine(reg_code=0x01)
        except Exception as e:
            self.log.error(e, exc_info=True)
            return None

    def AFT_register(self, mk_reg=False, **kwargs):
        if mk_reg is False:
            return True
        try:
            return self.AFT_register_gaming_machine(reg_code=0x00)
        except Exception as e:
            self.log.error(e, exc_info=True)
            return None

    def AFT_unregister(self, mk_reg=False, **kwargs):
        if mk_reg is False:
            return True
        try:
            return self.AFT_register_gaming_machine(reg_code=0x80)
        except Exception as e:
            self.log.error(e, exc_info=True)
            return None

    def AFT_register_gaming_machine(self, reg_code=0xff, **kwargs):
        # 73
        cmd = [0x73, 0x00]
        if reg_code == 0xFF:
            cmd.append(reg_code)
            cmd[1] = 0x01
        else:
            cmd.append(reg_code)
            tmp = self.asset_number + self.reg_key + self.POS_ID
            cmd[1] = 0x1D
            count = 0
            for i in range(int(len(tmp) / 2)):
                cmd.append(int(tmp[count:count + 2], 16))
                count += 2
        data = self._send_command(cmd, crc_need=True, size=34)
        # data = None
        if (data is not None):
            aft_statement = {}
            aft_statement['registration_status'] = AFT_REGISTRACION_STATUS[self.hexlify(self.bytearray(data[2:3]))]
            aft_statement['asset_number'] = self.hexlify(self.bytearray(data[3:7]))
            aft_statement['registration_key'] = self.hexlify(self.bytearray(data[7:27]))
            aft_statement['POS_ID'] = self.hexlify(self.bytearray(data[27:]))
            return aft_statement
        return None

    # def AFT_game_lock(self, lock_timeout=100, condition='01', **kwargs):
    #     return self.AFT_game_lock_and_status_request(lock_code='00', lock_timeout=lock_timeout,
    #                                                  condition=condition)
    #
    # def AFT_game_unlock(self, **kwargs):
    #     return self.AFT_game_lock_and_status_request(lock_code='80')

    def AFT_game_lock_and_status_request(self, lock_code='00', lock_timeout=200, condition='01', **kwargs):
        # 74
        try:
            lock_time = self.mony_to_hex(lock_timeout, 2, False)
        except Exception as e:
            raise ValueError(e.__str__())
        # if len(lock_time) == 1:
        #     lock_time = '000%s' % (lock_time)
        # elif len(lock_time) == 2:
        #     lock_time = '00%s' % (lock_time)
        # elif len(lock_time) == 3:
        #     lock_time = '0%s' % (lock_time)
        # elif len(lock_time) == 4:
        #     lock_time = '%s' % (lock_time)
        # else:
        #     raise ValueError('Invalid time')
        cmd = '74%s%s%s' % (lock_code, condition, lock_time)
        new_cmd = self.cmd_to_list(cmd)
        response = self._send_command(new_cmd, crc_need=True, size=40)
        if (response is not None):
            aft_statement = {}
            aft_statement['asset_number'] = str(self.hexlify(self.bytearray(response[2:6])))
            aft_statement['game_lock_status'] = str(self.hexlify(self.bytearray(response[6:7])))
            aft_statement['avilable_transfers'] = str(self.hexlify(self.bytearray(response[7:8])))
            aft_statement['host_cashout_status'] = str(self.hexlify(self.bytearray(response[8:9])))
            aft_statement['AFT_status'] = str(self.hexlify(self.bytearray(response[9:10])))
            aft_statement['max_buffer_index'] = str(self.hexlify(self.bytearray(response[10:11])))
            aft_statement['current_cashable_amount'] = str(self.hexlify(self.bytearray(response[11:16])))
            aft_statement['current_restricted_amount'] = str(self.hexlify(self.bytearray(response[16:21])))
            aft_statement['current_non_restricted_amount'] = str(self.hexlify(self.bytearray(response[21:26])))
            aft_statement['restricted_expiration'] = str(self.hexlify(self.bytearray(response[26:29])))
            aft_statement['restricted_pool_ID'] = str(self.hexlify(self.bytearray(response[29:31])))
            return aft_statement
        return None

    def AFT_cansel_request(self, **kwargs):
        cmd = [0x72, 0x01, 0x80]
        self.AFT_register()
        response = None
        data = self._send_command(cmd, crc_need=True, size=90)
        if (data is not None):
            a = int(self.hexlify(self.bytearray(data[26:27])), 16)
            response = {
                'Length': int(self.hexlify(self.bytearray(data[26:27])), 16),
                'Transfer status': AFT_TRANSFER_STATUS[self.hexlify(self.bytearray(data[3:4]))],
                'Receipt status': AFT_RECEIPT_STATUS[self.hexlify(self.bytearray(data[4:5]))],
                'Transfer type': AFT_TRANSFER_TYPE[self.hexlify(self.bytearray(data[5:6]))],
                'Cashable amount': round(int(self.hexlify(self.bytearray(data[6:11]))) * self.denom, 2),
                'Restricted amount': round(int(self.hexlify(self.bytearray(data[11:16]))) * self.denom, 2),
                'Nonrestricted amount': round(int(self.hexlify(self.bytearray(data[16:21]))) * self.denom, 2),
                'Transfer flags': self.hexlify(self.bytearray(data[21:22])),
                'Asset number': self.hexlify(self.bytearray(data[22:26])),
                'Transaction ID length': self.hexlify(self.bytearray(data[26:27])),
                'Transaction ID': self.hexlify(self.bytearray(data[27:(27 + a)]))
            }
        # try:
        self.AFT_unregister()
        # except:
        #     self.log.warning('AFT UNREGISTER ERROR')
        if response:
            if response['Transaction ID'] == hex(self.transaction)[2:]:
                return response
        # self.log.warning('NO CLEAN POLL: %s', response)
        return False

    def AFT_reciept_data(self, **kwargs):
        # 75
        return

    def AFT_set_custom_ticket_data(self, **kwargs):
        # 76
        return

    def exnended_validation_status(self, control_mask=[0, 0], status_bits=[0, 0], cashable_ticket_reciept_exp=0,
                                   restricted_ticket_exp=0, **kwargs):
        # 7B
        cmd = [0x7B, 0x08]

        cmd.extend(control_mask)
        cmd.extend(status_bits)
        cmd.extend(self.bcd_coder_array(cashable_ticket_reciept_exp, 2))
        cmd.extend(self.bcd_coder_array(restricted_ticket_exp, 2))

        # cmd.addend(0x23)

        data = self._send_command(cmd, True, crc_need=True)
        if (data is not None):
            aft_statement['asset_number'] = str(self.hexlify(self.bytearray(data[2:6])))
            aft_statement['status_bits'] = str(self.hexlify(self.bytearray(data[6:8])))
            aft_statement['cashable_ticket_reciept_exp'] = str(self.hexlify(self.bytearray(data[8:10])))
            aft_statement['restricted_ticket_exp'] = str(self.hexlify(self.bytearray(data[10:])))

            return data[1]
        return None

    def set_extended_ticket_data(self, **kwargs):
        # 7C
        return None

    def set_ticket_data(self, **kwargs):
        # 7D
        return None

    def current_date_time(self, **kwargs):
        # 7E
        cmd = [0x7E]
        data = self._send_command(cmd, crc_need=False, size=11)
        if (data is not None):
            data = str(self.hexlify(self.bytearray(data[1:8])))
            return datetime.datetime.strptime(data, '%m%d%Y%H%M%S')
        return None

    def recieve_date_time(self, dates, times, **kwargs):
        # 7F
        cmd = [0x7F]
        my_cmd = '' + dates.replace('.', '') + times.replace(':', '') + '00'
        count = 0
        for i in range(int(len(my_cmd) / 2)):
            cmd.append(int(my_cmd[count:count + 2], 16))
            count += 2

        if (self._send_command(cmd, True, crc_need=True) == self.adress):
            return True
        # else:
        return None
        # return None

    def recieve_progressive_amount(self, **kwargs):
        # 80
        return None

    def cumulative_progressive_wins(self, **kwargs):
        # 83
        return None

    def progressive_win_amount(self, **kwargs):
        # 84
        return None

    def SAS_progressive_win_amount(self, **kwargs):
        # 85
        return None

    def recieve_multiple_progressive_levels(self, **kwargs):
        # 86
        return None

    def multiple_SAS_progresive_win_amounts(self, **kwargs):
        # 87
        return None

    def initiate_legacy_bonus_pay(self, mony, tax='00', games=None, **kwargs):
        # 8A
        if games == None:
            for i in range(3):
                try:
                    game_selected = self.selected_game_number(in_hex=False)
                except:
                    game_selected = None
                if game_selected == None:
                    time.sleep(0.04)
                else:
                    break
        else:
            game_selected = games
        if game_selected == None:
            return None
        elif game_selected == 0:
            return 'NoGame'
        elif game_selected < 0:
            return 'NoGame'
        cmd = '8A' + self.mony_to_hex(mony, 4) + tax
        cmd = self.cmd_to_list(cmd)
        # cmd = str(int(round(mony / self.denom, 2)))
        # # cmd = cmd.replace('.', '')
        # cmd = '0' * (8 - len(cmd)) + cmd
        # my_cmd = cmd + tax
        # cmd = [0x8A]
        # count = 0
        # for i in range(int(len(my_cmd) / 2)):
        #     cmd.append(int(my_cmd[count:count + 2], 16))
        #     count += 2
        if (self._send_command(cmd, True, crc_need=True) == self.adress):
            return True
        # else:
        return None
        # return None

    def initiate_multiplied_jackpot_mode(self, **kwargs):
        # 8B
        return None

    def enter_exit_tournament_mode(self, **kwargs):
        # 8C
        return None

    def card_info(self, **kwargs):
        # 8E
        return None

    def physical_reel_stop_info(self, **kwargs):
        # 8F
        return None

    def legacy_bonus_win_info(self, **kwargs):
        # 90
        return None

    def remote_handpay_reset(self, **kwargs):
        # 94
        cmd = [0x94]
        if (self._send_command(cmd, True, crc_need=True) == self.adress):
            return True
        # else:
        return None
        # return

    def tournament_games_played(self, **kwargs):
        # 95
        return

    def tournament_games_won(self, **kwargs):
        # 96
        return

    def tournament_credits_wagered(self, **kwargs):
        # 97
        return

    def tournament_credits_won(self, **kwargs):
        # 98
        return

    def meters_95_98(self, **kwargs):
        # 99
        return

    def legacy_bonus_meters(self, denom=True, game_number='0000', **kwargs):
        # 9A
        game_number = int(game_number, 16)
        cmd = [0x9A, ((game_number >> 8) & 0xFF), (game_number & 0xFF)]
        # cmd.extend([(n&0xFF), ((n>>8)&0xFF)])
        # cmd=[0x19]
        data = self._send_command(cmd, crc_need=True, size=18)

        if (data is not None):
            meters = {}
            if denom == False:
                meters['game bumber'] = int(self.hexlify(self.bytearray(data[2:3])))
                meters['deductible'] = int(self.hexlify(self.bytearray(data[3:7])))
                meters['non-deductible'] = int(self.hexlify(self.bytearray(data[7:11])))
                meters['wager match'] = int(self.hexlify(self.bytearray(data[11:15])))

            else:
                meters['game bumber'] = int(self.hexlify(self.bytearray(data[2:3])))
                meters['deductible'] = round(int(self.hexlify(self.bytearray(data[3:7]))) * self.denom, 2)
                meters['non-deductible'] = round(int(self.hexlify(self.bytearray(data[7:11]))) * self.denom, 2)
                meters['wager match'] = round(int(self.hexlify(self.bytearray(data[11:15]))) * self.denom, 2)
            return meters
        return None

    def stop_autorebet(self, **kwargs):
        # AA00
        cmd = [0xAA, 0x00]
        if (self._send_command(cmd, True, crc_need=True) == self.adress):
            return True
        # else:
        return None
        # return

    def start_autorebet(self, **kwargs):
        # AA01
        cmd = [0xAA, 0x01]
        if (self._send_command(cmd, True, crc_need=True) == self.adress):
            return True
        # else:
        return None
        # return

    def enabled_features(self, game_nimber=0, **kwargs):
        # A0
        cmd = [0xA0]

        cmd.extend(self.bcd_coder_array(game_nimber, 2))

        data = self._send_command(cmd, True, crc_need=True)
        if (data is not None):
            aft_statement['game_number'] = str(self.hexlify(self.bytearray(data[1:3])))
            aft_statement['features_1'] = data[3]
            aft_statement['features_2'] = data[4]
            aft_statement['features_3'] = data[5]

            game_features['game_number'] = aft_statement.get('game_number')
            if (data[3] & 0b00000001):
                game_features['jackpot_multiplier'] = 1
            else:
                game_features['jackpot_multiplier'] = 0

            if (data[3] & 0b00000010):
                game_features['AFT_bonus_avards'] = 1
            else:
                game_features['AFT_bonus_avards'] = 0
            if (data[3] & 0b00000100):
                game_features['legacy_bonus_awards'] = 1
            else:
                game_features['legacy_bonus_awards'] = 0
            if (data[3] & 0b00001000):
                game_features['tournament'] = 1
            else:
                game_features['tournament'] = 0
            if (data[3] & 0b00010000):
                game_features['validation_extensions'] = 1
            else:
                game_features['validation_extensions'] = 0

            game_features['validation_style'] = data[3] & 0b01100000 >> 5

            if (data[3] & 0b10000000):
                game_features['ticket_redemption'] = 1
            else:
                game_features['ticket_redemption'] = 0

            return data[1]
        return None

    def cashout_limit(self, **kwargs):
        # A4
        return

    def enable_jackpot_handpay_reset_method(self, **kwargs):
        # A8
        return

    def extended_meters_game_alt(self, n=1, **kwargs):
        # AF
        return

    def multi_denom_preamble(self, **kwargs):
        # B0
        return

    def current_player_denomination(self, **kwargs):
        # B1
        return

    def enabled_player_denominations(self, **kwargs):
        # B2
        return

    def token_denomination(self, **kwargs):
        # B3
        return

    def wager_category_info(self, **kwargs):
        # B4
        return

    def extended_game_info(self, n=1, **kwargs):
        # B5
        return

    def event_response_to_long_poll(self, **kwargs):
        # FF
        return


    def bytearray(self, data):
        return data.hex()

    def hexlify(self, data):
        data = data.replace('-', '')
        return data


    def bcd_coder_array(self, value=0, lenght=5):
        return self.int_to_bcd(value, lenght)

    def int_to_bcd(self, number=0, lenght=5):
        n = 0
        m = 0
        bval = 0
        p = lenght - 1
        result = []
        for i in range(0, lenght):
            result.extend([0x00])
        while (p >= 0):
            if (number != 0):
                digit = int(number % 10)
                number = number / 10
                m = m + 1
            else:
                digit = 0
            if (n & 1):
                bval |= digit << 4
                result[p] = bval
                p = p - 1
                bval = 0
            else:
                bval = digit
            n = n + 1
        return result

    def mony_to_hex(self, mony=0, lenght=5, denom=True):
        if denom is True:
            mony = str(int((mony / self.denom)))
        else:
            mony = str(int(mony))
        mony = mony.replace('.', '')
        lenght = lenght * 2
        mony = '0' * (lenght - len(mony)) + mony
        return mony

    def cmd_to_list(self, cmd):
        intArray = list(map(lambda x: int(x, 16),
                            [cmd[i:i + 2] for i in range(0, len(cmd), 2)]))
        return intArray

class SAS_USB(Sas):

    def _send_command(self, command, no_response=False, timeout=None, crc_need=True, size=1):
        # if timeout == None:
        #     timeout = self.timeout + 1
        # time.sleep(0.04)
        busy = True
        response = b''
        # self.my_log.flush()
        try:
            # if self.poll_adres == '82':
            #     self.poll_adres = '80'
            # else:
            #     self.poll_adres = '82'

            buf_header = [self.adress]
            self._conf_port()
            # self.connection.write(('80' + self.mashin_n).decode("hex"))
            # self.close()
            # self.connection.parity = serial.PARITY_SPACE
            # self.open()

            buf_header.extend(command)
            buf_count = len(command)
            # self.log.debug('%s', buf_header)
            if (crc_need == True):
                crc = CRC16Kermit().calculate(bytes(buf_header))
                buf_header.extend([((crc >> 8) & 0xFF), (crc & 0xFF)])
            self.log.debug(buf_header)
            # time.sleep(0.04)
            self.connection.write([self.poll_adress, self.adress])
            time.sleep(self.sleep_time)
            # self.close()
            self.connection.parity = serial.PARITY_SPACE
            # self.open()
            # my_log = open('/home/colibri/dump.log', 'w')
            if self.sas_dump:
                self.my_log = open('/var/log/sas_dump.log', 'a')
                self.my_log.write('TX %s: %s\n' % (time.time(), binascii.hexlify(bytearray(buf_header))))
                self.my_log.close()

            # print self.connection.portstr
            # self.connection.write([0x31, 0x32,0x33,0x34,0x35])
            self.connection.write(buf_header[1:])


        except Exception as e:
            self.log.error(e, exc_info=True)

        try:
            buffer = []
            #            self.connection.flushInput()
            # time.sleep(0.04)
            # t = time.time()
            # while time.time() - t < timeout:
            response = self.connection.read(size)
            # self.log.error('%s', response)
            if no_response == True:
                try:
                    # raise KeyError(response)
                    return int(binascii.hexlify(response))
                except ValueError as e:
                    self.log.warning("wrong ardess or NACK")
                    return None
            #     else:
            #         # response += self.connection.read(size)
            #         if (self.checkResponse(response, size) is False):
            #             break
            #
            # if time.time() - t >= timeout:
            #     self.log.warning("sas timeout")
            #     # buffer.append(response)
            #     # print response))
            #     return None

            busy = False
            response = self.checkResponse(response)
            self.log.debug('sas response %s', response)
                # self.log.info('no sas response')
            return response
            # return None
        except Exception as e:
            self.log.error(e, exc_info=True)

        busy = False
        return None

def test_aft(types='in', mony=1, port='/dev/ttyS4'):
    sas = Sas(port)
    print(sas.start())
    print(sas.gaming_machine_ID())
    sas.transaction = sas.AFT_get_last_transaction()
    if types == 'in':
        print(sas.AFT_in(mony))
    elif types == 'out':
        print(sas.AFT_out())
    elif types == 'won':
        print(sas.AFT_won(mony))
    print(sas.AFT_clean_transaction_poll())

if __name__ == '__main__':
    sas = Sas('/dev/ttyS4')
    sas.mony_to_hex(10.00)
    print(sas.start())
    print(sas.gaming_machine_ID())
    sas.transaction = sas.AFT_get_last_transaction()
    print (sas.AFT_in(10, lock_timeout=10))
    # print(sas.AFT_clean_transaction_poll())
    # while True:
    #     print(sas.send_meters_10_15())
    #     print(sas.total_dollar_value_of_bills_meter())

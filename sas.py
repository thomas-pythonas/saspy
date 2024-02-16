#!/usr/bin/python
# -*- coding: utf8 -*-
import serial
import time
import binascii
import logging
import datetime

from PyCRC.CRC16Kermit import CRC16Kermit
from multiprocessing import log_to_stderr

from models import *
from error_handler import *

__author__ = "Zachary Tomlinson, Antonio D'Angelo"
__credits__ = ["Thomas Pythonas", "Grigor Kolev"]
__license__ = "MIT"
__version__ = "2.0.0"
__maintainer__ = "Zachary Tomlinson, Antonio D'Angelo"
__status__ = "Staging"


class Sas:
    """Main SAS Library Class"""

    def __init__(
        self,
        port,  # Serial Port full Address
        timeout=2,  # Connection timeout
        poll_address=0x82,  # Poll Address
        denom=0.01,  # Denomination
        asset_number="01000000",  # Asset Number
        reg_key="0000000000000000000000000000000000000000",  # Reg Key
        pos_id="B374A402",  # Pos ID
        key="44",  # Key
        debug_level="DEBUG",  # Debug Level
    ):
        # Let's address some internal var
        self.poll_timeout = timeout
        self.address = None
        self.machine_n = None
        self.aft_get_last_transaction = True
        self.denom = denom
        self.asset_number = asset_number
        self.reg_key = reg_key
        self.pos_id = pos_id
        self.transaction = None
        self.my_key = key
        self.poll_address = poll_address

        # Init the Logging system
        self.log = log_to_stderr()
        self.log.setLevel(logging.getLevelName(debug_level))

        # Open the serial connection
        while 1:
            try:
                self.connection = serial.Serial(
                    port=port,
                    baudrate=19200,
                    timeout=timeout,
                )
                self.close()
                self.timeout = timeout
                self.log.info("Connection Successful")
                break
            except:
                self.log.critical("Error while connecting to the machine....")
                time.sleep(1)

        return

    def is_open(self):
        return self.connection.is_open

    def flush(self):
        try:
            if not self.is_open():
                self.open()
            self.connection.flushOutput()
            self.connection.flushInput()
        except Exception as e:
            self.log.error(e, exc_info=True)

        self.close()

    def start(self):
        self.log.info("Connecting to the machine...")
        while True:
            if not self.is_open():
                try:
                    self.open()
                    if not self.is_open():
                        self.log.error("Port is NOT open")
                except SASOpenError:
                    self.log.critical("No SAS Port")
                except Exception as e:
                    self.log.critical(e, exc_info=True)
            else:
                self.connection.flushOutput()
                self.connection.flushInput()
                response = self.connection.read(1)

                if not response:
                    self.log.error("No SAS Connection")
                    time.sleep(1)

                if response != b"":
                    self.address = int(binascii.hexlify(response))
                    self.machine_n = response.hex()
                    self.log.info("Address Recognized " + str(self.address))
                    break
                else:
                    self.log.error("No SAS Connection")
                    time.sleep(1)

        self.close()
        return self.machine_n

    def close(self):
        self.connection.close()

    def open(self):
        try:
            if self.connection.isOpen() is not True:
                self.connection.open()
        except:
            raise SASOpenError

    def _conf_event_port(self):
        self.open()
        # time.sleep(0.04)
        self.connection.flush()
        self.connection.timeout = self.poll_timeout
        self.connection.parity = serial.PARITY_NONE
        self.connection.stopbits = serial.STOPBITS_TWO
        self.connection.flushInput()

    def _conf_port(self):
        self.open()
        # time.sleep(0.04)
        self.connection.flush()
        self.connection.timeout = self.timeout
        self.connection.parity = serial.PARITY_MARK
        self.connection.stopbits = serial.STOPBITS_ONE
        self.connection.flushInput()

    @staticmethod
    def _crc(response, chk=False, seed=0):
        # Old CRC method. Its work but is slowly.
        # --------------------------------------------------------------------------
        # Use  crc = CRC16Kermit().calculate(bytearray(buf_header).decode("utf-8"))
        #        buf_header.extend([((crc >> 8) & 0xFF), (crc & 0xFF)])
        # --------------------------------------------------------------------------
        c = ""
        if chk:
            crc = response[-4:]
            response = response[:-4]

        for x in response:
            c = c + x
            if len(c) == 2:
                q = (seed ^ int(c, 16)) & 0o17
                seed = (seed >> 4) ^ (q * 0o010201)
                q = (seed ^ (int(c, 16) >> 4)) & 0o17
                seed = (seed >> 4) ^ (q * 0o010201)
                c = ""
        data = hex(seed)
        tmp = []
        if len(data) == 5:
            data = data[0:2] + "0" + data[2:]
        elif len(data) == 4:
            data = data[0:2] + "00" + data[2:]
        elif len(data) == 3:
            data = data[0:2] + "000" + data[2:]
        elif len(data) == 2:
            data = data[0:2] + "0000"
        if not chk:
            data = data[4:] + data[2:-2]
        #            pass
        else:
            data = data[4:] + data[2:-2]
            if data == chk:
                return True
            else:
                raise BadCRC(response)

        return data

    def _send_command(
        self, command, no_response=False, timeout=None, crc_need=True, size=1
    ):
        try:
            buf_header = [self.address]
            self._conf_port()

            buf_header.extend(command)

            if crc_need:
                crc = CRC16Kermit().calculate(bytearray(buf_header).decode("utf-8"))
                buf_header.extend([((crc >> 8) & 0xFF), (crc & 0xFF)])

            self.connection.write([self.poll_address, self.address])
            # self.close()
            self.connection.flush()
            self.connection.parity = serial.PARITY_SPACE
            # self.open()

            self.connection.write((buf_header[1:]))

        except Exception as e:
            self.log.error(e, exc_info=True)

        try:
            response = self.connection.read(size)

            if no_response:
                try:
                    return int(binascii.hexlify(response))
                except ValueError as e:
                    self.log.critical("no sas response %s" % (str(buf_header[1:])))
                    return None

            response = self._check_response(response)

            self.log.debug("sas response %s", binascii.hexlify(response))

            return response

        except BadCRC as e:
            raise e

        except Exception as e:
            self.log.critical(e, exc_info=True)

        return None

    @staticmethod
    def _check_response(rsp):
        if rsp == "":
            raise NoSasConnection

        tmp_crc = binascii.hexlify(rsp[-2:])
        crc1 = CRC16Kermit().calculate(rsp[0:-2])
        crc1 = hex(crc1).zfill(4)
        crc1 = bytes(crc1, "utf-8")[2:]

        if tmp_crc != crc1:
            raise BadCRC(binascii.hexlify(rsp))
        else:
            return rsp[1:-2]

    def events_poll(self):
        self._conf_event_port()

        cmd = [0x80 + self.address]
        self.connection.write([self.poll_address])

        try:
            self.connection.write(cmd)
            event = self.connection.read(1)
            if event == "":
                raise NoSasConnection
            event = GPoll.GPoll.get_status(event.hex())
        except KeyError as e:
            raise EMGGpollBadResponse
        except Exception as e:
            raise e
        return event

    def shutdown(self):
        # [0x01]
        if self._send_command([0x01], True, crc_need=True) == self.address:
            return True

        return False

    def startup(self):
        # [0x02]
        if self._send_command([0x02], True, crc_need=True) == self.address:
            return True

        return False

    def sound_off(self):
        # [0x03]
        if self._send_command([0x03], True, crc_need=True) == self.address:
            return True

        return False

    def sound_on(self):
        # [0x04]
        if self._send_command([0x04], True, crc_need=True) == self.address:
            return True

        return False

    def reel_spin_game_sounds_disabled(self):
        # [0x05]
        if self._send_command([0x05], True, crc_need=True) == self.address:
            return True

        return False

    def enable_bill_acceptor(self):
        # [0x06]
        if self._send_command([0x06], True, crc_need=True) == self.address:
            return True

        return False

    def disable_bill_acceptor(self):
        # [0x07]
        if self._send_command([0x07], True, crc_need=True) == self.address:
            return True

        return False

    def configure_bill_denom(
        self, bill_denom=[0xFF, 0xFF, 0xFF], action_flag=[0xFF]
    ):
        cmd = [0x08, 0x00]
        cmd.extend(bill_denom)
        cmd.extend(action_flag)

        if self._send_command(cmd, True, crc_need=True) == self.address:
            return True

        return False

    def en_dis_game(self, game_number=None, en_dis=False):
        if not game_number:
            game_number = self.selected_game_number()

        game = int(str(game_number), 16)

        if en_dis:
            en_dis = [0]
        else:
            en_dis = [1]

        cmd = [0x09]

        cmd.extend([((game >> 8) & 0xFF), (game & 0xFF)])
        cmd.extend(bytearray(en_dis))

        if self._send_command(cmd, True, crc_need=True) == self.address:
            return True

        return False

    def enter_maintenance_mode(self):
        # [0x0A]
        if self._send_command([0x0A], True, crc_need=True) == self.address:
            return True

        return False

    def exit_maintenance_mode(self):
        # [0x0B]
        if self._send_command([0x0B], True, crc_need=True) == self.address:
            return True

        return False

    def en_dis_rt_event_reporting(self, enable=False):
        # 0E
        if not enable:
            enable = [0]
        else:
            enable = [1]

        cmd = [0x0E]
        cmd.extend(bytearray(enable))

        if self._send_command(cmd, True, crc_need=True) == self.address:
            return True

        return False

    def send_meters_10_15(self, denom=True):
        cmd = [0x0F]
        data = self._send_command(cmd, crc_need=False, size=28)
        if data:
            meters = {}
            if denom:
                Meters.Meters.STATUS_MAP["total_cancelled_credits_meter"] = round(
                    int((binascii.hexlify(bytearray(data[1:5])))) * self.denom, 2
                )
                Meters.Meters.STATUS_MAP["total_in_meter"] = round(
                    int(binascii.hexlify(bytearray(data[5:9]))) * self.denom, 2
                )
                Meters.Meters.STATUS_MAP["total_out_meter"] = round(
                    int(binascii.hexlify(bytearray(data[9:13]))) * self.denom, 2
                )
                Meters.Meters.STATUS_MAP["total_droup_meter"] = round(
                    int(binascii.hexlify(bytearray(data[13:17]))) * self.denom, 2
                )
                Meters.Meters.STATUS_MAP["total_jackpot_meter"] = round(
                    int(binascii.hexlify(bytearray(data[17:21]))) * self.denom, 2
                )
                Meters.Meters.STATUS_MAP["games_played_meter"] = int(
                    binascii.hexlify(bytearray(data[21:25]))
                )
            else:
                Meters.Meters.STATUS_MAP["total_cancelled_credits_meter"] = int(
                    (binascii.hexlify(bytearray(data[1:5])))
                )
                Meters.Meters.STATUS_MAP["total_in_meter"] = int(
                    binascii.hexlify(bytearray(data[5:9]))
                )
                Meters.Meters.STATUS_MAP["total_out_meter"] = int(
                    binascii.hexlify(bytearray(data[9:13]))
                )
                Meters.Meters.STATUS_MAP["total_droup_meter"] = int(
                    binascii.hexlify(bytearray(data[13:17]))
                )
                Meters.Meters.STATUS_MAP["total_jackpot_meter"] = int(
                    binascii.hexlify(bytearray(data[17:21]))
                )
                Meters.Meters.STATUS_MAP["games_played_meter"] = int(
                    binascii.hexlify(bytearray(data[21:25]))
                )

            return Meters.Meters.get_non_empty_status_map()

        return None

    def total_cancelled_credits(self, denom=True):
        # 10
        cmd = [0x10]
        data = self._send_command(cmd, crc_need=False, size=8)
        if data:
            if denom:
                return round(
                    int(binascii.hexlify(bytearray(data[1:5]))) * self.denom, 2
                )
            else:
                return int(binascii.hexlify(bytearray(data[1:5])))

        return None

    def total_bet_meter(self, denom=True):
        # 11
        cmd = [0x11]
        data = self._send_command(cmd, crc_need=False, size=8)
        if data:
            if denom:
                return round(
                    int(binascii.hexlify(bytearray(data[1:5]))) * self.denom, 2
                )
            else:
                return int(binascii.hexlify(bytearray(data[1:5])))

        return None

    def total_win_meter(self, denom=True):
        # 12
        cmd = [0x12]
        data = self._send_command(cmd, crc_need=False, size=8)
        if data:
            if denom:
                return round(
                    int(binascii.hexlify(bytearray(data[1:5]))) * self.denom, 2
                )
            else:
                return int(binascii.hexlify(bytearray(data[1:5])))

        return None

    def total_in_meter(self, denom=True):
        # 13
        cmd = [0x13]
        data = self._send_command(cmd, crc_need=False, size=8)
        if data:
            if denom:
                return round(
                    int(binascii.hexlify(bytearray(data[1:5]))) * self.denom, 2
                )
            else:
                return int(binascii.hexlify(bytearray(data[1:5])))

        return None

    def total_jackpot_meter(self, denom=True):
        # 14
        cmd = [0x14]
        data = self._send_command(cmd, crc_need=False, size=8)
        if data:
            if denom:
                return round(
                    int(binascii.hexlify(bytearray(data[1:5]))) * self.denom, 2
                )
            else:
                return int(binascii.hexlify(bytearray(data[1:5])))

        return None

    def games_played_meter(self):
        # 15
        cmd = [0x15]
        data = self._send_command(cmd, crc_need=False, size=8)
        if data:
            return int(binascii.hexlify(bytearray(data[1:5])))

        return None

    def games_won_meter(self, denom=True):
        # 16
        cmd = [0x16]
        data = self._send_command(cmd, crc_need=False, size=8)
        if data:
            if denom:
                return round(
                    int(binascii.hexlify(bytearray(data[1:5]))) * self.denom, 2
                )
            else:
                return int(binascii.hexlify(bytearray(data[1:5])))

        return None

    def games_lost_meter(self):
        # 17
        cmd = [0x17]
        data = self._send_command(cmd, crc_need=False, size=8)
        if data:
            return int(binascii.hexlify(bytearray(data[1:5])))

        return None

    def games_powerup_door_opened(self):
        # 18
        cmd = [0x18]
        data = self._send_command(cmd, crc_need=False, size=8)
        if data:
            Meters.Meters.STATUS_MAP["games_last_power_up"] = int(
                binascii.hexlify(bytearray(data[1:3]))
            )
            Meters.Meters.STATUS_MAP["games_last_slot_door_close"] = int(
                binascii.hexlify(bytearray(data[1:5]))
            )
            return Meters.Meters.get_non_empty_status_map()

        return None

    def meters_11_15(self, denom=True):
        # 19
        cmd = [0x19]
        data = self._send_command(cmd, crc_need=False, size=24)
        if data:
            if not denom:
                Meters.Meters.STATUS_MAP["total_bet_meter"] = int(
                    binascii.hexlify(bytearray(data[1:5]))
                )
                Meters.Meters.STATUS_MAP["total_win_meter"] = int(
                    binascii.hexlify(bytearray(data[5:9]))
                )
                Meters.Meters.STATUS_MAP["total_in_meter"] = int(
                    binascii.hexlify(bytearray(data[9:13]))
                )
                Meters.Meters.STATUS_MAP["total_jackpot_meter"] = int(
                    binascii.hexlify(bytearray(data[13:17]))
                )
                Meters.Meters.STATUS_MAP["games_played_meter"] = int(
                    binascii.hexlify(bytearray(data[17:21]))
                )
            else:
                Meters.Meters.STATUS_MAP["total_bet_meter"] = round(
                    int(binascii.hexlify(bytearray(data[1:5]))) * self.denom, 2
                )
                Meters.Meters.STATUS_MAP["total_win_meter"] = round(
                    int(binascii.hexlify(bytearray(data[5:9]))) * self.denom, 2
                )
                Meters.Meters.STATUS_MAP["total_in_meter"] = round(
                    int(binascii.hexlify(bytearray(data[9:13]))) * self.denom, 2
                )
                Meters.Meters.STATUS_MAP["total_jackpot_meter"] = round(
                    int(binascii.hexlify(bytearray(data[13:17]))) * self.denom, 2
                )
                Meters.Meters.STATUS_MAP["games_played_meter"] = int(
                    binascii.hexlify(bytearray(data[17:21]))
                )
            return Meters.Meters.get_non_empty_status_map()

        return None

    def current_credits(self, denom=True):
        # 1A
        cmd = [0x1A]
        data = self._send_command(cmd, crc_need=False, size=8)
        if data:
            if denom:
                return round(
                    int(binascii.hexlify(bytearray(data[1:5]))) * self.denom, 2
                )
            else:
                return int(binascii.hexlify(bytearray(data[1:5])))

        return None

    def handpay_info(self):
        # 1B
        cmd = [0x1B]
        data = self._send_command(cmd, crc_need=False)
        if data:
            Meters.Meters.STATUS_MAP["bin_progressive_group"] = int(
                binascii.hexlify(bytearray(data[1:2]))
            )
            Meters.Meters.STATUS_MAP["bin_level"] = int(
                binascii.hexlify(bytearray(data[2:3]))
            )
            Meters.Meters.STATUS_MAP["amount"] = int(
                binascii.hexlify(bytearray(data[3:8]))
            )
            Meters.Meters.STATUS_MAP["bin_reset_ID"] = int(
                binascii.hexlify(bytearray(data[8:]))
            )
            return Meters.Meters.get_non_empty_status_map()

        return None

    def meters(self, denom=True):
        # 1C
        cmd = [0x1C]
        data = self._send_command(cmd, crc_need=False, size=36)
        if data:
            if not denom:
                Meters.Meters.STATUS_MAP["total_bet_meter"] = int(
                    binascii.hexlify(bytearray(data[1:5]))
                )
                Meters.Meters.STATUS_MAP["total_win_meter"] = int(
                    binascii.hexlify(bytearray(data[5:9]))
                )
                Meters.Meters.STATUS_MAP["total_in_meter"] = int(
                    binascii.hexlify(bytearray(data[9:13]))
                )
                Meters.Meters.STATUS_MAP["total_jackpot_meter"] = int(
                    binascii.hexlify(bytearray(data[13:17]))
                )
                Meters.Meters.STATUS_MAP["games_played_meter"] = int(
                    binascii.hexlify(bytearray(data[17:21]))
                )
                Meters.Meters.STATUS_MAP["games_won_meter"] = int(
                    binascii.hexlify(bytearray(data[21:25]))
                )
                Meters.Meters.STATUS_MAP["slot_door_opened_meter"] = int(
                    binascii.hexlify(bytearray(data[25:29]))
                )
                Meters.Meters.STATUS_MAP["power_reset_meter"] = int(
                    binascii.hexlify(bytearray(data[29:33]))
                )
            else:
                Meters.Meters.STATUS_MAP["total_bet_meter"] = round(
                    int(binascii.hexlify(bytearray(data[1:5]))) * self.denom, 2
                )
                Meters.Meters.STATUS_MAP["total_win_meter"] = round(
                    int(binascii.hexlify(bytearray(data[5:9]))) * self.denom, 2
                )
                Meters.Meters.STATUS_MAP["total_in_meter"] = round(
                    int(binascii.hexlify(bytearray(data[9:13]))) * self.denom, 2
                )
                Meters.Meters.STATUS_MAP["total_jackpot_meter"] = round(
                    int(binascii.hexlify(bytearray(data[13:17]))) * self.denom, 2
                )
                Meters.Meters.STATUS_MAP["games_played_meter"] = int(
                    binascii.hexlify(bytearray(data[17:21]))
                )
                Meters.Meters.STATUS_MAP["games_won_meter"] = round(
                    int(binascii.hexlify(bytearray(data[21:25]))) * self.denom, 2
                )
                Meters.Meters.STATUS_MAP["slot_door_opened_meter"] = int(
                    binascii.hexlify(bytearray(data[25:29]))
                )
                Meters.Meters.STATUS_MAP["power_reset_meter"] = int(
                    binascii.hexlify(bytearray(data[29:33]))
                )

            return Meters.Meters.get_non_empty_status_map()

        return None

    def total_bill_meters(self):
        # 1E
        cmd = [0x1E]
        data = self._send_command(cmd, crc_need=False, size=28)
        if data:
            Meters.Meters.STATUS_MAP["s1_bills_accepted_meter"] = int(
                binascii.hexlify(bytearray(data[1:5]))
            )
            Meters.Meters.STATUS_MAP["s5_bills_accepted_meter"] = int(
                binascii.hexlify(bytearray(data[5:9]))
            )
            Meters.Meters.STATUS_MAP["s10_bills_accepted_meter"] = int(
                binascii.hexlify(bytearray(data[9:13]))
            )
            Meters.Meters.STATUS_MAP["s20_bills_accepted_meter"] = int(
                binascii.hexlify(bytearray(data[13:17]))
            )
            Meters.Meters.STATUS_MAP["s50_bills_accepted_meter"] = int(
                binascii.hexlify(bytearray(data[17:21]))
            )
            Meters.Meters.STATUS_MAP["s100_bills_accepted_meter"] = int(
                binascii.hexlify(bytearray(data[21:25]))
            )

            return Meters.Meters.get_non_empty_status_map()

        return None

    def gaming_machine_id(self):
        """
        @todo Check this one...something smell bad
        :return:
        """
        # 1F
        cmd = [0x1F]
        data = self._send_command(cmd, crc_need=False, size=24)
        if data is not None:
            denom = Denomination.Denomination.get_status(data[6:7].hex())
            self.log.info("Recognized " + str(denom))
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

    def total_dollar_value_of_bills_meter(self):
        # 20
        cmd = [0x20]
        data = self._send_command(cmd, crc_need=False, size=8)

        if data:
            return int(binascii.hexlify(bytearray(data[1:])))

        return None

    def rom_signature_verification(self):
        # 21
        cmd = [0x21, 0x00, 0x00]
        data = self._send_command(cmd, crc_need=True)
        if data:
            return int(binascii.hexlify(bytearray(data[1:3])))

        return None

    def eft_button_pressed(self, state=0):
        # 24
        cmd = [0x24, 0x03, state]
        data = self._send_command(cmd, crc_need=True)
        if data:
            return data

        return None

    def true_coin_in(self, denom=True):
        # 2A
        cmd = [0x2A]
        data = self._send_command(cmd, crc_need=False)
        if data:
            if not denom:
                return int(binascii.hexlify(bytearray(data[1:5])))
            else:
                return round(
                    int(binascii.hexlify(bytearray(data[1:5]))) * self.denom, 2
                )

        return None

    def true_coin_out(self, denom=True):
        # 2B
        cmd = [0x2B]
        data = self._send_command(cmd, crc_need=False)
        if data:
            if not denom:
                return int(binascii.hexlify(bytearray(data[1:5])))
            else:
                return round(
                    int(binascii.hexlify(bytearray(data[1:5]))) * self.denom, 2
                )

        return None

    def curr_hopper_level(self):
        # 2C
        cmd = [0x2C]
        data = self._send_command(cmd, crc_need=False)
        if data:
            return int(binascii.hexlify(bytearray(data[1:5])))

        return None

    def total_hand_paid_cancelled_credit(self):
        # 2D
        cmd = [0x2D]
        data = self._send_command(cmd, crc_need=False, size=8)
        if data:
            return int(binascii.hexlify(bytearray(data[1:5])))

        return None

    def delay_game(self, delay_time=100):
        # 2E
        delay_time = str(delay_time)
        delay_fmt = "" + ("0" * (4 - len(delay_time)) + delay_time)
        cmd = [0x2E]
        count = 0
        for i in range(len(delay_fmt) // 2):
            cmd.append(int(delay_fmt[count : count + 2], 16))
            count += 2
        if self._send_command(cmd, True, crc_need=True) == self.address:
            return True
        else:
            return False

    @staticmethod
    def selected_meters_for_game():
        # 2F
        # TODO: selected_meters_for_game
        return None

    def send_1_bills_in_meters(self):
        # 31
        cmd = [0x31]
        data = self._send_command(cmd, crc_need=False, size=8)
        if data:
            return int(binascii.hexlify(bytearray(data[1:5])))

        return None

    def send_2_bills_in_meters(self):
        # 32
        cmd = [0x32]
        data = self._send_command(cmd, crc_need=False, size=8)
        if data:
            return int(binascii.hexlify(bytearray(data[1:5])))

        return None

    def send_5_bills_in_meters(self):
        # 33
        cmd = [0x33]
        data = self._send_command(cmd, crc_need=False, size=8)
        if data:
            return int(binascii.hexlify(bytearray(data[1:5])))

        return None

    def send_10_bills_in_meters(self):
        # 34
        cmd = [0x34]
        data = self._send_command(cmd, crc_need=False, size=8)
        if data:
            return int(binascii.hexlify(bytearray(data[1:5])))

        return None

    def send_20_bills_in_meters(self):
        # 35
        cmd = [0x35]
        data = self._send_command(cmd, crc_need=False, size=8)
        if data:
            return int(binascii.hexlify(bytearray(data[1:5])))

        return None

    def send_50_bills_in_meters(self):
        # 36
        cmd = [0x36]
        data = self._send_command(cmd, crc_need=False, size=8)
        if data:
            return int(binascii.hexlify(bytearray(data[1:5])))

        return None

    def send_100_bills_in_meters(self):
        # 37
        cmd = [0x37]
        data = self._send_command(cmd, crc_need=False, size=8)
        if data:
            return int(binascii.hexlify(bytearray(data[1:5])))

        return None

    def send_500_bills_in_meters(self):
        # 38
        cmd = [0x38]
        data = self._send_command(cmd, crc_need=False, size=8)
        if data:
            return int(binascii.hexlify(bytearray(data[1:5])))

        return None

    def send_1000_bills_in_meters(self):
        # 39
        cmd = [0x39]
        data = self._send_command(cmd, crc_need=False, size=8)
        if data:
            return int(binascii.hexlify(bytearray(data[1:5])))

        return None

    def send_200_bills_in_meters(self):
        # 3A
        cmd = [0x3A]
        data = self._send_command(cmd, crc_need=False, size=8)
        if data:
            return int(binascii.hexlify(bytearray(data[1:5])))

        return None

    def send_25_bills_in_meters(self):
        # 3B
        cmd = [0x3B]
        data = self._send_command(cmd, crc_need=False, size=8)
        if data:
            return int(binascii.hexlify(bytearray(data[1:5])))

        return None

    def send_2000_bills_in_meters(self):
        # 3C
        cmd = [0x3C]
        data = self._send_command(cmd, crc_need=False, size=8)
        if data:
            return int(binascii.hexlify(bytearray(data[1:5])))
        return None

    def cash_out_ticket_info(self):
        # 3D
        cmd = [0x3D]
        data = self._send_command(cmd, crc_need=False)
        if data:
            return {
                "cashout_ticket_number": int(binascii.hexlify(bytearray(data[1:3]))),
                "cashout_amount_in_cents": int(binascii.hexlify(bytearray(data[3:]))),
            }

        return None

    def send_2500_bills_in_meters(self):
        # 3E
        cmd = [0x3E]
        data = self._send_command(cmd, crc_need=False, size=8)
        if data:
            return int(binascii.hexlify(bytearray(data[1:5])))

        return None

    def send_5000_bills_in_meters(self):
        # 3F
        cmd = [0x3F]
        data = self._send_command(cmd, crc_need=False, size=8)
        if data:
            return int(binascii.hexlify(bytearray(data[1:5])))

        return None

    def send_10000_bills_in_meters(self):
        # 40
        cmd = [0x40]
        data = self._send_command(cmd, crc_need=False, size=8)
        if data:
            return int(binascii.hexlify(bytearray(data[1:5])))

        return None

    def send_20000_bills_in_meters(self):
        # 41
        cmd = [0x41]
        data = self._send_command(cmd, crc_need=False, size=8)
        if data:
            return int(binascii.hexlify(bytearray(data[1:5])))

        return None

    def send_25000_bills_in_meters(self):
        # 42
        cmd = [0x42]
        data = self._send_command(cmd, crc_need=False, size=8)
        if data:
            return int(binascii.hexlify(bytearray(data[1:5])))

        return None

    def send_50000_bills_in_meters(self):
        # 43
        cmd = [0x43]
        data = self._send_command(cmd, crc_need=False, size=8)
        if data:
            return int(binascii.hexlify(bytearray(data[1:5])))

        return None

    def send_100000_bills_in_meters(self):
        # 44
        cmd = [0x44]
        data = self._send_command(cmd, crc_need=False, size=8)
        if data:
            return int(binascii.hexlify(bytearray(data[1:5])))

        return None

    def send_250_bills_in_meters(self):
        # 45
        cmd = [0x45]
        data = self._send_command(cmd, crc_need=False, size=8)
        if data:
            return int(binascii.hexlify(bytearray(data[1:5])))

        return None

    def credit_amount_of_all_bills_accepted(self):
        # 46
        cmd = [0x46]
        data = self._send_command(cmd, crc_need=False, size=8)
        if data:
            return int(binascii.hexlify(bytearray(data[1:5])))

        return None

    def coin_amount_accepted_from_external_coin_acceptor(self):
        # 47
        cmd = [0x47]
        data = self._send_command(cmd, crc_need=False, size=8)
        if data:
            return int(binascii.hexlify(bytearray(data[1:5])))

        return None

    def last_accepted_bill_info(self):
        # 48
        cmd = [0x48]
        data = self._send_command(cmd, crc_need=False)
        if data:
            Meters.Meters.STATUS_MAP["country_code"] = int(
                binascii.hexlify(bytearray(data[1:2]))
            )
            Meters.Meters.STATUS_MAP["bill_denomination"] = int(
                binascii.hexlify(bytearray(data[2:3]))
            )
            Meters.Meters.STATUS_MAP["meter_for_accepted_bills"] = int(
                binascii.hexlify(bytearray(data[3:6]))
            )
            return Meters.Meters.get_non_empty_status_map()

        return None

    def number_of_bills_currently_in_stacker(self):
        # 49
        cmd = [0x49]
        data = self._send_command(cmd, crc_need=False, size=8)
        if data:
            return int(binascii.hexlify(bytearray(data[1:5])))

        return None

    def total_credit_amount_of_all_bills_in_stacker(self):
        # 4A
        cmd = [0x49]
        data = self._send_command(cmd, crc_need=False, size=8)
        if data:
            return int(binascii.hexlify(bytearray(data[1:5])))

        return None

    def set_secure_enhanced_validation_id(
        self, machine_id=[0x01, 0x01, 0x01], seq_num=[0x00, 0x00, 0x01]
    ):
        """
        For a gaming machine to perform secure enhanced ticket/receipt/handpay validation, the host must use
        the type S long poll. The host may also use this long poll to retrieve the current gaming
        machine validation ID and validation sequence number by issuing the 4C command with a gaming
        machine validation ID of zero. If a gaming machine is not configured to perform secure enhanced
        validation, or is responding to a host that is not the validation controller, it ignores this long poll

        :param machine_id:
        :param seq_num:
        :param kwargs:
        :return:
        """
        # 4C
        # FIXME: set_secure_enhanced_validation_ID
        cmd = [0x4C, machine_id, seq_num]
        data = self._send_command(cmd, True, crc_need=True)
        if data:
            TitoStatement.Tito.STATUS_MAP["machine_ID"] = int(
                binascii.hexlify(bytearray(data[1:4]))
            )
            TitoStatement.Tito.STATUS_MAP["sequence_number"] = int(
                binascii.hexlify(bytearray(data[4:8]))
            )
            return data

        return None

    def enhanced_validation_information(self, curr_validation_info=0):
        # 4D
        # FIXME: enhanced_validation_information
        cmd = [0x4D, curr_validation_info]
        data = self._send_command(cmd, True, crc_need=True)
        if data:
            TitoStatement.Tito.STATUS_MAP["validation_type"] = int(
                binascii.hexlify(bytearray(data[1:2]))
            )
            TitoStatement.Tito.STATUS_MAP["index_number"] = int(
                binascii.hexlify(bytearray(data[2:3]))
            )
            TitoStatement.Tito.STATUS_MAP["date_validation_operation"] = str(
                binascii.hexlify(bytearray(data[3:7]))
            )
            TitoStatement.Tito.STATUS_MAP["time_validation_operation"] = str(
                binascii.hexlify(bytearray(data[7:10]))
            )
            TitoStatement.Tito.STATUS_MAP["validation_number"] = str(
                binascii.hexlify(bytearray(data[10:18]))
            )
            TitoStatement.Tito.STATUS_MAP["ticket_amount"] = int(
                binascii.hexlify(bytearray(data[18:23]))
            )
            TitoStatement.Tito.STATUS_MAP["ticket_number"] = int(
                binascii.hexlify(bytearray(data[23:25]))
            )
            TitoStatement.Tito.STATUS_MAP["validation_system_ID"] = int(
                binascii.hexlify(bytearray(data[25:26]))
            )
            TitoStatement.Tito.STATUS_MAP["expiration_date_printed_on_ticket"] = str(
                binascii.hexlify(bytearray(data[26:30]))
            )
            TitoStatement.Tito.STATUS_MAP["pool_id"] = int(
                binascii.hexlify(bytearray(data[30:32]))
            )

            return TitoStatement.Tito.get_non_empty_status_map()

        return None

    def current_hopper_status(self):
        # 4F
        # FIXME: current_hopper_status
        cmd = [0x4F]
        data = self._send_command(cmd, True, crc_need=False)
        if data:
            Meters.Meters.STATUS_MAP["current_hopper_lenght"] = int(
                binascii.hexlify(bytearray(data[1:2]))
            )
            Meters.Meters.STATUS_MAP["current_hopper_ststus"] = int(
                binascii.hexlify(bytearray(data[2:3]))
            )
            Meters.Meters.STATUS_MAP["current_hopper_percent_full"] = int(
                binascii.hexlify(bytearray(data[3:4]))
            )
            Meters.Meters.STATUS_MAP["current_hopper_level"] = int(
                binascii.hexlify(bytearray(data[4:]))
            )
            return Meters.Meters.get_non_empty_status_map()

        return None

    def validation_meters(self, type_of_validation=0x00):
        # 50
        # FIXME: validation_meters
        cmd = [0x50, type_of_validation]
        data = self._send_command(cmd, True, crc_need=True)
        if data:
            Meters.Meters.STATUS_MAP["bin_validation_type"] = int(
                binascii.hexlify(bytearray(data[1]))
            )
            Meters.Meters.STATUS_MAP["total_validations"] = int(
                binascii.hexlify(bytearray(data[2:6]))
            )
            Meters.Meters.STATUS_MAP["cumulative_amount"] = str(
                binascii.hexlify(bytearray(data[6:]))
            )
            return Meters.Meters.get_non_empty_status_map()

        return None

    def total_number_of_games_implemented(self):
        # 51
        cmd = [0x51]
        # FIXME: cmd.extend(type_of_validation)
        data = self._send_command(cmd, crc_need=False, size=6)
        if data:
            return str(binascii.hexlify(bytearray(data[1:])))

        return None

    def game_meters(self, n=None, denom=True):
        # 52
        cmd = [0x52]

        if not n:
            n = self.selected_game_number(in_hex=False)
        cmd.extend([((n >> 8) & 0xFF), (n & 0xFF)])

        data = self._send_command(cmd, crc_need=True, size=22)
        if data:
            meters = {}
            if not denom:
                Meters.Meters.STATUS_MAP["game_n_number"] = str(
                    binascii.hexlify(bytearray(data[1:3]))
                )
                Meters.Meters.STATUS_MAP["game_n_coin_in_meter"] = int(
                    binascii.hexlify(bytearray(data[3:7]))
                )
                Meters.Meters.STATUS_MAP["game_n_coin_out_meter"] = int(
                    binascii.hexlify(bytearray(data[7:11]))
                )
                Meters.Meters.STATUS_MAP["game_n_jackpot_meter"] = int(
                    binascii.hexlify(bytearray(data[11:15]))
                )
                Meters.Meters.STATUS_MAP["geme_n_games_played_meter"] = int(
                    binascii.hexlify(bytearray(data[15:]))
                )
            else:
                Meters.Meters.STATUS_MAP["game_n_number"] = str(
                    binascii.hexlify(bytearray(data[1:3]))
                )
                Meters.Meters.STATUS_MAP["game_n_coin_in_meter"] = round(
                    int(binascii.hexlify(bytearray(data[3:7]))) * self.denom, 2
                )
                Meters.Meters.STATUS_MAP["game_n_coin_out_meter"] = round(
                    int(binascii.hexlify(bytearray(data[7:11]))) * self.denom, 2
                )
                Meters.Meters.STATUS_MAP["game_n_jackpot_meter"] = round(
                    int(binascii.hexlify(bytearray(data[11:15]))) * self.denom, 2
                )
                Meters.Meters.STATUS_MAP["geme_n_games_played_meter"] = int(
                    binascii.hexlify(bytearray(data[15:]))
                )

            return Meters.Meters.get_non_empty_status_map()

        return None

    def game_configuration(self, n=None):
        # 53
        cmd = [0x53]
        # FIXME: game_configuration

        if not n:
            n = self.selected_game_number(in_hex=False)
        cmd.extend([(n & 0xFF), ((n >> 8) & 0xFF)])

        data = self._send_command(cmd, True, crc_need=True)
        if data:
            Meters.Meters.STATUS_MAP["game_n_number_config"] = int(
                binascii.hexlify(bytearray(data[1:3]))
            )
            Meters.Meters.STATUS_MAP["game_n_ASCII_game_ID"] = str(
                binascii.hexlify(bytearray(data[3:5]))
            )
            Meters.Meters.STATUS_MAP["game_n_ASCII_additional_id"] = str(
                binascii.hexlify(bytearray(data[5:7]))
            )
            Meters.Meters.STATUS_MAP["game_n_bin_denomination"] = str(
                binascii.hexlify(bytearray(data[7]))
            )
            Meters.Meters.STATUS_MAP["game_n_bin_progressive_group"] = str(
                binascii.hexlify(bytearray(data[8]))
            )
            Meters.Meters.STATUS_MAP["game_n_bin_game_options"] = str(
                binascii.hexlify(bytearray(data[9:11]))
            )
            Meters.Meters.STATUS_MAP["game_n_ASCII_paytable_ID"] = str(
                binascii.hexlify(bytearray(data[11:17]))
            )
            Meters.Meters.STATUS_MAP["game_n_ASCII_base_percentage"] = str(
                binascii.hexlify(bytearray(data[17:]))
            )
            return Meters.Meters.get_non_empty_status_map()

        return None

    def sas_version_gaming_machine_serial_id(self):
        # 54
        """
        This function should be checked at begin in order to address
        the changes from sas v6.02 and 6.03
        - Antonio
        """
        cmd = [0x54, 0x00]
        data = self._send_command(cmd, crc_need=False, size=20)
        if data:
            Meters.Meters.STATUS_MAP["ASCII_SAS_version"] = (
                int(binascii.hexlify(bytearray(data[2:5]))) * 0.01
            )
            Meters.Meters.STATUS_MAP["ASCII_serial_number"] = str(bytearray(data[5:]))
            return Meters.Meters.get_non_empty_status_map()

        return None

    def selected_game_number(self, in_hex=True):
        # 55
        cmd = [0x55]
        data = self._send_command(cmd, crc_need=False, size=6)
        if data:
            if not in_hex:
                return int(binascii.hexlify(bytearray(data[1:])))
            else:
                return binascii.hexlify(bytearray(data[1:]))

        return None

    def enabled_game_numbers(self):
        # 56
        cmd = [0x56]
        data = self._send_command(cmd, crc_need=False)
        if data:
            Meters.Meters.STATUS_MAP["number_of_enabled_games"] = int(
                binascii.hexlify(bytearray(data[2]))
            )
            Meters.Meters.STATUS_MAP["enabled_games_numbers"] = int(
                binascii.hexlify(bytearray(data[3:]))
            )
            return Meters.Meters.get_non_empty_status_map()

        return None

    def pending_cashout_info(self):
        # 57
        cmd = [0x57]
        data = self._send_command(cmd, crc_need=False)
        if data:
            TitoStatement.Tito.STATUS_MAP["cashout_type"] = int(
                binascii.hexlify(bytearray(data[1:2]))
            )
            TitoStatement.Tito.STATUS_MAP["cashout_amount"] = str(
                binascii.hexlify(bytearray(data[2:]))
            )
            return TitoStatement.Tito.get_non_empty_status_map()

        return None

    def validation_number(self, validation_id=1, valid_number=0):
        # 58
        cmd = [0x58, validation_id, self._bcd_coder_array(valid_number, 8)]
        data = self._send_command(cmd, crc_need=True)
        if data:
            return str(binascii.hexlify(bytearray(data[1])))

        return None

    """
    def eft_send_promo_to_machine(self, amount=0, count=1, status=0, **kwargs):
        # 63
        # FIXME: eft_send_promo_to_machine
        cmd = [0x63, count, status, self._bcd_coder_array(amount, 4)]
        # status 0-init 1-end
        data = self._send_command(cmd, crc_need=True)
        if data:
            EftStatement.eft_status = str(
                binascii.hexlify(bytearray(data[1:]))
            )
            EftStatement.promo_amount = str(
                binascii.hexlify(bytearray(data[4:]))
            )
            # eft_statement['eft_transfer_counter']=int(binascii.hexlify(bytearray(data[3:4])))
            return EftStatement

        return None

    def eft_load_cashable_credits(self, amount=0, count=1, status=0, **kwargs):
        # 69
        # FIXME: eft_load_cashable_credits
        cmd = [0x69, count, status, self._bcd_coder_array(amount, 4)]
        data = self._send_command(cmd, True, crc_need=True)
        if data:
            meters["eft_status"] = str(binascii.hexlify(bytearray(data[1:2])))
            meters["cashable_amount"] = str(binascii.hexlify(bytearray(data[2:5])))
            return data[3]

        return None

    def eft_available_transfers(self, **kwargs):
        # 6A
        # FIXME: eft_load_cashable_credits
        cmd = [0x6A]
        data = self._send_command(cmd, True, crc_need=False)
        if data:
            # meters['number_bills_in_stacker']=int(binascii.hexlify(bytearray(data[1:5])))
            return data

        return None
    """

    def authentication_info(
        self,
        action=0,
        addressing_mode=0,
        component_name="",
        auth_method=b"\x00\x00\x00\x00",
        seed="",
        seed_length=0,
        offset="",
        offset_length=0,
    ):
        # 6E
        # FIXME: authentication_info
        cmd = [0x6E, 0x00, action]
        if action == 0:
            cmd[1] = 1
        else:
            if action == 1 or action == 3:
                cmd.append(addressing_mode)
                cmd.append(len(bytearray(component_name)))
                cmd.append(bytearray(component_name))
                cmd[1] = len(bytearray(component_name)) + 3
            else:
                if action == 2:
                    cmd.append(addressing_mode)
                    cmd.append(len(bytearray(component_name)))
                    cmd.append(bytearray(component_name))
                    cmd.append(auth_method)
                    cmd.append(seed_length)
                    cmd.append(bytearray(seed))
                    cmd.append(offset_length)
                    cmd.append(bytearray(offset))

                    cmd[1] = (
                        len(bytearray(offset))
                        + len(bytearray(seed))
                        + len(bytearray(component_name))
                        + 6
                    )

        data = self._send_command(cmd, True, crc_need=True)
        if data:
            return data[1]

        return None

    @staticmethod
    def extended_meters_for_game():
        # TODO: extended_meters_for_game
        # 6F
        return None

    def ticket_validation_data(self):
        # 70
        # FIXME: ticket_validation_data
        cmd = [0x70]
        data = self._send_command(cmd, True, crc_need=False)
        if data:
            Meters.Meters.STATUS_MAP["ticket_status"] = int(
                binascii.hexlify(bytearray(data[2:3]))
            )
            Meters.Meters.STATUS_MAP["ticket_amount"] = str(
                binascii.hexlify(bytearray(data[3:8]))
            )
            Meters.Meters.STATUS_MAP["parsing_code"] = int(
                binascii.hexlify(bytearray(data[8:9]))
            )
            Meters.Meters.STATUS_MAP["validation_data"] = str(
                binascii.hexlify(bytearray(data[9:]))
            )
            return Meters.Meters.get_non_empty_status_map()

        return None

    def redeem_ticket(
        self,
        transfer_code=0,
        transfer_amount=0,
        parsing_code=0,
        validation_data=0,
        restricted_expiration=0,
        pool_id=0
    ):
        # 71
        # FIXME: redeem_ticket
        cmd = [
            0x71,
            0x21,
            transfer_code,
            self._bcd_coder_array(transfer_amount, 5),
            parsing_code,
            self._bcd_coder_array(validation_data, 8),
            self._bcd_coder_array(restricted_expiration, 4),
            self._bcd_coder_array(pool_id, 2),
        ]
        data = self._send_command(cmd, True, crc_need=True)
        if data:
            Meters.Meters.STATUS_MAP["ticket_status"] = int(
                binascii.hexlify(bytearray(data[2:3]))
            )
            Meters.Meters.STATUS_MAP["ticket_amount"] = int(
                binascii.hexlify(bytearray(data[3:8]))
            )
            Meters.Meters.STATUS_MAP["parsing_code"] = int(
                binascii.hexlify(bytearray(data[8:9]))
            )
            Meters.Meters.STATUS_MAP["validation_data"] = str(
                binascii.hexlify(bytearray(data[9:]))
            )
            return Meters.Meters.get_non_empty_status_map()

        return None

    def aft_jp(self, money, amount=1, lock_timeout=0, games=None):
        # FIXME: make logically coherent
        # self.lock_emg(lock_time=500, condition=1)
        money_1 = money_2 = money_3 = "0000000000"
        if self.denom > 0.01:
            return None

        if not games:
            for i in range(3):
                games = self.selected_game_number(in_hex=False)
                if not games:
                    time.sleep(0.04)
                else:
                    break

        if not games or games == 0 or games < 1:
            return "NoGame"

        if not money:
            money = str(self.current_credits(denom=False))
        else:
            money = str(int((money / self.denom)))
            money = money.replace(".", "")

        money = "0" * (10 - len(money)) + money

        match amount:
            case 1:
                money_1 = money
            case 2:
                money_2 = money
            case 3:
                money_3 = money
            case _:
                raise AFTBadAmount

        last_transaction = self.aft_format_transaction()
        len_transaction_id = hex(len(last_transaction) // 2)[
            2:
        ]  # the division result should be converted to an integer before using hex, added extra / to solve this
        if len(len_transaction_id) < 2:
            len_transaction_id = "0" + len_transaction_id
        elif len(len_transaction_id) % 2 == 1:
            len_transaction_id = "0" + len_transaction_id

        cmd = """72{my_key}{index}00{transfer_code}{money_1}{money_2}{money_3}
                 00{asset}{key}{len_transaction}{transaction}{times}0C0000""".format(
            transfer_code="11",
            index="00",
            money_1=money_1,
            money_2=money_2,
            money_3=money_3,
            asset=self.asset_number,
            key=self.reg_key,
            len_transaction=len_transaction_id,
            transaction=last_transaction,
            times=datetime.datetime.strftime(datetime.datetime.now(), "%m%d%Y"),
            my_key=self.my_key,
        )

        new_cmd = []
        count = 0
        for i in range(
            len(cmd) // 2
        ):  # Python3...not my fault...might be better using range(0, len(cmd), 2) ?
            new_cmd.append(int(cmd[count : count + 2], 16))
            count += 2

        response = None
        self.aft_register()
        if lock_timeout > 0:
            self.aft_game_lock(lock_timeout, condition=1)

        data = self._send_command(new_cmd, crc_need=True, size=82)

        if data:
            a = int(binascii.hexlify(bytearray(data[26:27])), 16)
            response = {
                "Length": int(binascii.hexlify(bytearray(data[26:27])), 16),
                "Transaction buffer position": int(
                    binascii.hexlify(bytearray(data[2:3]))
                ),
                "Transfer status": AftTransferStatus.AftTransferStatus.get_status(
                    binascii.hexlify(bytearray(data[3:4]))
                ),
                "Receipt status": AftTransferStatus.AftTransferStatus.get_status(
                    binascii.hexlify(bytearray(data[4:5]))
                ),
                "Transfer type": AftTransferStatus.AftTransferStatus.get_status(
                    binascii.hexlify(bytearray(data[5:6]))
                ),
                "Cashable amount": int(binascii.hexlify(bytearray(data[6:11])))
                * self.denom,
                "Restricted amount": int(binascii.hexlify(bytearray(data[11:16])))
                * self.denom,
                "Nonrestricted amount": int(binascii.hexlify(bytearray(data[16:21])))
                * self.denom,
                "Transfer flags": binascii.hexlify(bytearray(data[21:22])),
                "Asset number": binascii.hexlify(bytearray(data[22:26])),
                "Transaction ID length": binascii.hexlify(bytearray(data[26:27])),
                "Transaction ID": binascii.hexlify(
                    bytearray(data[27 : (27 + a)])
                ),  # WARNING: technically should be (27 + 2 * a) due to an off error....
            }
        try:
            self.aft_unregister()
        except:
            self.log.warning("AFT UNREGISTER ERROR: won to host")

        return response

    def aft_out(self, money=None, amount=1, lock_timeout=0):
        """
        aft_out is a function to make a machine cashout (effectively removes the credit in the machine)
        :param money:
        :param amount:
        :param lock_timeout:
        :param kwargs:
        :return:
        """
        # self.lock_emg(lock_time=500, condition=1)
        money_1 = money_2 = money_3 = "0000000000"
        if self.denom > 0.01:
            return None

        if not money:
            money = str(self.current_credits(denom=False))
        else:
            money = str(int((money / self.denom))).replace(".", "")

        money = "0" * (10 - len(money)) + money

        match amount:
            case 1:
                money_1 = money
            case 2:
                money_2 = money
            case 3:
                money_3 = money
            case _:
                raise AFTBadAmount

        last_transaction = self.aft_format_transaction()
        len_transaction_id = hex(len(last_transaction) // 2)[2:]
        if len(len_transaction_id) < 2:
            len_transaction_id = "0" + len_transaction_id
        elif len(len_transaction_id) % 2 == 1:
            len_transaction_id = "0" + len_transaction_id

        cmd = """72{my_key}{index}00{transfer_code}{money_1}{money_2}{money_3}
                 00{asset}{key}{len_transaction}{transaction}{times}0C0000""".format(
            transfer_code="80",
            index="00",
            money_1=money_1,
            money_2=money_2,
            money_3=money_3,
            asset=self.asset_number,
            key=self.reg_key,
            len_transaction=len_transaction_id,
            transaction=last_transaction,
            times=datetime.datetime.strftime(datetime.datetime.now(), "%m%d%Y"),
            my_key=self.my_key,
        )

        new_cmd = []
        count = 0
        for i in range(len(cmd) // 2):
            new_cmd.append(int(cmd[count : count + 2], 16))
            count += 2

        response = None
        self.aft_register()
        if lock_timeout > 0:
            self.aft_game_lock(lock_timeout, condition=1)
        try:
            data = self._send_command(new_cmd, crc_need=True, size=82)
            if data:
                a = int(binascii.hexlify(bytearray(data[26:27])), 16)
                response = {
                    "Length": int(binascii.hexlify(bytearray(data[26:27])), 16),
                    "Transaction buffer position": int(
                        binascii.hexlify(bytearray(data[2:3]))
                    ),
                    "Transfer status": AftTransferStatus.AftTransferStatus.get_status(
                        binascii.hexlify(bytearray(data[3:4]))
                    ),
                    "Receipt status": AftTransferStatus.AftTransferStatus.get_status(
                        binascii.hexlify(bytearray(data[4:5]))
                    ),
                    "Transfer type": AftTransferStatus.AftTransferStatus.get_status(
                        binascii.hexlify(bytearray(data[5:6]))
                    ),
                    "Cashable amount": int(binascii.hexlify(bytearray(data[6:11])))
                    * self.denom,
                    "Restricted amount": int(binascii.hexlify(bytearray(data[11:16])))
                    * self.denom,
                    "Nonrestricted amount": int(
                        binascii.hexlify(bytearray(data[16:21]))
                    )
                    * self.denom,
                    "Transfer flags": binascii.hexlify(bytearray(data[21:22])),
                    "Asset number": binascii.hexlify(bytearray(data[22:26])),
                    "Transaction ID length": binascii.hexlify(bytearray(data[26:27])),
                    "Transaction ID": binascii.hexlify(bytearray(data[27 : (27 + a)])),
                }
        except Exception as e:
            self.log.error(e, exc_info=True)

        self.aft_unregister()

        return response

    def aft_cashout_enable(self, amount=1, money="0000000000"):
        money_1 = money_2 = money_3 = "0000000000"

        match amount:
            case 1:
                money_1 = money
            case 2:
                money_2 = money
            case 3:
                money_3 = money
            case _:
                raise AFTBadAmount

        last_transaction = self.aft_format_transaction()
        len_transaction_id = hex(len(last_transaction) // 2)[2:]
        if len(len_transaction_id) < 2:
            len_transaction_id = "0" + len_transaction_id
        elif len(len_transaction_id) % 2 == 1:
            len_transaction_id = "0" + len_transaction_id

        cmd = """72{my_key}00{index}{transfer_code}{money_1}{money_2}{money_3}
                 02{asset}{key}{len_transaction}{transaction}{times}0C0000""".format(
            transfer_code="80",
            index="00",
            money_1=money_1,
            money_2=money_2,
            money_3=money_3,
            asset=self.asset_number,
            key=self.reg_key,
            len_transaction=len_transaction_id,
            transaction=last_transaction,
            times=datetime.datetime.strftime(datetime.datetime.now(), "%m%d%Y"),
            my_key=self.my_key,
        )

        new_cmd = []
        count = 0
        for i in range(len(cmd) // 2):
            new_cmd.append(int(cmd[count : count + 2], 16))
            count += 2

        self.aft_register()

        response = None
        try:
            data = self._send_command(new_cmd, crc_need=True, size=82)
            if data:
                a = int(binascii.hexlify(bytearray(data[26:27])), 16)
                response = {
                    "Length": int(binascii.hexlify(bytearray(data[26:27])), 16),
                    "Transaction buffer position": int(
                        binascii.hexlify(bytearray(data[2:3]))
                    ),
                    "Transfer status": AftTransferStatus.AftTransferStatus.get_status(
                        binascii.hexlify(bytearray(data[3:4]))
                    ),
                    "Receipt status": AftTransferStatus.AftTransferStatus.get_status(
                        binascii.hexlify(bytearray(data[4:5]))
                    ),
                    "Transfer type": AftTransferStatus.AftTransferStatus.get_status(
                        binascii.hexlify(bytearray(data[5:6]))
                    ),
                    "Cashable amount": int(binascii.hexlify(bytearray(data[6:11])))
                    * self.denom,
                    "Restricted amount": int(binascii.hexlify(bytearray(data[11:16])))
                    * self.denom,
                    "Nonrestricted amount": int(
                        binascii.hexlify(bytearray(data[16:21]))
                    )
                    * self.denom,
                    "Transfer flags": binascii.hexlify(bytearray(data[21:22])),
                    "Asset number": binascii.hexlify(bytearray(data[22:26])),
                    "Transaction ID length": binascii.hexlify(bytearray(data[26:27])),
                    "Transaction ID": binascii.hexlify(bytearray(data[27 : (27 + a)])),
                }
        except Exception as e:
            self.log.critical(e, exc_info=True)

        self.aft_unregister()
        try:
            self.aft_clean_transaction_poll()
        except:
            self.log.critical("Triggered unknown exception in aft_cashout_enable")
            return False

        return True

    def aft_won(
        self, money="0000000000", amount=1, games=None, lock_timeout=0
    ):
        money_1 = money_2 = money_3 = "0000000000"
        if self.denom > 0.01:
            return None

        if not games:
            for i in range(3):
                try:
                    games = self.selected_game_number(in_hex=False)
                except:
                    time.sleep(0.04)
                else:
                    break

        if not games or games < 1:
            return "NoGame"

        money = str(int(money / self.denom)).replace(".", "")
        money = "0" * (10 - len(money)) + money

        match amount:
            case 1:
                money_1 = money
            case 2:
                money_2 = money
            case 3:
                money_3 = money
            case _:
                raise AFTBadAmount

        last_transaction = self.aft_format_transaction()
        len_transaction_id = hex(len(last_transaction) // 2)[2:]
        if len(len_transaction_id) < 2:
            len_transaction_id = "0" + len_transaction_id
        elif len(len_transaction_id) % 2 == 1:
            len_transaction_id = "0" + len_transaction_id

        cmd = """72{my_key}{transfer_code}{index}{money_1}{money_2}{money_3}"
               "00{asset}{key}{len_transaction}{transaction}{times}0C0000""".format(
            transfer_code="0000",
            index="10",
            money_1=money_1,
            money_2=money_2,
            money_3=money_3,
            asset=self.asset_number,
            key=self.reg_key,
            len_transaction=len_transaction_id,
            transaction=last_transaction,
            times=datetime.datetime.strftime(datetime.datetime.now(), "%m%d%Y"),
            my_key=self.my_key,
        )

        new_cmd = []
        count = 0
        for i in range(len(cmd) // 2):
            new_cmd.append(int(cmd[count : count + 2], 16))
            count += 2

        response = None
        self.aft_register()
        if lock_timeout > 0:
            self.aft_game_lock(lock_timeout, condition=3)
        try:
            data = self._send_command(new_cmd, crc_need=True, size=82)
            if data:
                a = int(binascii.hexlify(bytearray(data[26:27])), 16)
                response = {
                    "Length": int(binascii.hexlify(bytearray(data[26:27])), 16),
                    "Transaction buffer position": int(
                        binascii.hexlify(bytearray(data[2:3]))
                    ),
                    "Transfer status": AftTransferStatus.AftTransferStatus.get_status(
                        binascii.hexlify(bytearray(data[3:4]))
                    ),
                    "Receipt status": AftTransferStatus.AftTransferStatus.get_status(
                        binascii.hexlify(bytearray(data[4:5]))
                    ),
                    "Transfer type": AftTransferStatus.AftTransferStatus.get_status(
                        binascii.hexlify(bytearray(data[5:6]))
                    ),
                    "Cashable amount": int(binascii.hexlify(bytearray(data[6:11])))
                    * self.denom,
                    "Restricted amount": int(binascii.hexlify(bytearray(data[11:16])))
                    * self.denom,
                    "Nonrestricted amount": int(
                        binascii.hexlify(bytearray(data[16:21]))
                    )
                    * self.denom,
                    "Transfer flags": binascii.hexlify(bytearray(data[21:22])),
                    "Asset number": binascii.hexlify(bytearray(data[22:26])),
                    "Transaction ID length": binascii.hexlify(bytearray(data[26:27])),
                    "Transaction ID": binascii.hexlify(bytearray(data[27 : (27 + a)])),
                }
        except Exception as e:
            self.log.error(e, exc_info=True)

        self.aft_unregister()

        return response

    def aft_in(self, money, amount=1):
        """
        aft_in is the function you want to use to charge money into your machine

        :param money:
        :param amount:
        :param lock_timeout:
        :param kwargs:
        :return:
        """
        money_1 = money_2 = money_3 = "0000000000"
        if self.denom > 0.01:
            return None

        money = str(int(money / self.denom)).replace(".", "")
        money = "0" * (10 - len(money)) + money

        match amount:
            case 1:
                money_1 = money
            case 2:
                money_2 = money
            case 3:
                money_3 = money
            case _:
                raise AFTBadAmount

        last_transaction = self.aft_format_transaction()
        len_transaction_id = hex(len(last_transaction) // 2)[2:]
        if len(len_transaction_id) < 2:
            len_transaction_id = "0" + len_transaction_id
        elif len(len_transaction_id) % 2 == 1:
            len_transaction_id = "0" + len_transaction_id

        cmd = """72{my_key}{transfer_code}{index}00{money_1}{money_2}{money_3}
                 00{asset}{key}{len_transaction}{transaction}{times}0C0000""".format(
            transfer_code="00",
            index="00",
            money_1=money_1,
            money_2=money_2,
            money_3=money_3,
            asset=self.asset_number,
            key=self.reg_key,
            len_transaction=len_transaction_id,
            transaction=last_transaction,
            times=datetime.datetime.strftime(datetime.datetime.now(), "%m%d%Y"),
            my_key=self.my_key,
        )

        new_cmd = []
        count = 0
        for i in range(len(cmd) // 2):
            new_cmd.append(int(cmd[count : count + 2], 16))
            count += 2

        try:
            data = self._send_command(new_cmd, crc_need=True, size=82)
            if data:
                a = int(binascii.hexlify(bytearray(data[26:27])), 16)
                response = {
                    "Length": int(binascii.hexlify(bytearray(data[26:27])), 16),
                    "Transaction buffer position": int(
                        binascii.hexlify(bytearray(data[2:3]))
                    ),
                    "Transfer status": AftTransferStatus.AftTransferStatus.get_status(
                        [binascii.hexlify(bytearray(data[3:4]))]
                    ),
                    "Receipt status": AftReceiptStatus.AftReceiptStatus.get_status(
                        [binascii.hexlify(bytearray(data[4:5]))]
                    ),
                    "Transfer type": AftTransferType.AftTransferType.get_status(
                        [binascii.hexlify(bytearray(data[5:6]))]
                    ),
                    "Cashable amount": int(binascii.hexlify(bytearray(data[6:11])))
                    * self.denom,
                    "Restricted amount": int(binascii.hexlify(bytearray(data[11:16])))
                    * self.denom,
                    "Nonrestricted amount": int(
                        binascii.hexlify(bytearray(data[16:21]))
                    )
                    * self.denom,
                    "Transfer flags": binascii.hexlify(bytearray(data[21:22])),
                    "Asset number": binascii.hexlify(bytearray(data[22:26])),
                    "Transaction ID length": binascii.hexlify(bytearray(data[26:27])),
                    "Transaction ID": binascii.hexlify(bytearray(data[27 : (27 + a)])),
                }

                self.aft_unregister()
                return response

        except Exception as e:
            self.aft_unregister()
            self.log.error(e, exc_info=True)

    def aft_clean_transaction_poll(self, register=False):
        """Remember to loop this function AFTER calling aft_in.
        If it raises an error or returns 'Transfer pending (not complete)'
        you continue to execute until 'Full transfer successful'.
        Otherwise, you break the cycle and make the request invalid.
        """
        if register:
            self.aft_register()

        if not self.transaction:
            self.aft_get_last_trx()

        cmd = "7202FF00"
        count = 0
        new_cmd = []
        for i in range(len(cmd) // 2):
            new_cmd.append(int(cmd[count : count + 2], 16))
            count += 2

        response = None
        try:
            data = self._send_command(new_cmd, crc_need=True, size=90)
            if data:
                a = int(binascii.hexlify(bytearray(data[26:27])), 16)
                response = {
                    "Length": int(binascii.hexlify(bytearray(data[26:27])), 16),
                    "Transfer status": AftTransferStatus.AftTransferStatus.get_status(
                        binascii.hexlify(bytearray(data[3:4]))
                    ),
                    "Receipt status": AftTransferStatus.AftTransferStatus.get_status(
                        binascii.hexlify(bytearray(data[4:5]))
                    ),
                    "Transfer type": AftTransferStatus.AftTransferStatus.get_status(
                        binascii.hexlify(bytearray(data[5:6]))
                    ),
                    "Cashable amount": int(binascii.hexlify(bytearray(data[6:11])))
                    * self.denom,
                    "Restricted amount": int(binascii.hexlify(bytearray(data[11:16])))
                    * self.denom,
                    "Nonrestricted amount": int(
                        binascii.hexlify(bytearray(data[16:21]))
                    )
                    * self.denom,
                    "Transfer flags": binascii.hexlify(bytearray(data[21:22])),
                    "Asset number": binascii.hexlify(bytearray(data[22:26])),
                    "Transaction ID length": binascii.hexlify(bytearray(data[26:27])),
                    "Transaction ID": binascii.hexlify(bytearray(data[27 : (27 + a)])),
                }

            if register:
                try:
                    self.aft_unregister()
                except:
                    self.log.warning("AFT UNREGISTER ERROR: clean poll")

            if hex(self.transaction)[2:-1] == response["Transaction ID"]:
                return response
            else:
                if self.aft_get_last_transaction:
                    raise BadTransactionID(
                        "last: %s, new:%s "
                        % (hex(self.transaction)[2:-1], response["Transaction ID"])
                    )
                else:
                    self.log.info(
                        "last: %s, new:%s "
                        % (hex(self.transaction)[2:-1], response["Transaction ID"])
                    )
        except BadCRC:
            pass

        return False

    def aft_transfer_funds(
        self,
        transfer_code=0x00,
        transaction_index=0x00,
        transfer_type=0x00,
        cashable_amount=0,
        restricted_amount=0,
        non_restricted_amount=0,
        transfer_flags=0x00,
        asset_number=b"\x00\x00\x00\x00\x00",
        registration_key=0,
        transaction_id="",
        expiration=0,
        pool_id=0,
        receipt_data="",
        lock_timeout=0
    ):
        # 72
        cmd = [
            0x72,
            2 * len(transaction_id) + 53,
            transfer_code,
            transaction_index,
            transfer_type,
            self._bcd_coder_array(cashable_amount, 5),
            self._bcd_coder_array(restricted_amount, 5),
            self._bcd_coder_array(non_restricted_amount, 5),
            transfer_flags,
            asset_number,
            self._bcd_coder_array(registration_key, 20),
            len(transaction_id),
            self._bcd_coder_array(expiration, 4),
            self._bcd_coder_array(pool_id, 2),
            len(receipt_data),
            receipt_data,
            self._bcd_coder_array(lock_timeout, 2)
        ]

        data = self._send_command(cmd, crc_need=True)
        if data:
            AftStatements.AftStatements.STATUS_MAP["transaction_buffer_position"] = int(
                binascii.hexlify(bytearray(data[2:3]))
            )
            AftStatements.AftStatements.STATUS_MAP["transfer_status"] = int(
                binascii.hexlify(bytearray(data[3:4]))
            )
            AftStatements.AftStatements.STATUS_MAP["receipt_status"] = int(
                binascii.hexlify(bytearray(data[4:5]))
            )
            AftStatements.AftStatements.STATUS_MAP["transfer_type"] = int(
                binascii.hexlify(bytearray(data[5:6]))
            )
            AftStatements.AftStatements.STATUS_MAP["cashable_amount"] = int(
                binascii.hexlify(bytearray(data[6:11]))
            )
            AftStatements.AftStatements.STATUS_MAP["restricted_amount"] = int(
                binascii.hexlify(bytearray(data[11:16]))
            )
            AftStatements.AftStatements.STATUS_MAP["nonrestricted_amount"] = int(
                binascii.hexlify(bytearray(data[16:21]))
            )
            AftStatements.AftStatements.STATUS_MAP["transfer_flags"] = int(
                binascii.hexlify(bytearray(data[21:22]))
            )
            AftStatements.AftStatements.STATUS_MAP["asset_number"] = binascii.hexlify(
                bytearray(data[22:26])
            )
            AftStatements.AftStatements.STATUS_MAP["transaction_id_length"] = int(
                binascii.hexlify(bytearray(data[26:27]))
            )
            a = int(binascii.hexlify(bytearray(data[26:27])))
            AftStatements.AftStatements.STATUS_MAP["transaction_id"] = str(
                binascii.hexlify(bytearray(data[27 : (27 + a + 1)]))
            )
            a = 27 + a + 1
            AftStatements.AftStatements.STATUS_MAP["transaction_date"] = str(
                binascii.hexlify(bytearray(data[a : a + 5]))
            )
            a = a + 5
            AftStatements.AftStatements.STATUS_MAP["transaction_time"] = str(
                binascii.hexlify(bytearray(data[a : a + 4]))
            )
            AftStatements.AftStatements.STATUS_MAP["expiration"] = str(
                binascii.hexlify(bytearray(data[a + 4 : a + 9]))
            )
            AftStatements.AftStatements.STATUS_MAP["pool_id"] = str(
                binascii.hexlify(bytearray(data[a + 9 : a + 11]))
            )
            AftStatements.AftStatements.STATUS_MAP[
                "cumulative_cashable_amount_meter_size"
            ] = binascii.hexlify(bytearray(data[a + 11 : a + 12]))
            b = a + int(binascii.hexlify(bytearray(data[a + 11 : a + 12])))
            AftStatements.AftStatements.STATUS_MAP[
                "cumulative_cashable_amount_meter"
            ] = binascii.hexlify(bytearray(data[a + 12 : b + 1]))
            AftStatements.AftStatements.STATUS_MAP[
                "cumulative_restricted_amount_meter_size"
            ] = binascii.hexlify(bytearray(data[b + 1 : b + 2]))
            c = b + 2 + int(binascii.hexlify(bytearray(data[b + 1 : b + 2])))
            AftStatements.AftStatements.STATUS_MAP[
                "cumulative_restricted_amount_meter"
            ] = binascii.hexlify(bytearray(data[b + 2 : c]))
            AftStatements.AftStatements.STATUS_MAP[
                "cumulative_nonrestricted_amount_meter_size"
            ] = binascii.hexlify(bytearray(data[c : c + 1]))
            b = int(binascii.hexlify(bytearray(data[c : c + 1]))) + c
            AftStatements.AftStatements.STATUS_MAP[
                "cumulative_nonrestricted_amount_meter"
            ] = binascii.hexlify(bytearray(data[c + 1 :]))

            return AftStatements.AftStatements.get_non_empty_status_map()

        return None

    def aft_get_last_trx(self):
        cmd = [0x72, 0x02, 0xFF, 0x00]
        data = self._send_command(cmd, crc_need=True, size=90)
        if data:
            try:
                if not self.aft_get_last_transaction:
                    raise ValueError

                count = int(binascii.hexlify(data[26:27]), 16)
                transaction = binascii.hexlify(data[27 : 27 + count])
                if transaction == "2121212121212121212121212121212121":
                    transaction = "2020202020202020202020202020202021"
                self.transaction = int(transaction, 16)

                return self.transaction

            except ValueError as e:
                self.log.warning(e, exc_info=True)
                self.transaction = int("2020202020202020202020202020202021", 16)
                self.log.warning("AFT no transaction")

            except Exception as e:
                self.log.error(e, exc_info=True)
                self.transaction = int("2020202020202020202020202020202021", 16)
                self.log.warning("AFT no transaction")

        else:
            self.transaction = int("2020202020202020202020202020202021", 16)
            self.log.warning("AFT no transaction")

        return self.transaction

    def aft_format_transaction(self, from_egm=False):
        if from_egm:
            self.aft_get_last_trx()

        if self.transaction is None:
            self.aft_get_last_trx()

        self.transaction += 1
        transaction = hex(self.transaction)[2:-1]
        count = 0
        tmp = []
        for i in range(len(transaction) // 2):
            tmp.append(transaction[count : count + 2])
            count += 2

        tmp.reverse()
        for i in range(len(tmp)):
            if int(tmp[i], 16) >= 124:
                tmp[i] = "20"
                tmp[i + 1] = hex(int(tmp[i + 1], 16) + 1)[2:]

        tmp.reverse()
        response = ""
        for i in tmp:
            response += i
        if response == "2121212121212121212121212121212121":
            response = "2020202020202020202020202020202021"

        self.transaction = int(response, 16)
        return response

    def aft_register(self, reg_code=0x01):
        try:
            return self.aft_register_gaming_machine(reg_code=reg_code)
        except Exception as e:
            self.log.error(e, exc_info=True)
            return None

    def aft_unregister(self, reg_code=0x80):
        try:
            return self.aft_register_gaming_machine(reg_code=reg_code)
        except Exception as e:
            self.log.error(e, exc_info=True)
            return None

    def aft_register_gaming_machine(self, reg_code=0xFF):
        # 73
        cmd = [0x73, 0x00, reg_code]

        if reg_code == 0xFF:
            cmd[1] = 0x01
        else:
            tmp = self.asset_number + self.reg_key + self.pos_id
            cmd[1] = 0x1D
            count = 0
            for i in range(len(tmp) // 2):
                cmd.append(int(tmp[count : count + 2], 16))
                count += 2

        data = self._send_command(cmd, crc_need=True, size=34)

        if data:
            AftStatements.AftStatements.STATUS_MAP[
                "registration_status"
            ] = binascii.hexlify(data[3:7])

            AftStatements.AftStatements.STATUS_MAP["registration_key"] = str(
                binascii.hexlify(data[7:27])
            )
            AftStatements.AftStatements.STATUS_MAP["POS_ID"] = str(
                binascii.hexlify((data[27:]))
            )
            return AftStatements.AftStatements.get_non_empty_status_map()

        return None

    def aft_game_lock(self, lock_timeout=100, condition=00):
        return self.aft_game_lock_and_status_request(
            lock_code=0x00, lock_timeout=lock_timeout, transfer_condition=condition
        )

    def aft_game_unlock(self):
        return self.aft_game_lock_and_status_request(lock_code=0x80)

    def aft_game_lock_and_status_request(
        self, lock_code=0x00, transfer_condition=00, lock_timeout=0
    ):
        # 74
        cmd = [
            0x74,
            lock_code,
            transfer_condition,
            self._bcd_coder_array(lock_timeout, 2),
        ]

        data = self._send_command(cmd, crc_need=True, size=40)
        if data:
            AftStatements.AftStatements.STATUS_MAP["asset_number"] = str(
                binascii.hexlify(bytearray(data[2:6]))
            )
            AftStatements.AftStatements.STATUS_MAP["game_lock_status"] = str(
                binascii.hexlify(bytearray(data[6:7]))
            )
            AftStatements.AftStatements.STATUS_MAP["avilable_transfers"] = str(
                binascii.hexlify(bytearray(data[7:8]))
            )
            AftStatements.AftStatements.STATUS_MAP["host_cashout_status"] = str(
                binascii.hexlify(bytearray(data[8:9]))
            )
            AftStatements.AftStatements.STATUS_MAP["AFT_status"] = str(
                binascii.hexlify(bytearray(data[9:10]))
            )
            AftStatements.AftStatements.STATUS_MAP["max_buffer_index"] = str(
                binascii.hexlify(bytearray(data[10:11]))
            )
            AftStatements.AftStatements.STATUS_MAP["current_cashable_amount"] = str(
                binascii.hexlify(bytearray(data[11:16]))
            )
            AftStatements.AftStatements.STATUS_MAP["current_restricted_amount"] = str(
                binascii.hexlify(bytearray(data[16:21]))
            )
            AftStatements.AftStatements.STATUS_MAP[
                "current_non_restricted_amount"
            ] = str(binascii.hexlify(bytearray(data[21:26])))
            AftStatements.AftStatements.STATUS_MAP["restricted_expiration"] = str(
                binascii.hexlify(bytearray(data[26:29]))
            )
            AftStatements.AftStatements.STATUS_MAP["restricted_pool_ID"] = str(
                binascii.hexlify(bytearray(data[29:31]))
            )

            return AftStatements.AftStatements.get_non_empty_status_map()

        return None

    def aft_cancel_request(self):
        cmd = [0x72, 0x01, 0x80]
        self.aft_register()
        response = None
        data = self._send_command(cmd, crc_need=True, size=90)
        if data:
            a = int(binascii.hexlify(bytearray(data[26:27])), 16)
            response = {
                "Length": int(binascii.hexlify(bytearray(data[26:27])), 16),
                "Transfer status": AftTransferStatus.AftTransferStatus.get_status(
                    binascii.hexlify(bytearray(data[3:4]))
                ),
                "Receipt status": AftReceiptStatus.AftReceiptStatus.get_status(
                    binascii.hexlify(bytearray(data[4:5]))
                ),
                "Transfer type": AftTransferType.AftTransferType.get_status(
                    binascii.hexlify(bytearray(data[5:6]))
                ),
                "Cashable amount": int(binascii.hexlify(bytearray(data[6:11])))
                * self.denom,
                "Restricted amount": int(binascii.hexlify(bytearray(data[11:16])))
                * self.denom,
                "Nonrestricted amount": int(binascii.hexlify(bytearray(data[16:21])))
                * self.denom,
                "Transfer flags": binascii.hexlify(bytearray(data[21:22])),
                "Asset number": binascii.hexlify(bytearray(data[22:26])),
                "Transaction ID length": binascii.hexlify(bytearray(data[26:27])),
                "Transaction ID": binascii.hexlify(bytearray(data[27 : (27 + a)])),
            }
        try:
            self.aft_unregister()
        except:
            self.log.warning("AFT UNREGISTER ERROR")

        if response["Transaction ID"] == hex(self.transaction)[2:-1]:
            return response

        return False

    def aft_receipt_data(self):
        # TODO: 75
        return NotImplemented

    def aft_set_custom_ticket_data(self):
        # TODO: 76
        return NotImplemented

    def extended_validation_status(
        self,
        control_mask=[0, 0],
        status_bits=[0, 0],
        cashable_ticket_receipt_exp=0,
        restricted_ticket_exp=0
    ):
        # 7B
        cmd = [
            0x7B,
            0x08,
            control_mask,
            status_bits,
            self._bcd_coder_array(cashable_ticket_receipt_exp, 2),
            self._bcd_coder_array(restricted_ticket_exp, 2),
        ]

        data = self._send_command(cmd, True, crc_need=True)
        if data:
            AftStatements.AftStatements.STATUS_MAP["asset_number"] = str(
                binascii.hexlify(bytearray(data[2:6]))
            )
            AftStatements.AftStatements.STATUS_MAP["status_bits"] = str(
                binascii.hexlify(bytearray(data[6:8]))
            )
            AftStatements.AftStatements.STATUS_MAP["cashable_ticket_receipt_exp"] = str(
                binascii.hexlify(bytearray(data[8:10]))
            )
            AftStatements.AftStatements.STATUS_MAP["restricted_ticket_exp"] = str(
                binascii.hexlify(bytearray(data[10:]))
            )

            return AftStatements.AftStatements.get_non_empty_status_map()

        return None

    def set_extended_ticket_data(self):
        # TODO: 7C
        return NotImplemented

    def set_ticket_data(self):
        # TODO: 7D
        return NotImplemented

    def current_date_time(self):
        # 7E
        cmd = [0x7E]
        data = self._send_command(cmd, crc_need=False, size=11)
        if data:
            data = str(binascii.hexlify(bytearray(data[1:8])))
            return datetime.datetime.strptime(data, "%m%d%Y%H%M%S")

        return None

    def receive_date_time(self, dates, times):
        # 7F
        cmd = [0x7F]
        fmt_cmd = "" + dates.replace(".", "") + times.replace(":", "") + "00"
        count = 0
        for i in range(len(fmt_cmd) // 2):
            cmd.append(int(fmt_cmd[count : count + 2], 16))
            count += 2

        if self._send_command(cmd, True, crc_need=True) == self.address:
            return True

        return False

    @staticmethod
    def receive_progressive_amount():
        # TODO: 80
        return NotImplemented

    @staticmethod
    def cumulative_progressive_wins():
        # TODO: 83
        return NotImplemented

    @staticmethod
    def progressive_win_amount():
        # TODO: 84
        return NotImplemented

    @staticmethod
    def sas_progressive_win_amount():
        # TODO: 85
        return NotImplemented

    @staticmethod
    def receive_multiple_progressive_levels():
        # TODO: 86
        return NotImplemented

    @staticmethod
    def multiple_sas_progressive_win_amounts():
        # TODO: 87
        return NotImplemented

    def initiate_legacy_bonus_pay(self, money, tax="00", games=None, ):
        # 8A
        if not games:
            for i in range(3):
                try:
                    games = self.selected_game_number(in_hex=False)
                except:
                    pass
                if not games:
                    time.sleep(0.04)
                else:
                    break

        if not games or games <= 0:
            return None

        t_cmd = str(int(round(money / self.denom, 2)))
        t_cmd = ("0" * (8 - len(t_cmd)) + t_cmd) + tax

        cmd = [0x8A]
        count = 0
        for i in range(len(t_cmd) // 2):
            cmd.append(int(t_cmd[count : count + 2], 16))
            count += 2

        if self._send_command(cmd, True, crc_need=True) == self.address:
            return True

        return False

    @staticmethod
    def initiate_multiplied_jackpot_mode():
        # TODO: 8B
        return NotImplemented

    @staticmethod
    def enter_exit_tournament_mode():
        # TODO: 8C
        return NotImplemented

    @staticmethod
    def card_info():
        # TODO: 8E
        return NotImplemented

    @staticmethod
    def physical_reel_stop_info():
        # TODO: 8F
        return NotImplemented

    @staticmethod
    def legacy_bonus_win_info():
        # TODO: 90
        return NotImplemented

    def remote_handpay_reset(self, ):
        # 94
        cmd = [0x94]
        if self._send_command(cmd, True, crc_need=True) == self.address:
            return True

        return False

    @staticmethod
    def tournament_games_played():
        # TODO: 95
        return NotImplemented

    @staticmethod
    def tournament_games_won():
        # TODO: 96
        return NotImplemented

    @staticmethod
    def tournament_credits_wagered():
        # TODO: 97
        return NotImplemented

    @staticmethod
    def tournament_credits_won():
        # TODO: 98
        return NotImplemented

    @staticmethod
    def meters_95_98():
        # TODO: 99
        return NotImplemented

    def legacy_bonus_meters(self, denom=True, n=0):
        # 9A
        cmd = [0x9A, ((n >> 8) & 0xFF), (n & 0xFF)]
        data = self._send_command(cmd, crc_need=True, size=18)
        if data:
            if not denom:
                Meters.Meters.STATUS_MAP["game number"] = int(
                    binascii.hexlify(bytearray(data[2:3]))
                )
                Meters.Meters.STATUS_MAP["deductible"] = int(
                    binascii.hexlify(bytearray(data[3:7]))
                )
                Meters.Meters.STATUS_MAP["non-deductible"] = int(
                    binascii.hexlify(bytearray(data[7:11]))
                )
                Meters.Meters.STATUS_MAP["wager match"] = int(
                    binascii.hexlify(bytearray(data[11:15]))
                )
            else:
                Meters.Meters.STATUS_MAP["game number"] = int(
                    binascii.hexlify(bytearray(data[2:3]))
                )
                Meters.Meters.STATUS_MAP["deductible"] = round(
                    int(binascii.hexlify(bytearray(data[3:7]))) * self.denom, 2
                )
                Meters.Meters.STATUS_MAP["non-deductible"] = round(
                    int(binascii.hexlify(bytearray(data[7:11]))) * self.denom, 2
                )
                Meters.Meters.STATUS_MAP["wager match"] = round(
                    int(binascii.hexlify(bytearray(data[11:15]))) * self.denom, 2
                )
            return Meters.Meters.get_non_empty_status_map()

        return None

    def toggle_autorebet(self, val=True):
        cmd = [0xAA]
        if not val:
            # AA00
            cmd.append(0x00)
        else:
            # AA01
            cmd.append(0x01)

        if self._send_command(cmd, True, crc_need=True) == self.address:
            return True

        return False

    def enabled_features(self, game_number=0):
        # A0
        # FIXME: This makes no sense
        # Basically tells which feature a selected games has. - Antonio

        cmd = [0xA0, self._bcd_coder_array(game_number, 2)]
        data = self._send_command(cmd, True, crc_need=True)
        if data:
            AftStatements.AftStatements.STATUS_MAP["game_number"] = str(
                binascii.hexlify(bytearray(data[1:3]))
            )
            AftStatements.AftStatements.STATUS_MAP["features_1"] = data[3]
            AftStatements.AftStatements.STATUS_MAP["features_2"] = data[4]
            AftStatements.AftStatements.STATUS_MAP["features_3"] = data[5]
            GameFeatures.GameFeatures.STATUS_MAP[
                "game_number"
            ] = AftStatements.AftStatements.get_status("game_number")
            if data[3] & 0b00000001:
                GameFeatures.GameFeatures.STATUS_MAP["jackpot_multiplier"] = 1
            else:
                GameFeatures.GameFeatures.STATUS_MAP["jackpot_multiplier"] = 0

            if data[3] & 0b00000010:
                GameFeatures.GameFeatures.STATUS_MAP["AFT_bonus_awards"] = 1
            else:
                GameFeatures.GameFeatures.STATUS_MAP["AFT_bonus_awards"] = 0

            if data[3] & 0b00000100:
                GameFeatures.GameFeatures.STATUS_MAP["legacy_bonus_awards"] = 1
            else:
                GameFeatures.GameFeatures.STATUS_MAP["legacy_bonus_awards"] = 0

            if data[3] & 0b00001000:
                GameFeatures.GameFeatures.STATUS_MAP["tournament"] = 1
            else:
                GameFeatures.GameFeatures.STATUS_MAP["tournament"] = 0

            if data[3] & 0b00010000:
                GameFeatures.GameFeatures.STATUS_MAP["validation_extensions"] = 1
            else:
                GameFeatures.GameFeatures.STATUS_MAP["validation_extensions"] = 0

            GameFeatures.GameFeatures.STATUS_MAP["validation_style"] = (
                data[3] & 0b01100000 >> 5
            )

            if data[3] & 0b10000000:
                GameFeatures.GameFeatures.STATUS_MAP["ticket_redemption"] = 1
            else:
                GameFeatures.GameFeatures.STATUS_MAP["ticket_redemption"] = 0

            return GameFeatures.GameFeatures.get_non_empty_status_map()

        return None

    @staticmethod
    def cashout_limit():
        # TODO: A4
        return NotImplemented

    @staticmethod
    def enable_jackpot_handpay_reset_method():
        # TODO: A8
        return NotImplemented

    @staticmethod
    def extended_meters_game_alt():
        # TODO: AF
        return NotImplemented

    @staticmethod
    def multi_denom_preamble():
        # TODO: B0
        return NotImplemented

    @staticmethod
    def current_player_denomination():
        # TODO: B1
        return NotImplemented

    @staticmethod
    def enabled_player_denominations():
        # TODO: B2
        return NotImplemented

    @staticmethod
    def token_denomination():
        # TODO: B3
        return NotImplemented

    @staticmethod
    def wager_category_info():
        # TODO: B4
        return NotImplemented

    @staticmethod
    def extended_game_info(n=1):
        # TODO: B5
        return NotImplemented

    @staticmethod
    def event_response_to_long_poll():
        # TODO: FF
        return NotImplemented

    def _bcd_coder_array(self, value=0, length=4):
        return self._int_to_bcd(value, length)

    @staticmethod
    def _int_to_bcd(number=0, length=5, ):
        n = m = bval = 0
        p = length - 1
        result = []
        for i in range(0, length):
            result.extend([0x00])

        while p >= 0:
            if number != 0:
                digit = number % 10
                number = number / 10
                m = m + 1
            else:
                digit = 0

            if n & 1:
                bval |= digit << 4
                result[p] = bval
                p = p - 1
                bval = 0
            else:
                bval = digit

            n = n + 1

        return result

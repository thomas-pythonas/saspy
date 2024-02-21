#!/usr/bin/python
# -*- coding: utf8 -*-
import serial
import time
import binascii
import logging
import datetime

from PyCRC.CRC16Kermit import CRC16Kermit
from utils import Crc
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
            perpetual=False  # When this is true the lib will try forever to connect to the serial
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
        self.perpetual = perpetual

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
                if not self.perpetual:
                    self.log.critical("Error while connecting to the machine....Quitting...")
                    exit(1)  # Make a graceful exit since it's expected behaviour

                self.log.critical("Error while connecting to the machine....")
                time.sleep(1)

        return

    def is_open(self):
        return self.connection.is_open

    def flush(self):
        """Flush the serial buffer in input and output"""
        try:
            if not self.is_open():
                self.open()
            self.connection.reset_output_buffer()
            self.connection.reset_input_buffer()
        except Exception as e:
            self.log.error(e, exc_info=True)

        self.close()

    def start(self):
        """Warm Up the connection to the VLT"""

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
                self.connection.reset_output_buffer()
                self.connection.reset_input_buffer()
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
        """Close the connection to the serial port"""
        self.connection.close()

    def open(self):
        """Open connection to the VLT"""
        try:
            if self.connection.is_open is not True:
                self.connection.open()
        except:
            raise SASOpenError

    def _conf_event_port(self):
        """Do magick to make SAS Happy and work with their effing parity"""
        self.open()
        self.connection.flush()
        self.connection.timeout = self.poll_timeout
        self.connection.parity = serial.PARITY_NONE
        self.connection.stopbits = serial.STOPBITS_TWO
        self.connection.reset_input_buffer()

    def _conf_port(self):
        """As per _conf_event_port Do magick to make SAS Happy and work with their effing parity"""
        self.open()
        self.connection.flush()
        self.connection.timeout = self.timeout
        self.connection.parity = serial.PARITY_MARK
        self.connection.stopbits = serial.STOPBITS_ONE
        self.connection.reset_input_buffer()

    def _send_command(
            self, command, no_response=False, timeout=None, crc_need=True, size=1
    ):
        """Main function to physically send commands to the VLT"""
        try:
            buf_header = [self.address]
            self._conf_port()

            buf_header.extend(command)

            if crc_need:
                crc = CRC16Kermit().calculate(bytearray(buf_header).decode("utf-8"))
                buf_header.extend([((crc >> 8) & 0xFF), (crc & 0xFF)])
                print(buf_header)
                print(Crc.calculate(bytearray(buf_header), 0))

            self.connection.write([self.poll_address, self.address])

            self.connection.flush()
            self.connection.parity = serial.PARITY_SPACE

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
        """Function in charge of the CRC Check"""
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
        """Events Poll function

        See Also
        --------
        WiKi : https://github.com/zacharytomlinson/saspy/wiki/4.-Important-To-Know#event-reporting
        """
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
        """Make the VLT unplayable
        :note: This is a LONG POLL COMMAND
        """
        # [0x01]
        if self._send_command([0x01], True, crc_need=True) == self.address:
            return True

        return False

    def startup(self):
        """Synchronize to the host polling cycle

        Notes
        -------
        This is a LONG POLL COMMAND
        """
        if self._send_command([0x02], True, crc_need=True) == self.address:
            return True

        return False

    def sound_off(self):
        """Disable VLT sounds

        Notes
        -------
        This is a LONG POLL COMMAND
        """
        if self._send_command([0x03], True, crc_need=True) == self.address:
            return True

        return False

    def sound_on(self):
        """Enable VLT sounds

        Notes
        -------
        This is a LONG POLL COMMAND
        """
        if self._send_command([0x04], True, crc_need=True) == self.address:
            return True

        return False

    def reel_spin_game_sounds_disabled(self):
        """Reel spin or game play sounds disabled

        Notes
        -------
        This is a LONG POLL COMMAND
        """
        if self._send_command([0x05], True, crc_need=True) == self.address:
            return True

        return False

    def enable_bill_acceptor(self):
        """Enable the Bill Acceptor

        Notes
        -------
        This is a LONG POLL COMMAND
        """
        if self._send_command([0x06], True, crc_need=True) == self.address:
            return True

        return False

    def disable_bill_acceptor(self):
        """Disable the Bill Acceptor

        Notes
        -------
        This is a LONG POLL COMMAND
        """
        if self._send_command([0x07], True, crc_need=True) == self.address:
            return True

        return False

    def configure_bill_denom(
            self, bill_denom=[0xFF, 0xFF, 0xFF], action_flag=[0xFF]
    ):
        """Configure Bill Denominations

        Parameters
        ----------
        bill_denom : dict
            Bill denominations sent LSB first (0 = disable, 1 = enable)

            =====  =====  ========  ========    =====
            Bit    LSB    2nd Byte  3rd Byte    MSB
            =====  =====  ========  ========    =====
            0      $1     $200      $20000      TBD
            1      $2     $250      $25000      TBD
            2      $5     $500      $50000      TBD
            3      $10    $1000     $100000     TBD
            4      $20    $2000     $200000     TBD
            5      $25    $2500     $250000     TBD
            6      $50    $5000     $500000     TBD
            7      $100   $10000    $1000000    TBD
            =====  =====  ========  ========    =====

        action_flag : dict
            Action of bill acceptor after accepting a bill

            =====  ===========
            Bit    Description
            =====  ===========
            0      0 = Disable bill acceptor after each accepted bill

                   1 = Keep bill acceptor enabled after each accepted bill
            =====  ===========

        Returns
        -------
        bool
            True if successful, False otherwise.

        Notes
        -------
        This is a LONG POLL COMMAND
        """
        cmd = [0x08, 0x00]
        cmd.extend(bill_denom)
        cmd.extend(action_flag)

        if self._send_command(cmd, True, crc_need=True) == self.address:
            return True

        return False

    def en_dis_game(self, game_number=None, en_dis=False):
        """Enable or Disable a specific game

        Parameters
        ----------
        game_number : bcd
            0001-9999 Game number

        en_dis : bool
            Default is False. True enable a game | False disable it

        Returns
        -------
        bool
            True if successful, False otherwise.

        """
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
        """Put the VLT in a state of maintenance mode
            Returns
            -------
            bool
                True if successful, False otherwise.

            Notes
            -------
            This is a LONG POLL COMMAND
        """
        if self._send_command([0x0A], True, crc_need=True) == self.address:
            return True

        return False

    def exit_maintenance_mode(self):
        """Recover  the VLT from a state of maintenance mode
            Returns
            -------
            bool
                True if successful, False otherwise.

            Notes
            -------
            This is a LONG POLL COMMAND
        """
        if self._send_command([0x0B], True, crc_need=True) == self.address:
            return True

        return False

    def en_dis_rt_event_reporting(self, enable=False):
        """For situations where real time event reporting is desired, the gaming machine can be configured to report events in response to long polls as well as general polls. This allows events such as reel stops, coins in, game end, etc., to be reported in a timely manner
            Returns
            -------
            bool
                True if successful, False otherwise.

            See Also
            --------
            WiKi : https://github.com/zacharytomlinson/saspy/wiki/4.-Important-To-Know#event-reporting
        """
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
        """Send meters 10 through 15

        Parameters
        ----------
        denom : bool
            If True will return the values of the meters in float format (i.e. 123.23)
            otherwise as int (i.e. 12323)

        Returns
        -------
        Mixed
            Object containing the translated meters or None

        Notes
        -------
        This is a LONG POLL COMMAND
        """
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
        """Send total cancelled credits meter 

            Parameters
            ----------
            denom : bool
                If True will return the values of the meters in float format (i.e. 123.23)
                otherwise as int (i.e. 12323)

            Returns
            -------
            Mixed
                Round | INT | None

            Notes
            -------
            This is a LONG POLL COMMAND
            """
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
        """Send total coin in meter
        Parameters
        ----------
        denom : bool
            If True will return the values of the meters in float format (i.e. 123.23)
            otherwise as int (i.e. 12323)

        Returns
        -------
        Mixed
            Round | INT | None

        Notes
        -------
        This is a LONG POLL COMMAND - Pretty sure that the param should not be used @todo CHECK ME
        """
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
        """Send total coin out meter
            Parameters
            ----------
            denom : bool
                If True will return the values of the meters in float format (i.e. 123.23)
                otherwise as int (i.e. 12323)

            Returns
            -------
            Mixed
                Round | INT | None

            Notes
            -------
            This is a LONG POLL COMMAND - Pretty sure that the param should not be used @todo CHECK ME
            """
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

    def total_drop_meter(self, denom=True):
        """Send total drop meter
        Parameters
        ----------
        denom : bool
            If True will return the values of the meters in float format (i.e. 123.23)
            otherwise as int (i.e. 12323)

        Returns
        -------
        Mixed
            Round | INT | None

        Notes
        -------
        This is a LONG POLL COMMAND - Pretty sure that the param should not be used @todo CHECK ME
        """
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
        """Send total jackpot meter
        Parameters
        ----------
        denom : bool
            If True will return the values of the meters in float format (i.e. 123.23)
            otherwise as int (i.e. 12323)

        Returns
        -------
        Mixed
            Round | INT | None

        Notes
        -------
        This is a LONG POLL COMMAND - Pretty sure that the param should not be used @todo CHECK ME
        """
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
        """Send games played meter

        Returns
        -------
        Mixed
            INT | None

        Notes
        -------
        This is a LONG POLL COMMAND
        """
        cmd = [0x15]
        data = self._send_command(cmd, crc_need=False, size=8)
        if data:
            return int(binascii.hexlify(bytearray(data[1:5])))

        return None

    def games_won_meter(self, denom=True):
        """Send games won meter
        Parameters
        ----------
        denom : bool
            If True will return the values of the meters in float format (i.e. 123.23)
            otherwise as int (i.e. 12323)

        Returns
        -------
        Mixed
            Round | INT | None

        Notes
        -------
        This is a LONG POLL COMMAND - Pretty sure that the param should not be used @todo CHECK ME
        """
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
        """Send games won meter
        Returns
        -------
        Mixed
            INT | None

        Notes
        -------
        This is a LONG POLL COMMAND
        """
        cmd = [0x17]
        data = self._send_command(cmd, crc_need=False, size=8)
        if data:
            return int(binascii.hexlify(bytearray(data[1:5])))

        return None

    def games_powerup_door_opened(self):
        """Send meters 10 through 15

        Returns
        -------
        Mixed
            Object containing the translated meters or None

        Notes
        -------
        This is a LONG POLL COMMAND
        """
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
        """Send meters 11 through 15

        Parameters
        ----------
        denom : bool
            If True will return the values of the meters in float format (i.e. 123.23)
            otherwise as int (i.e. 12323)

        Returns
        -------
        Mixed
            Object containing the translated meters or None

        Notes
        -------
        This is a LONG POLL COMMAND
        """
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
        """Send current credits

        Parameters
        ----------
        denom : bool
            If True will return the value in float format (i.e. 123.23)
            otherwise as int (i.e. 12323)

        Returns
        -------
        Mixed
            round | int | None

        Notes
        -------
        This is a LONG POLL COMMAND
        """
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
        """Send handpay information

        Returns
        -------
        Mixed
            Object containing the translated meters or None

        Notes
        -------
        This is a LONG POLL COMMAND - Warning: is missing 2-byte BCD Partial pay amount @todo FIX ME !
        """
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
        """Send Meters

        Parameters
        ----------
        denom : bool
            If True will return the value in float format (i.e. 123.23)
            otherwise as int (i.e. 12323)

        Returns
        -------
        Mixed
            Object containing the translated meters (in int or float) or None

        Notes
        -------
        This is a LONG POLL COMMAND
        """
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
                Meters.Meters.STATUS_MAP["total_drop_meter"] = int(
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
                Meters.Meters.STATUS_MAP["total_drop_meter"] = round(
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
        """Send total bill meters (# of bills)

        Returns
        -------
        Mixed
            Object containing the translated meters or None

        Notes
        -------
        This is a LONG POLL COMMAND
        """
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
        """Gaming machine information command
        @todo Check this one...something smell bad

        According to doc:
            =====================  ======  =================  ========================================================================================================================================
            Field                  Bytes   Value              Description
            =====================  ======  =================  ========================================================================================================================================
            Address                1       binary 01-7F       Address of gaming machine responding
            Command                1       binary 1F          Gaming machine information command
            Game ID                2       ASCII ??           Game ID in ASCII. (see Table C-1 in Appendix C)
            Additional ID          3       ASCII ???          Additional game ID in ASCII. If the gaming machine does not support an additional ID, this field should be padded with ASCII "0"s.
            Denomination           1       binary 00-FF       Binary number representing the SAS accounting denomination of this gaming machine
            Max bet                1       binary 01-FF       Largest configured max bet for the gaming machine, or FF if largest configured max bet greater than or equal to 255
            Progressive Group      1       binary 00-FF       Current configured progressive group for the gaming machine
            Game options           2       binary 0000-FFFF   Game options selected by the operator. The bit configurations are dependent upon the type of gaming machine.
            Paytable ID            6       ASCII ??????       Paytable ID in ASCII
            Base %                 4       ASCII ??.??        Theoretical base pay back percentage for maximum bet in ASCII. The decimal is implied and NOT transmitted.
            CRC                    2       binary 0000-FFFF   16-bit CRC
            =====================  ======  =================  ========================================================================================================================================

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
        """Send total dollar value of bills meter

        Returns
        -------
        Mixed
            int | none

        Notes
        -------
        This is a LONG POLL COMMAND
        """
        cmd = [0x20]
        data = self._send_command(cmd, crc_need=False, size=8)

        if data:
            return int(binascii.hexlify(bytearray(data[1:])))

        return None

    def rom_signature_verification(self):
        """ROM Signature Verification

        Returns
        -------
        Mixed
            int | none

        Notes
        -------
        This is a LONG POLL COMMAND
        """
        cmd = [0x21, 0x00, 0x00]
        data = self._send_command(cmd, crc_need=True)
        if data:
            return int(binascii.hexlify(bytearray(data[1:3])))

        return None

    def true_coin_in(self):
        """Send true coin in

        Returns
        -------
        Mixed
            int (meter in # of coins/tokens) | none

        Notes
        -------
        This is a LONG POLL COMMAND
        """
        cmd = [0x2A]
        data = self._send_command(cmd, crc_need=False)
        if data:
            return int(binascii.hexlify(bytearray(data[1:5])))

        return None

    def true_coin_out(self):
        """Send true coin out

        Returns
        -------
        Mixed
            int (meter in # of coins/tokens) | none

        Notes
        -------
        This is a LONG POLL COMMAND
        """
        cmd = [0x2B]
        data = self._send_command(cmd, crc_need=False)
        if data:
            return int(binascii.hexlify(bytearray(data[1:5])))

        return None

    def curr_hopper_level(self):
        """Send current hopper level

        Returns
        -------
        Mixed
            int (meter in # of coins/tokens) | none

        Notes
        -------
        This is a LONG POLL COMMAND
        """
        cmd = [0x2C]
        data = self._send_command(cmd, crc_need=False)
        if data:
            return int(binascii.hexlify(bytearray(data[1:5])))

        return None

    def total_hand_paid_cancelled_credit(self):
        """Send total hand paid cancelled credits

        Notes
        -------
        WARNING ! @todo i return: 2-byte BCD game number and 4-byte BCD meter in SAS accounting denom units. Therefore this code is WRONG

        This is a LONG POLL COMMAND
        """
        cmd = [0x2D]
        data = self._send_command(cmd, crc_need=False, size=8)
        if data:
            return int(binascii.hexlify(bytearray(data[1:5])))

        return None

    def delay_game(self, delay_time=100):
        """Delay Game
        Parameters
        ----------
        delay_time : int
            How long in ms to delay a game
            
        Returns
        -------
        bool
            True for a successful operation, False otherwise

        Notes
        -------
        This is a LONG POLL COMMAND
        """
        delay_time = str(delay_time)
        delay_fmt = "" + ("0" * (4 - len(delay_time)) + delay_time)
        cmd = [0x2E]
        count = 0
        for i in range(len(delay_fmt) // 2):
            cmd.append(int(delay_fmt[count: count + 2], 16))
            count += 2
        if self._send_command(cmd, True, crc_need=True) == self.address:
            return True
        else:
            return False

    @staticmethod
    def selected_meters_for_game():
        # 2F
        # TODO: selected_meters_for_game
        # As per above...NOT ME ! @well-it-wasnt-me
        return None

    def send_1_bills_in_meters(self):
        """Send 1$ bills in meters

        Returns
        -------
        mixed
            int (# of bills) or None

        Notes
        -------
        This is a LONG POLL COMMAND
        """
        cmd = [0x31]
        data = self._send_command(cmd, crc_need=False, size=8)
        if data:
            return int(binascii.hexlify(bytearray(data[1:5])))

        return None

    def send_2_bills_in_meters(self):
        """Send 2$ bills in meters

        Returns
        -------
        mixed
            int (# of bills) or None

        Notes
        -------
        This is a LONG POLL COMMAND
        """
        cmd = [0x32]
        data = self._send_command(cmd, crc_need=False, size=8)
        if data:
            return int(binascii.hexlify(bytearray(data[1:5])))

        return None

    def send_5_bills_in_meters(self):
        """Send 5$ bills in meters

        Returns
        -------
        mixed
            int (# of bills) or None

        Notes
        -------
        This is a LONG POLL COMMAND
        """
        cmd = [0x33]
        data = self._send_command(cmd, crc_need=False, size=8)
        if data:
            return int(binascii.hexlify(bytearray(data[1:5])))

        return None

    def send_10_bills_in_meters(self):
        """Send 10$ bills in meters

        Returns
        -------
        mixed
            int (# of bills) or None

        Notes
        -------
        This is a LONG POLL COMMAND
        """
        cmd = [0x34]
        data = self._send_command(cmd, crc_need=False, size=8)
        if data:
            return int(binascii.hexlify(bytearray(data[1:5])))

        return None

    def send_20_bills_in_meters(self):
        """Send 20$ bills in meters

        Returns
        -------
        mixed
            int (# of bills) or None

        Notes
        -------
        This is a LONG POLL COMMAND
        """
        cmd = [0x35]
        data = self._send_command(cmd, crc_need=False, size=8)
        if data:
            return int(binascii.hexlify(bytearray(data[1:5])))

        return None

    def send_50_bills_in_meters(self):
        """Send 50$ bills in meters

        Returns
        -------
        mixed
            int (# of bills) or None

        Notes
        -------
        This is a LONG POLL COMMAND
        """
        cmd = [0x36]
        data = self._send_command(cmd, crc_need=False, size=8)
        if data:
            return int(binascii.hexlify(bytearray(data[1:5])))

        return None

    def send_100_bills_in_meters(self):
        """Send 100$ bills in meters

        Returns
        -------
        mixed
            int (# of bills) or None

        Notes
        -------
        This is a LONG POLL COMMAND
        """
        cmd = [0x37]
        data = self._send_command(cmd, crc_need=False, size=8)
        if data:
            return int(binascii.hexlify(bytearray(data[1:5])))

        return None

    def send_500_bills_in_meters(self):
        """Send 500$ bills in meters

        Returns
        -------
        mixed
            int (# of bills) or None

        Notes
        -------
        This is a LONG POLL COMMAND
        """
        cmd = [0x38]
        data = self._send_command(cmd, crc_need=False, size=8)
        if data:
            return int(binascii.hexlify(bytearray(data[1:5])))

        return None

    def send_1000_bills_in_meters(self):
        """Send 1.000$ bills in meters

        Returns
        -------
        mixed
            int (# of bills) or None

        Notes
        -------
        This is a LONG POLL COMMAND
        """
        cmd = [0x39]
        data = self._send_command(cmd, crc_need=False, size=8)
        if data:
            return int(binascii.hexlify(bytearray(data[1:5])))

        return None

    def send_200_bills_in_meters(self):
        """Send 200$ bills in meters

        Returns
        -------
        mixed
            int (# of bills) or None

        Notes
        -------
        This is a LONG POLL COMMAND
        """
        cmd = [0x3A]
        data = self._send_command(cmd, crc_need=False, size=8)
        if data:
            return int(binascii.hexlify(bytearray(data[1:5])))

        return None

    def send_25_bills_in_meters(self):
        """Send 25$ bills in meters

        Returns
        -------
        mixed
            int (# of bills) or None

        Notes
        -------
        This is a LONG POLL COMMAND
        """
        cmd = [0x3B]
        data = self._send_command(cmd, crc_need=False, size=8)
        if data:
            return int(binascii.hexlify(bytearray(data[1:5])))

        return None

    def send_2000_bills_in_meters(self):
        """Send 2.000$ bills in meters

        Returns
        -------
        mixed
            int (# of bills) or None

        Notes
        -------
        This is a LONG POLL COMMAND
        """
        cmd = [0x3C]
        data = self._send_command(cmd, crc_need=False, size=8)
        if data:
            return int(binascii.hexlify(bytearray(data[1:5])))
        return None

    def cash_out_ticket_info(self):
        """Send cash out ticket information

        Returns
        -------
        mixed
            dict or None

        Notes
        -------
        This is a LONG POLL COMMAND
        """
        cmd = [0x3D]
        data = self._send_command(cmd, crc_need=False)
        if data:
            return {
                "cashout_ticket_number": int(binascii.hexlify(bytearray(data[1:3]))),
                "cashout_amount_in_cents": int(binascii.hexlify(bytearray(data[3:]))),
            }

        return None

    def send_2500_bills_in_meters(self):
        """Send 2.500$ bills in meters

        Returns
        -------
        mixed
            int (# of bills) or None

        Notes
        -------
        This is a LONG POLL COMMAND
        """
        cmd = [0x3E]
        data = self._send_command(cmd, crc_need=False, size=8)
        if data:
            return int(binascii.hexlify(bytearray(data[1:5])))

        return None

    def send_5000_bills_in_meters(self):
        """Send 5.000$ bills in meters

        Returns
        -------
        mixed
            int (# of bills) or None

        Notes
        -------
        This is a LONG POLL COMMAND
        """
        cmd = [0x3F]
        data = self._send_command(cmd, crc_need=False, size=8)
        if data:
            return int(binascii.hexlify(bytearray(data[1:5])))

        return None

    def send_10000_bills_in_meters(self):
        """Send 10.000$ bills in meters

        Returns
        -------
        mixed
            int (# of bills) or None

        Notes
        -------
        This is a LONG POLL COMMAND
        """
        cmd = [0x40]
        data = self._send_command(cmd, crc_need=False, size=8)
        if data:
            return int(binascii.hexlify(bytearray(data[1:5])))

        return None

    def send_20000_bills_in_meters(self):
        """Send 20.000$ bills in meters

        Returns
        -------
        mixed
            int (# of bills) or None

        Notes
        -------
        This is a LONG POLL COMMAND
        """
        cmd = [0x41]
        data = self._send_command(cmd, crc_need=False, size=8)
        if data:
            return int(binascii.hexlify(bytearray(data[1:5])))

        return None

    def send_25000_bills_in_meters(self):
        """Send 25.000$ bills in meters

        Returns
        -------
        mixed
            int (# of bills) or None

        Notes
        -------
        This is a LONG POLL COMMAND
        """
        cmd = [0x42]
        data = self._send_command(cmd, crc_need=False, size=8)
        if data:
            return int(binascii.hexlify(bytearray(data[1:5])))

        return None

    def send_50000_bills_in_meters(self):
        """Send 50.000$ bills in meters

        Returns
        -------
        mixed
            int (# of bills) or None

        Notes
        -------
        This is a LONG POLL COMMAND
        """
        cmd = [0x43]
        data = self._send_command(cmd, crc_need=False, size=8)
        if data:
            return int(binascii.hexlify(bytearray(data[1:5])))

        return None

    def send_100000_bills_in_meters(self):
        """Send 100.000$ bills in meters

        Returns
        -------
        mixed
            int (# of bills) or None

        Notes
        -------
        This is a LONG POLL COMMAND
        """
        cmd = [0x44]
        data = self._send_command(cmd, crc_need=False, size=8)
        if data:
            return int(binascii.hexlify(bytearray(data[1:5])))

        return None

    def send_250_bills_in_meters(self):
        """Send 250$ bills in meters

        Returns
        -------
        mixed
            int (# of bills) or None

        Notes
        -------
        This is a LONG POLL COMMAND
        """
        cmd = [0x45]
        data = self._send_command(cmd, crc_need=False, size=8)
        if data:
            return int(binascii.hexlify(bytearray(data[1:5])))

        return None

    def credit_amount_of_all_bills_accepted(self):
        """Send credit amount of all bills accepted

        Returns
        -------
        mixed
            meter in SAS accounting denom units or None

        """
        cmd = [0x46]
        data = self._send_command(cmd, crc_need=False, size=8)
        if data:
            return int(binascii.hexlify(bytearray(data[1:5])))

        return None

    def coin_amount_accepted_from_external_coin_acceptor(self):
        """Send coin amount accepted from an external coin acceptor

        Returns
        -------
        mixed
             meter in SAS accounting denom units or None

        """
        cmd = [0x47]
        data = self._send_command(cmd, crc_need=False, size=8)
        if data:
            return int(binascii.hexlify(bytearray(data[1:5])))

        return None

    def last_accepted_bill_info(self):
        """ Send last accepted bill information
        Returns
        -------
        mixed
            dict or None
        """
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
        """ Send number of bills currently in the stacker
        Returns
        -------
        mixed
            int ( meter in # of bills )  or None
        """
        cmd = [0x49]
        data = self._send_command(cmd, crc_need=False, size=8)
        if data:
            return int(binascii.hexlify(bytearray(data[1:5])))

        return None

    def total_credit_amount_of_all_bills_in_stacker(self):
        """Send total credit amount of all bills currently in the stacker

        Returns
        -------
        mixed
            int (# of bills) or None

        Notes
        -------
        This is a LONG POLL COMMAND
        """
        cmd = [0x4A]
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

        :param machine_id: 3 binary - Gaming machine validation ID number
        :param seq_num: 3 binary - Starting sequence number (incremented before being assigned to each event)
        :return:
        """
        # 4C
        # FIXME: set_secure_enhanced_validation_ID @todo... im beat...@well-it-wasnt-me
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
        """Send Enhanced Validation Information Command

        Parameters
        ----------
        curr_validation_info :
            Function code; 00 = read current validation info | 01-1F = validation info from buffer index n | FF = look ahead at current validation info

        Returns
        -------
        mixed :
            dict | none
        """
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
            TitoStatement.Tito.STATUS_MAP["amount"] = int(
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
        """Send Current Hopper Status
        Returns
        -------
        mixed :
            dict | none

        Notes
        ------
        Understanding the values:

        - current_hopper_length
        ==============      =====
        Code (Binary)       Description
        ==============      =====
        02                   Only status and % full
        06                   Status, % full and level
        ==============      =====

        - current_hopper_status
        ==============      =====
        Code (Binary)       Status
        ==============      =====
        00                   Hopper OK
        01                   Flooded Optics
        02                   Reverse Coin
        03                   Coin too short
        04                   Coin Jam
        05                   Hopper runaway
        06                   Optics Disconnected
        07                   Hopper Empty
        08-FE                Reserved
        FF                   Other
        ==============      =====

        - current_hopper_percent_full :
            Current hopper level as 0-100%, or FF if unable to detect hopper level percentage

        - current_hopper_level :
            4 BCD | Current hopper level in number of coins/tokens, only if EGM able to detect
        """
        # FIXME: current_hopper_status
        cmd = [0x4F]
        data = self._send_command(cmd, True, crc_need=False)
        if data:
            Meters.Meters.STATUS_MAP["current_hopper_length"] = int(
                binascii.hexlify(bytearray(data[1:2]))
            )
            Meters.Meters.STATUS_MAP["current_hopper_status"] = int(
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
        """Send validation meters
        Parameters
        ----------
        type_of_validation : int
            Type of validation

            ==============      =====
            Code (Binary)       Validation type
            ==============      =====
            00                   Cashable ticket from cashout or win, no handpay lockup
            01                   Restricted promotional ticket from cashout
            02                   Cashable ticket from AFT transfer
            03                   Restricted ticket from AFT transfer
            04                   Debit ticket from AFT transfer
            10                   Cancelled credit handpay (receipt printed
            20                   Jackpot handpay (receipt printed)
            40                   Cancelled credit handpay (no receipt)
            60                   Jackpot handpay (no receipt)
            80                   Cashable ticket redeemed
            81                   Restricted promotional ticket redeemed
            82                   Nonrestricted promotional ticket redeemed
            ==============      =====


        Returns
        -------
        mixed :
            dict | none

        Notes
        -------
        Understanding the response:
            - bin_validation_type :
                See the table "Type of validation"
            - total_validations : 4 BCD
                Total number of validations of type
            - cumulative_amount : 5 BCD
                Cumulative validation amount in units of cents
        """
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
        @todo...one day i'll see to this....
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

    def rcv_validation_number(self, validation_id=1, valid_number=0):
        """Receive Validation number
        Parameters
        ----------
        validation_id : int
            Validation System ID Code (00 = system validation denied)

        valid_number : int
            validation number to use for cashout (not used if validation denied)

        Returns
        -------
        Mixed
            str | none - 00 = command ack | 80 = Not in cashout | 81 = Improper validation rejected
        """
        cmd = [0x58, self._bcd_coder_array(validation_id, 1), self._bcd_coder_array(valid_number, 8)]
        data = self._send_command(cmd, crc_need=True)
        if data:
            return str(binascii.hexlify(bytearray(data[1])))

        return None

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
        """Authentication Info

        Parameters
        ----------
        action : 1 binary
            Requested authentication action:

            =====  =====
            Value  Description
            =====  =====
            00      Interrogate number of installed components
            01      Read status of component (address required)
            02      Authenticate component (address required)
            03      Interrogate authentication status
            =====  =====

        addressing_mode : 1 binary
            =====  =====
            Value  Description
            =====  =====
            00      Addressing by component index number
            01      Addressing by component name
            =====  =====

        component_name : x bytes
            ASCII component name if addressing mode = 01

        auth_method : 4 binary
            ==============      ============    ======================  =======================
            Code (Binary)       Method          Seed size (max bytes)   Result Size (max bytes)
            ==============      ============    ======================  =======================
            00000000            None            n/a                     n/a
            00000001            CRC16           2 binary                2 binary
            00000002            CRC32           4 binary                4 binary
            00000004            MD5             16 bytes                16 bytes
            00000008            Kobetron I      4 ASCII                 4 ASCII
            00000010            Kobetron II     4 ASCII                 4 ASCII
            00000020            SHA1            20 Bytes                20 Bytes
            ==============      ============    ======================  =======================

        Returns
        -------
        bytearray
            Response ACK/NACK

        Notes
        -------
        Actually the real response is way more long and complex. Planning to map and implement it in the future

        """
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
        # @todo This is wrong for sure....this should reply 9 BCD BCD-encoded 18 digit decimal validation number. The first two digits are a 2
        # digit system ID code indicating how to interpret the following 16 digits.
        # System ID code 00 indicates that the following 16 digits represent a SAS
        # secure enhanced validation number. Other system ID codes and parsing codes
        # will be assigned by IGT as needed
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
            Meters.Meters.STATUS_MAP["machine_status"] = int(
                binascii.hexlify(bytearray(data[2:3]))
            )
            Meters.Meters.STATUS_MAP["transfer_amount"] = int(
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
            new_cmd.append(int(cmd[count: count + 2], 16))
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
                    bytearray(data[27: (27 + a)])
                ),  # WARNING: technically should be (27 + 2 * a) due to an off error.... @todo...somebody see me !
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
            new_cmd.append(int(cmd[count: count + 2], 16))
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
                    "Transaction ID": binascii.hexlify(bytearray(data[27: (27 + a)])),
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
            new_cmd.append(int(cmd[count: count + 2], 16))
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
                    "Transaction ID": binascii.hexlify(bytearray(data[27: (27 + a)])),
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
            new_cmd.append(int(cmd[count: count + 2], 16))
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
                    "Transaction ID": binascii.hexlify(bytearray(data[27: (27 + a)])),
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
            new_cmd.append(int(cmd[count: count + 2], 16))
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
                    "Transaction ID": binascii.hexlify(bytearray(data[27: (27 + a)])),
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
            new_cmd.append(int(cmd[count: count + 2], 16))
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
                    "Transaction ID": binascii.hexlify(bytearray(data[27: (27 + a)])),
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
                binascii.hexlify(bytearray(data[27: (27 + a + 1)]))
            )
            a = 27 + a + 1
            AftStatements.AftStatements.STATUS_MAP["transaction_date"] = str(
                binascii.hexlify(bytearray(data[a: a + 5]))
            )
            a = a + 5
            AftStatements.AftStatements.STATUS_MAP["transaction_time"] = str(
                binascii.hexlify(bytearray(data[a: a + 4]))
            )
            AftStatements.AftStatements.STATUS_MAP["expiration"] = str(
                binascii.hexlify(bytearray(data[a + 4: a + 9]))
            )
            AftStatements.AftStatements.STATUS_MAP["pool_id"] = str(
                binascii.hexlify(bytearray(data[a + 9: a + 11]))
            )
            AftStatements.AftStatements.STATUS_MAP[
                "cumulative_cashable_amount_meter_size"
            ] = binascii.hexlify(bytearray(data[a + 11: a + 12]))
            b = a + int(binascii.hexlify(bytearray(data[a + 11: a + 12])))
            AftStatements.AftStatements.STATUS_MAP[
                "cumulative_cashable_amount_meter"
            ] = binascii.hexlify(bytearray(data[a + 12: b + 1]))
            AftStatements.AftStatements.STATUS_MAP[
                "cumulative_restricted_amount_meter_size"
            ] = binascii.hexlify(bytearray(data[b + 1: b + 2]))
            c = b + 2 + int(binascii.hexlify(bytearray(data[b + 1: b + 2])))
            AftStatements.AftStatements.STATUS_MAP[
                "cumulative_restricted_amount_meter"
            ] = binascii.hexlify(bytearray(data[b + 2: c]))
            AftStatements.AftStatements.STATUS_MAP[
                "cumulative_nonrestricted_amount_meter_size"
            ] = binascii.hexlify(bytearray(data[c: c + 1]))
            b = int(binascii.hexlify(bytearray(data[c: c + 1]))) + c
            AftStatements.AftStatements.STATUS_MAP[
                "cumulative_nonrestricted_amount_meter"
            ] = binascii.hexlify(bytearray(data[c + 1:]))

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
                transaction = binascii.hexlify(data[27: 27 + count])
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
            tmp.append(transaction[count: count + 2])
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
                cmd.append(int(tmp[count: count + 2], 16))
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
                "Transaction ID": binascii.hexlify(bytearray(data[27: (27 + a)])),
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
            cmd.append(int(fmt_cmd[count: count + 2], 16))
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
            cmd.append(int(t_cmd[count: count + 2], 16))
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

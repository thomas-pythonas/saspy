#!/usr/bin/python
# -*- coding: utf8 -*-
import bcd
import serial
import time
import binascii
#import string
from PyCRC.CRC16Kermit import CRC16Kermit
from array import array
#ser = serial.Serial('/dev/ttyS3','19200', timeout=1)  # open first serial port
data_to_sent=[0x01, 0x21, 0x00, 0x00]
#adress=1
#print "OK"
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


                ),[])
aft_statement=dict.fromkeys((
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

                 
             

        ),[])
tito_statement=dict.fromkeys((
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
        ),[])


eft_statement=dict.fromkeys((
        'eft_status',
        'promo_amount',
        'cashable_amount',
        'eft_transfer_counter'

        ),[])
game_features=dict.fromkeys((
        'game_number',
        'jackpot_multiplier',
        'AFT_bonus_avards',
        'legacy_bonus_awards',
        'tournament',
        'validation_extensions',
        'validation_style',
        'ticket_redemption'
        ),[])
class sas(object):
        adress=1
        
        def __init__(self, port):
                try:
                        #print 1
                        self.connection=serial.Serial(port=port,baudrate=19200, timeout=2)
                except:
                        print "port error"
                return
        def start(self):
                print 'Connecting SAS...'
                while True:
                        response =self.connection.read(1)
                        if (response<>''):
                                self.adress=int(binascii.hexlify(response))
                                if self.adress>=1:
                                        print 'adress recognised '+str(self.adress)
                                        break
                                
                        #print str(binascii.hexlifyself.adress))
                        time.sleep(.5)
                
                self.gaming_machine_ID()
                print meters.get('ASCII_game_ID')
                print meters.get('ASCII_additional_ID')
                print meters.get('bin_denomination')
                print meters.get('bin_max_bet')
                print meters.get('bin_progressive_mode')
                print meters.get('bin_game_options')
                print meters.get('ASCII_paytable_ID')
                print meters.get('ASCII_base_percentage')
                self.SAS_version_gaming_machine_serial_ID()
                print meters.get('ASCII_SAS_version')
                print meters.get('ASCII_serial_number')
                self.enabled_features() #todo
                
                # 7e date_time_add
                self.AFT_register_gaming_machine(reg_code=0xff)
                print aft_statement.get('registration_status')
                print aft_statement.get('asset_number')
                print aft_statement.get('registration_key')
                print aft_statement.get('POS_ID')

                
                
                
                return True
        
        def __send_command( self, command, no_response=False, timeout=3, crc_need=True):
                busy = True
                response=b''
                try:
                        buf_header=[self.adress]
                        buf_header.extend(command)
                        buf_count=len(command)
                        #buf_header[2]=buf_count+2
                        if (crc_need==True):
                                crc=CRC16Kermit().calculate(str(bytearray(buf_header)))
                                buf_header.extend([((crc>>8)&0xFF),(crc&0xFF)])
                        #print buf_header
                        print buf_header
                        #print self.connection.portstr
                        #self.connection.write([0x31, 0x32,0x33,0x34,0x35])
                        self.connection.write((buf_header))
                        
                except Exception as e:
                        print e

                try:
                        buffer = []
                        self.connection.flushInput()
                        t=time.time()
                        while time.time()-t<timeout:
                                response +=self.connection.read()
                                #print binascii.hexlify(response)
                                if (self.checkResponse(response)<>False):
                                        break

                        if time.time()-t>=timeout:
                                print "timeout waiting response"
                                #buffer.append(response)
                                #print binascii.hexlify(bytearray(response))
                                return None

                        busy = False
                        return self.checkResponse(response)
                        #return None
                except Exception as e:
                        print e

                busy = False
                return None

        def checkResponse(self, rsp):
                if (rsp==''):
                        print 'not response'
                        return False
		
                resp = bytearray(rsp)
                #print resp
                if (resp[0]<>self.adress):
                        print "wrong ardess or NACK"
                        return False

                CRC = binascii.hexlify(resp[-2:])

                
                command = resp[0:-2]

                crc1=crc=CRC16Kermit().calculate(str(bytearray(command)))
                
                data = resp[1:-2]

                crc1 = hex(crc1).split('x')[-1]

                while len(crc1)<4:
                        crc1 = "0"+crc1

                #print crc1
                #print CRC
                if(CRC != crc1):
                    
                            #print "Wrong response command hash " + str(CRC)
                            #print        "////" + str(hex(crc1).split('x')[-1])
                            #print        "////" + str(binascii.hexlify(command))
                            return False
                print binascii.hexlify(data)
                return data
##        def check_crc(self):
##                cmd=[0x01, 0x50, 0x81]
##                cmd=bytearray(cmd)
##                #print self.sas_CRC([0x01, 0x50, 0x81])
##                #print ('\\'+'\\'.join(hex(e)[1:] for e in cmd))
##
##                print (CRC16Kermit().calculate(str(cmd)))
##                return 
        
        def events_poll(self, timeout=1):
                event=''
                cmd=[0x80+self.adress]
                try:
                        self.connection.write(cmd) 
                        t=time.time()
                        while time.time()-t<timeout:
                            #print "time"+ str(time.time()-t)
                                event =self.connection.read()
                                if event!='':
                                        break
                        

                except Exception as e:
                        print e
                        return None
                return event
        
        
        def shutdown(self):
                #01
                #print "1"
                if (self.__send_command([0x01],True, crc_need=True)[0]==0x80+self.adress):
                        return "True"
                else:
                        return "False"
                return
        def startup(self, timeout=0.2):
                #02
                cmd=[self.adress, 0x02]
                try:
                        self.connection.write(cmd) 
                        t=time.time()
                        while time.time()-t<timeout:
                            #print "time"+ str(time.time()-t)
                                event =self.connection.read()
                                if event!='':
                                        break
                        

                except Exception as e:
                        print e
                        return None
                return event
        
        def sound_off(self):
                #03
                if (self.__send_command([0x03],True, crc_need=True)[0]==0x80+self.adress):
                        return "True"
                else:
                        return "False"
                return
        def sound_on(self):
                #04
                if (self.__send_command([0x04],True, crc_need=True)[0]==0x80+self.adress):
                        return "True"
                else:
                        return "False"
                return
        def reel_spin_game_sounds_disabled(self):
                #05
                if (self.__send_command([0x05],True, crc_need=True)[0]==0x80+self.adress):
                        return "True"
                else:
                        return "False"
                return
        def enable_bill_acceptor(self):
                #06
                if (self.__send_command([0x06],True, crc_need=True)[0]==0x80+self.adress):
                        return "True"
                else:
                        return "False"
                return
        def disable_bill_acceptor(self):
                #07
                if (self.__send_command([0x07],True, crc_need=True)[0]==0x80+self.adress):
                        return "True"
                else:
                        return "False"
                return
        def configure_bill_denom(self, bill_denom=[0xFF,0xFF,0xFF], action_flag=[0xff]):
                #08
                cmd=[0x08,0x00]
                ##print str(hex(bill_denom))
                s='00ffffff'
                #print bytes.fromhex(((s)))
                cmd.extend(bill_denom)
                cmd.extend(action_flag)
                print cmd
                if (self.__send_command(cmd,True, crc_need=True)[0]==0x80+self.adress):
                        return "True"
                else:
                        return "False"
                return
        def en_dis_game(self,  game_number=[1], en_dis=[1]):
                #09
                cmd=[0x09]
                cmd.extend(bytearray(game_number))
                cmd.extend(bytearray(en_dis))
                print cmd
                if (self.__send_command(cmd,True, crc_need=True)[0]==0x80+self.adress):
                        return "True"
                else:
                        return "False"
                
                return
        def enter_maintenance_mode(self):
                #0A
                return
        def exit_maintanance_mode(self):
                #0B
                return
        def en_dis_rt_event_reporting(self):
                #0E
                return
        def send_meters_10_15(self):
                #0F
                cmd=[0x0f]
                data=self.__send_command(cmd,True, crc_need=False)
                if(data<>''):
                        meters['total_cancelled_credits_meter']=int((binascii.hexlify(bytearray(data[1:5]))))
                        meters['total_in_meter']=int(binascii.hexlify(bytearray(data[5:9])))
                        meters['total_out_meter']=int(binascii.hexlify(bytearray(data[9:13])))
                        meters['total_droup_meter']=int(binascii.hexlify(bytearray(data[13:17])))
                        meters['total_jackpot_meter']=int(binascii.hexlify(bytearray(data[17:21])))
                        meters['games_played_meter']=int(binascii.hexlify(bytearray(data[21:25])))
                        return data
                return ''
        def total_cancelled_credits(self):
                #10
                cmd=[0x10]
                data=self.__send_command(cmd,True, crc_need=False)
                if(data<>''):
                        meters['total_cancelled_credits_meter']=int(binascii.hexlify(bytearray(data[1:5])))
                        return data                
                return ''
        def total_bet_meter(self):
                #11
                cmd=[0x11]
                data=self.__send_command(cmd,True, crc_need=False)
                if(data<>''):

                        meters['total_bet_meter']=int(binascii.hexlify(bytearray(data[1:5])))

                        return data
                return ''
        def total_win_meter(self):
                #12
                cmd=[0x12]
                data=self.__send_command(cmd,True, crc_need=False)
                if(data<>''):

                        meters['total_win_meter']=int(binascii.hexlify(bytearray(data[1:5])))

                        return data
                return ''
        def total_in_meter(self):
                #13
                cmd=[0x13]
                data=self.__send_command(cmd,True, crc_need=False)
                if(data<>''):

                        meters['total_in_meter']=int(binascii.hexlify(bytearray(data[1:5])))

                        return data
                return ''
        def total_jackpot_meter(self):
                #14
                cmd=[0x14]
                data=self.__send_command(cmd,True, crc_need=False)
                if(data<>''):

                        meters['total_jackpot_meter']=int(binascii.hexlify(bytearray(data[1:5])))

                        return data
                return ''
        def games_played_meter(self):
                #15
                cmd=[0x15]
                data=self.__send_command(cmd,True, crc_need=False)
                if(data<>''):

                        meters['games_played_meter']=int(binascii.hexlify(bytearray(data[1:5])))

                        return data
                return ''
        def games_won_meter(self):
                #16
                cmd=[0x16]
                data=self.__send_command(cmd,True, crc_need=False)
                if(data<>''):

                        meters['games_won_meter']=int(binascii.hexlify(bytearray(data[1:5])))

                        return data
                return ''
        def games_lost_meter(self):
                #17
                cmd=[0x17]
                data=self.__send_command(cmd,True, crc_need=False)
                if(data<>''):

                        meters['games_lost_meter']=int(binascii.hexlify(bytearray(data[1:5])))

                        return data
                return ''
        def games_powerup_door_opened(self):
                #18
                cmd=[0x18]
                data=self.__send_command(cmd,True, crc_need=False)
                if(data<>''):

                        meters['games_last_power_up']=int(binascii.hexlify(bytearray(data[1:3])))
                        meters['games_last_slot_door_close']=int(binascii.hexlify(bytearray(data[1:5])))

                        return data
                return ''
        def meters_11_15(self):
                #19
                cmd=[0x19]
                data=self.__send_command(cmd,True, crc_need=False)
                if(data<>''):
                        meters['total_bet_meter']=int(binascii.hexlify(bytearray(data[1:5])))
                        meters['total_win_meter']=int(binascii.hexlify(bytearray(data[5:9])))
                        meters['total_in_meter']=int(binascii.hexlify(bytearray(data[9:13])))
                        meters['total_jackpot_meter']=int(binascii.hexlify(bytearray(data[13:17])))
                        meters['games_played_meter']=int(binascii.hexlify(bytearray(data[17:21])))
                        return data
                return ''
        def current_credits(self):
                #1A
                cmd=[0x1A]
                data=self.__send_command(cmd,True, crc_need=False)
                if(data<>''):
                        meters['current_credits']=int(binascii.hexlify(bytearray(data[1:5])))

                        return data
                return ''
        def handpay_info(self):
                #1B
                cmd=[0x1B]
                data=self.__send_command(cmd,True, crc_need=False)
                if(data<>''):

                        meters['bin_progressive_group']=int(binascii.hexlify(bytearray(data[1:2])))
                        meters['bin_level']=int(binascii.hexlify(bytearray(data[2:3])))
                        meters['amount']=int(binascii.hexlify(bytearray(data[3:8])))
                        meters['bin_reset_ID']=int(binascii.hexlify(bytearray(data[8:])))
                        return data
                return ''
        def meters(self):
                #1C
                cmd=[0x1C]
                data=self.__send_command(cmd,True, crc_need=False)
                if(data<>''):
                        meters['total_bet_meter']=int(binascii.hexlify(bytearray(data[1:5])))
                        meters['total_win_meter']=int(binascii.hexlify(bytearray(data[5:9])))
                        meters['total_in_meter']=int(binascii.hexlify(bytearray(data[9:13])))
                        meters['total_jackpot_meter']=int(binascii.hexlify(bytearray(data[13:17])))
                        meters['games_played_meter']=int(binascii.hexlify(bytearray(data[17:21])))
                        meters['games_won_meter']=int(binascii.hexlify(bytearray(data[21:25])))
                        meters['slot_door_opened_meter']=int(binascii.hexlify(bytearray(data[25:29])))
                        meters['power_reset_meter']=int(binascii.hexlify(bytearray(data[29:33])))

                        return data
                return ''
        def total_bill_meters(self):
                #1E
                cmd=[0x1E]
                data=self.__send_command(cmd,True, crc_need=False)
                if(data<>''):
                        meters['s1_bills_accepted_meter']=int(binascii.hexlify(bytearray(data[1:5])))
                        meters['s5_bills_accepted_meter']=int(binascii.hexlify(bytearray(data[5:9])))
                        meters['s10_bills_accepted_meter']=int(binascii.hexlify(bytearray(data[9:13])))
                        meters['s20_bills_accepted_meter']=int(binascii.hexlify(bytearray(data[13:17])))
                        meters['s50_bills_accepted_meter']=int(binascii.hexlify(bytearray(data[17:21])))
                        meters['s100_bills_accepted_meter']=int(binascii.hexlify(bytearray(data[21:25])))
 
                        return data
                return ''
        def gaming_machine_ID(self):
                #1F
                cmd=[0x1F]
                data=self.__send_command(cmd,True, crc_need=False)
                if(data<>''):

                        meters['ASCII_game_ID']=(((data[1:3])))
                        meters['ASCII_additional_ID']=(((data[3:6])))
                        meters['bin_denomination']=int(binascii.hexlify(bytearray(data[6])))
                        meters['bin_max_bet']=(binascii.hexlify(bytearray(data[7:8])))
                        meters['bin_progressive_mode']=int(binascii.hexlify(bytearray(data[8:9])))
                        meters['bin_game_options']=(binascii.hexlify(bytearray(data[9:11])))
                        meters['ASCII_paytable_ID']=(((data[11:17])))
                        meters['ASCII_base_percentage']=(((data[17:21])))

                        return data
                return ''
        def total_dollar_value_of_bills_meter(self):
                #20
                
                cmd=[0x20]
                data=self.__send_command(cmd,True, crc_need=False)
                
                if(data<>''):

                        meters['bill_meter_in_dollars']=int(binascii.hexlify(bytearray(data[1:])))
                        
                        return data
                return ''
        def ROM_signature_verification(self):
                #21
                
                cmd=[0x21, 0x00, 0x00]
                data=self.__send_command(cmd,True, crc_need=True)
                print data
                if(data<>None):
                 
                        meters['ROM_signature']= int(binascii.hexlify(bytearray(data[1:3])))
                        print (str(meters.get('ROM_signature')))
                        return data
                return False

        def eft_button_pressed(self, state=0):
                #24
                
                cmd=[0x24, 0x03]
                cmd.append(state)
                
                data=self.__send_command(cmd,True, crc_need=True)
                print data
                if(data<>None):

                        return data
                return ''
                
        def true_coin_in(self):
                #2A
                cmd=[0x2A]
                data=self.__send_command(cmd,True, crc_need=False)
                if(data<>''):

                        meters['true_coin_in']=int(binascii.hexlify(bytearray(data[1:5])))

                        return data
                return ''
        def true_coin_out(self):
                #2B
                cmd=[0x2B]
                data=self.__send_command(cmd,True, crc_need=False)
                if(data<>''):

                        meters['true_coin_out']=int(binascii.hexlify(bytearray(data[1:5])))

                        return data
                return ''
        def curr_hopper_level(self):
                #2C
                cmd=[0x2C]
                data=self.__send_command(cmd,True, crc_need=False)
                if(data<>''):

                        meters['current_hopper_level']=int(binascii.hexlify(bytearray(data[1:5])))

                        return data
                return ''
        def total_hand_paid_cancelled_credit(self):
                #2D
                return
        def delay_game(self, delay=0x01):
                #2E
                cmd=[0x2E]
##                if (delay[0]<=0xff):
##                        cmd.extend([0x00])
                cmd.append(delay)
                

                #print cmd
                if (self.__send_command(cmd,True, crc_need=True)[0]==self.adress):
                        return "True"
                else:
                        return "False"
                
                return
        def selected_meters_for_game(self):
                #2F
                return
        def send_1_bills_in_meters(self):
                #31
                cmd=[0x31]
                data=self.__send_command(cmd,True, crc_need=False)
                if(data<>''):

                        meters['s1_bills_in_meter']=int(binascii.hexlify(bytearray(data[1:5])))

                        return data
                return ''
        def send_2_bills_in_meters(self):
                #32
                cmd=[0x32]
                data=self.__send_command(cmd,True, crc_need=False)
                if(data<>''):

                        meters['s2_bills_in_meter']=int(binascii.hexlify(bytearray(data[1:5])))

                        return data
                return ''             
        def send_5_bills_in_meters(self):
                #33
                cmd=[0x33]
                data=self.__send_command(cmd,True, crc_need=False)
                if(data<>''):

                        meters['s5_bills_in_meter']=int(binascii.hexlify(bytearray(data[1:5])))

                        return data
                return ''
        def send_10_bills_in_meters(self):
                #34
                cmd=[0x34]
                data=self.__send_command(cmd,True, crc_need=False)
                if(data<>''):

                        meters['s10_bills_in_meter']=int(binascii.hexlify(bytearray(data[1:5])))

                        return data
                return ''
        def send_20_bills_in_meters(self):
                #35
                cmd=[0x35]
                data=self.__send_command(cmd,True, crc_need=False)
                if(data<>''):

                        meters['s20_bills_in_meter']=int(binascii.hexlify(bytearray(data[1:5])))

                        return data
                return ''
        def send_50_bills_in_meters(self):
                #36
                cmd=[0x36]
                data=self.__send_command(cmd,True, crc_need=False)
                if(data<>''):

                        meters['s50_bills_in_meter']=int(binascii.hexlify(bytearray(data[1:5])))

                        return data
                return ''
        def send_100_bills_in_meters(self):
                #37
                cmd=[0x37]
                data=self.__send_command(cmd,True, crc_need=False)
                if(data<>''):

                        meters['s100_bills_in_meter']=int(binascii.hexlify(bytearray(data[1:5])))

                        return data
                return ''
        def send_500_bills_in_meters(self):
                #38
                cmd=[0x38]
                data=self.__send_command(cmd,True, crc_need=False)
                if(data<>''):

                        meters['s500_bills_in_meter']=int(binascii.hexlify(bytearray(data[1:5])))

                        return data
                return ''
        def send_1000_bills_in_meters(self):
                #39
                cmd=[0x39]
                data=self.__send_command(cmd,True, crc_need=False)
                if(data<>''):

                        meters['s1000_bills_in_meter']=int(binascii.hexlify(bytearray(data[1:5])))

                        return data
                return ''
        def send_200_bills_in_meters(self):
                #3A
                cmd=[0x3a]
                data=self.__send_command(cmd,True, crc_need=False)
                if(data<>''):

                        meters['s200_bills_in_meter']=int(binascii.hexlify(bytearray(data[1:5])))

                        return data
                return ''
        def send_25_bills_in_meters(self):
                #3B
                cmd=[0x3B]
                data=self.__send_command(cmd,True, crc_need=False)
                if(data<>''):

                        meters['s25_bills_in_meter']=int(binascii.hexlify(bytearray(data[1:5])))

                        return data
                return ''
        def send_2000_bills_in_meters(self):
                #3C
                cmd=[0x3C]
                data=self.__send_command(cmd,True, crc_need=False)
                if(data<>''):

                        meters['s2000_bills_in_meter']=int(binascii.hexlify(bytearray(data[1:5])))

                        return data
                return ''
        def cash_out_ticket_info(self):
                #3D
                cmd=[0x3D]
                data=self.__send_command(cmd,True, crc_need=False)
                if(data<>''):

                        tito_statement['cashout_ticket_number']=int(binascii.hexlify(bytearray(data[1:3])))
                        tito_statement['cashout_amount_in_cents']=int(binascii.hexlify(bytearray(data[3:])))

                        return data
                return ''
        def send_2500_bills_in_meters(self):
                #3E
                cmd=[0x3E]
                data=self.__send_command(cmd,True, crc_need=False)
                if(data<>''):

                        meters['s2500_bills_in_meter']=int(binascii.hexlify(bytearray(data[1:5])))

                        return data
                return ''
        def send_5000_bills_in_meters(self):
                #3F
                cmd=[0x3F]
                data=self.__send_command(cmd,True, crc_need=False)
                if(data<>''):

                        meters['s5000_bills_in_meter']=int(binascii.hexlify(bytearray(data[1:5])))

                        return data
                return ''
        def send_10000_bills_in_meters(self):
                #40
                cmd=[0x40]
                data=self.__send_command(cmd,True, crc_need=False)
                if(data<>''):

                        meters['s10000_bills_in_meter']=int(binascii.hexlify(bytearray(data[1:5])))

                        return data
                return ''
        def send_20000_bills_in_meters(self):
                #41
                cmd=[0x41]
                data=self.__send_command(cmd,True, crc_need=False)
                if(data<>''):

                        meters['s20000_bills_in_meter']=int(binascii.hexlify(bytearray(data[1:5])))

                        return data
                return ''
        def send_25000_bills_in_meters(self):
                #42
                cmd=[0x42]
                data=self.__send_command(cmd,True, crc_need=False)
                if(data<>''):

                        meters['s25000_bills_in_meter']=int(binascii.hexlify(bytearray(data[1:5])))

                        return data
                return ''
        def send_50000_bills_in_meters(self):
                #43
                cmd=[0x43]
                data=self.__send_command(cmd,True, crc_need=False)
                if(data<>''):

                        meters['s50000_bills_in_meter']=int(binascii.hexlify(bytearray(data[1:5])))

                        return data
                return ''
        def send_100000_bills_in_meters(self):
                #44
                cmd=[0x44]
                data=self.__send_command(cmd,True, crc_need=False)
                if(data<>''):

                        meters['s100000_bills_in_meter']=int(binascii.hexlify(bytearray(data[1:5])))

                        return data
                return ''
        def send_250_bills_in_meters(self):
                #45
                cmd=[0x45]
                data=self.__send_command(cmd,True, crc_need=False)
                if(data<>''):

                        meters['s250_bills_in_meter']=int(binascii.hexlify(bytearray(data[1:5])))

                        return data
                return ''
        def credit_amount_of_all_bills_accepted(self):
                #46
                
                cmd=[0x46]
                data=self.__send_command(cmd,True, crc_need=False)
                if(data<>''):

                        meters['credit_amount_of_all_bills_accepted']=int(binascii.hexlify(bytearray(data[1:5])))

                        return data
                return ''
        def coin_amount_accepted_from_external_coin_acceptor(self):
                #47
                cmd=[0x47]
                data=self.__send_command(cmd,True, crc_need=False)
                if(data<>None):

                        meters['coin_amount_accepted_from_external_coin_acceptor']=int(binascii.hexlify(bytearray(data[1:5])))

                        return data
                return ''
        def last_accepted_bill_info(self):
                #48
                cmd=[0x48]
                data=self.__send_command(cmd,True, crc_need=False)
                if(data<>None):
                        meters['country_code']=int(binascii.hexlify(bytearray(data[1:2])))
                        meters['bill_denomination']=int(binascii.hexlify(bytearray(data[2:3])))
                        meters['meter_for_accepted_bills']=int(binascii.hexlify(bytearray(data[3:6])))
                        return data
                return ''
        def number_of_bills_currently_in_stacker(self):
                #49
                cmd=[0x49]
                data=self.__send_command(cmd,True, crc_need=False)
                if(data<>None):
                        meters['number_bills_in_stacker']=int(binascii.hexlify(bytearray(data[1:5])))
                        return data
                return ''
        def total_credit_amount_of_all_bills_in_stacker(self):
                #4A 
                cmd=[0x49]
                data=self.__send_command(cmd,True, crc_need=False)
                if(data<>None):
                        meters['credits_SAS_in_stacker']=int(binascii.hexlify(bytearray(data[1:5])))
                        return data
                return ''
        def set_secure_enhanced_validation_ID(self, MachineID=[0x01,0x01,0x01], seq_num=[0x00,0x00,0x01]):
                #4C                
                cmd=[0x4C]
                
                cmd.extend(MachineID)
                cmd.extend(seq_num)
                cmd=bytearray(cmd)
                #print str(binascii.hexlify((cmd)))
                data=self.__send_command(cmd,True, crc_need=True)
                if(data<>None):
                        tito_statement['machine_ID']=int(binascii.hexlify(bytearray(data[1:4])))
                        tito_statement['sequence_number']=int(binascii.hexlify(bytearray(data[4:8])))

                        return data
                return ''
        def enhanced_validation_information(self, curr_validation_info=0):
                #4D

                cmd=[0x4D]
                
                #cmd.append(transfer_code)
                #cmd=cmd.extend(0)
                #rint str(binascii.hexlify(bytearray(cmd)))
                cmd.append((curr_validation_info))
                data=self.__send_command(cmd,True, crc_need=True)
                if(data<>None):
                        tito_statement['validation_type']=int(binascii.hexlify(bytearray(data[1:2])))
                        tito_statement['index_number']=int(binascii.hexlify(bytearray(data[2:3])))
                        tito_statement['date_validation_operation']=str(binascii.hexlify(bytearray(data[3:7])))
                        tito_statement['time_validation_operation']=str(binascii.hexlify(bytearray(data[7:10])))
                        tito_statement['validation_number']=str(binascii.hexlify(bytearray(data[10:18])))
                        tito_statement['ticket_amount']=int(binascii.hexlify(bytearray(data[18:23])))
                        tito_statement['ticket_number']=int(binascii.hexlify(bytearray(data[23:25])))
                        tito_statement['validation_system_ID']=int(binascii.hexlify(bytearray(data[25:26])))
                        tito_statement['expiration_date_printed_on_ticket']=str(binascii.hexlify(bytearray(data[26:30])))
                        tito_statement['pool_id']=int(binascii.hexlify(bytearray(data[30:32])))


                        return data
                return ''
        def current_hopper_status(self):
                #4F

                cmd=[0x4F]
                
                data=self.__send_command(cmd,True, crc_need=False)
                if(data<>None):
                        meters['current_hopper_lenght']=int(binascii.hexlify(bytearray(data[1:2])))
                        meters['current_hopper_ststus']=int(binascii.hexlify(bytearray(data[2:3])))
                        meters['current_hopper_percent_full']=int(binascii.hexlify(bytearray(data[3:4])))
                        meters['current_hopper_level']=int(binascii.hexlify(bytearray(data[4:])))
                        return data
                return ''
        def validation_meters(self, type_of_validation=0x00):
                #50

                cmd=[0x50]
                cmd.append(type_of_validation)
                data=self.__send_command(cmd,True, crc_need=True)                
                if(data<>None):
                        meters['bin_validation_type']=int(binascii.hexlify(bytearray(data[1])))
                        meters['total_validations']=int(binascii.hexlify(bytearray(data[2:6])))
                        meters['cumulative_amount']=str(binascii.hexlify(bytearray(data[6:])))

                        return data
                return ''
        def total_number_of_games_impimented(self):
                #51
                cmd=[0x51]
                cmd.extend(type_of_validation)
                data=self.__send_command(cmd,True, crc_need=False)                
                if(data<>None):
                        meters['total_number_of_games_impemented']=str(binascii.hexlify(bytearray(data[1:])))
 

                        return data
                return ''
        def game_meters(self, n=1):
                #52

                cmd=[0x52]
                cmd.extend([(n&0xFF), ((n>>8)&0xFF)])
                
                data=self.__send_command(cmd,True, crc_need=True)                
                if(data<>None):
                        meters['game_n_number']=str(binascii.hexlify(bytearray(data[1:3])))
                        meters['game_n_coin_in_meter']=str(binascii.hexlify(bytearray(data[3:7])))
                        meters['game_n_coin_out_meter']=str(binascii.hexlify(bytearray(data[7:11])))
                        meters['game_n_jackpot_meter']=str(binascii.hexlify(bytearray(data[11:15])))
                        meters['geme_n_games_played_meter']=str(binascii.hexlify(bytearray(data[15:])))
 

                        return data
                return ''
        def game_configuration(self, n=1):
                #53

                cmd=[0x53]
                cmd.extend([(n&0xFF), ((n>>8)&0xFF)])
                
                data=self.__send_command(cmd,True, crc_need=True)                
                if(data<>None):
                        meters['game_n_number_config']=int(binascii.hexlify(bytearray(data[1:3])))
                        meters['game_n_ASCII_game_ID']=str(binascii.hexlify(bytearray(data[3:5])))
                        meters['game_n_ASCII_additional_id']=str(binascii.hexlify(bytearray(data[5:7])))
                        meters['game_n_bin_denomination']=str(binascii.hexlify(bytearray(data[7])))
                        meters['game_n_bin_progressive_group']=str(binascii.hexlify(bytearray(data[8])))
                        meters['game_n_bin_game_options']=str(binascii.hexlify(bytearray(data[9:11])))
                        meters['game_n_ASCII_paytable_ID']=str(binascii.hexlify(bytearray(data[11:17])))
                        meters['game_n_ASCII_base_percentage']=str(binascii.hexlify(bytearray(data[17:])))
 

                        return data
                return ''
        def SAS_version_gaming_machine_serial_ID(self):
                #54
                cmd=[0x54]
                                
                data=self.__send_command(cmd,True, crc_need=False)                
                if(data<>None):
                        meters['ASCII_SAS_version']=data[2:5]
                        meters['ASCII_serial_number']=data[5:]
                        return data
                return ''
        def selected_game_number(self):
                #55
                cmd=[0x55]
                                
                data=self.__send_command(cmd,True, crc_need=False)                
                if(data<>None):
                        meters['selected_game_number']=int(binascii.hexlify(bytearray(data[1:])))
                        return data
                return ''
        def enabled_game_numbers(self):
                #56

                cmd=[0x56]
                                
                data=self.__send_command(cmd,True, crc_need=False)                
                if(data<>None):
                        meters['number_of_enabled_games']=int(binascii.hexlify(bytearray(data[2])))
                        meters['enabled_games_numbers']=int(binascii.hexlify(bytearray(data[3:])))

                        return data
                return ''
        def pending_cashout_info(self):
                #57

                cmd=[0x57]
                                
                data=self.__send_command(cmd,True, crc_need=False)                
                if(data<>None):
                        tito_statement['cashout_type']=int(binascii.hexlify(bytearray(data[1:2])))
                        tito_statement['cashout_amount']=str(binascii.hexlify(bytearray(data[2:])))

                        return data
                return ''
        def validation_number(self, validationID=1, valid_number=0):
                #58

                cmd=[0x58]
                cmd.append(validationID)
                cmd.extend(self.bcd_coder_array( valid_number,8))
                print cmd
                data=self.__send_command(cmd,True, crc_need=True)                
                if(data<>None):

                    return data[1]
                return ''
        def eft_send_promo_to_machine(self, amount=0, count=1, status=0):
                #63
                cmd=[0x63, count, ]
                #status 0-init 1-end
                cmd.append(status)
                cmd.extend(self.bcd_coder_array(amount, 4))
                data=self.__send_command(cmd,True, crc_need=True)

                if(data<>None):
                        eft_statement['eft_status']=str(binascii.hexlify(bytearray(data[1:])))
                        eft_statement['promo_amount']=str(binascii.hexlify(bytearray(data[4:])))
                       # eft_statement['eft_transfer_counter']=int(binascii.hexlify(bytearray(data[3:4])))
                     

                        return data[3]
                return ''
        def eft_load_cashable_credits(self, amount=0, count=1, status=0):
                #69
                cmd=[0x69, count, ]
                cmd.append(status)
                cmd.extend(self.bcd_coder_array(amount, 4))
                data=self.__send_command(cmd,True, crc_need=True)

                if(data<>None):
                        meters['eft_status']=str(binascii.hexlify(bytearray(data[1:2])))
                        meters['cashable_amount']=str(binascii.hexlify(bytearray(data[2:5])))
                     

                        return data[3]
                return ''

        def eft_avilable_transfers(self):
                #6A
                cmd=[0x6A]
                data=self.__send_command(cmd,True, crc_need=False)
                if(data<>None):
                        #meters['number_bills_in_stacker']=int(binascii.hexlify(bytearray(data[1:5])))
                        return data
                return ''


        def autentification_info(self, action=0, adressing_mode=0, component_name='', auth_method=b'\x00\x00\x00\x00', seed_lenght=0, seed='', offset_lenght=0, offset=''):
                #6E
                cmd=[0x6E, 0x00]
                cmd.append(action)
                if action==0:
                        #cmd.append(action)
                        cmd[1]=1
                else:
                        if (action==1 or action==3):
                                cmd.append(adressing_mode)
                                cmd.append(len(bytearray(component_name)))
                                cmd.append (bytearray(component_name))
                                cmd[1]=len(bytearray(component_name))+3
                        else:
                                if action==2:
                                        cmd.append(adressing_mode)
                                        cmd.append(len(bytearray(component_name)))
                                        cmd.append (bytearray(component_name))
                                        cmd.append(auth_metod)
                                        cmd.append(seed_lenght)
                                        cmd.append(bytearray(seed))
                                        cmd.append(offset_lenght)
                                        cmd.append(bytearray(offset))
                                        
                                        cmd[1]=len(bytearray(offset))+len(bytearray(seed))+len(bytearray(component_name))+6                       
                        

                data=self.__send_command(cmd,True, crc_need=True)                
                if(data<>None):

                    return data[1]
                return ''
        def extended_meters_for_game(self, n=1):
                #6F
                return
        def ticket_validation_data(self):
                #70

                cmd=[0x70]

                data=self.__send_command(cmd,True, crc_need=False)                
                if(data<>None):
                        meters['ticket_status']=int(binascii.hexlify(bytearray(data[2:3])))
                        meters['ticket_amount']=str(binascii.hexlify(bytearray(data[3:8])))
                        meters['parsing_code']=int(binascii.hexlify(bytearray(data[8:9])))
                        meters['validation_data']=str(binascii.hexlify(bytearray(data[9:])))


                        return data[1]
                return ''
        def redeem_ticket(self, transfer_code=0, transfer_amount=0, parsing_code=0, validation_data=0, rescticted_expiration=0, pool_ID=0):
                #71

                cmd=[0x71, 0x00]
                cmd.append(transfer_code)
                cmd.extend(self.bcd_coder_array(transfer_amount, 5))
                cmd.append(parsing_code)
                
                cmd.extend(self.bcd_coder_array(validation_data, 8))
                cmd.extend(self.bcd_coder_array(rescticted_expiration, 4))
                cmd.extend(self.bcd_coder_array(pool_ID,2))
                cmd[1]=8+13

                data=self.__send_command(cmd,True, crc_need=True)                
                if(data<>None):
                        meters['ticket_status']=int(binascii.hexlify(bytearray(data[2:3])))
                        meters['ticket_amount']=int(binascii.hexlify(bytearray(data[3:8])))
                        meters['parsing_code']=int(binascii.hexlify(bytearray(data[8:9])))
                        meters['validation_data']=str(binascii.hexlify(bytearray(data[9:])))


                        return data[1]
                return ''
        def AFT_transfer_funds(self, transfer_code=0x00, transaction_index=0x00, transfer_type=0x00, cashable_amount=0, restricted_amount=0, non_restricted_amount=0, transfer_flags=0x00, asset_number=b'\x00\x00\x00\x00\x00', registration_key=0, transaction_ID_lenght=0x00, transaction_ID='', expiration=0, pool_ID=0, reciept_data='', lock_timeout=0):
                #72
#sas.AFT_transfer_funds(0, 1, 0x60, 10000, 0, 0, 0b00000000,)
                cmd=[0x72, 0x00]
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
                cmd.extend(self.bcd_coder_array(lock_timeout,2))

                cmd[1]=len(transaction_ID)+len(transaction_ID)+53

                data=self.__send_command(cmd,True, crc_need=True)                
                if(data<>None):
                        aft_statement['transaction_buffer_position']=int(binascii.hexlify(bytearray(data[2:3])))
                        aft_statement['transfer_status']=int(binascii.hexlify(bytearray(data[3:4])))
                        aft_statement['receipt_status']=int(binascii.hexlify(bytearray(data[4:5])))
                        aft_statement['transfer_type']=int(binascii.hexlify(bytearray(data[5:6])))
                        aft_statement['cashable_amount']=int(binascii.hexlify(bytearray(data[6:11])))
                        aft_statement['restricted_amount']=int(binascii.hexlify(bytearray(data[11:16])))
                        aft_statement['nonrestricted_amount']=int(binascii.hexlify(bytearray(data[16:21])))
                        aft_statement['transfer_flags']=int(binascii.hexlify(bytearray(data[21:22])))
                        aft_statement['asset_number']=(binascii.hexlify(bytearray(data[22:26])))
                        aft_statement['transaction_ID_lenght']=int(binascii.hexlify(bytearray(data[26:27])))
                        a=int(binascii.hexlify(bytearray(data[26:27])))
                        aft_statement['transaction_ID']=str(binascii.hexlify(bytearray(data[27:(27+a+1)])))
                        a=27+a+1
                        aft_statement['transaction_date']=str(binascii.hexlify(bytearray(data[a:a+5])))
                        a=a+5
                        aft_statement['transaction_time']=str(binascii.hexlify(bytearray(data[a:a+4])))
                        aft_statement['expiration']=str(binascii.hexlify(bytearray(data[a+4:a+9])))
                        aft_statement['pool_ID']=str(binascii.hexlify(bytearray(data[a+9:a+11])))
                        aft_statement['cumulative_casable_amount_meter_size']=(binascii.hexlify(bytearray(data[a+11:a+12])))
                        b=a+int(binascii.hexlify(bytearray(data[a+11:a+12])))
                        aft_statement['cumulative_casable_amount_meter']=(binascii.hexlify(bytearray(data[a+12:b+1])))
                        aft_statement['cumulative_restricted_amount_meter_size']=(binascii.hexlify(bytearray(data[b+1:b+2])))
                        c=b+2+int(binascii.hexlify(bytearray(data[b+1:b+2])))
                        aft_statement['cumulative_restricted_amount_meter']=(binascii.hexlify(bytearray(data[b+2:c])))
                        aft_statement['cumulative_nonrestricted_amount_meter_size']=(binascii.hexlify(bytearray(data[c:c+1])))
                        b=int(binascii.hexlify(bytearray(data[c:c+1])))+c
                        aft_statement['cumulative_nonrestricted_amount_meter']=(binascii.hexlify(bytearray(data[c+1:])))


                        return data[1]
                return ''
        def AFT_register_gaming_machine(self, reg_code=0xff, asset_number=0, reg_key=0, POS_ID=b'\x00\x00\x00\x00'):
                #73
                cmd=[0x73, 0x00]
                if reg_code==0xFF:
                        cmd.append(reg_code)
                        cmd[1]=1
                                                       
                else:
                        cmd.append(reg_code)
                        cmd.extend(self.bcd_coder_array(asset_number, 4))
                        cmd.extend(self.bcd_coder_array(reg_key, 20))
                        cmd.extend(self.bcd_coder_array(POS_ID, 4))
                        cmd[1]=0x1D
                data=self.__send_command(cmd,True, crc_need=True)
                if(data<>None):
                        print len(data)
                        aft_statement['registration_status']=(binascii.hexlify((data[2:3])))
                        aft_statement['asset_number']=bytearray(data[3:7])
                        aft_statement['registration_key']=bytearray(data[7:27])
                        aft_statement['POS_ID']=str(binascii.hexlify((data[27:])))
                        return data[1]
                return ''
        def AFT_game_lock_and_status_request(self, lock_code=0x00, transfer_condition=0b00000000, lock_timeout=0):
                #74
                cmd=[0x74]

                cmd.append(lock_code)
                cmd.append(transfer_condition)
                cmd.extend(self.bcd_coder_array(lock_timeout, 2))
                #cmd.addend(0x23)

                data=self.__send_command(cmd,True, crc_need=True)
                if(data<>None):
                        aft_statement['asset_number']=str(binascii.hexlify(bytearray(data[2:6])))
                        aft_statement['game_lock_status']=str(binascii.hexlify(bytearray(data[6:7])))
                        aft_statement['avilable_transfers']=str(binascii.hexlify(bytearray(data[7:8])))
                        aft_statement['host_cashout_status']=str(binascii.hexlify(bytearray(data[8:9])))
                        aft_statement['AFT_status']=str(binascii.hexlify(bytearray(data[9:10])))
                        aft_statement['max_buffer_index']=str(binascii.hexlify(bytearray(data[10:11])))
                        aft_statement['current_cashable_amount']=str(binascii.hexlify(bytearray(data[11:16])))
                        aft_statement['current_restricted_amount']=str(binascii.hexlify(bytearray(data[16:21])))
                        aft_statement['current_non_restricted_amount']=str(binascii.hexlify(bytearray(data[21:26])))
                        aft_statement['restricted_expiration']=str(binascii.hexlify(bytearray(data[26:29])))
                        aft_statement['restricted_pool_ID']=str(binascii.hexlify(bytearray(data[29:31])))
                        
                        return data[1]
                return ''
        def set_AFT_reciept_data(self):
                #75
                return
        def set_custom_AFT_ticket_data(self):
                #76
                return
        def exnended_validation_status(self, control_mask=[0,0], status_bits=[0,0], cashable_ticket_reciept_exp=0, restricted_ticket_exp=0):
                #7B
                cmd=[0x7B, 0x08]

                cmd.extend(control_mask)
                cmd.extend(status_bits)
                cmd.extend(self.bcd_coder_array(cashable_ticket_reciept_exp, 2))
                cmd.extend(self.bcd_coder_array(restricted_ticket_exp, 2))

                #cmd.addend(0x23)


                data=self.__send_command(cmd,True, crc_need=True)
                if(data<>None):
                        aft_statement['asset_number']=str(binascii.hexlify(bytearray(data[2:6])))
                        aft_statement['status_bits']=str(binascii.hexlify(bytearray(data[6:8])))
                        aft_statement['cashable_ticket_reciept_exp']=str(binascii.hexlify(bytearray(data[8:10])))
                        aft_statement['restricted_ticket_exp']=str(binascii.hexlify(bytearray(data[10:])))
                        
                        return data[1]
                return ''
        def set_extended_ticket_data(self):
                #7C
                return
        def set_ticket_data(self):
                #7D
                return
        def current_date_time(self):
                #7E
                return
        def recieve_date_time(self):
                #7F
                return
        def recieve_progressive_amount(self):
                #80
                return
        def cumulative_progressive_wins(self):
                #83
                return
        def progressive_win_amount(self):
                #84
                return
        def SAS_progressive_win_amount(self):
                #85
                return
        def recieve_multiple_progressive_levels(self):
                #86
                return
        def multiple_SAS_progresive_win_amounts(self):
                #87
                return
        def initiate_legacy_bonus_pay(self):
                #8A
                return
        def initiate_multiplied_jackpot_mode(self):
                #8B
                return
        def enter_exit_tournament_mode(self):
                #8C
                return
        def card_info(self):
                #8E
                return
        def physical_reel_stop_info(self):
                #8F
                return
        def legacy_bonus_win_info(self):
                #90
                return
        def remote_handpay_reset(self):
                #94
                return
        def tournament_games_played(self):
                #95
                return
        def tournament_games_won(self):
                #96
                return
        def tournament_credits_wagered(self):
                #97
                return
        def tournament_credits_won(self):
                #98
                return
        def meters_95_98(self):
                #99
                return
        def legacy_bonus_meters(self):
                #9A
                return
        def enabled_features(self, game_nimber=0):
                #A0
                cmd=[0xA0]
               
                cmd.extend(self.bcd_coder_array(game_nimber, 2))
 
                data=self.__send_command(cmd,True, crc_need=True)
                if(data<>None):
                        aft_statement['game_number']=str(binascii.hexlify(bytearray(data[1:3])))
                        aft_statement['features_1']=data[3]
                        aft_statement['features_2']=data[4]
                        aft_statement['features_3']=data[5]

                        game_features['game_number']=aft_statement.get('game_number')
                        if (data[3]&0b00000001):
                                game_features['jackpot_multiplier']=1
                        else:
                                game_features['jackpot_multiplier']=0
                                
                        if (data[3]&0b00000010):
                                game_features['AFT_bonus_avards']=1
                        else:
                                game_features['AFT_bonus_avards']=0
                        if (data[3]&0b00000100):
                                game_features['legacy_bonus_awards']=1
                        else:
                                game_features['legacy_bonus_awards']=0
                        if (data[3]&0b00001000):
                                game_features['tournament']=1
                        else:
                                game_features['tournament']=0
                        if (data[3]&0b00010000):
                                game_features['validation_extensions']=1
                        else:
                                game_features['validation_extensions']=0
                                
                        game_features['validation_style']=data[3]&0b01100000>>5

                        if (data[3]&0b10000000):
                                game_features['ticket_redemption']=1
                        else:
                                game_features['ticket_redemption']=0
  
                               

                        
                        return data[1]
                return ''
        def cashout_limit(self):
                #A4
                return
        def enable_jackpot_handpay_reset_method(self):
                #A8
                return
        def en_dis_game_auto_rebet(self):
                #AA
                return
        def extended_meters_game_alt(self,n=1):
                #AF
                return
        def multi_denom_preamble(self):
                #B0
                return
        def current_player_denomination(self):
                #B1
                return
        def enabled_player_denominations(self):
                #B2
                return
        def token_denomination(self):
                #B3
                return
        def wager_category_info(self):
                #B4
                return
        def extended_game_info(self,n=1):
                #B5
                return
        def event_response_to_long_poll(self):
                #FF
                return
        def bcd_coder_array(self, value=0, lenght=4):
                return self.int_to_bcd(value, lenght)

        
        def int_to_bcd(self, number=0, lenght=5):
                n=0
                m=0
                bval=0
                p=lenght-1
                result=[]
                for i in range(0, lenght):
                        result.extend([0x00]) 
                while (p>=0):
                        if (number!=0):
                                digit=number%10
                                number=number/10
                                m=m+1
                        else:
                                digit=0
                        if (n&1):
                                bval |= digit<<4
                                result[p]=bval
                                p=p-1
                                bval=0
                        else:
                                bval=digit
                        n=n+1
                return result

        
if __name__ =="__main__":
        print "OK"
        sas=sas('/dev/ttyS3')
        #print ( bcd.bcd_to_int(100))
        #print int(bcd.int_to_bcd(0x1467))
        #a=sas.bcd_coder_array(value=100, lenght=10)
        #print ((a))
        print sas.int_to_bcd(1234567890365421,8)
        #sas.start()
        #sas.ROM_signature_verification()
        #sas.total_cancelled_credits()
        #sas.send_meters_10_15()
        #sas.total_bet_meter()
        #sas.total_win_meter()
        #sas.total_in_meter()
        #sas.total_jackpot_meter()



        #sas.SAS_version_gaming_machine_serial_ID()

##        sas.start( )  
##              
##        
##       
##        
  #      print sas.events_poll(  timeout=1)  
##                
##        
##        
##        sas.shutdown( )  
##                
##        sas.startup( )  
##                
##        sas.sound_off( )  
##
##        sas.sound_on( )  
##
##        sas.reel_spin_game_sounds_disabled( )  
## 
##        sas.enable_bill_acceptor( )  
##
##        sas.disable_bill_acceptor( )  
##
##        sas.configure_bill_denom( , bill_denom=[0xFF,0xFF,0xFF], action_flag=[0xff])  
##
##        sas.en_dis_game( ,  game_number=[1], en_dis=[1])  
##
##        sas.enter_maintenance_mode( )  
##
##        sas.exit_maintanance_mode( )  
##
##        sas.en_dis_rt_event_reporting( )  
##
##        sas.send_meters_10_15( )  
##
##        sas.total_cancelled_credits( )  
##
##        sas.total_bet_meter( )  
##
##        sas.total_win_meter( )  
##
##        sas.total_in_meter( )  
##
##        sas.total_jackpot_meter( )  
##


        
#        sas.games_played_meter( )  
##
 #       sas.games_won_meter( )  
##
#        sas.games_lost_meter( )  
##
  #      sas.games_powerup_door_opened( )  
##
  #      sas.meters_11_15( )  
##
 #       sas.current_credits( )  
##
 #       sas.handpay_info( )  
##
 #       sas.meters( )  
##
 #       sas.total_bill_meters( )  
##
#        sas.gaming_machine_ID( )  
##
#        sas.total_dollar_value_of_bills_meter( )  
##
 #       sas.ROM_signature_verification( )  # test usage?
##
 #       sas.true_coin_in( )  
##
#        sas.true_coin_out( )  
##
#        sas.curr_hopper_level( )  
##
 #       sas.total_hand_paid_cancelled_credit( )  #need for maid
##
#        sas.delay_game(  delay=1)  # need to test
##
 #       sas.selected_meters_for_game( )  #need to maid
##
#        sas.send_1_bills_in_meters( )  
##
 #       sas.send_2_bills_in_meters( )  
##            
 #       sas.send_5_bills_in_meters( )  
##
#        sas.send_10_bills_in_meters( )  
##
 #       sas.send_20_bills_in_meters( )  
##
#        sas.send_50_bills_in_meters( )  
##
 #       sas.send_100_bills_in_meters( )  
##
 #       sas.send_500_bills_in_meters( )  
##
 #       sas.send_1000_bills_in_meters( )  
##
 #       sas.send_200_bills_in_meters( )  
##
#        sas.send_25_bills_in_meters( )  
##
 #       sas.send_2000_bills_in_meters( )  
##
 #       sas.cash_out_ticket_info( )  
##
#        sas.send_2500_bills_in_meters( )  
##
#        sas.send_5000_bills_in_meters( )  
##
#        sas.send_10000_bills_in_meters( )  
##
#        sas.send_20000_bills_in_meters( )  
##
 #       sas.send_25000_bills_in_meters( )  
##
#        sas.send_50000_bills_in_meters( )  
##
#        sas.send_100000_bills_in_meters( )  
##
#        sas.send_250_bills_in_meters( )  
##
#        sas.credit_amount_of_all_bills_accepted( )  
##
 #       sas.coin_amount_accepted_from_external_coin_acceptor( )  
##
 #       sas.last_accepted_bill_info( )  
##
#        sas.number_of_bills_currently_in_stacker( )  
##
 #       sas.total_credit_amount_of_all_bills_in_stacker( )  
##
 #       sas.set_secure_enhanced_validation_ID( MachineID=b'\x01\x00\x01', seq_num=b'\x00\x01\x00')  # read manual
##
 #       sas.enhanced_validation_information(  curr_validation_info=0x00)  # asc Lena (append)
##
#        sas.current_hopper_status( )  
##
 #       sas.validation_meters( type_of_validation=0x01)  
##
##        sas.total_number_of_games_impimented( )  
##
##        sas.game_meters( , n=1)  
## 
##        sas.game_configuration( , n=1)  
##
##        sas.SAS_version_gaming_machine_serial_ID( )  
##
##        sas.selected_game_number( )  
##
##        sas.enabled_game_numbers( )  
##
##        sas.pending_cashout_info( )  
##
  #      sas.validation_number( 11, 123456)  
##
##        sas.autentification_info( )  
##
##        sas.extended_meters_for_game( , n=1)  
##                #6F
##          
##        sas.ticket_validation_data( )  
##                #70
##               
  #      sas.redeem_ticket( )  
##                #71
##                
  #      sas.AFT_transfer_funds(0x00, 0,0x00, 10000, 0, 0, 0, b'\xea\x03\x00\x00', b'\x67\x68\x6a\x68\x62\x76\x79\x64\x6a\x6c\x66\x79\x76\x6d\x6b\x64\x79\x79\x64\x72', transaction_ID_lenght=0x01, transaction_ID='1', expiration=b'\x03\x25\x20\x18', pool_ID=0x1010, reciept_data='fgh', lock_timeout=1)
#transfer_code=0x00, transaction_index=0x00, transfer_type=0x00, cashable_amount=0, restricted_amount=0, non_restricted_amount=0, transfer_flags=0x00, asset_number=b'\x00\x00\x00\x00\x00', registration_key=b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00', transaction_ID_lenght=0x00, transaction_ID='', expiration=b'\x00\x00\x00\x00', pool_ID=0, reciept_data='', lock_timeout=0):

##                #72
##                
##        sas.AFT_register_gaming_machine( )  
##                #73
##                
##        sas.AFT_game_lock_and_status_request( )  
##                #74
  #      sas.AFT_register_gaming_machine(reg_code=0x01, asset_number=b'\xea\x03\x00\x00', reg_key='ghjhbvydjlfyvmkdyydr', POS_ID=b'\x03\x04\x05\x06')
##                
##        sas.set_AFT_reciept_data( )  
##                #75
##                
##        sas.set_custom_AFT_ticket_data( )  
##                #76
##                
 #       sas.exnended_validation_status(control_mask=[0b00000011,0b00000000], status_bits=[0b00000011,0b00000000], cashable_ticket_reciept_exp=0, restricted_ticket_exp=0)
 
##                #7B
##                
##        sas.set_extended_ticket_data( )  
##                #7C
##                
##        sas.set_ticket_data( )  
##                #7D
##                
##        sas.current_date_time( )  
##                #7E
##                
##        sas.recieve_date_time( )  
##                #7F
##                
##        sas.recieve_progressive_amount( )  
##                #80
##                
##        sas.cumulative_progressive_wins( )  
##                #83
##                
##        sas.progressive_win_amount( )  
##                #84
##                
##        sas.SAS_progressive_win_amount( )  
##                #85
##                
##        sas.recieve_multiple_progressive_levels( )  
##                #86
##                
##        sas.multiple_SAS_progresive_win_amounts( )  
##                #87
##                
##        sas.initiate_legacy_bonus_pay( )  
##                #8A
##                
##        sas.initiate_multiplied_jackpot_mode( )  
##                #8B
##                
##        sas.enter_exit_tournament_mode( )  
##                #8C
##                
##        sas.card_info( )  
##                #8E
##                
##        sas.physical_reel_stop_info( )  
##                #8F
##                
##        sas.legacy_bonus_win_info( )  
##                #90
##                
##        sas.remote_handpay_reset( )  
##                #94
##                
##        sas.tournament_games_played( )  
##                #95
##                
##        sas.tournament_games_won( )  
##                #96
##                
##        sas.tournament_credits_wagered( )  
##                #97
##                
##        sas.tournament_credits_won( )  
##                #98
##                
##        sas.meters_95_98( )  
##                #99
##                
##        sas.legacy_bonus_meters( )  
##                #9A
##                
##        sas.enabled_features( )  
##                #A0
##                
##        sas.cashout_limit( )  
##                #A4
##                
##        sas.enable_jackpot_handpay_reset_method( )  
##                #A8
##                
##        sas.en_dis_game_auto_rebet( )  
##                #AA
##                
##        sas.extended_meters_game_alt( ,n=1)  
##                #AF
##                
##        sas.multi_denom_preamble( )  
##                #B0
##                
##        sas.current_player_denomination( )  
##                #B1
##                
##        sas.enabled_player_denominations( )  
##                #B2
##                
##        sas.token_denomination( )  
##                #B3
##                
##        sas.wager_category_info( )  
##                #B4
##                
##        sas.extended_game_info( ,n=1)  
##                #B5
##                
##        sas.event_response_to_long_poll( )  
##                #FF




##        
##        for keys, values in aft_statement.items():
##                print(keys)
##                print(values)
 
        #sas.enhanced_validation_information(0)
  
        #sas.set_secure_enhanced_validation_ID( MachineID=[0x01,0x01,0x01], seq_num=[0x00,0x00,0x01])
##        
        while True:
                state= binascii.hexlify(bytearray(sas.events_poll()))
                print state
                if (state=='57'):
                        sas.pending_cashout_info()
                        sas.validation_number( validationID=1, valid_number=1234567890365421)
                        
                        #sas.cash_out_ticket_info()
                        
                if (state=='67'): #cashin
                        sas.ticket_validation_data()
                        sas.redeem_ticket( transfer_code=0, transfer_amount=10000, parsing_code=0, validation_data=1234567891234567, rescticted_expiration=3, pool_ID=0)
                        time.sleep(.3)
                        sas.redeem_ticket( transfer_code=0xff, transfer_amount=10000, parsing_code=0, validation_data=1234567891234567, rescticted_expiration=3, pool_ID=0)

                #71
                
                time.sleep(1)

        for keys, values in tito_statement.items():
                print(keys)
                print(values)
        



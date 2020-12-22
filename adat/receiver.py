#!/usr/bin/env python3
from nmigen import Elaboratable, Array, Signal, Module

from bittimedetector import ADATBitTimeDetector
from shiftregister import ShiftRegister

class ADATReceiver(Elaboratable):
    def __init__(self):
        self.adat_in        = Signal()
        self.adat_clk_in    = Signal()
        self.clk_in         = Signal()
        self.channels_out   = Array(Signal(24) for _ in range(8))
        self.output_enable  = Signal()

    def elaborate(self, platform) -> Module:
        m = Module()

        sync_time_detector = ADATBitTimeDetector()
        m.submodules.sync_time_detector = sync_time_detector

        channel_outputs = Array(ShiftRegister(24) for _ in range(8))
        m.submodules += channel_outputs

        user_bits = ShiftRegister(24)
        m.submodules += user_bits

        got_sync                 = Signal()
        bit_time                 = Signal(10)
        bit_time_counter         = Signal(10)
        bit_time_counter_enable  = Signal()
        nibble_bitcounter        = Signal(3)
        num_nibbles_counter      = Signal(2)
        num_nibbles_counter_prev = Signal(2)
        active_channel           = Signal(3)
        reading_user_data        = Signal()
 
        last_adat_in             = Signal()

        for channel_no in range(8):
            m.d.comb += self.channels_out[channel_no].eq(channel_outputs[channel_no].value_out)

        m.d.comb += [
            sync_time_detector.clk_in.eq(self.clk_in),
            sync_time_detector.adat_in.eq(self.adat_in),
            got_sync.eq(sync_time_detector.bit_length_out > 0)
        ]

        m.d.sync += [
            last_adat_in.eq(self.adat_in)
        ]

        #bit counter
        with m.If(bit_time_counter_enable):
            with m.If(bit_time_counter < bit_time):
                m.d.sync += bit_time_counter.eq(bit_time_counter + 1)
            with m.Else():
                m.d.sync += bit_time_counter.eq(0)
            # reset bit counter on each positive edge of adat_in
            # to prevent counter drift
            with m.If(self.adat_in & ~last_adat_in):
                m.d.sync += bit_time_counter.eq(0)
            # we sample the bit in the middle
        
        with m.FSM() as fsm:
            with m.State("SYNC"):
                with m.If(got_sync):
                    m.d.sync += [
                        bit_time.eq(sync_time_detector.bit_length_out),
                        bit_time_counter.eq(3) # due to sync delays we are already at position 3 here
                    ]
                    m.next = "READ_FRAME"

            with m.State("READ_FRAME"):
                m.d.sync += [ 
                    bit_time_counter_enable.eq(1),
                    reading_user_data.eq(1),
                    active_channel.eq(0)
                ]
                with m.If(bit_time_counter == bit_time >> 1):
                    m.next = "READ_SYNC_BIT"

            with m.State("READ_SYNC_BIT"):
                with m.If(active_channel < 7):
                    with m.If((bit_time_counter == bit_time >> 1)):
                        m.d.sync += nibble_bitcounter.eq(0)
                        m.next = "READ_DATA_NIBBLE"
                with m.Else():
                    m.ext = "SYNC"

            with m.State("READ_DATA_NIBBLE"):
                with m.If((bit_time_counter > (bit_time >> 1)) & (nibble_bitcounter == 4) & self.adat_in):
                    m.d.sync += [ 
                        num_nibbles_counter_prev.eq(num_nibbles_counter),
                        num_nibbles_counter.eq(num_nibbles_counter + 1)
                    ]
                    with m.If((num_nibbles_counter == 3) & (~reading_user_data)):
                        m.d.sync += active_channel.eq(active_channel + 1)
                    m.next = "READ_SYNC_BIT"
                with m.Else():
                    with m.If(~reading_user_data):
                        with m.If(bit_time_counter == bit_time >> 1):
                            m.d.sync += [
                                channel_outputs[active_channel].enable_in.eq(1),
                                channel_outputs[active_channel].bit_in.eq(self.adat_in),
                                nibble_bitcounter.eq(nibble_bitcounter + 1)
                            ]
                        with m.Else():
                            m.d.sync += channel_outputs[active_channel].enable_in.eq(0)
                    with m.Else(): # reading user data
                        with m.If(bit_time_counter == bit_time >> 1):
                            with m.If(nibble_bitcounter < 4):
                                m.d.sync += [
                                    user_bits.enable_in.eq(1),
                                    user_bits.bit_in.eq(self.adat_in),
                                    nibble_bitcounter.eq(nibble_bitcounter + 1)
                                ]                            
                        with m.Else():
                            m.d.sync += user_bits.enable_in.eq(0)
                            with m.If(num_nibbles_counter_prev > num_nibbles_counter):
                                m.d.sync += reading_user_data.eq(0)


        return m
#!/usr/bin/env python3
"""ADAT receiver core"""
from nmigen     import Elaboratable, Signal, Module, ClockSignal, Mux
from nmigen.cli import main

from nrzidecoder     import NRZIDecoder
from shiftregister   import InputShiftRegister
from edgetopulse     import EdgeToPulse

class ADATReceiver(Elaboratable):
    """
        implements the ADAT protocol
    """
    def __init__(self, clk_freq):
        self.clk            = ClockSignal()
        self.reset_in       = Signal()
        self.adat_in        = Signal()
        self.addr_out       = Signal(3)
        self.sample_out     = Signal(24)
        self.output_enable  = Signal()
        self.user_data_out  = Signal(4)
        self.clk_freq       = clk_freq

    def elaborate(self, platform) -> Module:
        """build the module"""
        m = Module()
        sync = m.d.sync
        comb = m.d.comb

        nrzidecoder = NRZIDecoder(self.clk_freq)
        m.submodules.nrzi_decoder = nrzidecoder

        framedata_shifter = InputShiftRegister(24)
        m.submodules.framedata_shifter = framedata_shifter

        output_pulser = EdgeToPulse()
        m.submodules.output_pulser = output_pulser

        active_channel = Signal(3)
        # counts the number of bits output
        bit_counter      = Signal(8)
        # counts the bit position iside a nibble
        nibble_counter   = Signal(3)
        # counts, how many 0 bits it got in a row
        sync_bit_counter = Signal(4)

        comb += [ nrzidecoder.nrzi_in.eq(self.adat_in) ]

        with m.FSM():
            # wait for SYNC
            with m.State("WAIT_SYNC"):
                with m.If(nrzidecoder.running):
                    sync += [
                        bit_counter.eq(0),
                        nibble_counter.eq(0),
                        active_channel.eq(0),
                        output_pulser.edge_in.eq(0)
                    ]

                    with m.If(nrzidecoder.data_out_en):
                        m.d.sync += sync_bit_counter.eq(Mux(nrzidecoder.data_out, 0, sync_bit_counter + 1))
                        with m.If(sync_bit_counter == 9):
                            m.d.sync += sync_bit_counter.eq(0)
                            m.next = "READ_FRAME"

            with m.State("READ_FRAME"):
                # at which bit of bit_counter to output sample data at
                output_at = Signal(8)

                # user bits have been read
                with m.If(bit_counter == 5):
                    sync += [
                        # output user bits
                        self.user_data_out.eq(framedata_shifter.value_out[0:4]),
                        # at bit 35 the first channel has been read
                        output_at.eq(35)
                    ]

                # when each channel has been read, output the channel's sample
                with m.If((bit_counter > 5) & (bit_counter == output_at)):
                    sync += [
                        self.addr_out.eq(active_channel),
                        self.sample_out.eq(framedata_shifter.value_out),
                        self.output_enable.eq(1),
                        output_at.eq(output_at + 30),
                        active_channel.eq(active_channel + 1)
                    ]
                with m.Else():
                    sync += self.output_enable.eq(0)

                # we work and count only when we get
                # a new bit fron the NRZI decoder
                with m.If(nrzidecoder.data_out_en):
                    comb += [
                        framedata_shifter.bit_in.eq(nrzidecoder.data_out),
                        # skip sync bit, which is first
                        framedata_shifter.enable_in.eq(~(nibble_counter == 0))
                    ]
                    sync += [
                        nibble_counter.eq(nibble_counter + 1),
                        bit_counter.eq(bit_counter + 1),
                    ]
                    with m.If(nibble_counter >= 4):
                        sync += nibble_counter.eq(0)
                    # 239 channel bits and 5 user bits (including sync bits)
                    with m.If(bit_counter >= (239 + 5)):
                        sync += [
                            bit_counter.eq(0),
                            output_pulser.edge_in.eq(1)
                        ]
                        m.next = "READ_SYNC"
                with m.Else():
                    comb += framedata_shifter.enable_in.eq(0)

                with m.If(~nrzidecoder.running):
                    m.next = "WAIT_SYNC"

            # read the sync bits
            with m.State("READ_SYNC"):
                sync += [
                    self.output_enable.eq(output_pulser.pulse_out),
                    self.addr_out.eq(active_channel),
                    self.sample_out.eq(framedata_shifter.value_out),
                ]

                with m.If(nrzidecoder.data_out_en):
                    sync += [
                        nibble_counter.eq(0),
                        bit_counter.eq(bit_counter + 1),
                    ]

                    with m.If(bit_counter == 9):
                        comb += [
                            framedata_shifter.enable_in.eq(0),
                            framedata_shifter.clear_in.eq(1),
                        ]

                    #check last sync bit before sync trough
                    with m.If((bit_counter == 0) & ~nrzidecoder.data_out):
                        m.next = "WAIT_SYNC"
                    #check all the null bits in the sync trough
                    with m.Elif((bit_counter > 0) & nrzidecoder.data_out):
                        m.next = "WAIT_SYNC"
                    with m.Elif((bit_counter == 10) & ~nrzidecoder.data_out):
                        sync += [
                            bit_counter.eq(0),
                            nibble_counter.eq(0),
                            active_channel.eq(0),
                            output_pulser.edge_in.eq(0)
                        ]
                        m.next = "READ_FRAME"

                with m.If(~nrzidecoder.running):
                    m.next = "WAIT_SYNC"

        return m

if __name__ == "__main__":
    r = ADATReceiver(100e6)
    main(r, name="adat_receiver", ports=[
        r.clk, r.reset_in,
        r.adat_in, r.addr_out,
        r.sample_out, r.output_enable, r.user_data_out])

#!/usr/bin/env python3
"""ADAT receiver core"""
from nmigen     import Elaboratable, Signal, Module, ClockSignal
from nmigen.cli import main

from nrzidecoder     import NRZIDecoder
from shiftregister   import ShiftRegister
from edgetopulse     import EdgeToPulse

class ADATReceiver(Elaboratable):
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
        m = Module()

        nrzidecoder = NRZIDecoder(self.clk_freq)
        m.submodules.nrzi_decoder = nrzidecoder

        channel_output = ShiftRegister(24)
        m.submodules.channel_out_shifter = channel_output

        user_bits = ShiftRegister(4)
        m.submodules.user_bits_shifter = user_bits

        #output_enable_pulse = EdgeToPulse()
        #m.submodules.output_enable_pulse = output_enable_pulse

        active_channel = Signal(3)
        # counts the number of bits output
        bit_counter = Signal(5)

        m.d.comb += [
            #self.output_enable.eq(output_enable_pulse.pulse_out),
            nrzidecoder.nrzi_in.eq(self.adat_in)
        ]

        with m.FSM():
            with m.State("WAITING"):
                with m.If(nrzidecoder.running):
                    m.d.sync += bit_counter.eq(0)
                    m.next = "USERBITS"

            with m.State("USERBITS"):
                # we work and count only when we get
                # a new bit fron the NRZI decoder
                with m.If(nrzidecoder.data_out_en):
                    m.d.comb += [
                        user_bits.bit_in.eq(nrzidecoder.data_out),
                        # skip sync bit, which is first
                        user_bits.enable_in.eq(bit_counter > 0)
                    ]
                    m.d.sync += [
                        bit_counter.eq(bit_counter + 1),
                    ]
                    with m.If(bit_counter >= 4):
                        m.d.sync += bit_counter.eq(0)
                        m.next = "CHANNELS"
                with m.Else():
                    m.d.comb += user_bits.enable_in.eq(0)

                with m.If(~nrzidecoder.running):
                    m.next = "WAITING"

            with m.State("CHANNELS"):
                # turn off user bits reading as soon as we transition here
                m.d.comb += user_bits.enable_in.eq(0)

                # we work and count only when we get
                # a new bit fron the NRZI decoder
                with m.If(nrzidecoder.data_out_en):
                    m.d.comb += [
                        channel_output.bit_in.eq(nrzidecoder.data_out),
                        channel_output.enable_in.eq((bit_counter % 5) > 0)
                    ]
                    m.d.sync += [
                        bit_counter.eq(bit_counter + 1),
                    ]
                    # get 8 channels times 5 bits = 40 bits
                    with m.If(bit_counter >= 23):
                        m.d.sync += [
                            bit_counter.eq(0),
                            self.output_enable.eq(1)
                        ]
                        with m.If(active_channel == 8):
                            m.d.sync += [
                                self.output_enable.eq(0)
                            ]
                            m.next = "USERBITS"
                    with m.Else():
                        m.d.sync += self.output_enable.eq(0)
                with m.Else():
                    m.d.comb += channel_output.enable_in.eq(0)

                with m.If(~nrzidecoder.running):
                    m.next = "WAITING"


        return m

if __name__ == "__main__":
    r = ADATReceiver()
    main(r, name="adat_receiver", ports=[
        r.clk, r.reset_in,
        r.adat_in, r.addr_out,
        r.sample_out, r.output_enable, r.user_data_out])

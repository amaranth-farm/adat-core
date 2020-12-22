#!/usr/bin/env python3
from nmigen import Elaboratable, ClockDomain, Signal, Module
from dividingcounter import DividingCounter

class ADATBitTimeDetector(Elaboratable):
    def __init__(self):
        self.adat_in            = Signal()
        self.clk_in             = Signal()
        self.bit_length_out     = Signal(32)

    def setup_clockdomains(self, m):
        cd_adat = ClockDomain(reset_less=True)
        cd_sync = ClockDomain()
        cd_sync.clk = self.clk_in
        m.domains.adat = cd_adat
        m.domains.sync = cd_sync

    def elaborate(self, platform):
        m = Module()

        self.setup_clockdomains(m)

        sync_counter = DividingCounter(10, 32)
        m.submodules.sync_counter = sync_counter
        max_sync_counter = Signal(32)

        last_max = Signal(32)

        got_sync_frame = Signal()
        # these signals are used to convert got_sync_frame from step to pulse
        last_got_sync_frame = Signal()
        got_sync_frame_pulse = Signal()

        m.d.comb += [
            sync_counter.active_in.eq(~self.adat_in),
            got_sync_frame_pulse.eq(got_sync_frame ^ last_got_sync_frame)
        ]

        with m.If(~self.adat_in):
            m.d.sync += sync_counter.rst_in.eq(0),
            with m.If(sync_counter.counter_out > max_sync_counter):
                m.d.sync += [
                    max_sync_counter.eq(sync_counter.counter_out)
                ]

        with m.Else(): # adat_in is 1
            # if max_bitcounter is greater than 3/4 of its last value, we have a frame start 
            with m.If(max_sync_counter > 50):
                with m.If(max_sync_counter > ((last_max << 1) + last_max) >> 2):                
                    m.d.sync += [
                        got_sync_frame.eq(1),
                        last_got_sync_frame.eq(got_sync_frame),
                    ]

            m.d.sync += [
                last_max.eq(max_sync_counter),
                sync_counter.rst_in.eq(1),
            ]

        with m.If(got_sync_frame_pulse):
            m.d.sync += self.bit_length_out.eq(sync_counter.divided_counter_out)

        return m

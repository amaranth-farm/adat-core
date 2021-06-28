#!/usr/bin/env python3
#
# Copyright (c) 2021 Hans Baier <hansfbaier@gmail.com>
# SPDX-License-Identifier: CERN-OHL-W-2.0
#
"""Find bit timing and decode NRZI"""

import math

from nmigen         import Elaboratable, Signal, Module, ClockDomain
from nmigen.lib.cdc import FFSynchronizer

from adat.dividingcounter import DividingCounter

class NRZIDecoder(Elaboratable):
    """Converts a NRZI encoded ADAT stream into a synchronous stream of bits"""
    def __init__(self, clk_freq: int):
        self.nrzi_in             = Signal()
        self.invalid_frame_in    = Signal()
        self.data_out            = Signal()
        self.data_out_en         = Signal()
        self.recovered_clock_out = Signal()
        self.running             = Signal()
        self.clk_freq            = clk_freq

    @staticmethod
    def setup_clockdomains(m):
        """creates default and ADAT clock domains"""
        cd_adat = ClockDomain(reset_less=True)
        cd_sync = ClockDomain()

        m.domains.adat = cd_adat
        m.domains.sync = cd_sync

    @staticmethod
    def adat_freq(samplerate: int = 48000) -> int:
        """calculate the ADAT bit rate for the given samplerate"""
        return samplerate * ((24 + 6) * 8 + 1 + 10 + 1 + 4)

    def elaborate(self, platform) -> Module:
        """assemble the module"""
        m = Module()
        self.setup_clockdomains(m)
        comb = m.d.comb
        sync = m.d.sync

        nrzi      = Signal()
        nrzi_prev = Signal()
        got_edge  = Signal()

        m.submodules.cdc = FFSynchronizer(self.nrzi_in, nrzi)
        sync += nrzi_prev.eq(nrzi)
        comb += got_edge.eq(nrzi_prev ^ nrzi)

        # we are looking for 10 non changing bits
        # and those will be ~900ns long @48kHz
        # and if we clock at not more than 100MHz
        # the counter will run up to 900ns/10ns = 90
        # so 7 bits will suffice for the counter
        sync_counter = DividingCounter(divisor=12, width=7)
        m.submodules.sync_counter = sync_counter
        bit_time = sync_counter.divided_counter_out

        with m.FSM():
            with m.State("SYNC"):
                comb += self.running.eq(0)
                sync += [
                    self.data_out.eq(0),
                    self.data_out_en.eq(0),
                    sync_counter.reset_in.eq(0)
                ]
                self.find_bit_timings(m, sync_counter, got_edge)

            with m.State("DECODE"):
                comb += self.running.eq(1)
                self.decode_nrzi(m, bit_time, got_edge, sync_counter)

        return m

    def find_bit_timings(self, m: Module, sync_counter: DividingCounter, got_edge: Signal):
        """Waits for the ten zero bits of the SYNC section to determine the length of an ADAT bit"""
        sync = m.d.sync
        bit_time_44100 = math.ceil(110 * (self.clk_freq/self.adat_freq(44100) / 100))

        # as long as the input does not change, count up
        # else reset
        with m.If(got_edge):
            # if the sync counter is 10% over the sync time @44100Hz, then
            # the signal just woke up from the dead. Start counting again.
            with m.If(sync_counter.counter_out > 10 * bit_time_44100):
                sync += sync_counter.reset_in.eq(1)

            # if we are in the middle of the signal,
            # and got an edge, then we reset the counter on each edge
            with m.Else():
                # when the counter is bigger than 3/4 of the old max, then we have a sync frame
                with m.If(sync_counter.counter_out > 7 * bit_time_44100):
                    sync += sync_counter.active_in.eq(0) # stop counting, we found it
                    m.next = "DECODE"
                with m.Else():
                    sync += sync_counter.reset_in.eq(1)

        # when we have no edge, count...
        with m.Else():
            sync += [
                sync_counter.reset_in.eq(0),
                sync_counter.active_in.eq(1)
            ]

    def decode_nrzi(self, m: Module, bit_time: Signal, got_edge: Signal, sync_counter: DividingCounter):
        """Do the actual decoding of the NRZI bitstream"""
        sync = m.d.sync
        bit_counter  = Signal(7)
        # this counter is used to detect a dead signal
        # to determine when to go back to SYNC state
        dead_counter = Signal(8)
        output       = Signal(reset=1)

        # recover ADAT clock
        with m.If(bit_counter <= (bit_time >> 1)):
            m.d.comb += self.recovered_clock_out.eq(1)
        with m.Else():
            m.d.comb += self.recovered_clock_out.eq(0)

        # when the frame decoder got garbage
        # then we need to go back to SYNC state
        with m.If(self.invalid_frame_in):
            sync += [
                sync_counter.reset_in.eq(1),
                bit_counter.eq(0),
                dead_counter.eq(0)
            ]
            m.next = "SYNC"

        sync += bit_counter.eq(bit_counter + 1)
        with m.If(got_edge):
            sync += [
                # latch 1 until we read it in the middle of the bit
                output.eq(1),
                # resynchronize at each bit edge, 1 to compensate
                # for sync delay
                bit_counter.eq(1),
                # when we get an edge, the signal is alive, reset counter
                dead_counter.eq(0)
            ]
        with m.Else():
            sync += dead_counter.eq(dead_counter + 1)

        # wrap the counter
        with m.If(bit_counter == bit_time):
            sync += bit_counter.eq(0)
        # output at the middle of the bit
        with m.Elif(bit_counter == (bit_time >> 1)):
            sync += [
                self.data_out.eq(output),
                self.data_out_en.eq(1), # pulse out_en
                output.eq(0) # edge has been output, wait for new edge
            ]
        with m.Else():
            sync += self.data_out_en.eq(0)

        # when we had no edge for 16 bits worth of time
        # then we go back to sync state
        with m.If(dead_counter >= bit_time << 4):
            sync += dead_counter.eq(0)
            m.next = "SYNC"

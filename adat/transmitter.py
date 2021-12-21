#!/usr/bin/env python3
#
# Copyright (c) 2021 Hans Baier <hansfbaier@gmail.com>
# SPDX-License-Identifier: CERN-OHL-W-2.0
#
""" ADAT transmitter.
    Inputs are in the sync clock domain,
    ADAT output is in the ADAT clock domain
"""

from amaranth          import Elaboratable, Signal, Module, Cat, Const, Array
from amaranth.lib.fifo import AsyncFIFO

from amaranth_library.utils import NRZIEncoder

class ADATTransmitter(Elaboratable):
    """transmit ADAT from a multiplexed stream of eight audio channels

    Parameters
    ----------
    fifo_depth: capacity of the FIFO containing the ADAT frames to be transmitted

    Attributes
    ----------
    adat_out: Signal
        the ADAT signal to be transmitted by the optical transmitter
    addr_in: Signal
        contains the ADAT channel number (0-7) of the current sample to be written
        into the currently assembled ADAT frame
    sample_in: Signal
        the 24 bit sample to be written into the channel slot given by addr_in
        in the currently assembled ADAT frame
    user_data_in: Signal
        the user data bits of the currently assembled frame. Will be committed,
        when ``last_in`` is strobed high
    valid_in: Signal
        commits the data at sample_in into the currently assembled frame,
        but only if ``ready_out`` is high
    ready_out: Signal
        outputs if there is space left in the transmit FIFO. It also will
        prevent any samples to be committed into the currently assembled ADAT frame
    last_in: Signal
        needs to be strobed when the last sample has been committed into the currently
        assembled ADAT frame. This will commit the entire frame (including ``user_bits``)
        into the transmit FIFO.
    fifo_level_out: Signal
        outputs the number of entries in the transmit FIFO
    underflow_out: Signal
        this underflow indicator will be strobed, when a new ADAT frame needs to be
        transmitted but the transmit FIFO is empty. In this case, the last
        ADAT frame will be transmitted again.
    """

    def __init__(self, fifo_depth=4):
        self._fifo_depth    = fifo_depth
        self.adat_out       = Signal()
        self.addr_in        = Signal(3)
        self.sample_in      = Signal(24)
        self.user_data_in   = Signal(4)
        self.valid_in       = Signal()
        self.ready_out      = Signal()
        self.last_in        = Signal()
        self.fifo_level_out = Signal(range(fifo_depth))
        self.underflow_out  = Signal()

    @staticmethod
    def chunks(lst: list, n: int):
        """Yield successive n-sized chunks from lst."""
        for i in range(0, len(lst), n):
            yield lst[i:i + n]

    def elaborate(self, platform) -> Module:
        m = Module()
        sync = m.d.sync
        adat = m.d.adat
        comb = m.d.comb

        audio_channels  = Array([Signal(24, name=f"channel{c}") for c in range(8)])
        user_bits       = Signal(4)

        # 4b/5b coding: Every 24 bit channel has 6 nibbles.
        # 1 bit before the sync pad and one bit before the user data nibble
        filler_bits     = [Const(1, 1) for _ in range(8 * 6 + 2)]
        sync_pad        = Const(0, 10)

        # build ADAT frame
        assembled_frame = Signal(256)
        audio_bits      = Cat(audio_channels[::-1])[::-1]
        audio_nibbles   = list(self.chunks(audio_bits, 4))
        comb += assembled_frame.eq(Cat(zip(filler_bits, [sync_pad, reversed(user_bits)] + audio_nibbles)))

        transmit_fifo = AsyncFIFO(width=256, depth=self._fifo_depth, w_domain="sync", r_domain="adat")
        m.submodules.transmit_fifo = transmit_fifo

        comb += [
            self.ready_out.eq(transmit_fifo.w_rdy),
            self.fifo_level_out.eq(transmit_fifo.w_level),
        ]

        frame_complete = Signal()
        # make sure, w_en is only asserted when explicitly strobed
        sync += transmit_fifo.w_en.eq(0)

        with m.If(self.valid_in & self.ready_out):
            sync += audio_channels[self.addr_in].eq(self.sample_in)

            with m.If(self.last_in):
                sync += [
                    # we need to delay frame completion
                    # by one cycle, so that the last channel
                    # word transmitted can make it into assembled_frame
                    frame_complete.eq(1),
                    # user bits will be committed on the last frame
                    user_bits.eq(self.user_data_in),
                ]

        with m.If(frame_complete):
            # we can't process input on this cycle
            comb += self.ready_out.eq(0)
            sync += [
                # frame complete, queue it into the FIFO
                transmit_fifo.w_data.eq(assembled_frame),
                transmit_fifo.w_en.eq(1),
                frame_complete.eq(0)
            ]

        transmitted_frame_bits = Array([Signal(name=f"frame_bit{b}") for b in range(256)])
        transmitted_frame = Cat(transmitted_frame_bits)

        m.submodules.nrzi_encoder = nrzi_encoder = NRZIEncoder()
        comb += self.adat_out.eq(nrzi_encoder.nrzi_out)

        transmit_counter = Signal(8)
        # just wire up the transmitted frame bit so that it
        # is synchronous to transmit_counter
        # no necessity to add a cycle of latency here
        comb += nrzi_encoder.data_in.eq(transmitted_frame_bits[transmit_counter]),
        adat += transmit_counter.eq(transmit_counter + 1)

        adat += transmit_fifo.r_en.eq(0)
        comb += self.underflow_out.eq(0)

        with m.If(transmit_counter == 255):
            with m.If(transmit_fifo.r_rdy):
                adat += [
                    transmit_fifo.r_en.eq(1),
                    transmitted_frame.eq(transmit_fifo.r_data),
                ]
            with m.Else():
                comb += self.underflow_out.eq(1)

        return m

#!/usr/bin/env python3
#
# Copyright (c) 2021 Hans Baier <hansfbaier@gmail.com>
# SPDX-License-Identifier: CERN-OHL-W-2.0
#
""" ADAT transmitter.
    Inputs are in the sync clock domain,
    ADAT output is in the ADAT clock domain
"""

from amaranth          import Elaboratable, Signal, Module, Cat, Const, Array, Memory
from amaranth.lib.fifo import AsyncFIFO

from amlib.utils import NRZIEncoder


class ADATTransmitter(Elaboratable):
    """transmit ADAT from a multiplexed stream of eight audio channels

    Parameters
    ----------
    fifo_depth: capacity of the FIFO containing the ADAT frames to be transmitted

    Attributes
    ----------
    adat_out: Signal
        the ADAT signal to be transmitted by the optical transmitter
        This input is unused at the moment. Instead the caller needs to ensure
    addr_in: Signal
        contains the ADAT channel number (0-7) of the current sample to be written
        into the currently assembled ADAT frame
    sample_in: Signal
        the 24 bit sample to be written into the channel slot given by addr_in
        in the currently assembled ADAT frame. The samples need to be committed
        in order of channel number (0-7)
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
        assembled ADAT frame. This will commit the user bits to the current ADAT frame
    fifo_level_out: Signal
        outputs the number of entries in the transmit FIFO
    underflow_out: Signal
        this underflow indicator will be strobed, when a new ADAT frame needs to be
        transmitted but the transmit FIFO is empty. In this case, the last
        ADAT frame will be transmitted again.
    """

    def __init__(self, fifo_depth=9*4):
        self._fifo_depth    = fifo_depth
        self.adat_out       = Signal()
        self.addr_in        = Signal(3)
        self.sample_in      = Signal(24)
        self.user_data_in   = Signal(4)
        self.valid_in       = Signal()
        self.ready_out      = Signal()
        self.last_in        = Signal()
        self.fifo_level_out = Signal(range(fifo_depth+1))
        self.underflow_out  = Signal()

        self.mem = Memory(width=24, depth=8, name="sample_buffer")

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

        samples_write_port = self.mem.write_port()
        samples_read_port  = self.mem.read_port(domain='comb')
        m.submodules += [samples_write_port, samples_read_port]

        # the highest bit in the FIFO marks a frame border
        frame_border_flag = 24
        m.submodules.transmit_fifo = transmit_fifo = AsyncFIFO(width=25, depth=self._fifo_depth, w_domain="sync", r_domain="adat")

        # needed for output processing
        m.submodules.nrzi_encoder = nrzi_encoder = NRZIEncoder()

        transmitted_frame_bits = Array([Signal(name=f"frame_bit{b}") for b in range(30)])
        transmitted_frame      = Cat(transmitted_frame_bits)
        transmit_counter       = Signal(5)

        comb += [
            self.ready_out       .eq(transmit_fifo.w_rdy),
            self.fifo_level_out  .eq(transmit_fifo.w_level),
            self.adat_out        .eq(nrzi_encoder.nrzi_out),
            nrzi_encoder.data_in .eq(transmitted_frame_bits[transmit_counter]),
            self.underflow_out   .eq(0)
        ]

        #
        # Fill the transmit FIFO in the sync domain
        #
        channel_counter = Signal(3)

        # make sure, en is only asserted when explicitly strobed
        sync += samples_write_port.en.eq(0)

        with m.FSM():
            with m.State("DATA"):
                with m.If(transmit_fifo.w_rdy):
                    with m.If(self.valid_in):
                        sync += [
                            samples_write_port.data.eq(self.sample_in),
                            samples_write_port.addr.eq(self.addr_in),
                            samples_write_port.en.eq(1),
                        ]

                        with m.If(self.last_in):
                            sync += channel_counter.eq(0)
                            comb += [
                                transmit_fifo.w_data .eq((1 << frame_border_flag) | self.user_data_in),
                                transmit_fifo.w_en   .eq(1),
                            ]
                            m.next = "COMMIT"

                    # underflow: repeat last frame
                    with m.Elif(transmit_fifo.w_level == 0):
                        sync += channel_counter.eq(0)
                        comb += [
                            self.underflow_out   .eq(1),
                            transmit_fifo.w_data .eq((1 << frame_border_flag) | self.user_data_in),
                            transmit_fifo.w_en   .eq(1),
                        ]
                        m.next = "COMMIT"

            with m.State("COMMIT"):
                with m.If(transmit_fifo.w_rdy):
                    comb += [
                        self.ready_out.eq(0),
                        samples_read_port.addr .eq(channel_counter),
                        transmit_fifo.w_data   .eq(samples_read_port.data),
                        transmit_fifo.w_en     .eq(1)
                    ]
                    sync += channel_counter.eq(channel_counter + 1)

                    with m.If(channel_counter == 7):
                        m.next = "DATA"

        #
        # Read the FIFO and send data in the adat domain
        #
        # 4b/5b coding: Every 24 bit channel has 6 nibbles.
        # 1 bit before the sync pad and one bit before the user data nibble
        filler_bits = [Const(1, 1) for _ in range(7)]

        adat += [
            transmit_counter.eq(transmit_counter - 1),
            transmit_fifo.r_en.eq(0)
        ]

        with m.If(transmit_counter == 0):
            adat += transmit_counter.eq(0)
            with m.If(transmit_fifo.r_rdy):
                adat += transmit_fifo.r_en.eq(1)

                with m.If(transmit_fifo.r_data[frame_border_flag] == 0):
                    adat += [
                        transmit_counter.eq(29),
                        # generate the adat data for one channel 0b1dddd1dddd1dddd1dddd1dddd1dddd where d is the PCM audio data
                        transmitted_frame.eq(Cat(zip(list(self.chunks(transmit_fifo.r_data[:25], 4)), filler_bits)))
                    ]
                with m.Else():
                    adat += [
                        transmit_counter.eq(15),
                        # generate the adat sync_pad along with the user_bits 0b100000000001uuuu where u is user_data
                        transmitted_frame.eq((1 << 15) | (1 << 4) | Cat(transmit_fifo.r_data[:5]))
                    ]

            with m.Else():
                transmit_counter.eq(4), # start transmitting rather sooner than later
                adat += transmitted_frame.eq(0x00) # explicitly stop adat output

        return m

#!/usr/bin/env python3
""" ADAT transmitter.
    Inputs are in the sync clock domain,
    ADAT output is in the ADAT clock domain
"""

from nmigen          import Elaboratable, Signal, Module, Cat, Const, Array, \
                            ClockDomain, ClockSignal, ResetSignal
from nmigen.lib.fifo import AsyncFIFO
from nmigen.cli      import main

from nrziencoder import NRZIEncoder

class ADATTransmitter(Elaboratable):
    """ transmit ADAT from a multiplexed stream of eight audio channels """

    def __init__(self):
        self.adat_clk      = ClockSignal("adat")
        self.adat_rst      = ResetSignal("adat")
        self.adat_out      = Signal()
        self.addr_in       = Signal(3)
        self.sample_in     = Signal(24)
        self.user_data_in  = Signal(4)
        self.valid_in      = Signal()
        self.ready_out     = Signal()
        self.last_in       = Signal()

    @staticmethod
    def chunks(lst: list, n: int):
        """Yield successive n-sized chunks from lst."""
        for i in range(0, len(lst), n):
            yield lst[i:i + n]

    def elaborate(self, platform) -> Module:
        m = Module()
        cd_adat = ClockDomain()
        m.domains.adat = cd_adat
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
        audio_bits      = Cat(audio_channels)
        audio_nibbles   = list(self.chunks(audio_bits, 4))
        comb += assembled_frame.eq(Cat(zip(filler_bits, [sync_pad, user_bits] + audio_nibbles)))

        transmit_fifo = AsyncFIFO(width=256, depth=4, w_domain="sync", r_domain="adat")
        m.submodules.transmit_fifo = transmit_fifo

        comb += self.ready_out.eq(transmit_fifo.w_rdy)

        frame_complete = Signal()
        with m.If(self.valid_in & self.ready_out):
            sync += audio_channels[self.addr_in].eq(self.sample_in)

            with m.If(self.last_in):
                sync += [
                    # we need to delay frame completion
                    # by one cycle, so that the last channel
                    # word transmitted can make it into assembled_frame
                    frame_complete.eq(1),
                    # user bits will be committed on the last frame
                    user_bits.eq(self.user_data_in)
                ]

        with m.Elif(frame_complete):
            sync += [
                # frame complete, queue it into the FIFO
                transmit_fifo.w_data.eq(assembled_frame),
                transmit_fifo.w_en.eq(1),
                frame_complete.eq(0)
            ]

        with m.Else():
            # make sure, w_en is only asserted for one cycle
            sync += transmit_fifo.w_en.eq(0)

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

        with m.If((transmit_counter == 255) & transmit_fifo.r_rdy):
            adat += [
                transmit_fifo.r_en.eq(1),
                transmitted_frame.eq(transmit_fifo.r_data)
            ]
        with m.Else():
            adat += transmit_fifo.r_en.eq(0)

        return m

if __name__ == "__main__":
    t = ADATTransmitter()
    main(t, name="adat_transmitter", ports=[
        t.addr_in,
        t.sample_in,
        t.user_data_in,
        t.valid_in,
        t.ready_out,
        t.last_in,
        t.adat_clk,
        t.adat_rst,
        t.adat_out,
    ])

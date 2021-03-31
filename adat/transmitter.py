#!/usr/bin/env python3
""" ADAT transmitter.
    Inputs are in the sync clock domain,
    ADAT output is in the ADAT clock domain
"""

from nmigen          import Elaboratable, Signal, Module, Cat, Const, Array, ClockDomain
from nmigen.lib.fifo import AsyncFIFO
from nmigen.cli      import main

from nrziencoder import NRZIEncoder

class ADATTransmitter(Elaboratable):
    """ transmit ADAT from a multiplexed stream of eight audio channels """
    def __init__(self):
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
        cd_adat = ClockDomain(reset_less=True)
        m.domains.adat = cd_adat
        sync = m.d.sync
        adat = m.d.adat
        comb = m.d.comb

        audio_channels  = Array([Signal(24) for _ in range(8)])
        user_bits       = Signal(4)

        # 4b/5b coding: Every 24 bit channel has 6 nibbles.
        # 1 bit before the sync pad and one bit before the user data nibble
        filler_bits     = [Const(1, 1) for _ in range(8 * 6 + 2)]
        sync_pad        = Const(0, 10)

        audio_bits      = Cat(audio_channels)
        audio_nibbles   = list(self.chunks(audio_bits, 4))
        assembled_frame = Cat(zip(filler_bits, audio_nibbles + [sync_pad, user_bits]))

        transmit_fifo = AsyncFIFO(width=256, depth=4, w_domain="sync", r_domain="adat")

        comb += self.ready_out.eq(transmit_fifo.w_rdy)

        with m.If(self.valid_in & self.ready_out):
            sync += [
                audio_channels[self.addr_in].eq(self.sample_in),
                user_bits.eq(self.user_data_in)
            ]
            with m.If(self.last_in):
                sync += [
                    transmit_fifo.w_data.eq(assembled_frame),
                    transmit_fifo.w_en.eq(1)
                ]
        with m.Else():
            sync += transmit_fifo.w_en.eq(0)

        transmitted_frame_bits = Array([Signal() for _ in range(256)])
        transmitted_frame = Cat(transmitted_frame_bits)

        nrzi_encoder = NRZIEncoder()
        comb += self.adat_out.eq(nrzi_encoder.nrzi_out)

        transmit_counter = Signal(8)
        adat += [
            nrzi_encoder.data_in.eq(transmitted_frame_bits[transmit_counter]),
            transmit_counter.eq(transmit_counter + 1)
        ]

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
        t.adat_out,
        t.addr_in,
        t.sample_in,
        t.user_data_in,
        t.valid_in,
        t.ready_out,
        t.last_in
    ])

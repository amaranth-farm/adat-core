#!/usr/bin/env python3

from nmigen import *
from nmigen.sim import *
from nmigen.back import verilog, rtlil

class ADATTransmitter(Elaboratable):
    def __init__(self):
        self.clk_in         = Signal()

    def elaborate(self, platform):
        m = Module()
        return m

from random import randrange
from testdata import *

if __name__ == "__main__":
    __name__ = "adat"
    transmitter = ADATTransmitter()

    clk_freq = 120e6
    # 24 bit plus the 6 nibble separator bits for eight channel
    # then 1 separator, 10 sync bits (zero), 1 separator and 4 user bits
    adat_freq = 48000 * ((24 + 6) * 8 + 1 + 10 + 1 + 4)
    clockratio = clk_freq / adat_freq
    sim = Simulator(transmitter)
    #sim.add_clock(1.0/clk_freq)

    def adat_process():
        testdata = one_empty_adat_frame() + generate_sixteen_frames_with_channel_numbers_in_most_significant_nibble_and_sample_numbers_in_sample()
        for bit in testdata[224:512 * 2]:
            yield transmitter.adat_in.eq(bit)
            yield Tick()

    with sim.write_vcd('transmitter-smoke-test.vcd', traces=[transmitter.clk_in]):
        sim.run()
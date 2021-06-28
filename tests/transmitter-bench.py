#!/usr/bin/env python3
#
# Copyright (c) 2021 Hans Baier <hansfbaier@gmail.com>
# SPDX-License-Identifier: CERN-OHL-W-2.0
#
import sys
sys.path.append('.')

from nmigen.sim import Simulator, Tick

from adat.transmitter import ADATTransmitter
from adat.nrzidecoder import NRZIDecoder

def test_with_samplerate(samplerate: int=48000):
    clk_freq = 100e6
    dut = ADATTransmitter()
    adat_freq = NRZIDecoder.adat_freq(samplerate)
    clockratio = clk_freq / adat_freq

    print(f"FPGA clock freq: {clk_freq}")
    print(f"ADAT clock freq: {adat_freq}")
    print(f"FPGA/ADAT freq: {clockratio}")

    sim = Simulator(dut)
    sim.add_clock(1.0/clk_freq, domain="sync")
    sim.add_clock(1.0/adat_freq, domain="adat")

    def write(addr: int, sample: int, last: bool = False):
        if last:
            yield dut.last_in.eq(1)
        yield dut.addr_in.eq(addr)
        yield dut.sample_in.eq(sample)
        yield dut.valid_in.eq(1)
        yield Tick("sync")
        yield dut.valid_in.eq(0)
        if last:
            yield dut.last_in.eq(0)

    def wait(n_cycles: int):
        for _ in range(int(clockratio) * n_cycles):
            yield Tick("sync")

    def sync_process():
        yield Tick("sync")
        yield Tick("sync")
        yield dut.user_data_in.eq(0xf)
        for i in range(4):
            yield from write(i, i)
        for i in range(4):
            yield from write(4 + i, 0xc + i, i == 3)
        yield from wait(300)
        yield dut.user_data_in.eq(0x5)
        for i in range(4):
            yield from write(i, i << 20)
        for i in range(4):
            yield from write(4 + i, (0xc + i) << 20, i == 3)
        yield from wait(900)

    sim.add_sync_process(sync_process, domain="sync")

    with sim.write_vcd(f'transmitter-smoke-test-{str(samplerate)}.vcd'):
        sim.run()

if __name__ == "__main__":
    test_with_samplerate(48000)
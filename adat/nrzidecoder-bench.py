#!/usr/bin/env python3
from nmigen.sim import Simulator, Tick

from nrzidecoder import NRZIDecoder
from testdata import one_empty_adat_frame, sixteen_frames_with_channel_num_msb_and_sample_num, encode_nrzi

def test_with_samplerate(samplerate: int=48000):
    # 24 bit plus the 6 nibble separator bits for eight channel
    # then 1 separator, 10 sync bits (zero), 1 separator and 4 user bits

    CLK_FREQ = 100e6
    dut = NRZIDecoder(CLK_FREQ)
    adat_freq = dut.adat_freq(samplerate)
    clockratio = CLK_FREQ / adat_freq

    sim = Simulator(dut)
    sim.add_clock(1.0/CLK_FREQ, domain="sync")
    sim.add_clock(1.0/adat_freq, domain="adat")
    testdata = encode_nrzi(
        one_empty_adat_frame() +
        sixteen_frames_with_channel_num_msb_and_sample_num())

    print(f"FPGA clock freq: {CLK_FREQ}")
    print(f"ADAT clock freq: {adat_freq}")
    print(f"FPGA/ADAT freq: {clockratio}")

    no_cycles = 10

    def sync_process():
        for _ in range(int(clockratio) * no_cycles):
            yield Tick("sync")

    def adat_process():
        for bit in testdata: #[224:512 * 2]:
            yield dut.nrzi_in.eq(bit)
            yield Tick("adat")

    sim.add_sync_process(sync_process, domain="sync")
    sim.add_sync_process(adat_process, domain="adat")
    with sim.write_vcd(f'nrzi-decoder-bench-{str(samplerate)}.vcd'):
        sim.run()

if __name__ == "__main__":
    test_with_samplerate(48000)
    test_with_samplerate(44100)

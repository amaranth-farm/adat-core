#!/usr/bin/env python3
from random import randrange
from nmigen.sim import Simulator, Tick

from receiver import ADATReceiver
from testdata import one_empty_adat_frame, generate_sixteen_frames_with_channel_numbers_in_most_significant_nibble_and_sample_numbers_in_sample

if __name__ == "__main__":
    receiver = ADATReceiver()

    CLK_FREQ = 120e6
    # 24 bit plus the 6 nibble separator bits for eight channel
    # then 1 separator, 10 sync bits (zero), 1 separator and 4 user bits
    ADAT_FREQ = 48000 * ((24 + 6) * 8 + 1 + 10 + 1 + 4)
    CLOCKRATIO = CLK_FREQ / ADAT_FREQ
    sim = Simulator(receiver)
    sim.add_clock(1.0/CLK_FREQ, domain="sync")
    sim.add_clock(1.0/ADAT_FREQ, domain="adat")
    print(f"clock ratio: {CLOCKRATIO}")

    CYCLES = 10

    def sync_process():
        for _ in range(int(CLOCKRATIO) * CYCLES):
            yield Tick("sync")

    def adat_process():
        testdata = one_empty_adat_frame() + generate_sixteen_frames_with_channel_numbers_in_most_significant_nibble_and_sample_numbers_in_sample()
        for bit in testdata[224:512 * 2]:
            yield receiver.adat_in.eq(bit)
            yield Tick("adat")

    sim.add_sync_process(sync_process, domain="sync")
    sim.add_sync_process(adat_process, domain="adat")
    with sim.write_vcd('receiver-smoke-test.vcd', traces=[receiver.adat_in, receiver.clk_in]):
        sim.run()
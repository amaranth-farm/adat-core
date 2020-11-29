from nmigen import *
from nmigen.sim import *
from nmigen.back import verilog, rtlil
from receiver import ADATReceiver

from random import randrange
from test.testdata import *


def simulation():
    receiver = ADATReceiver()
    #print(verilog.convert(receiver, ports=[receiver.adat_in, receiver.adat_clk_in, receiver.clk_in, receiver.sample]))

    clk_freq = 120e6
    # 24 bit plus the 6 nibble separator bits for eight channel
    # then 1 separator, 10 sync bits (zero), 1 separator and 4 user bits
    adat_freq = 48000 * ((24 + 6) * 8 + 1 + 10 + 1 + 4)
    clockratio = clk_freq / adat_freq
    sim = Simulator(receiver)
    sim.add_clock(1.0/clk_freq, domain="sync")
    sim.add_clock(1.0/adat_freq, domain="adat")
    print(f"clock ratio: {clockratio}")

    cycles = 10

    def sync_process():
        for _ in range(int(clockratio) * cycles):
            yield Tick()

    def adat_process():
        testdata = one_empty_adat_frame() + generate_sixteen_frames_with_channel_numbers_in_most_significant_nibble_and_sample_numbers_in_sample()
        for bit in testdata[224:512 * 2]:
            yield receiver.adat_in.eq(bit)
            yield Tick("adat")

    sim.add_sync_process(sync_process, domain="sync")
    sim.add_sync_process(adat_process, domain="adat")
    with sim.write_vcd('checker-test.vcd', traces=[receiver.adat_clk_in, receiver.adat_in, receiver.clk_in]):
        sim.run()

if __name__ == "__main__":
    simulation()
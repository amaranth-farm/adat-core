#!/usr/bin/env python3
#
# Copyright (c) 2021 Hans Baier <hansfbaier@gmail.com>
# SPDX-License-Identifier: CERN-OHL-W-2.0
#
import sys
sys.path.append(".")

from amaranth.sim import Simulator, Tick

from adat.receiver    import ADATReceiver
from adat.nrzidecoder import NRZIDecoder
from testdata         import one_empty_adat_frame, \
                        sixteen_frames_with_channel_num_msb_and_sample_num, \
                        encode_nrzi, print_frame
from amaranth import Elaboratable, Signal, Module

# This class simplifies testing since the receiver does not use the adat domain.
# Therefore we simulate the input from the adat domain with this wrapper class.
class ADATReceiverTester(Elaboratable):
    def __init__(self, clk_freq: int):
        self.adat_in = Signal()
        self.addr_out = Signal(3)
        self.sample_out = Signal(24)
        self.output_enable = Signal()
        self.user_data_out = Signal(4)
        self.recovered_clock_out = Signal()
        self.synced_out = Signal()
        self.clk_freq = clk_freq

    def elaborate(self, platform) -> Module:
        m = Module()
        m.submodules.receiver = receiver = ADATReceiver(self.clk_freq)

        m.d.adat += receiver.adat_in.eq(self.adat_in)

        m.d.sync += [
            self.addr_out.eq(receiver.addr_out),
            self.sample_out.eq(receiver.sample_out),
            self.output_enable.eq(receiver.output_enable),
            self.user_data_out.eq(receiver.user_data_out),
            self.recovered_clock_out.eq(receiver.recovered_clock_out),
            self.synced_out.eq(receiver.synced_out)
        ]
        return m


def test_with_samplerate(samplerate: int=48000):
    """run adat signal simulation with the given samplerate"""
    # 24 bit plus the 6 nibble separator bits for eight channel
    # then 1 separator, 10 sync bits (zero), 1 separator and 4 user bits

    clk_freq = 100e6
    dut = ADATReceiverTester(clk_freq)
    adat_freq = NRZIDecoder.adat_freq(samplerate)
    clockratio = clk_freq / adat_freq

    sim = Simulator(dut)
    sim.add_clock(1.0/clk_freq, domain="sync")

    sixteen_adat_frames = sixteen_frames_with_channel_num_msb_and_sample_num()

    testdata = \
        one_empty_adat_frame() + \
        sixteen_adat_frames[0:256] + \
        [0] * 64 + \
        sixteen_adat_frames[256:]

    testdata_nrzi = encode_nrzi(testdata)

    print(f"FPGA clock freq: {clk_freq}")
    print(f"ADAT clock freq: {adat_freq}")
    print(f"FPGA/ADAT freq: {clockratio}")

    no_cycles = len(testdata_nrzi) + 500

    # Send the adat stream
    def adat_process():
        for bit in testdata_nrzi:  # [224:512 * 2]:
            yield dut.adat_in.eq(bit)
            yield Tick("adat")

    # Process the adat stream and validate output
    def sync_process():
        # Obtain the output data
        out_data = [[0 for x in range(9)] for y in range(16)] #store userdata in the 9th column
        sample = 0
        for _ in range(int(clockratio) * no_cycles):
            yield Tick("sync")
            if (yield dut.output_enable == 1):
                channel = yield dut.addr_out

                out_data[sample][channel] = yield dut.sample_out

                if (channel == 7):
                    out_data[sample][8] = yield dut.user_data_out
                    sample += 1

        #print(out_data)


        #
        # The receiver needs 2 sync pads before it starts outputting data:
        #   * The first sync pad is needed for the nrzidecoder to sync
        #   * The second sync pad is needed for the receiver to sync
        #   Therefore each time after the connection was lost the first frame will be lost while syncing.
        # In our testdata we loose the initial one_empty_adat_frame and the second sample (#1, count starts with 0)
        #

        sampleno = 0
        for i in range(16):
            if (sampleno == 1): #skip the first frame while the receiver syncs after an interruption
                sampleno += 1
            elif (sampleno == 16): #ensure the data ended as expected
                assert out_data[i] == [0, 0, 0, 0, 0, 0, 0, 0, 0], "Sample {} was: {}".format(sampleno, print_frame(out_data[sampleno]))
            else:
                assert out_data[i] == [((0 << 20) | sampleno), ((1 << 20) | sampleno), ((2 << 20) | sampleno),
                                       ((3 << 20) | sampleno), ((4 << 20) | sampleno), ((5 << 20) | sampleno),
                                       ((6 << 20) | sampleno), ((7 << 20) | sampleno), 0b0101]\
                    , "Sample #{} was: {}".format(sampleno, print_frame(out_data[sampleno]))
            sampleno += 1

        print("Success!")

    sim.add_sync_process(sync_process, domain="sync")
    with sim.write_vcd(f'receiver-smoke-test-{str(samplerate)}.vcd'):
        sim.run()

if __name__ == "__main__":
    test_with_samplerate(48000)
    test_with_samplerate(44100)

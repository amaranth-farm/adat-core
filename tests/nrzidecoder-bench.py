#!/usr/bin/env python3
import sys
from amaranth.hdl.cd import ClockDomain
sys.path.append('.')
from amaranth.sim import Simulator, Tick
from amaranth import Elaboratable, Signal, Module

from adat.nrzidecoder import NRZIDecoder
from testdata    import one_empty_adat_frame, \
                        sixteen_frames_with_channel_num_msb_and_sample_num, \
                        encode_nrzi, validate_output

# This class simplifies testing since the nrzidecoder does not use the adat
# domain. Therefore we simulate the input from the adat domain with this wrapper class.
class NRZIDecoderTester(Elaboratable):
    def __init__(self, clk_freq: int):
        self.nrzi_in = Signal()
        self.invalid_frame_in = Signal()
        self.data_out = Signal()
        self.data_out_en = Signal()
        self.recovered_clock_out = Signal()
        self.clk_freq = clk_freq

    def elaborate(self, platform) -> Module:
        m = Module()
        m.submodules.nrzidecoder = nrzidecoder = NRZIDecoder(self.clk_freq)
        m.d.adat += [
            nrzidecoder.nrzi_in.eq(self.nrzi_in),
            nrzidecoder.invalid_frame_in.eq(self.invalid_frame_in)
        ]
        m.d.sync += [
            self.data_out.eq(nrzidecoder.data_out),
            self.data_out_en.eq(nrzidecoder.data_out_en),
            self.recovered_clock_out.eq(nrzidecoder.recovered_clock_out)
        ]
        return m

def test_with_samplerate(samplerate: int=48000):
    """run adat signal simulation with the given samplerate"""
    # 24 bit plus the 6 nibble separator bits for eight channel
    # then 1 separator, 10 sync bits (zero), 1 separator and 4 user bits

    clk_freq = 100e6
    dut = NRZIDecoderTester(clk_freq)
    adat_freq = NRZIDecoder.adat_freq(samplerate)
    clockratio = clk_freq / adat_freq


    sim = Simulator(dut)
    sim.add_clock(1.0/clk_freq, domain="sync")
    sim.add_clock(1.0/adat_freq, domain="adat")

    print(f"FPGA clock freq: {clk_freq}")
    print(f"ADAT clock freq: {adat_freq}")
    print(f"FPGA/ADAT freq: {clockratio}")

    sixteen_adat_frames = sixteen_frames_with_channel_num_msb_and_sample_num()
    interrupted_adat_stream = [0] * 64

    testdata = one_empty_adat_frame() + \
        sixteen_adat_frames[0:256] + \
        interrupted_adat_stream + \
        sixteen_adat_frames[256:]

    testdata_nrzi = encode_nrzi(testdata)

    no_cycles = len(testdata_nrzi)

    # Send the adat stream
    def adat_process():
        bitcount :int = 0
        for bit in testdata_nrzi: #[224:512 * 2]:
            if (bitcount == 4 * 256 + 64):
                yield dut.invalid_frame_in.eq(1)
                yield Tick("adat")
                yield dut.invalid_frame_in.eq(0)
                for _ in range(20):
                    yield Tick("adat")
            else:
                yield dut.invalid_frame_in.eq(0)

            yield dut.nrzi_in.eq(bit)
            yield Tick("adat")
            bitcount += 1

    # Process the adat stream and validate output
    def sync_process():
        # Obtain the output data
        out_data = []
        for _ in range(int(clockratio) * no_cycles):
            yield Tick("sync")
            if (yield dut.data_out_en == 1):
                bit = yield dut.data_out
                yield out_data.append(bit)

        #
        # Validate output
        #

        # omit a 1 at the end of the sync pad
        out_data = out_data[1:]

        # Whenever the state machine switches from SYNC to DECODE we need to omit the first 11 sync bits
        validate_output(out_data[:256 - 12], one_empty_adat_frame()[12:256])
        out_data = out_data[256-12:]

        validate_output(out_data[:256], sixteen_adat_frames[:256])
        out_data = out_data[256:]

        # now the adat stream was interrupted, it continues to output zeroes, until it enters the SYNC state
        validate_output(out_data[:10], interrupted_adat_stream[:10])
        out_data = out_data[10:]

        # followed by 2 well formed adat frames

        # omit the first 11 sync bits
        validate_output(out_data[:256 - 12], sixteen_adat_frames[256 + 12:2 * 256])
        out_data = out_data[256 - 12:]

        validate_output(out_data[:256], sixteen_adat_frames[2 * 256:3 * 256])
        out_data = out_data[256:]

        # followed by one invalid frame - the state machine SYNCs again

        # followed by 13 well-formed frames

        # omit the first 11 sync bits
        validate_output(out_data[:256 - 12], sixteen_adat_frames[3 * 256 + 12:4 * 256])
        out_data = out_data[256-12:]

        for i in range(4, 16):
            validate_output(out_data[:256], sixteen_adat_frames[i * 256:(i + 1) * 256])
            out_data = out_data[256:]

        print("Success!")


    sim.add_sync_process(sync_process, domain="sync")
    sim.add_sync_process(adat_process, domain="adat")
    with sim.write_vcd(f'nrzi-decoder-bench-{str(samplerate)}.vcd'):
        sim.run()


if __name__ == "__main__":
    test_with_samplerate(48000)
    test_with_samplerate(44100)

#!/usr/bin/env python3

from nmigen import *
from nmigen.sim import *
from nmigen.back import verilog, rtlil

class ADATReceiver(Elaboratable):
    def __init__(self):
        self.adat_in        = Signal()
        self.adat_clk_in    = Signal()
        self.clk_in         = Signal()

    def setup_clockdomains(self, m):
        cd_adat = ClockDomain(reset_less=True)
        cd_adat.clk = self.adat_clk_in
        cd_sync = ClockDomain()       
        cd_sync.clk = self.clk_in
        m.domains.adat = cd_adat
        m.domains.sync = cd_sync

    def elaborate(self, platform):
        m = Module()
        self.setup_clockdomains(m)

        bitcounter = Signal(32)
        max_bitcounter = Signal(32)
        adat_syncbitstime = Signal(32)
        adat_nibbletime = Signal(32)
        last_max = Signal(32)
        frame_start = Signal()

        m.d.comb += adat_nibbletime.eq(adat_syncbitstime >> 1)

        with m.If(~self.adat_in):
            m.d.sync += bitcounter.eq(bitcounter + 1)
            with m.If(bitcounter > max_bitcounter):
                m.d.sync += [
                    max_bitcounter.eq(bitcounter)
                ]
        with m.Else(): # adat_in is 1
            # if max_bitcounter is greater than 3/4 of its last value, we have a frame start 
            with m.If(max_bitcounter > 50):
                with m.If(max_bitcounter > ((last_max << 1) + last_max) >> 2):                
                    m.d.sync += [
                        frame_start.eq(1),
                        adat_syncbitstime.eq(max_bitcounter)
                    ]
            with m.Else():
                m.d.sync += [
                    max_bitcounter.eq(bitcounter),
                    frame_start.eq(0)
                ]

            m.d.sync += [
                last_max.eq(max_bitcounter),
                bitcounter.eq(0),
            ]

        
        with m.FSM() as fsm:
            with m.State("SYNC"):
                with m.If(frame_start):
                    m.d.sync += frame_start.eq(0)
                    m.next = "READ_FRAME"

            with m.State("READ_FRAME"):
                with m.If(bitcounter > max_bitcounter):
                    m.d.sync += [
                        max_bitcounter.eq(bitcounter)
                    ]
                    m.next = "SYNC"
                    
        return m

from random import randrange
from test.testdata import *


if __name__ == "__main__":
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
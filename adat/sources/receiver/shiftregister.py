#!/usr/bin/env python3

from nmigen import *
from nmigen.sim import *
from nmigen.back import verilog, rtlil

class ShiftRegister(Elaboratable):
    def __init__(self, depth):
        self.rst_in = Signal()
        self.enable_in = Signal()
        self.bit_in = Signal()
        self.value_out = Signal(depth)

    def elaborate(self, platform):
        m = Module()
        
        with m.If(self.enable_in):
            m.d.sync += self.value_out.eq((self.value_out << 1) | self.bit_in)

        return m

if __name__ == "__main__":
    dut = ShiftRegister(24)
    sim = Simulator(dut)

    def sync_process():
        yield dut.enable_in.eq(0)
        yield Tick()
        yield dut.bit_in.eq(1)
        yield Tick()
        yield dut.bit_in.eq(0)
        yield Tick()
        yield dut.bit_in.eq(1)
        yield Tick()
        yield dut.bit_in.eq(1)
        yield Tick()
        yield dut.bit_in.eq(0)
        yield Tick()
        yield dut.bit_in.eq(1)
        yield dut.enable_in.eq(1)
        yield Tick()
        yield dut.enable_in.eq(0)
        yield Tick()
        yield dut.enable_in.eq(1)
        yield Tick()
        yield dut.bit_in.eq(0)
        yield Tick()
        yield dut.bit_in.eq(1)
        yield Tick()
        yield dut.bit_in.eq(1)
        yield Tick()
        yield dut.bit_in.eq(0)
        yield Tick()
        yield dut.bit_in.eq(1)
        yield Tick()
        yield dut.enable_in.eq(0)
        yield Tick()
        yield Tick()
        yield Tick()
        yield dut.enable_in.eq(1)
        for _ in range(13):
            yield dut.bit_in.eq(1)
            yield Tick()
            yield dut.bit_in.eq(0)
            yield Tick()
            yield dut.bit_in.eq(1)
            yield Tick()
            yield dut.bit_in.eq(0)
            yield Tick()

    sim.add_sync_process(sync_process)
    sim.add_clock(1e-6)
    with sim.write_vcd('shift-register.vcd', traces=[dut.enable_in, dut.value_out, dut.bit_in]):
        sim.run()
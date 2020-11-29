#!/usr/bin/env python3

from nmigen import *
from nmigen.sim import *
from nmigen.back import verilog, rtlil

class DividingCounter(Elaboratable):
    def __init__(self, divisor, width):
        self.clk_in = Signal()
        self.active_in = Signal()
        self.counter_out = Signal(width)
        self.divided_counter_out = Signal(width)
        self.dividable_out = Signal()
        self.divisor = divisor

    def elaborate(self, platform):
        m = Module()

        dividing_cycle_counter = Signal(range(0, self.divisor))

        with m.If(self.active_in):
            with m.If(dividing_cycle_counter == self.divisor - 1):
                m.d.sync += [
                    dividing_cycle_counter.eq(0),
                    self.divided_counter_out.eq(self.divided_counter_out + 1),
                    self.dividable_out.eq(1)
                ]

            with m.Else():
                m.d.sync += [
                    self.dividable_out.eq(0),
                    dividing_cycle_counter.eq(dividing_cycle_counter + 1)
                ]

            # when the main counter wraps around to zero, the dividing counter needs to reset too
            with m.If(self.counter_out == (2 ** self.counter_out.width) - 1):
                m.d.sync += dividing_cycle_counter.eq(0)

            m.d.sync += [
                self.counter_out.eq(self.counter_out + 1),
            ]

        return m
print(__name__)

if __name__ == "__main__":
    dut = DividingCounter(5, 5)
    #print(verilog.convert(dut, ports=[dut.divided_counter_out, dut.dividable_out]))
    sim = Simulator(dut)

    def sync_process():
        for _ in range(0, 5):
            yield dut.active_in.eq(0)
            yield Tick()

        for _ in range(0, 50):
            yield dut.active_in.eq(1)
            yield Tick()

        yield dut.active_in.eq(0)
        yield Tick()
        yield Tick()
        yield Tick()
        return

    sim.add_sync_process(sync_process)
    sim.add_clock(1e-6)
    with sim.write_vcd('dividing-counter.vcd', traces=[dut.active_in, dut.counter_out, dut.dividable_out, dut.divided_counter_out]):
        sim.run()
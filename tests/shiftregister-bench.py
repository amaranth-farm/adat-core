#!/usr/bin/env python3
import sys
sys.path.append('.')

from nmigen.sim import Simulator, Tick
from adat.shiftregister import InputShiftRegister, OutputShiftRegister

def simulate_input_shiftregister():
    dut = InputShiftRegister(8)
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
    with sim.write_vcd('shift-register-in.vcd', traces=[dut.enable_in, dut.value_out, dut.bit_in]):
        sim.run()

def simulate_output_shiftregister():
    dut = OutputShiftRegister(8, rotate=True)
    sim = Simulator(dut)

    def sync_process():
        yield dut.enable_in.eq(0)
        yield dut.value_in.eq(0xaa)
        yield dut.we_in.eq(1)
        yield Tick()
        yield dut.we_in.eq(0)
        yield Tick()
        yield Tick()
        yield dut.enable_in.eq(1)
        yield Tick()
        yield Tick()
        yield Tick()
        yield Tick()
        yield Tick()
        yield dut.enable_in.eq(0)
        yield Tick()
        yield Tick()
        yield Tick()
        yield dut.enable_in.eq(1)
        yield Tick()
        yield Tick()
        yield dut.value_in.eq(0x55)
        yield dut.we_in.eq(1)
        yield Tick()
        yield dut.we_in.eq(0)
        yield Tick()
        yield Tick()
        yield Tick()
        yield dut.we_in.eq(1)
        yield dut.value_in.eq(0b10000000)
        yield Tick()
        yield dut.we_in.eq(0)
        yield Tick()
        yield Tick()
        yield Tick()
        yield Tick()
        yield Tick()
        yield Tick()
        yield Tick()
        yield Tick()
        yield Tick()
        yield Tick()
        yield Tick()
        yield Tick()
        yield Tick()
        yield dut.we_in.eq(1)
        yield dut.value_in.eq(0)
        yield Tick()
        yield dut.we_in.eq(0)
        yield Tick()
        yield Tick()
        yield Tick()

    sim.add_sync_process(sync_process)
    sim.add_clock(1e-6)
    with sim.write_vcd('shift-register-out.vcd', traces=[dut.enable_in, dut.we_in, dut.bit_out, dut.value_in]):
        sim.run()

if __name__ == "__main__":
    simulate_input_shiftregister()
    simulate_output_shiftregister()

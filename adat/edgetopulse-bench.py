#!/usr/bin/env python3
from nmigen.sim import Simulator, Tick
from edgetopulse import EdgeToPulse

if __name__ == "__main__":
    dut = EdgeToPulse()
    sim = Simulator(dut)

    def sync_process():
        yield dut.edge_in.eq(0)
        yield Tick()
        yield dut.edge_in.eq(0)
        yield Tick()
        yield dut.edge_in.eq(0)
        yield Tick()
        yield dut.edge_in.eq(1)
        yield Tick()
        yield Tick()
        yield Tick()
        yield Tick()
        yield Tick()
        yield dut.edge_in.eq(0)
        yield Tick()
        yield Tick()
        yield Tick()
        yield Tick()
        yield Tick()
        yield dut.edge_in.eq(1)
        yield Tick()
        yield Tick()
        yield dut.edge_in.eq(0)
        yield Tick()
        yield Tick()
        yield Tick()
        yield Tick()
        yield dut.edge_in.eq(1)
        yield Tick()
        yield dut.edge_in.eq(0)
        yield Tick()
        yield dut.edge_in.eq(1)
        yield Tick()
        yield Tick()
        yield dut.reset_in.eq(1)
        yield Tick()
        yield Tick()
        yield dut.reset_in.eq(0)
        yield Tick()
        yield Tick()
        yield Tick()
        yield dut.edge_in.eq(1)
        yield Tick()
        yield dut.edge_in.eq(0)
        yield Tick()
        yield Tick()
        yield dut.edge_in.eq(1)
        yield Tick()
        yield dut.edge_in.eq(0)
        yield Tick()
        yield Tick()
        yield Tick()

    sim.add_sync_process(sync_process)
    sim.add_clock(1e-6)
    with sim.write_vcd('edgetopulse.vcd', traces=[dut.edge_in, dut.pulse_out, dut.reset_in]):
        sim.run()

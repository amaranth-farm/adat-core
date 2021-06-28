#!/usr/bin/env python3
#
# Copyright (c) 2021 Hans Baier <hansfbaier@gmail.com>
# SPDX-License-Identifier: CERN-OHL-W-2.0
#
import sys
sys.path.append('.')

from nmigen.sim import Simulator, Tick
from adat.edgetopulse import EdgeToPulse

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
    with sim.write_vcd('edgetopulse.vcd', traces=[dut.edge_in, dut.pulse_out]):
        sim.run()

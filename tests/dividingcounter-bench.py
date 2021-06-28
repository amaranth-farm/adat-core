#!/usr/bin/env python3
#
# Copyright (c) 2021 Hans Baier <hansfbaier@gmail.com>
# SPDX-License-Identifier: CERN-OHL-W-2.0
#
import sys
sys.path.append('.')

from nmigen.sim import Simulator, Tick

from adat.dividingcounter import DividingCounter

if __name__ == "__main__":
    dut = DividingCounter(5, 5)
    sim = Simulator(dut)

    def sync_process():
        yield dut.active_in.eq(0)
        for _ in range(0, 5):
            yield Tick()

        yield dut.active_in.eq(1)
        for _ in range(0, 50):
            yield Tick()

        yield dut.reset_in.eq(1)
        yield Tick()
        yield Tick()
        yield Tick()
        yield Tick()
        yield Tick()
        yield Tick()
        yield Tick()
        yield dut.reset_in.eq(0)

        for _ in range(0, 20):
            yield Tick()

        yield dut.active_in.eq(0)
        yield Tick()
        yield Tick()
        yield Tick()
        return

    sim.add_sync_process(sync_process)
    sim.add_clock(1e-6)
    with sim.write_vcd('dividing-counter.vcd',
        traces=[
            dut.active_in,
            dut.counter_out,
            dut.dividable_out,
            dut.divided_counter_out]):
        sim.run()

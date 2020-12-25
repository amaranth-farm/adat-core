#!/usr/bin/env python3
"""converts a rising edge to a single clock pulse"""
from nmigen     import Elaboratable, Signal, Module, ClockDomain
from nmigen.cli import main

class EdgeToPulse(Elaboratable):
    """
        each rising edge of the signal edge_in will be
        converted to a single clock pulse on pulse_out
    """
    def __init__(self):
        self.reset_in         = Signal()
        self.edge_in          = Signal()
        self.pulse_out        = Signal()

    def elaborate(self, platform) -> Module:
        m = Module()

        edge_last = Signal()

        with m.If(self.reset_in):
            m.d.sync += edge_last.eq(0)
            m.d.comb += self.pulse_out.eq(0)

        with m.Else():
            m.d.sync += edge_last.eq(self.edge_in)
            with m.If(self.edge_in & ~edge_last):
                m.d.comb += self.pulse_out.eq(1)
            with m.Else():
                m.d.comb += self.pulse_out.eq(0)

        return m

if __name__ == "__main__":
    m = EdgeToPulse()
    main(m, ports=[m.edge_in, m.pulse_out, m.reset_in])

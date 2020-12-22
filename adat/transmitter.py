#!/usr/bin/env python3

from nmigen import *
from nmigen.sim import *
from nmigen.back import verilog, rtlil

class ADATTransmitter(Elaboratable):
    def __init__(self):
        self.clk_in         = Signal()

    def elaborate(self, platform) -> Module:
        m = Module()
        return m
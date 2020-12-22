#!/usr/bin/env python3
from nmigen import Elaboratable, Signal, Module

class ShiftRegister(Elaboratable):
    def __init__(self, depth):
        self.rst_in = Signal()
        self.enable_in = Signal()
        self.bit_in = Signal()
        self.value_out = Signal(depth)

    def elaborate(self, platform) -> Module:
        m = Module()

        with m.If(self.enable_in):
            m.d.sync += self.value_out.eq((self.value_out << 1) | self.bit_in)

        return m

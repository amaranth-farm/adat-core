#!/usr/bin/env python3
from nmigen import Elaboratable, Signal, Module
from nmigen.cli import main

class DividingCounter(Elaboratable):
    def __init__(self, divisor, width):
        self.reset_in            = Signal()
        self.active_in           = Signal()
        self.counter_out         = Signal(width)
        self.divided_counter_out = Signal(width)
        self.dividable_out       = Signal()
        self.divisor = divisor

    def elaborate(self, platform) -> Module:
        m = Module()

        dividing_cycle_counter = Signal(range(0, self.divisor))

        with m.If(self.reset_in):
            m.d.sync += [
                self.counter_out.eq(0),
                self.divided_counter_out.eq(0),
                dividing_cycle_counter.eq(0)
            ]
        with m.Else():
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

                # when the main counter wraps around to zero, the dividing counter needs reset too
                with m.If(self.counter_out == (2 ** self.counter_out.width) - 1):
                    m.d.sync += dividing_cycle_counter.eq(0)

                m.d.sync += [
                    self.counter_out.eq(self.counter_out + 1),
                ]

        return m

if __name__ == "__main__":
    m = DividingCounter()
    main(m, name="dividing_counter", ports=[m.reset_in, m.active_in, m.counter_out, m.divided_counter_out, m.dividable_out])
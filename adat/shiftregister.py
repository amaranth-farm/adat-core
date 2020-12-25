#!/usr/bin/env python3
"""
    synchronous shift register: bits appear in the output at the next
                                clock cycle
"""
from nmigen import Elaboratable, Signal, Module
from nmigen.cli import main_parser, main_runner

class ShiftRegister(Elaboratable):
    def __init__(self, depth):
        self.enable_in = Signal()
        self.bit_in    = Signal()
        self.value_out = Signal(depth)

    def elaborate(self, platform) -> Module:
        m = Module()

        with m.If(self.enable_in):
            m.d.sync += self.value_out.eq((self.value_out << 1) | self.bit_in)

        return m

if __name__ == "__main__":
    parser = main_parser()
    parser.add_argument("-d", "--depth", dest="depth",
        metavar="DEPTH", type=int, default=8,
        help="set depth of shiftregister to DEPTH  (default: %(default)s)")
    args = parser.parse_args()
    depth = args.depth
    m = ShiftRegister(depth)
    main_runner(parser, args, m, name="ShiftRegister", ports=[m.enable_in, m.bit_in, m.value_out])

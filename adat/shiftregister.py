#!/usr/bin/env python3
"""
    synchronous shift register: bits appear in the output at the next
                                clock cycle
"""
from nmigen import Elaboratable, Signal, Module
from nmigen.cli import main_parser, main_runner

# pylint: disable=too-few-public-methods
class ShiftRegister(Elaboratable):                                                                                
    """shift register with given depth in bits"""
    def __init__(self, depth):
        self.enable_in = Signal()
        self.bit_in    = Signal()
        self.value_out = Signal(depth)

    def elaborate(self, platform) -> Module:
        """build the module"""
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
    reg_depth = args.depth
    module = ShiftRegister(reg_depth)
    main_runner(parser, args, module, name="ShiftRegister",
                ports=[module.enable_in, module.bit_in, module.value_out])

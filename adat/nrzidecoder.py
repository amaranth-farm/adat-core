#!/usr/bin/env python3

from nmigen         import Elaboratable, Signal, Module
from nmigen.lib.cdc import FFSynchronizer
from nmigen.cli     import main

class NRZIDecoder(Elaboratable):
    def __init__(self):
        self.nrzi_in = Signal()
        self.data_out = Signal()

    def elaborate(self, platform) -> Module:
        m = Module()
        nrzi = Signal()
        m.submodules += FFSynchronizer(self.nrzi_in, nrzi)

        return m
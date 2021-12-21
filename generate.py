#!/usr/bin/env python3
#
# Copyright (c) 2021 Hans Baier <hansfbaier@gmail.com>
# SPDX-License-Identifier: CERN-OHL-W-2.0
#
import sys
from amaranth.cli import main
from adat import *

if __name__ == "__main__":
    modulename = sys.argv[1]
    sys.argv[1] = "generate"

    if modulename == "nrzidecoder":
        module = NRZIDecoder(100e6)
        main(module, name="nrzi_decoder", ports=[module.nrzi_in, module.data_out])
    elif modulename == "receiver":
        r = ADATReceiver(100e6)
        main(r, name="adat_receiver", ports=[
            r.clk, r.reset_in,
            r.adat_in, r.addr_out,
            r.sample_out, r.output_enable, r.user_data_out])
    elif modulename == "transmitter":
        t = ADATTransmitter()
        main(t, name="adat_transmitter", ports=[
            t.addr_in,
            t.sample_in,
            t.user_data_in,
            t.valid_in,
            t.ready_out,
            t.last_in,
            t.adat_out,
        ])
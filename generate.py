#!/usr/bin/env python3
import sys
from nmigen.cli import main
from adat import *
from adat.shiftregister import *

if __name__ == "__main__":
    modulename = sys.argv[1]
    sys.argv[1] = "generate"

    if modulename == "nrzidecoder":
        module = NRZIDecoder(100e6)
        main(module, name="nrzi_decoder", ports=[module.nrzi_in, module.data_out])
    elif modulename == "dividingcounter":
        module = DividingCounter(10, 16)
        main(module, name="dividing_counter", ports=module.ports)
    elif modulename == "edgetopulse":
        m = EdgeToPulse()
        main(m, name="edge_to_pulse", ports=[m.edge_in, m.pulse_out])
    elif modulename == "nrziencoder":
        module = NRZIEncoder()
        main(module, name="nrzi_encoder", ports=[module.data_in, module.nrzi_out])
    elif modulename == "receiver":
        r = ADATReceiver(100e6)
        main(r, name="adat_receiver", ports=[
            r.clk, r.reset_in,
            r.adat_in, r.addr_out,
            r.sample_out, r.output_enable, r.user_data_out])
    elif modulename == "shiftregister":
        reg_depth = int(sys.argv[2])
        del(sys.argv[2])
        module = InputShiftRegister(reg_depth)
        main(module, name="InputShiftRegister",
             ports=[module.enable_in, module.bit_in, module.value_out])
        module = OutputShiftRegister(reg_depth)
        main(module, name="OutputShiftRegister",
             ports=[module.enable_in, module.we_in, module.bit_out, module.value_in])
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

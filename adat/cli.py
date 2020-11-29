import argparse
import warnings
from nmigen import cli

def main():
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument("--reset-addr",
            type=lambda s: int(s, 16), default="0x00000000",
            help="reset vector address")

    parser.add_argument("--with-rvfi",
            default=False, action="store_true",
            help="enable the riscv-formal interface")

    icache_group = parser.add_argument_group("icache options")
    icache_group.add_argument("--icache-nways",
            type=int, choices=[1, 2], default=1,
            help="number of ways")
    icache_group.add_argument("--icache-nlines",
            type=int, default=32,
            help="number of lines")

    cli.main_parser(parser)

    args = parser.parse_args()

    cpu =   (args.reset_addr,
            args.with_icache, args.icache_nways, args.icache_nlines, args.icache_nwords,
            args.icache_base, args.icache_limit,
            args.with_dcache, args.dcache_nways, args.dcache_nlines, args.dcache_nwords,
            args.dcache_base, args.dcache_limit,
            args.with_muldiv,
            args.with_debug,
            args.with_trigger, args.nb_triggers,
            args.with_rvfi)

    ports = [
        cpu.external_interrupt, cpu.timer_interrupt, cpu.software_interrupt,
        cpu.ibus.ack, cpu.ibus.adr, cpu.ibus.bte, cpu.ibus.cti, cpu.ibus.cyc, cpu.ibus.dat_r,
        cpu.ibus.dat_w, cpu.ibus.sel, cpu.ibus.stb, cpu.ibus.we, cpu.ibus.err,
        cpu.dbus.ack, cpu.dbus.adr, cpu.dbus.bte, cpu.dbus.cti, cpu.dbus.cyc, cpu.dbus.dat_r,
        cpu.dbus.dat_w, cpu.dbus.sel, cpu.dbus.stb, cpu.dbus.we, cpu.dbus.err
    ]

    if args.with_debug:
        ports += [cpu.jtag.tck, cpu.jtag.tdi, cpu.jtag.tdo, cpu.jtag.tms]

    if args.with_rvfi:
        ports += [
            cpu.rvfi.valid, cpu.rvfi.order, cpu.rvfi.insn, cpu.rvfi.trap, cpu.rvfi.halt,
            cpu.rvfi.intr, cpu.rvfi.mode, cpu.rvfi.ixl, cpu.rvfi.rs1_addr, cpu.rvfi.rs2_addr,
            cpu.rvfi.rs1_rdata, cpu.rvfi.rs2_rdata, cpu.rvfi.rd_addr, cpu.rvfi.rd_wdata,
            cpu.rvfi.pc_rdata, cpu.rvfi.pc_wdata, cpu.rvfi.mem_addr, cpu.rvfi.mem_rmask,
            cpu.rvfi.mem_wmask, cpu.rvfi.mem_rdata, cpu.rvfi.mem_wdata
        ]

    cli.main_runner(parser, args, cpu, name="minerva_cpu", ports=ports)


if __name__ == "__main__":
    main()

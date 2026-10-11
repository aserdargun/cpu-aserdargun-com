set platform $::env(CPU_PLATFORM)
set out $::env(CPU_PHYSICAL_OUT)
set_thread_count 4
read_lef $platform/lef/sky130_fd_sc_hd.tlef
read_lef $platform/lef/sky130_fd_sc_hd_merged.lef
read_liberty $platform/lib/sky130_fd_sc_hd__tt_025C_1v80.lib
read_db $out/routed.odb
read_sdc $out/routed.sdc
extract_parasitics -ext_model_file $platform/rcx_patterns.rules
write_spef $out/routed.spef
report_worst_slack -max
report_tns
report_checks -path_delay max -format full_clock_expanded -digits 4
report_wire_length -net * -detailed_route -file $out/wire-length.rpt
check_antennas -report_violating_nets -report_file $out/antenna.rpt
exit

set platform $::env(CPU_PLATFORM)
set out $::env(CPU_PHYSICAL_OUT)
set_thread_count 4
read_liberty $platform/lib/sky130_fd_sc_hd__tt_025C_1v80.lib
read_db $out/global.odb
create_clock -name core_clock -period 100 [get_ports clk]
set_input_delay 5 -clock core_clock [get_ports {reset i_ready i_data* i_fault d_ready d_rdata* d_fault}]
set_output_delay 5 -clock core_clock [all_outputs]
set_driving_cell -lib_cell sky130_fd_sc_hd__buf_2 [all_inputs]
set_load 0.01 [all_outputs]
set_propagated_clock [all_clocks]
foreach net [[ord::get_db_block] getNets] {
 if {[llength [$net getITerms]] == 0 && [llength [$net getBTerms]] == 0} {odb::dbNet_destroy $net}
}
detailed_route -min_access_points 1 -output_drc $out/drc.rpt -output_maze $out/maze.log -verbose 1
write_def $out/routed.def
write_db $out/routed.odb
write_verilog $out/routed.v
write_sdc $out/routed.sdc
exit

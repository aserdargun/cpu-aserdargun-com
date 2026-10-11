set platform $::env(CPU_PLATFORM)
set out $::env(CPU_PHYSICAL_OUT)
set_thread_count 4
read_lef $platform/lef/sky130_fd_sc_hd.tlef
read_lef $platform/lef/sky130_fd_sc_hd_merged.lef
read_liberty $platform/lib/sky130_fd_sc_hd__tt_025C_1v80.lib
read_verilog $out/mapped.v
link_design physical_core
initialize_floorplan -utilization 30 -aspect_ratio 1 -core_space 20 -site unithd
source $platform/make_tracks.tcl
source $platform/setRC.tcl
create_clock -name core_clock -period 100 [get_ports clk]
set_input_delay 5 -clock core_clock [get_ports {reset i_ready i_data* i_fault d_ready d_rdata* d_fault}]
set_output_delay 5 -clock core_clock [all_outputs]
set_driving_cell -lib_cell sky130_fd_sc_hd__buf_2 [all_inputs]
set_load 0.01 [all_outputs]
place_pins -hor_layers met3 -ver_layers met2
tapcell -distance 14 -tapcell_master sky130_fd_sc_hd__tapvpwrvgnd_1
source $platform/pdn.tcl
pdngen
global_placement -density 0.45
repair_tie_fanout -separation 1 sky130_fd_sc_hd__conb_1/HI
repair_tie_fanout -separation 1 sky130_fd_sc_hd__conb_1/LO
estimate_parasitics -placement
repair_design
detailed_placement
clock_tree_synthesis -root_buf sky130_fd_sc_hd__clkbuf_16 -buf_list {sky130_fd_sc_hd__clkbuf_2 sky130_fd_sc_hd__clkbuf_4 sky130_fd_sc_hd__clkbuf_8} -sink_clustering_enable
repair_clock_nets
detailed_placement
set_propagated_clock [all_clocks]
check_placement -verbose
write_db $out/placed.odb
write_def $out/placed.def
set_routing_layers -signal met1-met5 -clock met3-met5
set_global_routing_layer_adjustment met1-met5 0.2
global_route -guide_file $out/route.guide -verbose
estimate_parasitics -global_routing
report_design_area
report_worst_slack -max
report_tns
report_checks -path_delay max -format full_clock_expanded -digits 4
write_db $out/global.odb
write_def $out/global.def
foreach net [[ord::get_db_block] getNets] {
 if {[llength [$net getITerms]] == 0 && [llength [$net getBTerms]] == 0} {odb::dbNet_destroy $net}
}
detailed_route -min_access_points 1 -output_drc $out/drc.rpt -output_maze $out/maze.log -verbose 1
write_def $out/routed.def
write_db $out/routed.odb
write_verilog $out/routed.v
write_sdc $out/routed.sdc
exit

# Third-party provenance / Üçüncü taraf kaynakları

The CPU RTL, simulator adapters, UI and geometry exporters are original project code. This document identifies the external inputs used to produce the lab. Exact revisions, source hashes and binary hashes are recorded in generated manifests.

| Input | Provenance | License / role |
|---|---|---|
| RISC-V ISA | [official specification](https://docs.riscv.org/reference/isa/v20260120/unpriv/rv32.html) | Architectural reference; RV32I/M semantics |
| Spike | `riscv-software-src/riscv-isa-sim`, commit `17e8a69fb75546dea445cfc0fb78769d2510f339` | BSD-3-Clause; independent ISA reference, local tooling |
| riscv-formal | `YosysHQ/riscv-formal`, commit `c992aa61fdfe0846c5ed90324c596202a1c69b76` | ISC; bounded instruction checks |
| SymbiYosys | `YosysHQ/sby`, commit `b1a1e98cba941ec8433f8dc27f416cd7bb7f14be` | ISC; formal runner |
| ORFS | `The-OpenROAD-Project/OpenROAD-flow-scripts`, commit `3451ca1f56902a49baf50bb8eba345eb709cf9c8` | [BSD-3-Clause scripts license](licenses/ORFS-BSD-3-Clause.txt); platform integration |
| SKY130 HD Liberty / LEF / GDS | ORFS `flow/platforms/sky130hd`; upstream `google/skywater-pdk-libs-sky130_fd_sc_hd` | [Apache-2.0](licenses/SKY130-HD-Apache-2.0.txt); standard-cell geometry and cell functions |
| OpenROAD | official `Precision-Innovations/OpenROAD` release `2.0-17598-ga008522d8` | BSD-3-Clause engine plus its bundled dependencies; local x86 Linux tool |
| KLayout | Ubuntu package inside dedicated VM | GPL-2.0-or-later; GDS export/read-back tooling |
| ORFS SKY130 DRC runset | platform `drc/sky130hd.lydrc`, header credits Antoine Masse | GPLv3 runset, local tool; BEOL/OFFGRID checks, FEOL disabled by default |
| ngspice | Homebrew ngspice 47 | BSD-family licenses; standalone educational transistor circuits |
| Verilator | Homebrew 5.052 | LGPL-3.0 / Artistic-2.0 dual licensing; generated simulation model runtime |
| Emscripten / LLVM | Homebrew Emscripten 6.0.10 | MIT / LLVM Apache-2.0 with exception; native model compiled to WASM |
| React / Three / R3F / drei / idb-keyval | `package-lock.json` | MIT; browser runtime |
| Lucide icons | `lucide-react` npm | ISC |
| DM Sans / IBM Plex Mono | files under `public/fonts` | SIL OFL-1.1, full license texts alongside the fonts |

The LEVEL=1 MOS parameters are explicit educational parameters in `scripts/spice.py`. They are not SKY130 transistor models. The 3D mask elevations are illustrative; native GDS supplies XY geometry and layer IDs. Routed GDS and DRC/STA results are engineering artifacts, not fabrication signoff.

Türkçe: Lisans metinleri, kaynak revizyonları ve dosya özetleri saklanır. Hücre geometrisi SKY130 kütüphanesinden, gerçek sinyal değerleri ayrı kapı simülasyonundan gelir. Örnek MOS devrelerinin analog modeli bu kütüphanenin proses modeli değildir.

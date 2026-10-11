# Mühendislik araç zinciri / Engineering toolchain

Hazır `public/` dosyalarıyla CPU Atlas’ı açmak için Node yeterlidir. RTL, kapı modeli ve fiziksel çıktıları yeniden üretmek aşağıdaki yerel araçları gerektirir. Bu akış macOS üzerinde doğrulandı. Fiziksel araç, yalnızca bu proje için oluşturulan `cpu-lab` Lima VM içinde çalışır.

The checked-in browser artifacts run with Node alone. Regenerating them uses native host tools and a dedicated Linux VM. Commands below are sequential; do not overwrite mapped outputs while a matching gate model is being built.

## Host prerequisites

```sh
# macOS + Apple command-line C++ tools
xcode-select --install
brew install verilator emscripten yosys ngspice riscv64-elf-gcc z3 lima qemu
npm ci
npx playwright install chromium
```

Tested versions are recorded in `build/toolchain-check.json`: Node 22.23.1, Python 3.14.8, Verilator 5.052, Emscripten 6.0.10, Yosys 0.69, ngspice 47, GCC 16.2, Lima 2.2.1, OpenROAD 2.0-17598-ga008522d8. Installing formulae today may select newer versions; retain the manifest and rerun checks if versions differ. Clang requires C++17 for the DUT and C++20 for Spike.

## Pinned upstreams and dedicated physical VM

```sh
python3 scripts/setup_tools.py
python3 scripts/setup_tools.py --physical
python3 scripts/setup_tools.py --fast   # Apple Silicon: same pinned binary through Rosetta
python3 scripts/setup_tools.py --check
```

`setup_tools.py` fetches exact Spike, riscv-formal, SymbiYosys and ORFS commits. Existing checkouts with another revision cause a clear error and are preserved. `--check` verifies host tools and revisions without installing packages. `--physical` downloads checksum-verified official OpenROAD and Ubuntu libpython3.10 packages, prepares a 4-CPU / 6-GiB / 24-GiB x86_64 Ubuntu VM, mounts only this workspace writable and extracts OpenROAD into the guest user's `cpu-lab-tools/openroad` directory. On Apple Silicon, x86 emulation makes detailed routing slow. `--fast` packages the exact executable and its 46 resolved ELF runtime files from that VM, then runs them in the dedicated ARM/VZ `cpu-lab-fast` VM through Rosetta. This acceleration was executed and the engine version verified. The runner selects that environment when its runtime manifest exists; the ordinary x86 environment remains available for KLayout. It does not reuse another project's listener or VM.

The new bootstrap code was syntax checked and its `--check` path executed against the working environment. A second fresh VM installation was not performed. The current VM's actual placement/routing and KLayout runs provide execution evidence for the described package/tool arrangement.

## RTL, analog, C and reference model

```sh
npm run sim:build
npm run synth
npm run spice
npm run compile:c
python3 scripts/build_spike.py
python3 scripts/formal.py
(cd formal && ../build/tools/formal-venv/bin/python ../build/tools/sby/sbysrc/sby.py -f core.sby)
```

- `build_sim.py`: original RTL → separate native and WASM models, source/tool/model hashes.
- `synthesize.py`: generic logic netlists for each CPU and the educational full adder.
- `spice.py`: three explicit LEVEL=1 MOS circuits and 30 steady-state truth checks. Pulse curves are precomputed ngspice runs; UI switches illustrate static logic states.
- `build_spike.py`: independent upstream `processor_t` with the same execution environment; no DUT implementation is shared.
- `formal.py`: 37 RV32I instruction checks per control variant at BMC cycle 18. M arithmetic and access-fault inputs are excluded from these ISA checks. `formal/core.sby` separately checks pipeline control (M disabled): x0, halted state, stalled bus requests and register stability with arbitrary fault/ready signals.

## Your own C program

```sh
python3 scripts/compile_c.py --source examples/factorial.c --isa rv32im --name factorial
```

Outputs are `public/programs/factorial.elf`, `.disassembly.txt`, `.debug.json`, and `.experiment.json`. Import the experiment JSON using the toolbar's upload button to retain C source, instruction-to-line mapping and ISA configuration. Import ELF32 using the experiment bar for binary-only execution. Entry PC must be zero. Use `main()`, one freestanding C translation unit, no libc. Code and data are limited to 64 KiB each. The startup supplies a stack and halts on EBREAK after `main`; ELF load initializes `.bss` to zero. RV32IM compiler output requires the RV32IM core.

## Physical implementation

```sh
python3 scripts/physical.py
python3 scripts/build_gates.py
python3 scripts/export_physical.py
python3 scripts/post_route.py
```

The flow maps cacheless RTL to SKY130 HD TT 25°C / 1.8 V, places actual standard cells, inserts taps/ties/clock buffers, builds the power grid, globally routes and detailed-routes signals. Clock target is 100 ns with 5 ns I/O delays. `build/physical/<core>` retains every synthesis and OpenROAD log plus mapped Verilog, DEF/ODB, SDC, DRC, antenna and extracted SPEF reports. `--map-only` is available on `physical.py` for synthesis alone.

The physical boundary excludes the optional cache and external memories. Their browser experiments use `lab_soc.sv`. Physical cell coloring uses a separate mapped functional model; it is zero-delay Liberty logic with the same cacheless memory environment, not SDF timing simulation. `build_gates.py` emits every mapped-cell output plus retained RTL aliases and pin connections. The worker verifies JS/WASM hashes before publishing the matching DesignMap. Placed cells inserted after mapping are gray/unknown.

GDS export uses KLayout's embedded Python (`pya`), not host Python:

```sh
limactl shell cpu-lab klayout -b -r "$PWD/scripts/export_cells.py"
limactl shell cpu-lab klayout -b -r "$PWD/scripts/make_gds.py"
```

All 437 standard-cell masters can be inspected as XY mask geometry in the physical tab. Chip GDS is read back and checked for missing/orphan cells. Layer spacing in 3D is illustrative. Router DRC and antenna results are reported explicitly; GDS read-back alone does not prove DRC/LVS/manufacturing signoff. OpenRCX extracts routed parasitics for the post-route STA report. The educational original design is not a taped-out or FPGA-tested processor.

## Acceptance and evidence

Start the app on its scoped port first:

```sh
npm run dev
```

In another terminal:

```sh
npm test -- --reporter=json --outputFile=build/evidence/unit-tests.json
python3 -m unittest tests/def_routes_test.py
npm audit --json > build/evidence/npm-audit.json
npx playwright test --reporter=json > build/evidence/browser-tests.json
npm run build
python3 scripts/verify_artifacts.py
npm run build
```

`verify_artifacts.py` rejects failed/missing test reports, mismatched source/model/gate/DEF/GDS hashes and incomplete routing, then publishes `public/evidence/verification.json`. The second build includes that evidence in the distributable files. Chromium on macOS uses the Metal GPU for performance measurements. Tablet/phone tests emulate viewport size on this Mac; they are not physical tablet acceptance.

If the UI reports a stale gate hash, finish mapping/building/exporting the same generation and reload. If a native check fails, preserve the corresponding JSON and log; never replace an observed failure with a declared pass. The browser has a 2D fallback for unavailable WebGL and can recreate its 3D context.

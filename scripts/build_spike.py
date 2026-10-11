"""Build the independent upstream ISA oracle; no DUT implementation is shared."""
import pathlib, subprocess, json, hashlib
root = pathlib.Path(__file__).resolve().parents[1]
source = root/'build/tools/spike'
build = root/'build/tools/spike-build'
revision = 'master'  # Existing checkout is preserved; manifest records exact commit.
def run(args, cwd=root): subprocess.run(args, cwd=cwd, check=True)
if not source.exists():
    run(['git','clone','--depth','1','https://github.com/riscv-software-src/riscv-isa-sim.git',str(source)])
build.mkdir(parents=True, exist_ok=True)
if not (build/'Makefile').exists(): run([str(source/'configure'),'--with-boost=no'],build)
run(['make','-j6','spike'],build)
run(['clang++','-std=c++20','-O2',*['-I'+str(p) for p in [build,source/'riscv',source/'fesvr',source]],'sim/spike_reference.cpp',*[str(build/p) for p in ['libriscv.a','libdisasm.a','libsoftfloat.a','libfesvr.a','libfdt.a']],'-lpthread','-o','build/tools/spike-reference'])
manifest={'oracle':'upstream Spike processor_t','commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=source,text=True).strip(),'adapterSha256':hashlib.sha256((root/'sim/spike_reference.cpp').read_bytes()).hexdigest(),'eei':'RV32 little endian; code 0/64KiB, data 0x10000000/64KiB, UART 0x20000000, GPIO 0x20000004; trap terminates execution'}
(root/'public/sim/spike-manifest.json').write_text(json.dumps(manifest,indent=2))

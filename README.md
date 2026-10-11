# CPU LAB · RISC-V dijital ikiz / digital twin

Özgün SystemVerilog işlemcileri gerçek Verilator/WASM simülasyonuyla çalıştıran, Türkçe/İngilizce 3D öğrenme ve mühendislik laboratuvarı. Programdan saat çevrimine, yazmaçlara, mantık kapılarına, CMOS deneylerine ve SKY130 fiziksel maskelerine kadar inceleyebilirsiniz.

## Çalıştır / Run

```sh
npm ci
npm run dev
```

[Laboratuvarı aç](http://127.0.0.1:5196). Hazır deneyi seçip **Çalıştır** düğmesine basın. **Çevrim** ve **Komut** düğmeleri yürütmeyi adım adım gösterir. **Karşılaştır**, iki çekirdeğin aynı programdaki sonuçlarını ve çevrim sayılarını karşılaştırır. **Ayır**, **Kesit** ve sürükleme/yakınlaştırma ile 3D yapıyı inceleyin. **Fiziksel → GDS maskelerini aç**, seçilen hücrenin gerçek XY maskelerini gösterir; **Hücre ve katmanlar** panelini kapatarak görünümü büyütebilirsiniz.

Open the lab, choose a program and Run. Step cycles/instructions, compare both cores, inspect live state and scrub the timeline. Physical cell search opens actual SKY130 mask polygons. Switch TR/EN in the header. All runtime artifacts and fonts are local; no account/API key is needed.

## İçerik / Contents

- Özgün RV32I çok çevrimli çekirdek ve beş aşamalı RV32IM pipeline; forwarding, stall/flush, kesin hata etkileri ve gerçek 1 KiB I/D önbellek deneyleri.
- RTL ile sürülen 3D sistem/veri yolu, mantık kapıları, transistor deneyleri, gerçek DEF/LEF yerleşimi ve metal yönlendirmeleri; 437 SKY130 hücre tipi için GDS maskeleri.
- Assembly editörü, ELF32 ve freestanding C/DWARF eşlemesi, 32 yazmaç, RAM, UART/GPIO, breakpoint/watchpoint, çevrim geri oynatma, deney/trace aktarımı.
- İki dilde 12 ders, hazır programlar, cihaz boyutuna uyum, klavye kısayolları, 2D erişim ve WebGL kaybından geri dönüş.
- Spike karşılaştırması, bounded formal denetimler, kapı/RTL çevrim eşitliği, ngspice ve kaynak özetleriyle izlenen OpenROAD/KLayout çıktıları.

## Doğrulama / Verification

```sh
npm test -- --reporter=json --outputFile=build/evidence/unit-tests.json
python3 -m unittest tests/def_routes_test.py
npx playwright test --reporter=json > build/evidence/browser-tests.json
python3 scripts/verify_artifacts.py
npm run build
```

[Makine tarafından okunabilir kabul raporu](public/evidence/verification.json), çalıştırılmış testleri, gerçek performans ölçümlerini, kaynak SHA-256 özetlerini ve fiziksel sınırları kaydeder. Tarayıcıdaki **Kanıtlar / Evidence** sayfasından aynı raporları ve GDS dosyalarını indirebilirsiniz. Kontrol komutları mühendislik araçları gerektirir; önceden üretilmiş laboratuvarı açmak için Node/npm yeterlidir.

## Mühendislik akışını yeniden üret / Reproduce

[Toolchain](docs/TOOLCHAIN.md) pinlenmiş kaynakları, bağımlılıkları, yerel derlemeyi ve bu projeye özel Linux VM akışını anlatır. [Kullanım kılavuzu](docs/USER_GUIDE.md) deneyleri ve C derlemesini; [mimari sözleşme](docs/ARCHITECTURE.md) ISA, bellek ve sinyal davranışlarını; [uygulama denetimi](docs/IMPLEMENTATION_STATUS.md) planın sonuçlarını; [kaynak ve lisanslar](docs/THIRD_PARTY.md) üçüncü taraf bileşenleri açıklar.

CPU entry PC=0; program/data RAM 64 KiB each at 0x00000000/0x10000000; UART/GPIO at 0x20000000/0x20000004. This is a bare-metal teaching target without privileged CSRs, interrupts, virtual memory or Linux. The mapped physical cores omit caches/debug observation ports. Gate simulation is zero-delay; transistor networks use educational LEVEL=1 models. GDS supplies exact XY geometry; vertical 3D spacing is explanatory. Routing/STA/antenna reports are engineering evidence, not foundry signoff, fabricated-silicon measurements or physical tablet/FPGA acceptance.

## GitHub / Azure publication

Public repository: [aserdargun/cpu-aserdargun-com](https://github.com/aserdargun/cpu-aserdargun-com). Azure URL: [CPU LAB](https://happy-field-0e86cdc03.1.azurestaticapps.net). See [deployment contract](docs/DEPLOYMENT.md). The single production workflow builds `dist/` on `main`, runs the 55 portable assembler/RTL-WASM/mapped-gate checks plus DEF parser tests, verifies the previously generated engineering evidence against source hashes and uploads the prebuilt site to `swa-cpu-aserdargun-com` (West Europe, Free). Native Spike/formal/OpenROAD work is reproduced locally using TOOLCHAIN.md; CI does not claim to rerun those tools. `/release.json` records the actual deployed Git commit, run ID and hashes of every asset.

Run browser acceptance against a live deployment with:

```sh
CPU_LAB_BASE_URL=https://<azure-generated-host> npx playwright test
```

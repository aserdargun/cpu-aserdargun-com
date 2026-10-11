# Plan uygulama ve kabul denetimi / Implementation audit

Çalışan yerel CPU laboratuvarı ve mühendislik çıktıları tamamlandı. Aşağıdaki sonuçlar çalıştırılmış denetimlerden gelir. Üretim signoff'u, fiziksel FPGA/tablet kabulü ve silikon ölçümü bu yerel teslimatın kapsamı değildir.

## Planın altı aşaması

| Aşama | Gerçekleşen sonuç | Kanıt |
|---|---|---|
| 1. ISA / mimari sözleşme | RV32I, RV32IM, EEI, adres haritası, trap ve cache davranışı | ARCHITECTURE.md; rtl/execute.sv, cpu.sv, cache.sv |
| 2. Özgün RTL | Çok çevrimli ve beş aşamalı çekirdek, forwarding/stall/flush, RVFI, gerçek cache verisi | Native/WASM eşitliği; Spike retirement ve seeded ISA testleri |
| 3. Yerel mühendislik zinciri | C ELF/DWARF, Verilator/Emscripten, Yosys, ngspice, bounded formal, SKY130 OpenROAD/KLayout | Pinlenmiş kaynaklar, setup_tools.py --check, araç raporları ve SHA-256 |
| 4. Çok ölçekli dijital ikiz | Canlı RTL sistem/veri yolu, kapı/pin eşlemesi, CMOS deneyleri, tam DEF yerleşimi/LI1+metal yönlendirmesi, gerçek GDS maskeleri | Gate/RTL çevrim karşılaştırmaları; GDS geri okuma; kaynak eşleşmesi |
| 5. Öğrenme ve deney | TR/EN, 12 ders, hazır programlar, editör, ELF/deney/trace aktarımı, breakpoint/watchpoint, replay, IndexedDB | Tarayıcı kabul senaryoları; USER_GUIDE.md |
| 6. Kabul ve teslimat | Build, responsive viewport, context loss/2D, klavye/focus, C yükleme iptali, FPS/pause ölçümü, lisanslar | public/evidence/verification.json ve tam test raporları |

## Son işlevsel kabul

- 85 / 85 işlevsel test PASS; 9 tarayıcı akışı PASS, skip/failure yok; 3 DEF parser regresyon testi PASS.
- 74 upstream RV32I instruction BMC işi PASS: iki kontrol varyantı × 37, derinlik 18. M ve erişim fault'ları bu ISA formal koşularının dışında.
- Ek bir RV32I pipeline invariants BMC işi PASS: M kapalı; x0, halted, register hold, stalled request; arbitrary ready/fault/data.
- 3 ngspice ağı × 10 kararlı doğruluk denetimi; 437 GDS hücre tipi ve tüm dışa aktarılan maskeler doğrulandı.
- 504 dosya/kaynak eşleşme denetimi PASS. RTL/WASM, gate JS/WASM, mapped Verilog, DEF, SPEF ve GDS aynı tasarım nesliyle ilişkilendirildi.
- npm audit: 0 bildirilen açık. Test edilmiş production build için build/frontend-final.log.
- Ölçülen worker pause: 0.2 ms.
- system, 1600×1000: 60 FPS; p95 16.8 ms.
- system, 820×1180: 60.1 FPS; p95 16.8 ms.
- rv32im detailed physical routing, 1600×1000: 60 FPS; p95 17.1 ms.
- rv32im detailed physical routing, 820×1180: 60 FPS; p95 17.1 ms.

Bu FPS değerleri Apple M4 Pro / Chromium Metal ölçümüdür. Tablet/telefon boyutları aynı Mac üzerinde viewport emülasyonudur. Gerçek tablette veya gerçek çipte aynı sonuç iddia edilmez.

## Fiziksel sonuçlar

Saat hedefi 100 ns; SKY130 HD TT 25°C / 1.8 V; OpenRCX çıkarılmış yönlendirme parazitleri.

| Çekirdek | Yerleşen hücre | DEF kesiti | Router DRC | WNS | TNS | Anten net / pin |
|---|---:|---:|---:|---:|---:|---:|
| RV32I | 11,589 | 89,950 | 0 | +89.06 ns | 0.00 ns | 14 / 18 |
| RV32IM | 36,009 | 241,542 | 0 | -14.39 ns | -383.17 ns | 42 / 52 |

İki çekirdeğin global routing congestion raporunda toplam overflow sıfırdır; detailed-router DRC dosyaları boştur (0 ihlal). KLayout chip GDS merge/read-back denetiminde eksik/orphan hücre yoktur. Bunlar full foundry DRC/LVS signoff'u değildir.

RV32I zamanlama hedefini karşılar; RV32IM karşılamaz. M birimi kombinasyonel çarpma/bölme hesaplar ve EX'i 4/32 çevrim meşgul tutar. Bu öğretim modeli iteratif bölücü değildir; çevrim bekletme fiziksel combinational critical path'i ortadan kaldırmaz. Daha hızlı bir ASIC revizyonu için iteratif M birimi veya daha düşük saat hedefi ve ardından yeniden sentez/yerleşim/yönlendirme/zamanlama denetimi gerekir. Anten ihlalleri de üretim revizyonunda onarılmalıdır. Bu teslimat bunları giderilmiş göstermez.

## Katmanların kapsamı

Architecture/full-adder/CMOS shapes are explanatory geometry with real input values. Mapped SKY130 simulation is functional and zero-delay, cacheless, with exact mapped-netlist/model hashes and matching cycle before coloring. Inserted/unmapped cells remain gray. DEF supplies exact XY placement and routed centerlines; native GDS preserves wire widths and vias. Cell GDS supplies actual XY masks, while vertical spacing is illustrative. ngspice LEVEL=1 circuits are separate educational experiments, not whole-chip transistor simulation, power/thermal extraction or a fabrication PDK.

The complete local lab is delivered with the physical issues above recorded. Silicon manufacture, foundry signoff, SDF timing simulation, physical FPGA bring-up, physical tablet testing, privileged architecture/Linux and a future iterative divider are not accepted outcomes of this run. No deployment was requested.

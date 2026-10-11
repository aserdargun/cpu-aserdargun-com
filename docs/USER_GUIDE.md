# CPU Atlas kullanım rehberi

CPU Atlas, işlemci mimarisini görsel açıklamalar, dersler ve etkileşimli RISC-V örnekleriyle öğrenmek için hazırlanmış bir bilgi rehberidir. **Dersler** bölümünde temelden başlayabilir, **Atlas** bölümünde kavramların çalışmasını inceleyebilir, **Kaynaklar** bölümünde model ve raporların kapsamını okuyabilirsin.

## Bir komutu izlemek

1. `npm run dev` ile CPU Atlas’ı aç; `http://127.0.0.1:5196` adresine git.
2. **İlk toplama** deneyinde **Komut** düğmesine üç kez bas. x1 = 5, x2 = 7, x3 = 12 değerlerini gör.
3. **Çevrim** ile IF → ID → EX → MEM → WB aşamalarını ve sağ panelde gerçek operand/sinyal değerlerini incele.
4. Zamanlama tablosundaki çevrime veya **Önceki çevrim** düğmesine basarak aynı ikiliyi deterministik olarak yeniden yürüt.
5. **Karşılaştır** ile aynı programı çok çevrimli RV32I ve beş aşamalı RV32IM modellerinde çalıştır. Mimari sonuçlar ile çevrim sayısını ayrı değerlendir.

Çalıştırma EBREAK/ECALL veya bir hizalama/erişim/geçersiz-komut trap’inde durur. Trap kodları Atlas’ın yürütme ortamına aittir; privileged `mcause` CSR uygulanmaz. x0 daima sıfırdır. Bellek gecikmesi 1–20 çevrim arasında ayarlanabilir.

## Beş ölçekte inceleme

| Görünüm | Ne gösterir? | Nasıl incelemeli? |
|---|---|---|
| Sistem | CPU blokları, UART/GPIO, gerçek aşama ve operand değerleri | Sürükle, yakınlaştır; bileşen seç; Ayır/Kesit |
| Veri yolu | Komut çözme, yazmaçlar, ALU ve bellek arasındaki yol | Çevrim adımla; opcode/rd/rs1/rs2/funct alanlarını izle |
| Kapılar | 32 bit tam toplayıcı açıklaması ve gerçek SKY130 hücre/pin tablosu | Bit kaydırıcısı; `core.regs`, `core.ex`, `nand` filtreleri; Pins aç |
| Transistör | CMOS inverter, NAND ve iki inverter; ngspice eğrileri | A/B girişlerini değiştir; ON/OFF yollarını ve önceden hesaplanan darbe eğrilerini karşılaştır |
| Fiziksel | Gerçek DEF/LEF yerleşimi ve yönlendirme; seçilen hücrenin GDS maskeleri | Hücre adı/tipi ara, hücre seç, GDS maskelerini aç, katman seç, Ayır/Kesit |

Fiziksel çekirdek önbelleksizdir. Kapı/RTL eşlemesi için I/D Cache’i kapat. Hücre renklerinde mavi = 0, turkuaz = 1, gri = hesaplanmamış/eşlenmemiş, turuncu = seçilen hücredir; mor, birden çok çıkış pininin farklı değerler taşıdığını gösterir. Fiziksel renkler aynı çevrim ve aynı mapped-netlist hash’i eşleştiğinde gösterilir. Ayrı kapı tablosu kendi gerçek simülasyon çevrimini belirtir. Yönlendirme çizgilerinin renkleri metal katmanlarını ayırır; elektriksel voltaj iddiası taşımaz. Hücre maskelerinin düşey aralıkları açıklama amaçlıdır; GDS gerçek XY verisini sağlar.

## Deneyler

Toplama; Fibonacci; bellekten dizi toplamı; load-use bağımlılığı; UART/GPIO; fonksiyon/stack; çarpma/bölme; önbellek yerelliği; bellek sıralama; C → ELF32 dizi toplamı. **Dersler** bölümündeki 12 ders bu deneylere bağlanır. Doğru cevaplar, dil, son yüklenen program ve CPU ayarı yerel IndexedDB’de saklanır.

RV32IM’de I/D Cache’i açarak yerellik deneyini çalıştır. 1 KiB komut ve 1 KiB veri önbelleği gerçek RTL satır verisi, refill ve write-through akışına sahiptir. Soğuk ve sıcak erişimlerin hit/miss sayılarını ve bekleme çevrimlerini incele.

UART deneyinin çıktısı `Hi` olur; GPIO bitleri LED görünümüne yansır. Veri belleği 0x10000000 adresinde başlar. MMIO adresleri 0x20000000 ve 0x20000004’tür.

## Kaynak ve hata ayıklama

Assembly alanını düzenle, **Derle ve yükle** ile ikiliyi değiştir. Derlenmeyen değişiklikler yüklenen CPU programını etkilemez. PC durdurma noktası onaltılık adres alır ve komut ID aşamasına geldiğinde durur; eski pipeline etkilerini geri almaz. RAM watchpoint gözlenen veri-belleği isteğinde durur.

Yerel C derleyicisi için [araç zinciri rehberine](TOOLCHAIN.md) bak. C experiment JSON’u kaynak satırlarını ve ISA’yı korur; ELF içe aktarma ikili programı yükler. ELF başlangıç adresi 0 olmalıdır. Deneyi dışa aktarmak ikili segmentleri, CPU/bellek/önbellek ayarını, çevrimi ve durdurma noktalarını saklar. İçe aktarma o çevrime kadar yeniden yürütür. Trace dışa aktarma son 512 sinyal çevrimini saklar.

Kısayollar: Space çalıştır/duraklat; S çevrim; I komut; sol ok önceki çevrim; Escape pencereyi kapat. Program ve adres alanlarına yazarken kısayollar işlem yapmaz. **2D** düğmesi erişilebilir aynı RTL verilerini gösterir; WebGL kaybolduğunda otomatik 2D görünümü ve **3D** ile yeniden oluşturma vardır. **FPS** düğmesi o sahnede iki saniyelik ölçüm yapar. Tam ekran düğmesi tarayıcı tam ekranını kullanır.

## Kanıtları okumak

**Kaynaklar** sayfası son test raporlarını, kaynak/model özetlerini, formal kapsamını, fiziksel DRC/STA/GDS sonuçlarını ve indirilebilir dosyaları gösterir. BMC 18 çevrimlik sınırlı denetimdir; üretim signoff’u veya fiziksel tablet/FPGA/silikon kabulü değildir. Çip GDS ve yerleşim, öğrenme ve mühendislik incelemesi için hazırlanmıştır.

Metal 0, yerel bağlantı katmanı LI1’i gösterir; 1–5 metal katmanlarını ekler. **Hücre ve katmanlar** başlığıyla ayar panelini kapatıp maskelere daha fazla alan açabilirsin.

# English quick guide

Run `npm run dev` and open `http://127.0.0.1:5196`. Step three instructions in **First addition** to observe x1 = 5, x2 = 7, x3 = 12. Select an architecture block, follow actual stage/operand values, rewind a timeline cycle, and compare both independently executed RTL models. Switch to RV32IM for multiply/divide or cache experiments.

The five views cover architecture, datapath, an explanatory full adder plus real mapped-cell probes, standalone educational transistor circuits, and actual placed/routed geometry with selectable native GDS masks. Search any placed cell by instance or master. Disable caches for gate correspondence. Colors represent computed ideal logic states only when mapping hashes and cycles agree; inserted cells stay unknown. Transistor plots are precomputed ngspice pulse experiments, not live analog simulation of the complete chip.

Import ELF32 for binary execution or a generated C experiment JSON for source-line mapping. Export/import experiments to replay the exact cycle/configuration/binary. Workspace/language/lesson progress persist locally. Space runs/pauses; S steps a cycle; I steps an instruction; Left rewinds; Escape closes the comparison. 2D fallback is keyboard accessible; 3D can be recreated after context loss. FPS measures the current scene.

Evidence separates functional RTL, independent Spike checks, bounded formal checks, zero-delay mapped gates and physical artifacts. The execution environment is freestanding, entry PC zero, 64 KiB code and data, UART/GPIO MMIO. This target has no privileged CSRs, interrupts, virtual memory or Linux. Manufacturing and physical-device acceptance are outside the educational scope of CPU Atlas.

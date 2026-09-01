# Fleet — Kurumsal AI Operasyon Platformu
## Sunum Kaynak Metni (Sprint 1–6 Tamamlandı, Sprint 7–10 Planlandı)

> Bu doküman, projenin mevcut durumunu ve yol haritasını sunum üretimi için özetler.
> Kaynak: `docs/reports/sprint-1..6.md`, `docs/IMPLEMENTATION_PLAN.md`, `docs/PROJECT_OVERVIEW.md`.
> Son güncelleme: 2026-07-22

> [!WARNING]
> **Bu metin Sprint 6 sonundaki duruma göre yazıldı ve o tarihte dondu (2026-07-22).**
> O günden bu yana Sprint 7 ve Sprint 8 tamamlandı, dolayısıyla aşağıdaki bazı
> bilgiler artık güncel değil. Sunum hazırlarken şu farklara dikkat:
>
> | Metinde yazan | Güncel durum (2026-09-01) |
> |---|---|
> | "Sprint 1–6 Tamamlandı, Sprint 7–10 Planlandı" | **Sprint 1–8 tamamlandı**, 9–10 planlı |
> | 4 çalışan ajan | **6** (+ `hr_agent`, `hr_onboarding`) |
> | 348 unit + 40 entegrasyon testi | **450 unit + 69 entegrasyon** |
> | §4'teki Sprint 7 ve 8 tabloları "planlanan" | İkisi de **canlı doğrulandı** — bkz. `docs/reports/sprint-7.md`, `sprint-8.md` |
> | "İK: CV eleme (Sprint 8'de yerel şeritte)" | **Yapıldı** — HR senaryosu canlı, eval %100 (15/15) |
>
> Kanonik durum kaynağı her zaman `docs/PROGRESS.md` ve `docs/reports/`'tır.
> Bu doküman bir anlatı taslağıdır, durum kaydı değildir.

---

## 1. Proje Nedir?

**Fleet**, ~600 beyaz yakalı çalışanı olan bir kurumun tüm departmanlarının tek bir platform üzerinden yapay zekâ kullanabilmesini sağlayan **dahili AI operasyon platformudur**.

Tek cümlelik konumlandırma:
> *"Her departman için ayrı ayrı AI çözümü satın almak yerine, bir kez kurulan yönetişimli (governed) bir platform üzerine sınırsız sayıda ajan eklemek."*

Platformun sunduğu 4 temel yetenek:

1. **Sohbet** — şirket verisini bilen ve gerçek aksiyon alabilen AI ajanları
2. **Otomasyon** — Jira, GitHub, Slack, e-posta, dahili API'leri birbirine bağlayan iş akışları
3. **Bilgi Bankası** — doküman yükle, izin bazlı ortak hafıza (RAG)
4. **Ajan İnşası** — yeni ajan/entegrasyon eklemek için mühendislik döngüsü beklemeye gerek yok

**Ayırt edici nokta:** Guardrail, insan onayı, bütçe ve denetim izi sonradan eklenen özellikler değil — platformun çekirdek mimarisi. Kurumsal AI benimsenmesini sürdürülebilir kılan şey bu.

### Çözülen Problemler

| Gözlem | Sonuç |
|---|---|
| Her departmanda manuel, tekrarlayan iş akışları (ticket triyajı, fatura girişi, CV eleme, ilan moderasyonu, rapor yazımı) | Nitelikli insanlar düşük katma değerli işe saatler harcıyor |
| Bilgi PDF'lerde, e-postalarda ve insanların kafasında sıkışmış | Yavaş oryantasyon, tutarsız cevaplar, tekrarlayan sorular |
| Entegrasyonlar mühendislik ticket'ı gerektiriyor | İş birimleri basit otomasyon için haftalarca bekliyor |
| AI denemeleri izole şekilde yapılıyor | Ortak guardrail yok, ölçüm yok, yeniden kullanım yok |

---

## 2. Şu An Ne Çalışıyor? (6 Sprint Sonunda)

| Alan | Durum |
|---|---|
| **Çalışan AI ajanı** | **4 adet** — Support Copilot, Analytics, Dev Agent, Invoice Agent |
| **MCP araç sunucusu** | **7+ adet** — pg_ro, ocr, email, jira, github, slack, erp (+ internal-mock) |
| **n8n otomasyonu** | **2 adet** — haftalık analiz raporu, fatura giriş hattı |
| **Test** | 348 unit + 40 entegrasyon testi (gerçek container'lara karşı) |
| **Eval (kalite ölçümü)** | 4 ajanın tamamı **%100** (eşik %90) |
| **Altyapı** | 12+ servisli Docker Compose stack + Kubernetes (Helm + k3d) hazır |
| **CI/CD** | GitHub Actions: lint → unit → entegrasyon → güvenlik taraması → imaj build |
| **Veritabanı** | 8 Alembic migrasyonu, salt-okunur analitik rolü ayrıştırılmış |

---

## 3. Tamamlanan Sprintler (1–6)

### Sprint 1 — Temel: Repo, Stack, CI, Kimlik Doğrulama
Monorepo yapısı, 12 servisli geliştirme ortamı, GitHub Actions CI hattı, veritabanı migrasyonları, OIDC kimlik doğrulama + rol bazlı yetkilendirme (RBAC), ve tüm isteklerde çalışan çapraz kesen katman: **trace_id takibi, değiştirilemez denetim kaydı (audit log), hız sınırlama**. Kubernetes Helm chart'ı da bu sprintte — platform ilk günden üretime taşınabilir mimaride.

**Kanıt:** `make k3d-up` ile gerçek bir Kubernetes cluster'ında 8/8 servis pod'u ayağa kalktı; 5 CI job'ı GitHub'da yeşil.

### Sprint 2 — LLM Gateway ve Maliyet Kontrolü
Tüm LLM çağrılarının **tek bir kapıdan** geçmesi sağlandı. 9 modelli sabitlenmiş matris, model bazlı yedekleme zincirleri (bir sağlayıcı düşerse otomatik alternatife geçiş — canlıda kanıtlandı), harcama defteri ve **bütçe ön-kontrolü** (%80 uyarı / %100 durdurma).

En kritik özellik: **hassasiyet yönlendirmesi** — `pii` etiketli veri hiçbir koşulda buluta gitmez, yerel modele yönlendirilir. Bu KVKK uyumunun teknik garantisi.

### Sprint 3 — RAG: Bilgi Bankası
Uçtan uca doküman hattı: yükleme → metin çıkarma → **OCR** → **PII tespiti (Türkçe TCKN/IBAN/telefon tanıyıcıları dahil)** → parçalama → vektörleştirme. Koleksiyon bazlı izin ve saklama süresi yönetimi, otomatik veri imha (retention purge).

Sorgu tarafında **kaynak gösterme zorunluluğu**: cevap kaynak gösteremiyorsa bir kez yeniden üretilir, yine olmuyorsa "yetersiz" olarak işaretlenir — halüsinasyona karşı yapısal önlem. İlk web arayüzü (Knowledge ekranı) da burada.

### Sprint 4 — Ajan Çalışma Zamanı ve İlk Ajan
Tüm ajanların üzerine kurulduğu **LangGraph tabanlı çekirdek graf**: guardrail → model çağrısı → insan onayı kesme noktası → araç çalıştırma → kaynak ekleme. Ajan kayıt defteri, **semantik önbellek** (aynı soruya tekrar para ödememek için), **acil durdurma düğmesi** (bir ajanı 5 saniye içinde durdurma / tüm platformu salt-okunur moda alma). Gerçek token-token akan sohbet arayüzü ve 👍/👎 geri bildirimi (Langfuse'a skor olarak düşüyor).

**İlk ajan: Support Copilot** — müşteri hizmetleri için RAG tabanlı, kaynak gösteren, konu dışı soruları reddeden, **prompt injection saldırısına dirençli** (bilerek zehirlenmiş bir dokümana karşı test edildi). Gerçek Chromium tarayıcısıyla uçtan uca E2E testi geçiyor. Eval: 15/15.

### Sprint 5 — Entegrasyon Katmanı, 2 Ajan Daha, Onay Kuyruğu
**MCP araç katmanı**: her aracın bir `risk_class`'ı var (`read` / `write:internal` / `write:external`). Veritabanı aracı sadece SELECT çalıştırır (SQL parser + tablo beyaz listesi + salt-okunur DB rolü — üç kat savunma).

- **Analytics Agent** — iş birimlerinin doğal dille soru sorup **çalıştırılan SQL'i de görerek** cevap alması. Veri ekibinin ad-hoc sorgu yükünü ortadan kaldırır.
- **Dev Agent** — Jira'dan etiketli ticket alır → plan çıkarır → branch açar → kod yazar → PR açar → Slack'e haber verir. **Gerçek bir GitHub deposunda canlı kanıtlandı.** Asla merge etmez, `agent/*` branch kısıtı var.
- **Onay Kuyruğu (HITL)** — `write:external` sınıfı her aksiyon insan onayına düşer. Graf duraklar, veritabanına kalıcı olarak yazılır, insan onaylayınca tam kaldığı yerden devam eder. Red edilirse temiz iptal. İkisi de canlıda kanıtlandı.

### Sprint 6 — n8n Otomasyonları
n8n gerçek **queue mode**'da (ana düğüm + worker), Keycloak SSO proxy'si arkasında. Otomasyonların Fleet API'yi çağırabilmesi için **API anahtar servisi** (üretim/iptal, iptal edilen anahtar anında 401).

İki gerçek otomasyon:
- **Haftalık özet** — her Pazartesi 08:00 → yönetişimli SQL → Slack
- **Fatura girişi** — webhook → OCR → alan çıkarımı → sipariş eşleştirme/mükerrer kontrolü → **insan onayı** → ERP taslak kaydı

Dördüncü ajan: **Invoice Agent** — finansal sistemlere asla otonom yazmaz.

---

## 4. Planlanan Sprintler (7–10)

### Sprint 7 — Yönetim Paneli & Gözlemlenebilirlik
Platformun "kontrol kulesi" katmanı. Şu ana kadar API/seed ile yapılan yönetim işleri arayüze taşınıyor.

| Görev | İçerik | Kabul Kriteri |
|---|---|---|
| **7.1** Admin: kullanıcılar, modeller, bütçeler, API anahtarları | Kullanıcı/rol ekranları; model CRUD + ekleme anında smoke test; bütçe editörü; API anahtarı yönetimi (üret/iptal, scope) | Rol değişikliği bir sonraki istekte etkili olur; modelin eklenmesi UI'dan smoke test çalıştırır; UI'dan iptal edilen anahtar reddedilir |
| **7.2** Maliyet paneli, onaylar, denetim gezgini | Departman/ajan/model bazında harcama, tükenme eğrisi, önbellek tasarrufu; tüm departmanların onay görünümü; denetim kaydı gezgini + Langfuse derin bağlantısı | Denetim satırı kendi trace'ine derin bağlantı verir; panel gerçek trafikle render olur |
| **7.3** *[Ertelenebilir]* Sistem sağlığı ekranı | Kuyruklar/worker'lar/sağlayıcılar. Şimdilik Grafana yeterli | Durdurulmuş bir worker tek yenilemede ekrana yansır |
| **7.4** Grafana + kod olarak alarm | Dashboard'lar kod olarak sağlanır; Alertmanager → Slack kuralları (bütçe, hata oranı, gecikme, kuyruk derinliği, **maliyet anomalisi**: departman günlük harcaması 7 günlük ortalamanın 3 katını aşarsa) | Bütçe yumuşak limiti senaryo testinde Slack + UI uyarısı tetikler |

**Neden önemli:** Bu sprint, platformu "çalışıyor"dan "yönetilebiliyor"a taşır. Yönetime gösterilecek maliyet ve benimsenme metrikleri buradan gelir.

### Sprint 8 — KVKK Şeridi
Yerel model şeridinin ciddiye alınıp ölçüldüğü sprint. Sprint 2'de mimari garanti kuruldu; burada **kalite kanıtlanıyor**.

| Görev | İçerik | Kabul Kriteri |
|---|---|---|
| **8.1** Yerel şerit kalite provası | Tesseract `tur` + yerel Qwen modelini gerçekçi **sentetik** TR CV ve fatura taramalarında çalıştır; doğruluk ölçümü; eşiğin altındaysa seçenekleri raporla (14b model, görüntü ön işleme, yerel VLM) — karar kullanıcıda | Doküman tipi başına doğruluk sayıları içeren bulgu raporu; demo fixture seti seçilir |
| **8.2** İK CV mini-akışı (pii şeridi) | İK `pii` koleksiyonu + CV ayrıştırma görevi Ollama'ya sabitlenir; bge-m3 embedding. CI notu: "buluta çıkış yok" iddiası GPU'suz koşucuda yönlendirme *hedefi* olarak, tam çıkarım eval'i ise self-hosted GPU koşucusunda test edilir | Entegrasyon testi bir `pii` isteğinin asla bir bulut sağlayıcısına ulaşmadığını kanıtlar; CV → yapılandırılmış profil yerel modelle doğrulanır |
| **8.3** Silme (erasure) + yetki matrisi | Veri silme endpoint'i; saklama işi doğrulanır; hassasiyet yetki matrisi Admin→Models'ta gösterilir | Silme, ilgili kişinin verisini kaldırır; denetim kaydı takma adlaştırılmış olarak korunur |
| **8.4** PII maskeleme doğrulaması | Loglarda ve trace'lerde maskeleme doğrulanır | Tespit edilen kimlik bilgileri Loki ve Langfuse'da maskeli görünür |

**Neden önemli:** Türkiye'de kurumsal AI benimsenmesinin en büyük engeli KVKK. Bu sprint, "hassas veri buluta gitmiyor" iddiasını sözden kanıta çevirir.

### Sprint 9 — Sertleştirme (Hardening)
Üretim öncesi dayanıklılık kanıtı.

| Görev | İçerik | Kabul Kriteri |
|---|---|---|
| **9.1** Yük testi | k6: `chat_smoke` + `mixed_day` senaryoları k3d'ye karşı; darboğaz düzeltmeleri (pool boyutları, HPA değerleri) | SLO eşikleri k6 raporunda geçer (rapor repoda saklanır) |
| **9.2** Güvenlik | `make scan` yüksek önem dereceli bulgudan temiz; repo içi **prompt injection korpusu** Support Copilot'a karşı çalıştırılır, bulgular triyaj edilir | Injection korpusu: karantinaya alınmış içerikten **0 başarılı talimat takibi** |
| **9.3** *[Ertelenebilir]* Chaos-lite + garak | garak prob paketi; kill-switch tatbikatı (yük altında ajanı durdur); ajan çalışırken pod öldürme → checkpoint'ten devam doğrulaması | Devam testi yeşil; kill switch yük altında ≤5 sn'de etkili olur |
| **9.4** Yedekleme & geri yükleme tatbikatı | CloudNativePG zamanlanmış yedekler (WAL → MinIO), Qdrant gecelik snapshot → MinIO, MinIO versiyonlama; geri yükleme runbook'u uygulanır | Postgres zaman-noktası geri yüklemesi ve Qdrant snapshot geri yüklemesi temiz bir k3d cluster'ında başarılı; `docs/runbooks/restore.md` gerçek komutlarla güncellenir |

**Neden önemli:** "AI demo çalışıyor" ile "AI üretimde güvenle çalışıyor" arasındaki fark bu sprint.

### Sprint 10 — Demo Kurgusu & Dokümantasyon
Teslim edilebilir hale getirme.

| Görev | İçerik | Kabul Kriteri |
|---|---|---|
| **10.1** Sıfırdan kurulum provası | README finalize (kurulum adımları, demo yürüyüşü); temiz bir makinede sadece README'yi takip ederek `make k3d-up`; demo senaryo verisi | Temiz makine → çalışan demo, **≤30 dakika** |
| **10.2** Doküman + sürüm | Runbook'lar (geri yükleme, nöbet temelleri); demo senaryosu provası; sunum için ekran görüntüleri/GIF'ler; `v0.1.0` etiketi. Etiket tetiklemeli GitHub Actions sürüm hattı tüm kontrol paketini çalıştırıp sürüm imajlarını üretir | Etiket hattı `v0.1.0` üzerinde tüm CI job'larını yeşil geçer; prova ≤15 dakikada tamamlanır |

---

## 5. Planlanan 15 Dakikalık Demo Senaryosu

Sprint 10'da provası yapılacak akış — sunumun anlatı iskeleti olarak da kullanılabilir:

1. **Keşif çerçevesi (2')** — departman haritası bir hipotezdir; platform bunu doğrulamayı ucuzlatır
2. **Support Copilot (3')** — canlı doküman yükle → sor → kaynaklı akan cevap → 👎 ver → Langfuse trace'inde maliyetiyle birlikte göster
3. **Dev Agent (4')** — mock Jira ticket → plan → onay kuyruğu → onayla → gerçek PR + Slack bildirimi; `agent/*` branch guardrail'ini göster
4. **Fatura otomasyonu (2')** — n8n çalıştır → OCR alanları → onay kuyruğunda taslak (`write:external` asla otomatik çalışmaz)
5. **KVKK şeridi (2')** — CV yerel modelle ayrıştırılır; gateway logu `pii` için buluta hiç çıkış olmadığını gösterir
6. **Yönetim (2')** — maliyet paneli, bütçe limiti tetiklenmesi, denetim→trace derin bağlantısı, acil durdurma. Faz haritasıyla kapanış

---

## 6. Teknoloji Seçimleri ve Gerekçeleri

| Teknoloji | Neden seçildi |
|---|---|
| **LangGraph** | Ajanların çok adımlı akışında **duraklatılabilir/devam ettirilebilir** durum gerekiyordu. İnsan onayı için grafın Postgres'e kalıcı yazılıp saatler sonra kaldığı yerden devam etmesi zorunlu — basit bir zincir kütüphanesi bunu veremez. |
| **LiteLLM (gateway)** | Sağlayıcı bağımsızlığı. Tek noktadan model değişimi, otomatik yedekleme zinciri, merkezi maliyet ölçümü. Sağlayıcı SDK'sını kod içine dağıtmak = kilitlenme. |
| **Qdrant** | Vektör veritabanı. Filtreli arama (koleksiyon/izin bazlı) ve kendi barındırılabilir olması — veri şirket dışına çıkmıyor. |
| **MCP (Model Context Protocol)** | Her entegrasyon için özel kod yazmak yerine standart araç arayüzü. Yeni bir REST API eklemek = sunucuya tanımlamak. Ajan katmanında sıfır yapıştırıcı kod. |
| **Keycloak** | Kurumsal SSO + rol bazlı yetkilendirme standardı. Hem web arayüzü hem n8n aynı kimlikle korunuyor. |
| **n8n** | İş birimlerinin **kod yazmadan** otomasyon kurabilmesi. Kod ile no-code arasında köprü: workflow'lar ajanları çağırabiliyor, ajanlar workflow tetikleyebiliyor. |
| **Langfuse** | LLM gözlemlenebilirliği. Her cevabın hangi modele, hangi maliyetle, hangi kaynakla üretildiği izlenebilir + kullanıcı geri bildirimi trace'e bağlanıyor. |
| **Presidio + özel TR tanıyıcılar** | KVKK. Hazır PII tespiti Türkçe TCKN/IBAN formatlarını bilmiyor — checksum doğrulamalı özel tanıyıcılar yazıldı. |
| **Ollama (yerel model)** | KVKK şeridi. Hassas veri buluta gitmiyor, aynı sunucudaki yerel modelle işleniyor. Teknik zorunluluk, tercih değil. |
| **FastAPI + Python 3.12** | Async I/O, tam tip desteği, otomatik OpenAPI şeması (TypeScript istemcisi buradan üretiliyor — arayüz/API uyumsuzluğu derleme zamanında yakalanıyor). |
| **Next.js 15 + TypeScript** | Sunucu bileşenleri, akış (streaming) desteği, i18n (TR/EN). |
| **Docker Compose + Helm/k3d** | Geliştirme ortamı üretimin aynası. İlk günden Kubernetes'e taşınabilir. |
| **Prometheus + Grafana + Loki** | Standart gözlemlenebilirlik yığını; Sprint 7'de alarm kuralları kod olarak eklenecek. |
| **Alembic** | Şema değişikliği sadece migrasyonla — geri alınabilir, denetlenebilir. |
| **sqlglot** | Analitik ajanının ürettiği SQL'i çalıştırmadan önce ayrıştırıp doğrulamak; SELECT dışını yapısal olarak engellemek. |
| **k6** (Sprint 9) | Yük testi senaryolarının kod olarak repoda durması; SLO eşiklerinin CI'da ölçülebilmesi. |

---

## 7. Yönetişim: "Neden Güvenle Kullanılabilir?"

Sunumda en çok vurgulanması gereken kısım — çünkü rakip demolar bunu yapmaz:

1. **Tek LLM kapısı** — sağlayıcı SDK'sını başka yerden import etmek CI'da build'i kırıyor (mimari kural, tavsiye değil)
2. **Hassasiyet yönlendirmesi** — `pii`/`gizli` etiketli veri buluta çıkamaz, testlerle korunuyor
3. **Tüm dış etkiler MCP'den** — `write:external` = zorunlu insan onayı. İstisna yok, demoda bile
4. **Alınan içerik güvenilmezdir** — RAG'den ve araçlardan gelen her şey karantina bloğuna sarılır, sistem prompt'una asla ham eklenmez (prompt injection savunması, canlı test edildi; Sprint 9'da korpusla sistematik ölçülecek)
5. **Bütçe kontrolü** — her çağrı öncesi kontrol; %80 uyarı, %100 durdurma
6. **Değiştirilemez denetim kaydı** — kim, ne zaman, hangi aracı, hangi veriyle çağırdı
7. **Acil durdurma** — tek ajan veya tüm platform saniyeler içinde durdurulabilir
8. **Eval kapısı** — prompt değişikliği altın test setini çalıştırmadan geçemez. 4 ajan da %100

---

## 8. Departman Senaryoları

### Kanıtlanmış (çalışıyor)

| Departman | Ajan | Ne yapıyor |
|---|---|---|
| Müşteri Hizmetleri | Support Copilot | Bilgi bankasından kaynak göstererek cevap taslağı |
| Veri & Analitik | Analytics Agent | Doğal dil → salt-okunur SQL → tablo + çalıştırılan sorgu |
| IT / Mühendislik | Dev Agent | Ticket → plan → branch → PR → Slack |
| Finans | Invoice Agent | Fatura OCR → alan çıkarımı → PO eşleştirme → onay → ERP taslağı |
| (Otomasyon) | n8n | Haftalık analiz raporu → Slack |

### Yol Haritasında (aynı platform, ek geliştirme değil ek konfigürasyon)

| Departman | Ajan | Ne yapacak |
|---|---|---|
| İnsan Kaynakları | Talent & Onboarding | CV eleme (Sprint 8'de yerel şeritte), İK politika Q&A |
| İlan Operasyonları | Listing Quality | Multimodal ilan denetimi (fotoğraf-açıklama tutarlılığı, plaka bulanıklaştırma) |
| Trink Sat | Vehicle Intake | Ekspertiz PDF OCR + hasar analizi + emsal fiyat → fiyat bandı önerisi |
| Pazarlama | Insights Publisher | Aylık pazar raporu + sosyal içerik taslağı, marka sesi prompt kütüphanesi |
| Kurumsal Satış | Dealer Onboarding | Bayi belge doğrulama + eksik evrak talebi |
| Hukuk & Uyum | Document Review | Sözleşme riskli madde tespiti, KVKK kontrolü (danışma amaçlı) |

---

## 9. Yayılım Stratejisi (Faz Haritası)

- **Faz 0 — Keşif (1–3. hafta):** Her departmanla yapılandırılmış görüşme; süreç haritalama; fırsatları (etki × yapılabilirlik × risk) ile skorlama
- **Faz 1 — Temel + İlk Kazanım (4–8. hafta):** Platform çekirdeği devreye; TEK bir yüksek görünürlüklü, düşük riskli ajan uçtan uca
- **Faz 2 — Genişleme (3–6. ay):** Kanıtlanmış platform üzerine 3–4 departman daha; n8n workflow'ları ve onay kuyruğu; "kendi ajanını kur" iç eğitimleri
- **Faz 3 — Ölçek (6–12. ay):** Kalan departmanlar; ölçüm verisi destekliyorsa daha fazla otonomi; yeniden kullanılabilir bileşen kütüphanesi; yönetime benimsenme metrikleri

---

## 10. Başarı Metrikleri (Platform Seviyesi)

- Aylık otomatikleştirilen manuel iş saati (departman bazında ve toplam)
- Aktif ajan / workflow / haftalık aktif kullanıcı sayısı
- İnsan onayı geçersiz kılma oranı (kalite göstergesi — düşmesi beklenir)
- Ajan sürümü başına eval geçme oranı
- "Departman talebi"nden "çalışan ajan"a geçen süre (hedef: ay değil, gün)

---

## 11. Anahtar Mesajlar (Sunum Kapanışı İçin)

- **"Bir mühendis, tüm organizasyon."** İlk departman pahalı, sonraki her departman ucuz — platform yeniden kullanılıyor.
- **"Demo değil, çalışan sistem."** Her kabul kriteri gerçek servislere karşı doğrulandı: gerçek GitHub deposuna açılmış PR, gerçek tarayıcıyla SSO girişi, gerçek n8n worker çalıştırması, gerçek vektör veritabanı. Mock ile "geçti" denmedi.
- **"Güven tasarımdan gelir."** Guardrail, onay ve ölçüm platformun kendisi — sonradan yamalanan bir katman değil.
- **"KVKK teknik olarak zorunlu kılındı."** Hassas veri buluta gidemez; bu bir politika değil, kodla ve testlerle kapatılmış bir yol.
- **"6 sprint = 4 çalışan ajan + 7 entegrasyon + 2 otomasyon + tam yönetişim katmanı."**
- **"Kalan 4 sprint teknoloji riski değil, olgunlaşma."** Sprint 7–10 yeni mimari getirmiyor; yönetim arayüzü, KVKK ölçümü, dayanıklılık kanıtı ve teslim paketi. Zor kısım bitti.

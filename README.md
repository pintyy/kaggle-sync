# Kaggle to GitHub Sync 🔄

Kaggle hesabınızdaki tüm notebook'ları otomatik olarak GitHub'a senkronize eden Python aracı. Her notebook için ayrı bir GitHub repository'si oluşturulur ve notebook output'ları korunur.

## 🎯 Özellikler

- ✅ Tüm Kaggle notebook'larınızı otomatik olarak GitHub'a aktarır
- ✅ Her notebook için ayrı bir GitHub repository'si oluşturur
- ✅ Notebook **output'larını korur** (grafikler, tablolar, sonuçlar)
- ✅ Otomatik README.md oluşturur (Türkçe/İngilizce)
- ✅ Mevcut repository'leri günceller (tekrar oluşturmaz)
- ✅ Türkçe karakter desteği (ş→s, ç→c, ğ→g, vb.)
- ✅ Hata yönetimi ve ilerleme takibi
- ✅ Rate limiting ve API hatalarını yönetir

## 📋 Gereksinimler

- Python 3.8 veya üzeri
- Kaggle hesabı ve API key
- GitHub hesabı ve Personal Access Token

## 🚀 Kurulum

### 1. Repository'yi klonlayın

```bash
git clone https://github.com/pintyy/kaggle-sync.git
cd kaggle-sync
```

### 2. Bağımlılıkları yükleyin

```bash
pip install -r requirements.txt
```

### 3. Kaggle API Ayarları

#### Seçenek A: Kaggle API key dosyası (Önerilen)

1. [Kaggle Account](https://www.kaggle.com/account) sayfasına gidin
2. "Create New API Token" butonuna tıklayın
3. İndirilen `kaggle.json` dosyasını şu konuma taşıyın:
   - **Linux/Mac:** `~/.kaggle/kaggle.json`
   - **Windows:** `C:\Users\<username>\.kaggle\kaggle.json`

4. Dosya izinlerini ayarlayın (Linux/Mac):
   ```bash
   chmod 600 ~/.kaggle/kaggle.json
   ```

#### Seçenek B: Environment Variables

```bash
export KAGGLE_USERNAME="your_kaggle_username"
export KAGGLE_KEY="your_kaggle_api_key"
```

### 4. GitHub Token Ayarları

1. [GitHub Settings > Developer settings > Personal access tokens](https://github.com/settings/tokens) sayfasına gidin
2. "Generate new token (classic)" seçeneğine tıklayın
3. Token'a bir isim verin (örn: "Kaggle Sync")
4. Şu izinleri seçin:
   - ✅ `repo` (tüm repo izinleri)
   - ✅ `delete_repo` (opsiyonel, repo silme için)
5. "Generate token" butonuna tıklayın
6. Token'ı kopyalayın ve environment variable olarak ayarlayın:

```bash
export GITHUB_TOKEN="your_github_token"
```

**Not:** Token'ı güvenli bir yerde saklayın, bir daha göremezsiniz!

## 💻 Kullanım

### Basit Kullanım

Tüm notebook'larınızı senkronize etmek için:

```bash
python sync.py
```

### Nasıl Çalışır?

Script şu adımları takip eder:

1. **Kaggle API** ile kullanıcının tüm notebook'larını listeler
2. Her notebook için:
   - Notebook'un **title**'ını alır
   - Title'dan GitHub repo adı üretir (slug formatı)
     - Örnek: "Veri Analizi Çalışması" → `veri-analizi-calismasi`
   - **GitHub API** ile yeni repo oluşturur (varsa atlar)
   - Notebook'u **output'larla birlikte** indirir (`.ipynb` formatı)
   - İndirilen dosyayı repo'ya push eder
   - Otomatik `README.md` oluşturup push eder

### Çıktı Örneği

```
🚀 Kaggle to GitHub Sync Tool
============================================================

🔑 Checking credentials...
✅ Kaggle user: pintyy
✅ GitHub token configured
✅ GitHub user: pintyy

📋 Listing notebooks for user: pintyy
✅ Found 3 notebook(s)

📦 Starting sync of 3 notebook(s)...

[1/3]
============================================================
📓 Processing: My First Data Analysis
============================================================
  🏷️  Repository slug: my-first-data-analysis
  📥 Downloading notebook: pintyy/my-first-data-analysis
  ✅ Downloaded notebook
  🆕 Creating repository 'my-first-data-analysis'
  ✅ Repository created
  📤 Pushing files to GitHub
  ✅ Created my-first-data-analysis.ipynb
  ✅ Created README.md
  🎉 Successfully synced to https://github.com/pintyy/my-first-data-analysis

...

============================================================
✅ Sync complete!
   Successfully synced: 3/3
============================================================
```

## 🔧 Sorun Giderme

### "Kaggle credentials not found" hatası

- `~/.kaggle/kaggle.json` dosyasının var olduğundan emin olun
- VEYA `KAGGLE_USERNAME` ve `KAGGLE_KEY` environment variable'larını ayarlayın

### "GitHub token not found" hatası

- `GITHUB_TOKEN` environment variable'ının ayarlı olduğundan emin olun

### "Rate limit exceeded" hatası

- GitHub API rate limit'ine ulaştınız
- Bir süre bekleyin ve tekrar deneyin
- Authenticated istekler için limit: 5000 istek/saat

### Notebook output'ları kayboldu

- Script `kaggle kernels pull` komutunu `-m` (metadata) flag'i ile kullanır
- Bu, notebook'un output'larını korur
- Eğer output'lar hala kayboluyorsa, Kaggle'da notebook'un output'larla kaydedildiğinden emin olun

## 📁 Proje Yapısı

```
kaggle-sync/
├── sync.py              # Ana script
├── requirements.txt     # Python bağımlılıkları
└── README.md           # Bu dosya
```

## 🛠️ Teknik Detaylar

### Slug Üretimi

Title'dan slug üretilirken:
- Türkçe karakterler ASCII'ye dönüştürülür (ş→s, ç→c, ğ→g, ü→u, ö→o, ı→i)
- Unicode karakterler ASCII'ye normalize edilir
- Özel karakterler kaldırılır
- Boşluklar tire (-) ile değiştirilir
- Küçük harfe çevrilir

**Örnek dönüşümler:**
- "Veri Analizi Çalışması" → `veri-analizi-calismasi`
- "My Cool Analysis!" → `my-cool-analysis`
- "Öğrenci Başarı Tahmini" → `ogrenci-basari-tahmini`

### Output Koruma

Notebook output'ları şu şekilde korunur:
- `kaggle kernels pull` komutu `-m` flag'i ile çalıştırılır
- Bu, notebook'un tüm cell output'larını (grafikler, tablolar, print sonuçları) korur
- `.ipynb` dosyası output'larla birlikte GitHub'a push edilir

### Mevcut Repo Güncelleme

Eğer bir repo zaten varsa:
- Yeni repo oluşturmaya çalışmaz
- Mevcut repo'yu günceller
- Dosyalar üzerine yazılır (en son versiyon kullanılır)

## 🤝 Katkıda Bulunma

Pull request'ler kabul edilir! Büyük değişiklikler için lütfen önce bir issue açın.

## 📄 Lisans

Bu proje MIT lisansı altında lisanslanmıştır.

## ⚠️ ÖNEMLİ UYARILAR

- ⚠️ **GİZLİLİK:** Script tüm notebook'larınızı **PUBLIC** (herkese açık) GitHub repository'leri olarak oluşturur
  - Private Kaggle notebook'larınız da public olarak paylaşılacaktır
  - Private repo'lar oluşturmak istiyorsanız, sync.py dosyasındaki `private=False` satırını `private=True` olarak değiştirin
- 🔐 GitHub token'ınızı **asla** public repository'lere commit etmeyin
- 🔐 Kaggle API key'inizi **asla** paylaşmayın

## 📞 Destek

Bir sorun mu yaşıyorsunuz? [Issue açın](https://github.com/pintyy/kaggle-sync/issues)!
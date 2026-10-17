# AUTOCLIP AI V1.1

Dari iPhone, buka repository GitHub > Issues > New issue.

- Judul: `[CLIP] Video Pertama`
- Deskripsi: **satu URL** video YouTube/TikTok, atau satu URL lampiran MP4 dari GitHub Issue.
- Untuk MP4: pada editor Issue, gunakan tombol attach files untuk mengunggah MP4. Tunggu hingga muncul tautan lampiran di deskripsi, lalu buat Issue.
- Buka Actions > workflow run > Artifacts > `autoclip-results` untuk mengunduh hasil ZIP (3 MP4 + 3 SRT).

**Penting:** Repository Public berarti Issue dan lampiran yang dibagikan bisa terlihat publik. Gunakan video yang boleh Anda proses dan bagikan. Jangan unggah video pribadi atau cookies login. GitHub membatasi ukuran lampiran dan durasi Actions. Tidak ada jaminan tautan YouTube/TikTok dapat diambil otomatis. Subtitle SRT terpisah, belum dibakar ke video. Pilihan momen masih heuristik berdasarkan kepadatan transkrip, bukan penilaian viralitas AI tingkat lanjut. Tidak ada UI website khusus pada versi ini.

Unggah file `clipper.py`, `requirements.txt` ke root repository dan `.github/workflows/clip.yml` ke path yang tepat. Jangan membuat folder `.github/workflows` ganda.

# AUTOCLIP AI V2 — Free Edition

Workflow: halaman GitHub Pages -> Issue `[CLIP]` dengan URL -> GitHub Actions -> 3 MP4 + 3 SRT di Actions artifacts.

## Instalasi
1. Salin seluruh isi paket ke root repository `kerjaansidangpemuda-bot/autoclip-ai`, menggantikan `clipper.py` dan `.github/workflows/clip.yml` lama.
2. Di Settings > Pages, pilih Deploy from a branch, branch `main`, folder `/docs`.
3. Buka website Pages yang ditampilkan di Settings > Pages.
4. Tempel URL YouTube/TikTok, klik Generate, lalu kirim issue yang terisi.
5. Buka Actions > AUTOCLIP AI V2 > run terbaru > Artifacts dan unduh ZIP berisi 3 MP4 dan 3 SRT.

## Batasan
- GitHub Pages adalah situs statis: tidak bisa menyimpan token GitHub atau menjalankan pemrosesan video. Login GitHub dan konfirmasi Issue masih diperlukan.
- Tidak menjamin unduhan YouTube/TikTok karena pembatasan platform, autentikasi, geoblocking, dan hak akses.
- Skoring berbasis kepadatan kata (Whisper tiny), bukan AI pemahaman adegan atau jaminan viral.
- MP4 720x1280 center crop; SRT disediakan terpisah, belum burned-in.
- Durasi sumber minimum 45 detik. Durasi tiap Shorts 15-25 detik.
- Gunakan hanya konten yang diizinkan untuk diproses.
- Hasil disimpan sebagai artifact selama 7 hari.

## Pemeriksaan tanpa run GitHub berulang
`python -m py_compile clipper.py`

## Catatan keamanan
Hanya issue yang dibuat oleh pemilik repository dan diawali `[CLIP]` yang diproses. Input issue diperlakukan sebagai data, bukan perintah shell. URL dibatasi ke domain resmi YouTube/TikTok. Jangan menyimpan token GitHub dalam HTML.

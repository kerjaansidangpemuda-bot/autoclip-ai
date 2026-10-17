# AUTOCLIP AI — versi gratis untuk iPhone

**Hasil:** 3 klip MP4 vertikal 9:16, masing-masing 15–30 detik, plus subtitle SRT. Tidak perlu PC pribadi. Pemrosesan dilakukan di GitHub Actions. Ini adalah MVP, bukan aplikasi web satu-tombol; kualitas pemilihan highlight belum setara layanan komersial.

## Instalasi dari iPhone

1. Masuk ke github.com di Safari, buat **repository public** baru (misalnya `autoclip-ai`).
2. Upload seluruh isi ZIP ini ke root repository, termasuk folder `.github` (cara termudah: gunakan editor web `github.dev` atau upload folder/file lewat komputer sekali jika antarmuka HP menyulitkan).
3. Buka tab **Settings → Actions → General**, pastikan GitHub Actions diizinkan. Jika diperlukan, atur izin workflow agar bisa menulis issues; pemrosesan tidak membutuhkan izin ini, jadi bisa tetap read-only.
4. Buka tab **Issues → New issue → Generate 3 Clips**. Judul: `[CLIP] Video pertama`. Tempel satu URL di kolom link, lalu submit.
5. Buka **Actions → Generate 3 Clips**, tunggu run selesai, lalu buka run tersebut dan download artifact **autoclip-3-videos** (ZIP). Ekstrak lewat aplikasi Files di iPhone.

## Catatan penting

- Video harus cukup panjang (minimal ~45 detik), publik, bisa diakses, dan tidak dibatasi DRM/login.
- YouTube/TikTok dapat mengubah mekanisme akses; `yt-dlp` tidak dijamin selalu berhasil.
- Video diproses di server GitHub; jangan masukkan video privat atau sensitif. Issue dan URL pada repo public juga terlihat publik.
- Runner gratis memiliki batas kuota dan sumber daya sesuai kebijakan GitHub. Tidak benar-benar unlimited.
- Subtitle **SRT terpisah**, belum dibakar ke gambar. Belum ada face-tracking; crop dipusatkan.
- Gunakan hanya konten sendiri atau konten yang memiliki izin untuk diedit dan didistribusikan.
- Bila video pendek atau highlight tidak cukup, job akan gagal daripada membuat tiga potongan palsu.

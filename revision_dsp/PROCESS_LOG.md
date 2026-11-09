# Riwayat proses eksperimen: revisi Paper 1 DSP-D-26-02462 (GWi+ODPS)

Dibuat dari `process_log.csv` oleh `tools/render_process_log.py`; jangan diedit langsung.
Waktu dalam WIB (UTC+7). Durasi = selesai − mulai (j:mm:ss).
Fase mengikuti agenda KDC (https://kdc-2026.vercel.app/agenda).
Sumber waktu: log di `logs_local/`, `logs_local/runs.csv` (tools/run_logged.sh),
commit dan tag git, dan riwayat sesi kerja. Baris tanpa jam ditandai di kolom Ref.
Temuan lengkap ada di FINDINGS.md; perubahan protokol di CHANGELOG.md.

## Ringkasan per fase

| Fase | Agenda | Kegiatan tercatat | Waktu komputasi (run) | Belum dijalankan |
|---|---|---|---|---|
| 1. Persiapan data & eksperimen | 7-9 Nov | 26 | 11:15:09 | - |
| 2. Penetapan konfigurasi & evaluasi uji | 10 Nov | 6 | 2:27:33 | - |
| 3. Analisis & pengukuran | 11-14 Nov | 4 | 0:01:31 | E21, E23, E24, E25, E26 |

## Fase 1. Persiapan data & eksperimen (agenda 7-9 Nov)

| ID | Jenis | Kegiatan | Mulai | Selesai | Durasi | Status | Output | Hasil | Ref |
|---|---|---|---|---|---|---|---|---|---|
| P-00 | tulis | Protokol v1: border reflect untuk semua metode; seleksi k, λ, d dengan ODS GWi+ODPS | 2026-11-07 |  |  | selesai | config.yaml (v1) | Diganti protokol v2 pada 8 Nov | CHANGELOG.md baris 1 (jam tidak tercatat) |
| P-01 | tulis | Protokol v2: protokol naskah submit, hanya diubah sesuai permintaan reviewer | 2026-11-08 |  |  | selesai | config.yaml, scripts 10-26, README.md | Protokol yang dipakai untuk revisi | CHANGELOG.md baris 1 (jam tidak tercatat) |
| S-00 | run | Smoke test: 12 skrip pada data sintetis | 2026-11-09 12:07:35 | 2026-11-09 12:09:45 | 0:02:10 | selesai | logs_local/S00_smoke/ | Semua skrip berjalan |  |
| E00-02 | run | Cek lingkungan, ekuivalensi dengan kode submit, dan mekanisme (run_all.sh check) | 2026-11-09 12:09:54 | 2026-11-09 12:15:42 | 0:05:48 | rc 0 | logs_local/E00-02_check.log | 11 PASS: kernel, peta GWi/GWC, ODPS, normalisasi, dan counts identik dengan kode submit (04c); evaluator 3,78 s per citra per metode |  |
| E10-0 | run | Uji jalur data: seleksi terbatas 2 citra | 2026-11-09 12:15:55 | 2026-11-09 12:21:19 | 0:05:24 | selesai | results/counts/*_limit2 (tidak di-commit) | Jalur data BSDS500 dan BIPED benar |  |
| D-01 | keputusan | Persetujuan menjalankan E10 | 2026-11-09 12:43:07 |  |  | disetujui |  | "Ya, lanjut E10" |  |
| PR-1 | commit | Pre-registrasi protokol v2 | 2026-11-09 12:43:24 |  |  | selesai |  |  | commit 749931b; tag prereg-dsp-2026-11-08 |
| E10 | run | Seleksi kernel 5 kandidat (Tabel 1-4) pada BSDS500 train+val dan BIPED train | 2026-11-09 12:43:27 | 2026-11-09 14:58:48 | 2:15:21 | rc 0 | results/selection/ (versi commit aa2bc01); logs_local/E10_select.log | Terpilih k7 λ5 (rata-rata ODS GWi 0,4742), bukan k5 λ4 |  |
| E11 | run | Ablasi d, λ, N, σ, γ di sekitar k7 λ5 (BSDS500 train+val) | 2026-11-09 15:10:20 | 2026-11-09 15:53:27 | 0:43:07 | rc 0 | results/ablation/ (versi commit aa2bc01); logs_local/E11_ablation.log | ODS GWi masih naik di λ6, tepi rentang; dasar amandemen 1 |  |
| D-02 | keputusan | Seleksi ulang dengan 18 kandidat (amandemen 1) | 2026-11-09 16:11:59 |  |  | disetujui |  |  |  |
| C-01 | commit | Hasil E10 + E11 (5 kandidat) | 2026-11-09 16:12:35 |  |  | selesai |  |  | commit aa2bc01 |
| PR-2 | commit | Amandemen 1: grid k {5,7,9} × λ {3..8} dan aturan tepi | 2026-11-09 16:13:05 |  |  | selesai |  |  | commit 2df5279; tag prereg-dsp-amend1-2026-11-09 |
| E10b | run | Seleksi 18 kandidat | 2026-11-09 16:13:13 | 2026-11-09 21:14:21 | 5:01:08 | rc 2 | results/selection/amend1_18cand/; logs_local/E10b_select_18cand.log | Terpilih k7 λ8 (tepi atas grid). rc 2 karena run_all.sh diedit saat berjalan; output seleksi lengkap, E11 lanjutan tidak jalan (FINDINGS F6) |  |
| PR-3 | commit | Hipotesis H1/H2 ditulis sebelum hasil 18 kandidat | 2026-11-09 16:43:01 |  |  | selesai | HYPOTHESES.md |  | commit d5fa797; tag hyp-dsp-2026-11-09 |
| E13 | run | Uji hipotesis H1/H2 (18 kandidat) | 2026-11-09 21:15:25 | 2026-11-09 21:15:28 | 0:00:03 | rc 0 | results/hypotheses/ | H1 didukung (Spearman 0,92 / 0,90); H2a gagal; H2b didukung; H2c hanya trivial |  |
| E10c-1 | run | Aturan tepi ronde 1: + k7 λ9 | 2026-11-09 21:16:06 | 2026-11-09 21:37:41 | 0:21:35 | rc 0 | logs_local/E10c_edge_k7l9.log | k7 λ9 terbaik (0,5366), masih di tepi |  |
| E11b | insiden | E11 terpicu terlalu awal (CRLF di skrip ronde), dihentikan | 2026-11-09 21:38:48 | 2026-11-09 21:40:02 | 0:01:14 | dihentikan | logs_local/E11b_aborted_early_2138.log | Tidak ada file hasil yang ditulis (FINDINGS F6) |  |
| E10c-2..4 | run | Aturan tepi ronde 2-4: + k7 λ10, λ11, λ12 | 2026-11-09 21:40:50 | 2026-11-09 22:47:42 | 1:06:52 | rc 3 (berhenti di batas λ12) | logs_local/E10c_edge_k7l10.log, _k7l11.log, _k7l12.log (selesai 22:02:58, 22:25:15, 22:47:41) | ODS GWi naik monoton sampai λ12 (+0,0006 per langkah terakhir): tidak ada optimum interior (FINDINGS F4) |  |
| D-03 | keputusan | Pilih opsi A: kriteria seleksi ODS GWi+ODPS (amandemen 2), semua temuan dilaporkan terbuka | 2026-11-09 23:15:02 |  |  | disetujui |  |  |  |
| PR-4 | commit | Amandemen 2 dan buku temuan FINDINGS.md | 2026-11-09 23:18:37 |  |  | selesai | config.yaml, FINDINGS.md |  | commit 31494a6; tag prereg-dsp-amend2-2026-11-09 |
| E10d | run | Seleksi amandemen 2, ronde 1-3 (+ k9 λ9, k9 λ10) | 2026-11-09 23:19:12 | 2026-11-10 00:04:28 | 0:45:16 | rc 0 | results/selection/; logs_local/E10d_amend2_round1-3.log (selesai 23:19:14, 23:40:56, 00:04:28) | Terpilih k9 λ9, d 4,5 (rata-rata ODS GWi+ODPS 0,5558; BSDS500 0,4953; BIPED 0,6163). k9 λ10 0,5552 (plateau) |  |
| D-04 | keputusan | OIS/AP memakai akumulasi dataset, selaras dengan A-GWi | 2026-11-09 23:53:34 |  |  | disetujui |  |  |  |
| E11c | run | Ablasi di k9 λ9: λ 3-10 × d; N, σ/λ, γ (BSDS500 train+val) | 2026-11-10 00:04:28 | 2026-11-10 00:52:53 | 0:48:25 | rc 0 | results/ablation/; logs_local/E11c_amend2_ablation.log | d = λ/2 hampir optimal (selisih ≤ 0,0034); N = 4 setara N = 8; σ/λ dan γ mengubah ODS ≤ 0,0006 |  |
| X-01 | diagnostik | Diagnostik border zero padding vs reflect-101 (20 citra BSDS500 val), bukan hasil untuk naskah | 2026-11-10 00:09:52 |  |  | selesai sebelum 00:24:35 | FINDINGS.md H5 | Pada zero padding 15-20% piksel di atas ambang berada di pita tepi; F per citra +0,03 s.d. +0,05 dengan reflect | tools/session/border_diag.py |
| D-05 | keputusan | Zero padding dipertahankan, seleksi tidak diulang (sekitar 10 jam) | 2026-11-10 00:24:28 |  |  | diputuskan |  |  |  |
| D-06 | keputusan | Tidak menambah baris sensitivitas border (tidak diminta reviewer) | 2026-11-10 00:35:58 |  |  | diputuskan |  |  |  |

## Fase 2. Penetapan konfigurasi & evaluasi uji (agenda 10 Nov)

| ID | Jenis | Kegiatan | Mulai | Selesai | Durasi | Status | Output | Hasil | Ref |
|---|---|---|---|---|---|---|---|---|---|
| E12 | run | Freeze: config_final.yaml dengan 14 metode | 2026-11-10 00:54:19 | 2026-11-10 00:54:20 | 0:00:01 | rc 0 | results/freeze/freeze.json; results/config_final.yaml | k9 λ9 dan k5 λ4 (GWi, GWi+ODPS, GWC raw, GWC zero-DC) + 6 baseline |  |
| D-07 | keputusan | Persetujuan freeze | 2026-11-10 00:57:21 |  |  | disetujui |  | "Ya, freeze" |  |
| PR-5 | commit | Freeze | 2026-11-10 00:57:31 |  |  | selesai |  |  | commit 7ae7ba5; tag freeze-2026-11-10 |
| D-08 | keputusan | Persetujuan menjalankan E20 | 2026-11-10 00:59:21 |  |  | disetujui |  | "Jalankan sekarang" |  |
| E20 | run | Evaluasi data uji, sekali: 14 metode × BSDS500 (200), BIPED (50), UDED (30) + cek reproduksi | 2026-11-10 00:59:36 | 2026-11-10 03:27:08 | 2:27:32 | rc 0 | results/test/summary.csv; results/test/legacy_check.csv; logs_local/E20_test.log | Angka submit k5 λ4 tereproduksi tepat 4 desimal. GWi+ODPS k9 λ9: 0,5120 / 0,6281 / 0,6451. GaussGradMag σ1,4 peringkat 1 di ketiga dataset |  |
| A-01 | analisis | Analisis E20 dan pencatatan F20-F24 di FINDINGS.md | 2026-11-10 03:27:08 | 2026-11-10 03:30:48 | 0:03:40 | selesai | FINDINGS.md bagian I |  |  |

## Fase 3. Analisis & pengukuran (agenda 11-14 Nov)

| ID | Jenis | Kegiatan | Mulai | Selesai | Durasi | Status | Output | Hasil | Ref |
|---|---|---|---|---|---|---|---|---|---|
| D-09 | keputusan | Persetujuan E22 dan penyimpanan riwayat proses | 2026-11-10 05:25:32 |  |  | disetujui |  |  |  |
| E22 | run | Statistik berpasangan: bootstrap 2000 (95% CI ΔODS), Wilcoxon + Holm | 2026-11-10 05:26:10 | 2026-11-10 05:27:41 | 0:01:31 | rc 0 | results/stats/pairs.csv; variability.csv; claims_guard.json; logs_local/E22_stats.log | ODPS vs GWi: meningkat di BSDS500 (+0,0122; CI [0,0090; 0,0158]); tidak berbeda di BIPED dan UDED. GWi di atas GWC raw dan GWC zero-DC di ketiga dataset | commit 7ae7ba5 (tools/run_logged.sh) |
| A-02 | analisis | Analisis E22 (F25) dan penyusunan riwayat proses (PROCESS_LOG.md, process_log.csv/json) | 2026-11-10 05:27:41 | 2026-11-10 05:33:44 | 0:06:03 | selesai | FINDINGS.md F25; PROCESS_LOG.md; process_log.csv; process_log.json |  |  |
| A-03 | analisis | Integrasi riwayat proses ke halaman agenda KDC (bagian Riwayat proses eksperimen) | 2026-11-10 05:46:49 | 2026-11-10 05:52:08 | 0:05:19 | selesai | kdc: index.html; revisi_dsp_log.json | Diuji di preview lokal, di-push ke kdc main, dan tampil di https://kdc-2026.vercel.app/agenda | kdc commit 0eb2b27 |
| E21 | run | Ablasi preprocessing (R2.7) |  |  |  | belum dijalankan |  |  |  |
| E23 | run | Evaluasi peta detektor deep learning eksternal (R1.2) |  |  |  | belum dijalankan |  | Butuh peta TEED/PiDiNet/LDC |  |
| E24 | run | Pengukuran waktu (R1.4, R2.10, R3.3, R3.6), satu thread, mesin idle |  |  |  | belum dijalankan |  |  |  |
| E25 | run | Kualitatif ODPS (R1.3) |  |  |  | belum dijalankan |  |  |  |
| E26 | run | Tabel akhir |  |  |  | belum dijalankan |  |  |  |

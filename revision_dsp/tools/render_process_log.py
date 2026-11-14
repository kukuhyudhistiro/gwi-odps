"""Render the process history of the revision from process_log.csv.

process_log.csv is the source (one row per run, commit, decision or analysis
step; times in WIB, UTC+7). This script writes:
    PROCESS_LOG.md    readable history for the experiment work report
    process_log.json  the same rows with durations, for the KDC agenda page

Usage (from revision_dsp):  .venv/Scripts/python.exe tools/render_process_log.py
                            [--kdc <path to the kdc site folder>]   (also writes kdc/revisi_dsp_log.json)
Timing of a new stage: run it with  bash tools/run_logged.sh <id> <stage>,  which
appends start, end, duration and exit code to logs_local/runs.csv; then add the
row to process_log.csv and run this script.
"""
import argparse
import csv
import json
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "process_log.csv"

# Agenda of the KDC page (https://kdc-2026.vercel.app/agenda), Revisi Paper 1 DSP
AGENDA = {
    1: ("7-9 Nov", "Persiapan data & eksperimen"),
    2: ("10 Nov", "Penetapan konfigurasi & evaluasi uji"),
    3: ("11-14 Nov", "Analisis & pengukuran"),
    4: ("15-18 Nov", "Penulisan ulang"),
    5: ("19 Nov", "Kirim draf"),
    6: ("20-21 Nov", "Telaah Promotor & Ko-promotor"),
    7: ("22 Nov", "Perbaikan akhir"),
    8: ("23 Nov", "Unggah revisi"),
    9: ("24 Nov", "Batas akhir dari editor"),
}
FMT = "%Y-%m-%d %H:%M:%S"


def parse(s):
    try:
        return datetime.strptime(s, FMT)
    except (TypeError, ValueError):
        return None


def hms(sec):
    h, r = divmod(int(sec), 3600)
    m, s = divmod(r, 60)
    return f"{h}:{m:02d}:{s:02d}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--kdc", help="path of the local KDC repo clone; also writes revisi_dsp_log.json there")
    args = ap.parse_args()
    rows = list(csv.DictReader(SRC.open(encoding="utf-8")))
    bad = [r["id"] for r in rows if None in r or None in r.values()]
    if bad:
        raise SystemExit(f"wrong number of columns (quote fields with commas): {bad}")
    for r in rows:
        a, b = parse(r["start"]), parse(r["end"])
        r["duration_s"] = int((b - a).total_seconds()) if a and b else None
        r["duration"] = hms(r["duration_s"]) if r["duration_s"] is not None else ""
        r["phase"] = int(r["phase"])
    def dump(rs, source):
        return json.dumps({"timezone": "WIB (UTC+7)", "source": source,
                           "generated": datetime.now().strftime(FMT),
                           "agenda": {str(k): {"dates": v[0], "name": v[1]} for k, v in AGENDA.items()},
                           "rows": rs}, ensure_ascii=False, indent=1) + "\n"

    (ROOT / "process_log.json").write_text(dump(rows, "gwi-odps, revision_dsp/process_log.csv"),
                                           encoding="utf-8", newline="\n")
    if args.kdc:
        # Data file of the "Riwayat proses eksperimen" section of the KDC agenda page.
        # Only rows marked web = ya: the stages of the runbook (E00-E26) and the
        # pre-registration tags. web_status / web_note replace status / result there.
        web = []
        for r in rows:
            if r.get("web") != "ya":
                continue
            w = {k: v for k, v in r.items() if not k.startswith("web")}
            if r.get("web_status"):
                w["status"] = r["web_status"]
            elif w["status"] == "rc 0":
                w["status"] = "selesai"
            if r.get("web_note"):
                w["result"] = r["web_note"]
            web.append(w)
        (Path(args.kdc) / "revisi_dsp_log.json").write_text(
            dump(web, "gwi-odps, revision_dsp (tahapan sesuai runbook revisi)"), encoding="utf-8", newline="\n")
        print(f"-> {Path(args.kdc) / 'revisi_dsp_log.json'} ({len(web)} rows)")

    out = ["# Riwayat proses eksperimen: revisi Paper 1 DSP-D-26-02462 (GWi+ODPS)", "",
           "Dibuat dari `process_log.csv` oleh `tools/render_process_log.py`; jangan diedit langsung.",
           "Waktu dalam WIB (UTC+7). Durasi = selesai − mulai (j:mm:ss).",
           "Fase mengikuti agenda KDC (https://kdc-2026.vercel.app/agenda).",
           "Sumber waktu: log di `logs_local/`, `logs_local/runs.csv` (tools/run_logged.sh),",
           "commit dan tag git, dan riwayat sesi kerja. Baris tanpa jam ditandai di kolom Ref.",
           "Temuan lengkap ada di FINDINGS.md; perubahan protokol di CHANGELOG.md.",
           "Kolom Web: baris yang ditampilkan di halaman agenda KDC (tahapan runbook dan tag pra-registrasi).",
           "Kolom Komentar reviewer: komentar yang dijawab tahap itu (register komentar, runbook §6-§7).",
           "Baris yang bukan jawaban atas komentar reviewer ditandai 'pendukung' atau 'bukan permintaan reviewer'.",
           "Susunan tiap baris (juga di halaman KDC): judul dan kode; waktu dan durasi; status dan komentar reviewer;",
           "hasil; temuan/catatan; file output (log, CSV, gambar). File di `logs_local/` hanya ada di mesin lokal.", ""]
    out += ["## Ringkasan per fase", "",
            "| Fase | Agenda | Kegiatan tercatat | Waktu komputasi (run) | Belum dijalankan |",
            "|---|---|---|---|---|"]
    for p, (dates, name) in AGENDA.items():
        pr = [r for r in rows if r["phase"] == p]
        if not pr:
            continue
        comp = sum(r["duration_s"] or 0 for r in pr if r["kind"] == "run")
        todo = [r["id"] for r in pr if r["status"].startswith("belum")]
        out.append(f"| {p}. {name} | {dates} | {len(pr) - len(todo)} | {hms(comp)} | "
                   f"{', '.join(todo) or '-'} |")
    out.append("")
    for p, (dates, name) in AGENDA.items():
        pr = [r for r in rows if r["phase"] == p]
        if not pr:
            continue
        out += [f"## Fase {p}. {name} (agenda {dates})", "",
                "| ID | Judul | Jenis | Kegiatan | Mulai | Selesai | Durasi | Status | Komentar reviewer | Hasil | Temuan/Catatan | File output | Ref | Web |",
                "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
        for r in pr:
            cells = [r["id"], r.get("title", ""), r["kind"], r["activity"], r["start"], r["end"],
                     r["duration"], r["status"], r.get("reviewer", ""), r["result"], r.get("finding", ""),
                     r["outputs"], r["ref"], "ya" if r.get("web") == "ya" else ""]
            out.append("| " + " | ".join(c.replace("|", "/") for c in cells) + " |")
        out.append("")
    (ROOT / "PROCESS_LOG.md").write_text("\n".join(out), encoding="utf-8", newline="\n")
    print(f"{len(rows)} rows -> PROCESS_LOG.md, process_log.json")


if __name__ == "__main__":
    main()

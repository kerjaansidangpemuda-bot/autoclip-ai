
import argparse
import json
import re
import subprocess
import sys
import urllib.request
from pathlib import Path
from urllib.parse import urlparse

OUT = Path("output")
MAX_SIZE = 500 * 1024 * 1024


def run(cmd):
    subprocess.run(cmd, check=True)


def duration(path):
    result = subprocess.run(
        [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "json", str(path)
        ],
        capture_output=True,
        text=True,
        check=True
    )
    return float(json.loads(result.stdout)["format"]["duration"])


def allowed_github(url):
    parsed = urlparse(url)
    host = (parsed.hostname or "").lower()

    return (
        parsed.scheme == "https"
        and (
            host == "github.com"
            or host.endswith(".github.com")
            or host == "githubusercontent.com"
            or host.endswith(".githubusercontent.com")
            or host == "githubassets.com"
            or host.endswith(".githubassets.com")
        )
    )


class SafeRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if not allowed_github(newurl):
            raise ValueError("Redirect lampiran tidak diizinkan.")
        return super().redirect_request(
            req, fp, code, msg, headers, newurl
        )


def acquire(url):
    parsed = urlparse(url)
    host = (parsed.hostname or "").lower()

    if parsed.scheme != "https":
        raise ValueError("URL harus menggunakan HTTPS.")

    platform = (
        host in ("youtube.com", "youtu.be", "tiktok.com")
        or host.endswith(".youtube.com")
        or host.endswith(".tiktok.com")
    )

    if platform:
        run([
            "yt-dlp",
            "--no-playlist",
            "--max-filesize", "500M",
            "-f", "bv*+ba/b",
            "--merge-output-format", "mp4",
            "-o", "source.%(ext)s",
            url
        ])

        paths = [
            p for p in Path(".").glob("source.*")
            if p.suffix.lower() in (".mp4", ".mkv", ".webm")
        ]

        if not paths:
            raise RuntimeError("Gagal mengambil video dari platform.")

        return paths[0]

    if not allowed_github(url):
        raise ValueError("Link lampiran harus berasal dari GitHub.")

    opener = urllib.request.build_opener(SafeRedirect())
    request = urllib.request.Request(
        url, headers={"User-Agent": "AUTOCLIP-AI/1.2"}
    )

    with opener.open(request, timeout=60) as response:
        if not allowed_github(response.url):
            raise ValueError("Redirect lampiran tidak diizinkan.")

        with open("source.mp4", "wb") as file:
            size = 0

            while True:
                chunk = response.read(1024 * 1024)

                if not chunk:
                    break

                size += len(chunk)

                if size > MAX_SIZE:
                    raise ValueError("File melebihi 500 MB.")

                file.write(chunk)

    return Path("source.mp4")


def transcribe(src):
    from faster_whisper import WhisperModel

    model = WhisperModel(
        "tiny", device="cpu", compute_type="int8"
    )

    segments, _ = model.transcribe(
        str(src), vad_filter=True, beam_size=1
    )

    return [
        {
            "start": s.start,
            "end": s.end,
            "text": s.text.strip()
        }
        for s in segments
    ]


def windows(segs, d):
    if d < 45:
        raise ValueError("Video harus minimal 45 detik.")

    length = min(25.0, d / 3.0)
    candidates = []

    for s in segs:
        a = max(0.0, min(d - length, s["start"] - 1))
        b = a + length

        covered = [
            x for x in segs
            if x["start"] < b and x["end"] > a
        ]

        score = sum(
            len(x["text"].split()) for x in covered
        )

        candidates.append((score, a, b))

    candidates.sort(reverse=True)
    picked = []

    for _, a, b in candidates:
        if all(b <= x or a >= y for x, y in picked):
            picked.append((a, b))

        if len(picked) == 3:
            break

    if len(picked) < 3:
        picked = [
            (i * length, (i + 1) * length)
            for i in range(3)
        ]

    return sorted(picked)


def srt(segs, a, b, path):
    def ts(value):
        n = round(max(0, value) * 1000)
        h, n = divmod(n, 3600000)
        m, n = divmod(n, 60000)
        s, n = divmod(n, 1000)

        return f"{h:02}:{m:02}:{s:02},{n:03}"

    lines = []
    index = 1

    for seg in segs:
        x = max(a, seg["start"])
        y = min(b, seg["end"])

        if y - x < 0.15 or not seg["text"]:
            continue

        lines.extend([
            str(index),
            f"{ts(x-a)} --> {ts(y-a)}",
            seg["text"],
            ""
        ])

        index += 1

    path.write_text(
        "\n".join(lines), encoding="utf-8"
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", required=True)
    args = parser.parse_args()

    OUT.mkdir(exist_ok=True)

    print("Mengambil video...", flush=True)
    src = acquire(args.url)

    print("Menganalisis video...", flush=True)
    d = duration(src)
    segs = transcribe(src)
    spans = windows(segs, d)

    for i, (a, b) in enumerate(spans, 1):
        print(f"Membuat Shorts {i}/3...", flush=True)

        srt(segs, a, b, OUT / f"clip_{i}.srt")

        vf = (
            "scale=720:1280:"
            "force_original_aspect_ratio=increase,"
            "crop=720:1280,setsar=1"
        )

        run([
            "ffmpeg",
            "-hide_banner", "-loglevel", "error",
            "-y",
            "-ss", str(a),
            "-i", str(src),
            "-t", str(b-a),
            "-vf", vf,
            "-c:v", "libx264",
            "-preset", "veryfast",
            "-crf", "27",
            "-c:a", "aac",
            "-b:a", "96k",
            "-movflags", "+faststart",
            str(OUT / f"clip_{i}.mp4")
        ])

    print("SELESAI! 3 Shorts tersedia di output/")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)

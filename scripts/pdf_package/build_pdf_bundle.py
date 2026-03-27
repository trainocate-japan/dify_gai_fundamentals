#!/usr/bin/env python
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def as_file_uri(path: Path) -> str:
    # Preserve Windows drive letters and encode spaces safely.
    posix = path.resolve().as_posix()
    return f"file:///{quote(posix)}"


def find_chrome(explicit_path: str | None) -> Path:
    if explicit_path:
        p = Path(explicit_path)
        if p.exists():
            return p
        raise FileNotFoundError(f"chrome path not found: {p}")

    env_path = os.environ.get("CHROME_PATH")
    if env_path:
        p = Path(env_path)
        if p.exists():
            return p

    candidates = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        "/c/Program Files/Google/Chrome/Application/chrome.exe",
        "/c/Program Files (x86)/Google/Chrome/Application/chrome.exe",
        "/c/Program Files/Microsoft/Edge/Application/msedge.exe",
        "/c/Program Files (x86)/Microsoft/Edge/Application/msedge.exe",
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
        "/usr/bin/google-chrome",
        "/usr/bin/chromium",
        "/usr/bin/chromium-browser",
        "/snap/bin/chromium",
    ]
    for candidate in candidates:
        p = Path(candidate)
        if p.exists():
            return p

    raise FileNotFoundError(
        "Chrome/Edge executable not found. Set CHROME_PATH or pass --chrome."
    )


def run(cmd: list[str], cwd: Path | None = None) -> None:
    subprocess.run(cmd, cwd=str(cwd) if cwd else None, check=True)


def collect_markdown_files(docs_dir: Path) -> list[Path]:
    mds: list[Path] = []
    for p in docs_dir.rglob("*.md"):
        rel_parts = p.relative_to(docs_dir).parts
        if "assets" in rel_parts:
            continue
        mds.append(p)
    return sorted(mds)


def build_bundle(
    repo_root: Path,
    output_dir: Path,
    temp_dir: Path,
    chrome_path: Path,
    clean: bool,
    keep_temp: bool,
) -> None:
    docs_dir = repo_root / "docs"
    downloads_zip = docs_dir / "downloads" / "downloads.zip"
    scripts_dir = repo_root / "scripts" / "pdf_package"
    preprocess_script = scripts_dir / "preprocess_mkdocs_admonitions.py"
    css_file = scripts_dir / "pdf_style.css"

    if not docs_dir.exists():
        raise FileNotFoundError(f"docs dir not found: {docs_dir}")
    if not preprocess_script.exists():
        raise FileNotFoundError(f"preprocess script not found: {preprocess_script}")
    if not css_file.exists():
        raise FileNotFoundError(f"css file not found: {css_file}")
    if not downloads_zip.exists():
        raise FileNotFoundError(f"downloads zip not found: {downloads_zip}")

    markdown_files = collect_markdown_files(docs_dir)
    if not markdown_files:
        raise RuntimeError("No markdown files found under docs/")

    if clean and output_dir.exists():
        shutil.rmtree(output_dir)
    output_pdf_root = output_dir / "pdf"
    output_downloads_root = output_dir / "downloads"
    output_pdf_root.mkdir(parents=True, exist_ok=True)
    output_downloads_root.mkdir(parents=True, exist_ok=True)

    if temp_dir.exists() and clean:
        shutil.rmtree(temp_dir)
    temp_dir.mkdir(parents=True, exist_ok=True)

    generated: list[dict[str, str]] = []

    for src_md in markdown_files:
        rel_md = src_md.relative_to(docs_dir)
        rel_pdf = rel_md.with_suffix(".pdf")
        out_pdf = output_pdf_root / rel_pdf
        out_pdf.parent.mkdir(parents=True, exist_ok=True)

        pre_md = temp_dir / rel_md.with_suffix(".pre.md")
        html = temp_dir / rel_md.with_suffix(".html")
        pre_md.parent.mkdir(parents=True, exist_ok=True)
        html.parent.mkdir(parents=True, exist_ok=True)

        run([sys.executable, str(preprocess_script), str(src_md), str(pre_md)])

        resource_path = os.pathsep.join([str(docs_dir), str(src_md.parent), str(temp_dir)])
        title = rel_md.as_posix()
        run(
            [
                "pandoc",
                str(pre_md),
                "-f",
                "gfm+fenced_divs",
                "-t",
                "html5",
                "-s",
                "--syntax-highlighting=none",
                "--embed-resources",
                "--metadata",
                f"title={title}",
                "--css",
                str(css_file),
                "--resource-path",
                resource_path,
                "-o",
                str(html),
            ]
        )

        run(
            [
                str(chrome_path),
                "--headless=new",
                "--disable-gpu",
                f"--print-to-pdf={out_pdf}",
                "--print-to-pdf-no-header",
                as_file_uri(html),
            ]
        )

        generated.append(
            {
                "source_md": rel_md.as_posix(),
                "output_pdf": Path("pdf", rel_pdf).as_posix(),
                "source_sha256": sha256_file(src_md),
                "pdf_sha256": sha256_file(out_pdf),
            }
        )

    copied_zip = output_downloads_root / "downloads.zip"
    shutil.copy2(downloads_zip, copied_zip)

    # Remove stale PDFs that are no longer mapped from source markdown.
    if output_pdf_root.exists():
        expected_disk = {str((output_pdf_root / p.relative_to(docs_dir).with_suffix(".pdf")).resolve()) for p in markdown_files}
        for existing in output_pdf_root.rglob("*.pdf"):
            if str(existing.resolve()) not in expected_disk:
                try:
                    existing.unlink()
                except OSError:
                    # Non-fatal: stale files can remain if locked by another process.
                    pass

    # Safety checks: missing PDF or count mismatch should fail the build.
    expected_set = {p.relative_to(docs_dir).with_suffix(".pdf").as_posix() for p in markdown_files}
    actual_set = {Path(item["output_pdf"]).relative_to("pdf").as_posix() for item in generated}
    if expected_set != actual_set:
        missing = sorted(expected_set - actual_set)
        extra = sorted(actual_set - expected_set)
        raise RuntimeError(
            "PDF output mismatch. "
            f"missing={missing[:5]} extra={extra[:5]} "
            f"(missing_count={len(missing)} extra_count={len(extra)})"
        )

    manifest = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_count": len(markdown_files),
        "pdf_count": len(generated),
        "downloads_zip": {
            "path": str(Path("downloads") / "downloads.zip"),
            "sha256": sha256_file(copied_zip),
        },
        "files": generated,
    }
    manifest_path = output_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    summary = (
        f"PDF bundle generated successfully.\n"
        f"- source markdown: {len(markdown_files)}\n"
        f"- output pdf:      {len(generated)}\n"
        f"- bundle dir:      {output_dir}\n"
        f"- manifest:        {manifest_path}\n"
    )
    (output_dir / "SUMMARY.txt").write_text(summary, encoding="utf-8")
    print(summary.strip())

    if not keep_temp and temp_dir.exists():
        try:
            shutil.rmtree(temp_dir)
        except OSError as exc:
            # Non-fatal (e.g. OneDrive/AV/chrome lock). Temp files can remain.
            print(f"[pdf-bundle] warning: failed to clean temp dir: {exc}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build PDF bundle from docs markdown (excluding docs/assets)."
    )
    parser.add_argument(
        "--out",
        default="local_artifacts/pdf_bundle",
        help="Output directory for generated bundle.",
    )
    parser.add_argument(
        "--temp",
        default=".tmp_pdf_build",
        help="Temporary working directory.",
    )
    parser.add_argument(
        "--chrome",
        default=None,
        help="Path to Chrome/Edge executable. Optional if CHROME_PATH is set.",
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Clean output/temp directories before build.",
    )
    parser.add_argument(
        "--keep-temp",
        action="store_true",
        help="Keep temporary files after build.",
    )
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[2]
    output_dir = (repo_root / args.out).resolve()
    temp_dir = (repo_root / args.temp).resolve()

    try:
        chrome_path = find_chrome(args.chrome)
        build_bundle(
            repo_root=repo_root,
            output_dir=output_dir,
            temp_dir=temp_dir,
            chrome_path=chrome_path,
            clean=args.clean,
            keep_temp=args.keep_temp,
        )
    except Exception as exc:
        print(f"[pdf-bundle] ERROR: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

# PDF Bundle Automation (Local)

## What it does

- Converts all `docs/**/*.md` (excluding files under `docs/assets/`) to PDF.
- Keeps folder structure under `local_artifacts/pdf_bundle/pdf/`.
- Copies `docs/downloads/downloads.zip` to `local_artifacts/pdf_bundle/downloads/`.
- Creates `manifest.json` and `SUMMARY.txt` to verify no missing output.

## Run manually

```powershell
python scripts/pdf_package/build_pdf_bundle.py
```

## Install pre-push hook

```powershell
git config core.hooksPath .githooks
```

After this, every `git push` runs local PDF generation first.
(`.githooks/pre-push` -> `scripts/pdf_package/pre_push_pdf_bundle.ps1`)
The hook is optimized to run only when pushed changes include `docs/` (excluding `docs/assets/`).

## Optional controls

- Full clean build:

```powershell
python scripts/pdf_package/build_pdf_bundle.py --clean
```

- Skip once:

```powershell
$env:SKIP_PDF_BUNDLE="1"; git push
```

- Custom browser path:

```powershell
python scripts/pdf_package/build_pdf_bundle.py --chrome "C:\Program Files\Google\Chrome\Application\chrome.exe"
```

# PDF配布物 運用手順（短縮版）

このファイルは、受講者向けPDF配布物をローカルで作成・確認するための最小手順です。

## 1. 前提

- Python 3.x
- `pandoc`
- Chrome または Edge（headless PDF出力用）

## 2. 初回設定（1回だけ）

```bash
git config core.hooksPath .githooks
```

これで `git push` 時に pre-push フックが有効になります。

## 3. 通常運用

1. `docs/` を更新する
2. `git add` / `git commit`
3. `git push`

push時に、**push対象に `docs/` 変更がある場合のみ** PDF生成が実行されます。  
`docs/assets/` のみ変更ならPDF生成はスキップされます。

## 4. 手動で生成したい場合

```bash
python scripts/pdf_package/build_pdf_bundle.py
```

出力先:

- `local_artifacts/pdf_bundle/pdf/`（PDF本体）
- `local_artifacts/pdf_bundle/downloads/downloads.zip`
- `local_artifacts/pdf_bundle/manifest.json`
- `local_artifacts/pdf_bundle/SUMMARY.txt`

完全再生成（出力を一度クリーン）:

```bash
python scripts/pdf_package/build_pdf_bundle.py --clean
```

## 5. 一時的にフックをスキップしたい場合

PowerShell:

```powershell
$env:SKIP_PDF_BUNDLE="1"; git push
```

Bash:

```bash
SKIP_PDF_BUNDLE=1 git push
```

## 6. よくあるエラー

- `Chrome/Edge executable not found`  
  Chrome または Edge をインストールし、必要なら `CHROME_PATH` を設定。

- `.tmp_pdf_build` の削除警告（アクセス拒否）  
  OneDrive/AV/ブラウザロック時に発生することがあります。  
  生成自体が成功していれば運用上は問題ありません。


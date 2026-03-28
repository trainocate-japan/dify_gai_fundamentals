# dify_gai_fundamentals

## 使い方

このリポジトリは MkDocs を使用して、`docs/` 配下の教材をビルド・配信します。

### ローカルプレビュー

1. Python 3.x をインストールします。
2. 依存関係をインストールします:

```bash
pip install -r requirements.txt
```

3. ローカルサーバーを起動します:

```bash
mkdocs serve
```

表示されたローカルURL（通常は `http://127.0.0.1:8000`）をブラウザで開いてください。

### 静的サイトのビルド

```bash
mkdocs build
```

生成されたファイルは `site/` に出力されます。

### PDF配布物のローカル生成（push前チェック用）

受講者向け配布のために、`docs/assets` を除く `docs/**/*.md` を PDF 化し、
`downloads.zip` を同梱したバンドルをローカルで作成できます。

事前に以下が必要です。

- `pandoc`
- Chrome/Edge（headless PDF出力に使用）

```bash
python scripts/pdf_package/build_pdf_bundle.py
```

生成先は `local_artifacts/pdf_bundle/` です。
漏れ確認用に `manifest.json` と `SUMMARY.txt` も作成されます。

完全再生成（出力先を一度クリーンにする）:

```bash
python scripts/pdf_package/build_pdf_bundle.py --clean
```

#### push前に自動実行したい場合

```bash
git config core.hooksPath .githooks
```

これで `git push` 時に `pre-push` フックが走り、ローカルでPDFバンドル生成を実行します。
ただし、最適化のため **push対象に `docs/` の変更がある場合のみ** 実行されます（`docs/assets/` は除外）。
生成に失敗した場合は push を中断します。

一時的にスキップする場合:

```bash
SKIP_PDF_BUNDLE=1 git push
```

PowerShell の場合:

```powershell
$env:SKIP_PDF_BUNDLE="1"; git push
```

### GitHub Pages（自動デプロイ）

`main` ブランチへの push をトリガーに、GitHub Actions（`.github/workflows/deploy.yml`）が
`mkdocs gh-deploy --force` を実行し、生成したサイトを `gh-pages` ブランチへ公開します。
GitHub Pages を有効化し、ソースを `gh-pages` ブランチ（root）に設定すると、
GitHub Pages でサイトが閲覧できます。

### Azure Static Web Apps（バックアップ配信）

企業ネットワーク制限などで GitHub Pages にアクセスできない場合に備え、Azure Static Web Apps へも同じコンテンツを配信します。

- ワークフロー: `.github/workflows/azure-static-web-apps-icy-sea-0bdb7af00.yml`
- トリガー: `main` ブランチへの `push`
- デプロイ方式: `mkdocs build` で `site/` を生成後、SWA にアップロード

これにより、`main` への push で以下 2 系統が同時に更新されます。

- GitHub Pages: `https://trainocate-japan.github.io/dify_gai_fundamentals/`
- Azure Static Web Apps: `https://icy-sea-0bdb7af00.1.azurestaticapps.net`

研修当日は、GitHub Pages を主系、Azure Static Web Apps を予備系として案内してください。

## License

(c) 2026 Trainocate, Inc.

本リポジトリは**トレノケート株式会社の研修目的に限り**公開されています。

- 明示的な許可なく、再利用・改変・再配布、研修用途、商用利用、派生物の作成はできません。

All rights reserved.

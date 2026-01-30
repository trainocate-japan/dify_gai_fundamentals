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

### GitHub Pages（自動デプロイ）

`main` ブランチへの push をトリガーに、GitHub Actions（`.github/workflows/deploy.yml`）が
`mkdocs gh-deploy --force` を実行し、生成したサイトを `gh-pages` ブランチへ公開します。
GitHub Pages を有効化し、ソースを `gh-pages` ブランチ（root）に設定すると、
GitHub Pages でサイトが閲覧できます。

## License

(c) 2026 Trainocate, Inc.

本リポジトリは**トレノケート株式会社の研修目的に限り**公開されています。

- 明示的な許可なく、再利用・改変・再配布、研修用途、商用利用、派生物の作成はできません。

All rights reserved.


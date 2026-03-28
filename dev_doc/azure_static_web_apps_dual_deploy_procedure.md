# Azure Static Web Apps 追加デプロイ手順（GitHub Pages 併用）

## 目的

研修受講者向けサイトを、以下の 2 系統で同時配信する。

- 主系: GitHub Pages
- 予備系: Azure Static Web Apps

これにより、企業ネットワーク制限などで片系にアクセスできない場合でも、もう片系で参照を継続できる。

## 前提

- リポジトリ: `trainocate-japan/dify_gai_fundamentals`
- 既存の GitHub Pages デプロイ: `.github/workflows/deploy.yml`（`main` push で `gh-pages` 公開）
- ドキュメント生成: MkDocs（`mkdocs build` の出力先は `site/`）

## 実施手順

### 1. Azure Static Web Apps リソースを作成

Azure Portal の「静的 Web アプリの作成」で以下を設定する。

- 組織: `trainocate-japan`
- リポジトリ: `dify_gai_fundamentals`
- 分岐: `main`
- ビルドのプリセット: `Custom`
- アプリの場所: `/`
- API の場所: 空欄
- 出力先: `site`
- デプロイ認可ポリシー: `GitHub`

作成完了後、GitHub 側に `azure-static-web-apps-<id>.yml` が自動作成される。

### 2. ローカルに最新 `main` を取り込む

```bash
git pull --ff-only origin main
```

### 3. Azure 用 workflow を MkDocs 向けに修正

対象ファイル:

- `.github/workflows/azure-static-web-apps-icy-sea-0bdb7af00.yml`

修正内容:

- Python セットアップを追加
- 依存インストールを追加（`pip install -r requirements.txt`）
- `mkdocs build` を実行して `site/` を先に生成
- SWA アクションは事前ビルド成果物をアップロードする設定へ変更
  - `app_location: "site"`
  - `output_location: ""`
  - `skip_app_build: true`

### 4. GitHub Pages workflow は維持

既存の `.github/workflows/deploy.yml` は削除しない。  
`main` への push 1 回で、以下 2 本の workflow が並行実行される構成にする。

- GitHub Pages 公開 (`deploy.yml`)
- Azure Static Web Apps 公開 (`azure-static-web-apps-*.yml`)

### 5. README に運用方針を追記

`README.md` に Azure Static Web Apps のバックアップ配信手順と URL を追記する。

追記要点:

- 二重配信の目的
- 使用 workflow 名
- `main` push で 2 系統同時更新されること
- GitHub Pages / Azure SWA の URL
- 研修時は主系/予備系として案内すること

### 6. commit / push

```bash
git add .github/workflows/azure-static-web-apps-icy-sea-0bdb7af00.yml README.md
git commit -m "Configure Azure SWA prebuilt deploy and document dual hosting"
git push origin main
```

## 動作確認

### GitHub Actions

`main` push 後に以下 2 ジョブが `Success` になることを確認する。

- GitHub Pages 用 workflow（`deploy.yml`）
- Azure SWA 用 workflow（`azure-static-web-apps-icy-sea-0bdb7af00.yml`）

### 公開 URL

両方で最新コンテンツが表示されることを確認する。

- GitHub Pages: `https://trainocate-japan.github.io/dify_gai_fundamentals/`
- Azure Static Web Apps: `https://icy-sea-0bdb7af00.1.azurestaticapps.net`

## 補足

- ローカルに `mkdocs` コマンドが未導入でも、Azure workflow 内で依存インストールとビルドを行うため CI 上で完結する。
- 将来、Azure リソースを再作成した場合は workflow ファイル名・シークレット名・公開 URL が変わる可能性があるため、README と本手順書を更新する。

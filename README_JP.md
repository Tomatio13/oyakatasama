<h1 align="center">Oyakata</h1>

<p align="center">
  <img src="assets/oyakata-crest.png" width="260" alt="武家社会の御館様を表す兜と旗の紋章" />
</p>

<p align="center">
  <a href="README.md">English</a> ·
  <a href="README_JP.md">日本語</a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Lead-Codex-412991?style=flat-square" alt="設定可能な Lead" />
  <img src="https://img.shields.io/badge/Routing-CodexBar-1f6feb?style=flat-square" alt="CodexBar による振り分け" />
  <img src="https://img.shields.io/badge/Contracts-YAML-cb171e?style=flat-square" alt="YAML 契約" />
</p>

Oyakata は、複雑なソフトウェア開発を設定可能な役割分担で進めるワークフローです。名称は現代の大工の親方ではなく、武家社会で家臣を率いる**御館様（おやかたさま）**をイメージしています。Lead が計画とレビューを担い、ゴールごとに独立したローカル契約を持ち、各タスクは担当 executor を記録します。CodexBar の残量情報による自動振り分けにも対応します。

## ⚙️ Executor 定義

[`executors.yaml`](./executors.yaml) は Lead、Reviewer、executor、コマンド、引数、モデル、quota provider、調査担当、selector 候補の唯一の定義です。このファイルを編集して、スキルが使うコマンドとモデルの組み合わせを変更します。

既定では Codex を Lead と Reviewer、Grok・OpenCode・Antigravity を executor として定義します。アーキテクチャ、セキュリティ、受け入れ判断、最終承認は設定済み Lead が担います。`executors.yaml` に API キー、Cookie、トークン、パスワード、`.env` の値を書かないでください。

## 🚀 使い方

対象の Git リポジトリで Codex を起動し、Oyakata を明示して依頼します。

```text
$oyakata

重複メールアドレスを拒否するユーザー登録とテストを実装してください。
README を実装済みの振る舞いに合わせて更新してください。
```

## 🔧 CodexBar CLI の準備

`selection` タスクを使う前に、公式 CodexBar CLI をユーザー自身でインストールしてください。Oyakata はダウンロード、インストール、更新、設定を行いません。

1. [CodexBar Releases](https://github.com/steipete/CodexBar/releases) から OS に合う CLI アーカイブをダウンロードします。
2. `CodexBarCLI` と `codexbar` のシンボリックリンクを `$HOME/.local/bin` などユーザー管理のディレクトリへ展開し、`PATH` に追加します。
3. 目的のバイナリと必要な provider が設定済みであることを確認します。

```bash
command -v codexbar
codexbar --version
codexbar usage --provider <quota_provider> --format json --pretty --no-color
python3 <skill-dir>/scripts/validate_executors.py <skill-dir>/executors.yaml <skill-dir>/references/.todo.yaml
```

公式 CLI は `--provider` と JSON 出力をサポートします。provider の認証情報と設定はユーザーが管理してください。

## 🗂️ 最小のゴール契約

```yaml
# .oyakata/L-001_auth_refactor.yaml
backlog:
  - id: T001
    title: 認証ドキュメントを更新する
    status: pending
    executor: agy
    executor_history:
      - executor: agy
        reason: ドキュメントタスク
        changed_by: lead
    target_files: [README.md]
    verification: git diff --check
```

`executor` には `executors.yaml` で定義した executor または selector のキーを指定します。

## 🔁 実行フロー

1. Lead はゴールごとに `.oyakata/L-NNN_short_goal.yaml` を作成します。
2. 契約にはゴール、制約、分割済みタスク、編集可能ファイル、検証、状態、`executor` を記録します。
3. executor は担当タスクを `pending` から `in_progress` に変更し、`target_files` だけを編集し、ローカル検証後に `completed` に変更します。
4. `executor` には `executors.yaml` の executor または selector キーを指定します。
5. selector の場合、Lead は `executors.yaml` の `quota_provider` ごとに公式 `codexbar` CLI を実行し、JSON の残量を比較します。
6. CodexBar が利用不能、失敗、または不正な JSON を返した場合、Lead は理由を残し、その selector の `fallback_executor` を使います。
7. 全タスク完了後、設定済み Reviewer が差分と検証を独立して確認します。指摘があれば同じゴール契約へ修正タスクを追加します。
8. 承認できるのは設定済み Reviewer だけです。

executor は自分の作業を承認したり、レビュー指摘を完了扱いにしたりできません。

## 📊 振り分け規則

selector は、各候補のすべての残量ウィンドウ中で最小の残量を使います。残量が最大の候補を優先し、最大値との差が5ポイント以内ならリセット時刻が早い候補を優先します。なお同じ場合は selector の `tie_breaker` を使います。CLI または残量結果が利用できない場合は `fallback_executor` を使います。

## 📁 ファイル

- `SKILL.md` — 完全なワークフローとコマンドテンプレート
- `executors.yaml` — ユーザーが編集する executor のコマンドとモデル
- `README.md` — 英語版の概要
- `README_JP.md` — 日本語版の概要
- `assets/oyakata-crest.png` — 御館様をイメージした紋章ロゴ
- `references/.todo.yaml` — ゴール契約へコピーするテンプレート
- `scripts/validate_executors.py` — executor とテンプレートの検証

## 📄 ライセンス

MIT

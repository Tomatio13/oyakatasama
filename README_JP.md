<h1 align="center">Oyakatasama</h1>

<p align="center">
  <img src="assets/oyakatasama-crest.jpg" width="260" alt="戦国武将の真田昌幸（お館様）をイメージした兜と旗の紋章" />
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

Oyakatasama は、複雑なソフトウェア開発を設定可能な役割分担で進めるワークフローです。名称は現代の大工の親方ではなく、戦国武将の真田昌幸のような家臣を率いる　**お館様（おやかたさま）**　をイメージしています。Lead が計画とレビューを担い、ゴールごとに独立したローカル契約を持ち、各タスクは担当 executor を記録します。CodexBar の残量情報による自動振り分けにも対応します。

## ⚙️ Executor 定義

[`executors.yaml`](./executors.yaml) は Lead、Reviewer、executor、コマンド、引数、モデル、quota provider、調査担当、selector 候補の唯一の定義です。このファイルを編集して、スキルが使うコマンドとモデルの組み合わせを変更します。

既定では Codex を Lead と Reviewer、Grok・OpenCode・Antigravity を executor として定義します。Lead と Reviewer は委譲先ではなく、タスクの `target_files` を編集しません。アーキテクチャ、セキュリティ、受け入れ判断、最終承認は設定済み Lead が担います。`executors.yaml` に API キー、Cookie、トークン、パスワード、`.env` の値を書かないでください。

## 🚀 使い方

対象の Git リポジトリで Codex を起動し、Oyakatasama を明示して依頼します。

```text
$oyakatasama

重複メールアドレスを拒否するユーザー登録とテストを実装してください。
README を実装済みの振る舞いに合わせて更新してください。
```

## 🔧 CodexBar CLI の準備

`selection` タスクを使う前に、公式 CodexBar CLI をユーザー自身でインストールしてください。Oyakatasama はダウンロード、インストール、更新、設定を行いません。また、残量を見るのは新しいゴール契約か修正 task で selector を使う時だけです。

1. [CodexBar Releases](https://github.com/steipete/CodexBar/releases) から OS に合う CLI アーカイブをダウンロードします。
2. `CodexBarCLI` と `codexbar` のシンボリックリンクを `$HOME/.local/bin` などユーザー管理のディレクトリへ展開し、`PATH` に追加します。
3. 目的のバイナリと必要な provider が設定済みであることを確認します。

```bash
command -v codexbar
codexbar --version
codexbar usage --provider <quota_provider> --format json --pretty --no-color
python3 <skill-dir>/scripts/validate_executors.py <skill-dir>/executors.yaml
```

ゴール契約が作成されたら、`python3 <skill-dir>/scripts/validate_executors.py <skill-dir>/executors.yaml .oyakatasama/L-001_auth_refactor.yaml` のように、実際の `L-NNN_*.yaml` を第二引数にして再検証してください。

公式 CLI は `--provider` と JSON 出力をサポートします。provider の認証情報と設定はユーザーが管理してください。

## 🗂️ 最小のゴール契約

```yaml
# .oyakatasama/L-001_auth_refactor.yaml
backlog:
  - id: T001
    title: 認証ドキュメントを更新する
    status: pending
    executor: agy
    executor_history:
      - executor: agy
        reason: ドキュメントタスク
        changed_by: lead
    delegation:
      approval: not_requested
      approved_executor: null
      approved_target_files: []
    target_files: [README.md]
    verification: git diff --check
```

`executor` には `executors.yaml` で定義した executor または selector のキーを指定します。

## 🔁 実行フロー

1. Lead はゴールごとに `.oyakatasama/L-NNN_short_goal.yaml` を作成します。
2. 契約にはゴール、制約、分割済みタスク、編集可能ファイル、検証、状態、`executor` を記録します。
3. executor は担当タスクを `pending` から `in_progress` に変更し、`target_files` だけを編集し、ローカル検証後に `completed` に変更します。
4. `executor` には `executors.yaml` の executor または selector キーを指定します。
5. Lead は実装を担当せず、すべてのタスクは `delegable: true` の executor へ割り当てます。
6. 外部 executor または CodexBar selector を実行する前に、Lead はプロジェクト制約が外部送信を許可するか確認し、executor と `target_files` を明示した承認を取得します。
7. 承認済み selector の場合、Lead は `executors.yaml` の `quota_provider` ごとに公式 `codexbar` CLI を実行し、JSON の残量を比較します。
8. fallback executor が選ばれた場合も、実行前にその executor への新しい承認を取得します。
9. 全タスク完了後、設定済み Reviewer が差分と検証を独立して確認します。指摘があれば同じゴール契約へ修正タスクを追加します。
10. 承認できるのは設定済み Reviewer だけです。

executor は自分の作業を承認したり、レビュー指摘を完了扱いにしたりできません。

## 🧭 停止点と次アクション

Oyakatasama は、終了時にステータスだけを返して終わるべきではありません。停止点では必ず次を返します。

1. 現在位置
2. 完了サマリまたは blocker の要約
3. 選択肢、推奨理由、コピペ用プロンプトからなる次アクション

次の場面では必ずこの形式にします。

- タスク完了
- レビュー完了
- 検証失敗
- quota ルーティング失敗
- 外部委譲の承認衝突

終了前には、未完了 task の有無、修正や再試行の要否、自然につながる次ゴールの有無も確認します。

未処理の task が残っているなら、黙って終わらず、次の task か次の stage を提案します。

同じゴールを翌日に再開するときは、まず active contract を読んで、現在位置、完了済み、保留中や blocker、次の具体アクションを返します。

## 📊 振り分け規則

承認済み selector は、各候補で設定した `quota_windows` だけを使います。`safe_remaining` が最大の候補を優先し、最大値との差が5ポイント以内ならリセット時刻が早い候補を優先します。なお同じ場合は selector の `tie_breaker` を使います。残量の再取得は新しい selector 付きゴール契約か修正 task を作る時だけにし、同じ契約の後続 task では読み直しません。CLI または残量結果が利用できない場合は `fallback_executor` を選び、実行前に承認を取得します。サンドボックスのログ、ソケット、権限エラーではタスクを pending のままにし、別 provider へ自動で切り替えません。

## 📁 ファイル

- `SKILL.md` — 完全なワークフローとコマンドテンプレート
- `executors.yaml` — ユーザーが編集する executor のコマンドとモデル
- `README.md` — 英語版の概要
- `README_JP.md` — 日本語版の概要
- `assets/oyakatasama-crest.jpg` — 戦国武将の真田昌幸（お館様）をイメージした紋章ロゴ
- `references/.todo.yaml` — ゴール契約へコピーするテンプレート
- `scripts/validate_executors.py` — executor とテンプレートの検証

## 📄 ライセンス

MIT

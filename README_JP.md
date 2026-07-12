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
- `references/contract_cli.md` — Contract CLI と直接編集の使い分け
- `references/executor_contract_update_policy.md` — contract 更新における executor 制約
- `references/legacy_contract_migration.md` — 古い invalid contract を移行すべきか判断する基準
- `scripts/todo_cli.py` — 契約の要約表示と task 状態更新
- `scripts/validate_executors.py` — executor とテンプレートの検証

## 🧰 Contract CLI

契約 YAML 全体を毎回 LLM に読ませず、小さく決定的に更新したい場合はローカル CLI を使います。詳細な運用規約は `references/contract_cli.md` に置き、この README では利用可能コマンドだけを要約します。

```bash
python3 scripts/todo_cli.py create "Implement duplicate-email-safe registration"
python3 scripts/todo_cli.py list-active
python3 scripts/todo_cli.py list-active --format text
python3 scripts/todo_cli.py summary .oyakatasama/L-001_auth_refactor.yaml
python3 scripts/todo_cli.py set-status .oyakatasama/L-001_auth_refactor.yaml T001 in_progress
python3 scripts/todo_cli.py assign .oyakatasama/L-001_auth_refactor.yaml T001 grok "Quota winner"
python3 scripts/todo_cli.py approve .oyakatasama/L-001_auth_refactor.yaml T001 grok README.md
python3 scripts/todo_cli.py add-learning .oyakatasama/L-001_auth_refactor.yaml "Fallback executor required fresh approval"
python3 scripts/todo_cli.py validate executors.yaml .oyakatasama/L-001_auth_refactor.yaml
```

現時点の対応範囲:

- `create` は `references/.todo.yaml` を次の `.oyakatasama/L-*.yaml` へ複製し、`project.id` と `project.goal` を埋めます。
- `list-active` は active / invalid / completed の状態と `recommended_contract` を返します。
- `list-active --format text` は再開判断向けの簡易要約を表示します。
- invalid 項目には Next Action 判断用の category / rule / auto-migration 候補情報を含みます。
- `summary` は project、task 件数、task メタデータをコンパクトな JSON で出力します。
- `set-status` は 1 task の状態を更新して契約へ書き戻します。
- `assign` は 1 task の executor を更新し、`executor_history` を追記します。
- `approve` は 1 task の delegation 承認内容を正確に記録します。
- `add-learning` は `learnings` に 1 行追記します。
- `validate` は `scripts/validate_executors.py` を再利用します。

active contract は機械更新される YAML として扱います。詳しい説明コメントは `references/.todo.yaml` テンプレート側に残し、CLI で書き戻した契約は整形が正規化されます。

ガード:

- 書き込み系コマンドは `references/.todo.yaml` を拒否します。更新対象は `.oyakatasama/` 配下の active contract だけです。

## 🧭 Contract 運用の参照先

詳細な運用ポリシーは、この README ではなく reference を見てください。

- `references/contract_cli.md` — 直接編集と決定的 CLI 更新のユースケース分離
- `references/executor_contract_update_policy.md` — Lead と委譲 executor の責務分離
- `references/legacy_contract_migration.md` — invalid / 履歴 contract の移行判断基準

`agy`、`grok`、`opencode` のような外部 executor が、repository 内のファイルだけから contract 管理ポリシー全体を自然に推論する前提は置きません。Lead としての Codex が次を担保します。

- route の選定
- `assign` と `approve` の記録
- 委譲 prompt の制約注入
- 戻ってきた contract 状態の validate

現在のゴールが明示されていないときは、次の推奨を書く前に `list-active` を使って再開対象を 1 つ選びます。これで repository 全体の曖昧な状態ではなく、選択済み contract に対して Next Action を返せます。

## 📄 ライセンス

MIT

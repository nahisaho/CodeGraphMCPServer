---
title: 'Claude Code + CodeGraph MCPでLinuxカーネルのコードを分析してみた'
tags:
  - Linux
  - Kernel
  - MCP
  - ClaudeCode
  - AI
private: false
updated_at: '2025-11-27'
id: null
organization_url_name: null
slide: false
---

# はじめに

Linuxカーネルは約3,000万行のCコードで構成される世界最大級のオープンソースプロジェクトです。その構造を理解するのは、熟練の開発者でも容易ではありません。

本記事では、**Claude Code**（Anthropic社のAIコーディングエージェント）と**CodeGraph MCP Server**を組み合わせて、Linuxカーネルのコードを効率的に分析する方法を紹介します。

## この記事でわかること

- Claude CodeでMCPサーバーを設定する方法
- CodeGraph MCPでLinuxカーネルをインデックスする方法
- Claude Codeを使ったカーネルコード分析の実例

## 前提条件

- Python 3.11以上
- Claude Code（`claude` CLIコマンド）
- Linuxカーネルソースコード

---

# 第1章 環境構築

## 1.1 CodeGraph MCPのインストール

```bash
# 仮想環境を作成
python -m venv .venv
source .venv/bin/activate

# CodeGraph MCPをインストール
pip install codegraph-mcp-server

# バージョン確認（v0.7.1以降でC言語サポート）
codegraph-mcp --version
```

## 1.2 Linuxカーネルソースの取得

```bash
# カーネルソースをクローン（shallow cloneで高速化）
git clone --depth 1 https://github.com/torvalds/linux.git
cd linux
```

## 1.3 Claude Code MCP設定

### 方法1: CLIコマンドで追加（推奨）

**stdio トランスポート（プロセス直接起動）:**

```bash
claude mcp add codegraph -- codegraph-mcp serve --repo /path/to/linux
```

**HTTP トランスポート（SSEサーバー経由）:**

まず別ターミナルでSSEサーバーを起動：

```bash
cd /path/to/linux
codegraph-mcp start --port 8080
```

次に Claude Code に追加：

```bash
claude mcp add --transport http codegraph http://0.0.0.0:8080
```

> **💡 ヒント**: HTTP トランスポートは複数のクライアントから同時接続でき、サーバーを起動したままインデックスを更新できます。

### 方法2: 設定ファイルで追加

Claude Codeの設定ファイル `~/.claude/claude_desktop_config.json` を編集：

```json
{
  "mcpServers": {
    "codegraph": {
      "command": "codegraph-mcp",
      "args": ["serve", "--repo", "/path/to/linux"]
    }
  }
}
```

または、プロジェクトごとの設定 `.mcp.json`：

```json
{
  "mcpServers": {
    "codegraph": {
      "command": "codegraph-mcp",
      "args": ["serve", "--repo", "."]
    }
  }
}
```

---

# 第2章 カーネルのインデックス作成

## 2.1 部分インデックス（推奨）

カーネル全体は巨大なので、まずは特定のサブシステムから始めます。

```bash
# kernel/ ディレクトリのみをインデックス
cd /path/to/linux
codegraph-mcp index ./kernel --full --no-community
```

**実行結果:**

```
┏━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━┓
┃ Metric        ┃ Value         ┃
┡━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━┩
│ Entities      │ 54,748        │
│ Relations     │ 142,532       │
│ Files Indexed │ 596           │
│ Files Skipped │ 0             │
│ Duration      │ 5.77s         │
└───────────────┴───────────────┘

Indexing completed successfully!
```

## 2.2 他のサブシステム

```bash
# メモリ管理
codegraph-mcp index ./mm --full --no-community

# ファイルシステム
codegraph-mcp index ./fs --full --no-community

# ネットワーク
codegraph-mcp index ./net --full --no-community
```

> **💡 ヒント**: `--no-community` オプションでコミュニティ検出をスキップすると、インデックス速度が向上します。

---

# 第3章 Claude Codeでの分析

## 3.1 Claude Codeの起動

```bash
cd /path/to/linux
claude
```

Claude Codeが起動すると、自動的にCodeGraph MCPサーバーが起動し、インデックスされたコードグラフが利用可能になります。

## 3.2 分析例1: スケジューラの構造を理解する

**プロンプト:**
```
Linuxカーネルのスケジューラの主要な関数とその関係を教えて
```

**Claude Codeの回答:**

```
CodeGraph MCPの query_codebase と find_dependencies を使用して分析しました。

## スケジューラの主要関数

### コアスケジューリング
1. **schedule()** - kernel/sched/core.c:6847
   - メインのスケジューリングエントリポイント
   - __schedule() を呼び出す

2. **__schedule()** - kernel/sched/core.c:6780
   - 実際のコンテキストスイッチを実行
   - pick_next_task() で次のタスクを選択
   - context_switch() でCPUコンテキストを切り替え

### タスク選択
3. **pick_next_task()** - kernel/sched/core.c:5890
   - スケジューリングクラスから次のタスクを選択
   - CFS、RT、Deadlineなど複数のスケジューラを考慮

### ウェイクアップ
4. **wake_up_process()** - kernel/sched/core.c:4534
   - スリープ中のプロセスを起床
   - try_to_wake_up() を呼び出す

5. **try_to_wake_up()** - kernel/sched/core.c:4234
   - タスクを実行可能状態にする
   - 適切なCPUにタスクをキューイング

## 呼び出し関係

schedule()
└── __schedule()
    ├── pick_next_task()
    │   └── fair_sched_class.pick_next_task()  [CFS]
    ├── context_switch()
    │   ├── switch_mm()
    │   └── switch_to()
    └── update_rq_clock()
```

## 3.3 分析例2: システムコールの実装を追跡

**プロンプト:**
```
fork システムコールの実装を追跡して、主要な関数の呼び出し階層を示して
```

**Claude Codeの回答:**

```
find_callees を使用して fork の呼び出しチェーンを分析しました。

## fork システムコールの実装階層

sys_fork() [kernel/fork.c]
└── kernel_clone()
    ├── copy_process()
    │   ├── dup_task_struct()      # タスク構造体の複製
    │   ├── copy_creds()           # 認証情報のコピー
    │   ├── copy_semundo()         # セマフォundo情報
    │   ├── copy_files()           # ファイルディスクリプタ
    │   ├── copy_fs()              # ファイルシステム情報
    │   ├── copy_sighand()         # シグナルハンドラ
    │   ├── copy_signal()          # シグナル情報
    │   ├── copy_mm()              # メモリマッピング (COW)
    │   ├── copy_namespaces()      # 名前空間
    │   ├── copy_io()              # I/Oコンテキスト
    │   ├── copy_thread()          # アーキテクチャ固有スレッド情報
    │   └── pid_alloc()            # 新しいPID割り当て
    └── wake_up_new_task()         # 新プロセスを実行可能に

## 重要なポイント

1. **Copy-on-Write (COW)**: copy_mm() ではメモリを実際にコピーせず、
   ページテーブルを共有して書き込み時にコピーする

2. **名前空間**: copy_namespaces() でプロセスの隔離レベルを制御

3. **スレッド vs プロセス**: clone_flags によって共有する
   リソースを細かく制御可能
```

## 3.4 分析例3: 特定の関数の影響範囲

**プロンプト:**
```
mutex_lock 関数を変更した場合、どのコードに影響がありますか？
```

**Claude Codeの回答:**

```
find_callers を使用して mutex_lock の呼び出し元を分析しました。

## mutex_lock の影響範囲

mutex_lock() は kernel/ 配下だけで 500+ 箇所から呼び出されています。

### 主要な呼び出し元カテゴリ

1. **スケジューラ** (kernel/sched/)
   - task_rq_lock()
   - __sched_setscheduler()

2. **プロセス管理** (kernel/fork.c, kernel/exit.c)
   - copy_process()
   - do_exit()

3. **シグナル処理** (kernel/signal.c)
   - do_sigaction()
   - send_signal()

4. **時間管理** (kernel/time/)
   - do_timer()
   - hrtimer_run_queues()

### 変更時の注意点

⚠️ mutex_lock は非常に広く使われているため、
   変更は以下に影響する可能性があります：

- デッドロック検出ロジック
- ロック順序の規約
- パフォーマンス（特にスピンロック fallback）
- CONFIG_DEBUG_MUTEXES 関連のデバッグ機能
```

## 3.5 分析例4: コードスニペットの取得

**プロンプト:**
```
context_switch 関数のソースコードを見せて
```

**Claude Codeの回答:**

```
get_code_snippet を使用してソースコードを取得しました。

## context_switch() - kernel/sched/core.c

```c
/*
 * context_switch - switch to the new MM and the new thread's register state.
 */
static __always_inline struct rq *
context_switch(struct rq *rq, struct task_struct *prev,
               struct task_struct *next, struct rq_flags *rf)
{
    prepare_task_switch(rq, prev, next);

    /*
     * For paravirt, this is coupled with an exit in switch_to to
     * combine the page table reload and the switch backend into
     * one hypercall.
     */
    arch_start_context_switch(prev);

    /*
     * kernel -> kernel   lazy + transfer active
     *   user -> kernel   lazy + mmgrab() active
     *
     * kernel ->   user   switch + mmdrop() active
     *   user ->   user   switch
     */
    if (!next->mm) {                                // to kernel
        enter_lazy_tlb(prev->active_mm, next);
        next->active_mm = prev->active_mm;
        if (prev->mm)                               // from user
            mmgrab(prev->active_mm);
        else
            prev->active_mm = NULL;
    } else {                                        // to user
        membarrier_switch_mm(rq, prev->active_mm, next->mm);
        switch_mm_irqs_off(prev->active_mm, next->mm, next);
        if (!prev->mm) {                            // from kernel
            rq->prev_mm = prev->active_mm;
            prev->active_mm = NULL;
        }
    }

    /* switch_to() に続く... */
    switch_to(prev, next, prev);
    barrier();

    return finish_task_switch(prev);
}
```

### コードの解説

1. **prepare_task_switch**: コンテキストスイッチの準備
2. **enter_lazy_tlb / switch_mm_irqs_off**: メモリマッピングの切り替え
3. **switch_to**: アーキテクチャ固有のレジスタ切り替え（アセンブラ）
4. **finish_task_switch**: 後処理
```

---

# 第4章 実践的なユースケース

## 4.1 バグ調査

特定のパニックやクラッシュの原因を調査：

```
プロンプト: schedule_timeout 関数でタイムアウトが
正しく動作しない場合、どの関数を確認すべき？
```

## 4.2 パッチ作成支援

新機能を追加する際の影響範囲を確認：

```
プロンプト: task_struct に新しいフィールドを
追加した場合、どのファイルを更新する必要がある？
```

## 4.3 コードレビュー

サブミットされたパッチのレビュー支援：

```
プロンプト: このパッチは sched_entity 構造体を
変更していますが、影響を受ける関数を列挙して
```

## 4.4 ドキュメント生成

コードからドキュメントを自動生成：

```
プロンプト: kernel/sched/ ディレクトリの
モジュール構造をドキュメント化して
```

---

# 第5章 Tips & トラブルシューティング

## 5.1 パフォーマンス最適化

| 状況 | 推奨設定 |
|------|----------|
| 特定サブシステムの分析 | 該当ディレクトリのみインデックス |
| 高速インデックス | `--no-community` オプション |
| メモリ節約 | サブシステム単位で分割インデックス |

## 5.2 よくある問題

### MCPサーバーが起動しない

```bash
# サーバーの手動テスト
codegraph-mcp serve --repo /path/to/linux

# ログを確認
cat ~/.codegraph/server.log
```

### インデックスが古い

```bash
# 増分インデックスで更新
codegraph-mcp index /path/to/linux/kernel
```

### メモリ不足

大規模コードベースでは、サブシステム単位でインデックスを作成：

```bash
# 個別にインデックス
codegraph-mcp index ./kernel --full --no-community
codegraph-mcp index ./mm --full --no-community
codegraph-mcp index ./fs --full --no-community
```

---

# 第6章 まとめ

## Claude Code + CodeGraph MCP の利点

1. **自然言語でコード分析**: 複雑なgrepコマンド不要
2. **構造的理解**: 関数の呼び出し関係を自動追跡
3. **影響範囲分析**: 変更の影響を事前に把握
4. **高速**: 5万エンティティを6秒でインデックス
5. **ゼロ構成**: pip installですぐ使える

## 活用シーン

- カーネルハッカーの日常的なコードナビゲーション
- 新人開発者のオンボーディング
- バグ調査時の影響範囲特定
- パッチ作成・レビューの効率化

## リンク

- **CodeGraph MCP**: https://github.com/nahisaho/CodeGraphMCPServer
- **PyPI**: https://pypi.org/project/codegraph-mcp-server/
- **Claude Code**: https://claude.ai/code
- **Linux Kernel**: https://github.com/torvalds/linux

---

# 参考資料

- [CodeGraph MCP 紹介記事](https://qiita.com/)
- [Linux Kernel Documentation](https://www.kernel.org/doc/html/latest/)
- [Model Context Protocol](https://spec.modelcontextprotocol.io/)
- [Claude Code Documentation](https://docs.anthropic.com/claude-code)

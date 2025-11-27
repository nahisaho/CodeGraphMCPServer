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
codegraphでLinuxカーネルのスケジューラに関する主要な関数を検索した結果をまとめます。

## Linuxカーネル スケジューラ関連関数 (codegraph検索結果)

### コアスケジューラ (kernel/sched/core.c)

| 関数名                | 位置          | 説明               |
|--------------------|-------------|------------------|
| try_to_wake_up     | core.c:4143 | タスクを起床させる        |
| enqueue_task       | core.c:2080 | タスクをランキューに追加     |
| dequeue_task       | core.c:2106 | タスクをランキューから削除    |
| pick_next_task     | core.c:5986 | 次に実行するタスクを選択     |
| sched_core_enqueue | core.c:298  | コアスケジューリング用エンキュー |
| sched_core_dequeue | core.c:311  | コアスケジューリング用デキュー  |
| prio_less          | core.c:219  | 優先度比較            |
| __task_prio        | core.c:191  | タスク優先度取得         |

### CFS (Completely Fair Scheduler) (kernel/sched/fair.c)

| 関数名                     | 位置             | 説明            |
|-------------------------|----------------|---------------|
| enqueue_task_fair       | fair.c:6917    | CFSランキューへの追加  |
| dequeue_task_fair       | fair.c:7161    | CFSランキューからの削除 |
| calc_delta_fair         | fair.c:290     | 公平な実行時間の計算    |
| update_load_add/sub/set | fair.c:165-177 | 負荷の更新         |
| list_add_leaf_cfs_rq    | fair.c:310     | CFS rqリスト操作   |

### リアルタイムスケジューラ (kernel/sched/rt.c)

| 関数名                   | 位置        | 説明             |
|-----------------------|-----------|----------------|
| enqueue_task_rt       | rt.c:1430 | RTタスクの追加       |
| dequeue_task_rt       | rt.c:1450 | RTタスクの削除       |
| init_rt_rq            | rt.c:68   | RTランキューの初期化    |
| sched_rt_period_timer | rt.c:101  | RTスケジューラ周期タイマー |
| init_rt_bandwidth     | rt.c:125  | RT帯域幅の初期化      |

### デッドラインスケジューラ (kernel/sched/deadline.c)

| 関数名             | 位置              | 説明       |
|-----------------|-----------------|----------|
| enqueue_task_dl | deadline.c:2054 | DLタスクの追加 |
| dequeue_task_dl | deadline.c:2114 | DLタスクの削除 |

### sched_ext (BPF拡張スケジューラ) (kernel/sched/ext.c)

| 関数名              | 位置         | 説明         |
|------------------|------------|------------|
| enqueue_task_scx | ext.c:1334 | SCXタスクの追加  |
| dequeue_task_scx | ext.c:1430 | SCXタスクの削除  |
| do_enqueue_task  | ext.c:1215 | タスクエンキュー実行 |

### 統計・PSI (kernel/sched/stats.h)

| 関数名                | 位置          | 説明            |
|--------------------|-------------|---------------|
| psi_enqueue        | stats.h:130 | PSIエンキュー処理    |
| psi_dequeue        | stats.h:169 | PSIデキュー処理     |
| psi_sched_switch   | stats.h:213 | PSIコンテキストスイッチ |
| sched_info_arrive  | stats.h:263 | スケジュール情報到着    |
| sched_info_enqueue | stats.h:289 | スケジュール情報エンキュー |

より詳細な検索をするには:
codegraph-mcp query "<キーワード>" --format text
```

## 3.3 分析例2: システムコールの実装を追跡

**プロンプト:**
```
forkシステムコールの実装を追跡して、主要な関数の呼び出し階層を示して
```

**Claude Codeの回答:**

```
Linuxカーネル fork システムコール 呼び出し階層

User Space
    │
    ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│  SYSCALL_DEFINE0(fork)                         [kernel/fork.c:2689]          │
│  SYSCALL_DEFINE0(vfork)                        [kernel/fork.c:2705]          │
│  SYSCALL_DEFINE5(clone, ...)                   [kernel/fork.c:2718-2738]     │
│  SYSCALL_DEFINE2(clone3, ...)                  [kernel/fork.c:2890]          │
└──────────────────────────────────────────────────────────────────────────────┘
                    │
                    ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│  kernel_clone(struct kernel_clone_args *args)  [kernel/fork.c:2568]          │
│    ├─ ptrace_event_enabled() - ptraceイベント判定                             │
│    ├─ copy_process() ─────────────────┐                                      │
│    ├─ trace_sched_process_fork()      │                                      │
│    ├─ get_task_pid()                  │                                      │
│    ├─ wake_up_new_task() ────────┐    │                                      │
│    └─ wait_for_vfork_done()      │    │                                      │
└──────────────────────────────────┼────┼──────────────────────────────────────┘
                                   │    │
                    ┌──────────────┘    │
                    ▼                   │
┌─────────────────────────────────┐     │
│  wake_up_new_task()             │     │
│  [kernel/sched/core.c:4813]     │     │
│    ├─ __set_task_cpu()          │     │
│    ├─ select_task_rq()          │     │
│    ├─ activate_task()           │     │
│    │    └─ enqueue_task()       │     │
│    ├─ wakeup_preempt()          │     │
│    └─ task_woken() callback     │     │
└─────────────────────────────────┘     │
                                        │
         ┌──────────────────────────────┘
         ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│  copy_process()                                [kernel/fork.c:1926]          │
│  (プロセス複製の中核関数)                                                      │
│                                                                              │
│  1. フラグ検証                                                                │
│     ├─ CLONE_NEWNS, CLONE_FS, CLONE_THREAD 等の組み合わせチェック              │
│                                                                              │
│  2. タスク構造体の複製                                                         │
│     └─ dup_task_struct()              [kernel/fork.c:866]                    │
│          ├─ alloc_task_struct_node() - task_struct メモリ確保                 │
│          ├─ arch_dup_task_struct() - アーキテクチャ依存コピー                   │
│          ├─ alloc_thread_stack_node() - スタック割り当て                       │
│          └─ setup_thread_stack() - スタック設定                               │
│                                                                              │
│  3. 資格情報のコピー                                                          │
│     └─ copy_creds()                   [kernel/cred.c]                        │
│                                                                              │
│  4. スケジューラ初期化                                                        │
│     └─ sched_fork()                   [kernel/sched/core.c:4678]             │
│          ├─ __sched_fork() - スケジューリングデータ初期化                       │
│          ├─ p->__state = TASK_NEW                                            │
│          ├─ uclamp_fork()                                                    │
│          ├─ sched_class 設定 (rt/fair/ext)                                   │
│          └─ init_entity_runnable_average()                                   │
│                                                                              │
│  5. 各種リソースのコピー                                                       │
│     ├─ copy_files()                   [kernel/fork.c:1573] - fdテーブル       │
│     ├─ copy_fs()                      [kernel/fork.c:1552] - ファイルシステム  │
│     ├─ copy_sighand()                 [kernel/fork.c:1603] - シグナルハンドラ  │
│     ├─ copy_signal()                  [kernel/fork.c:1652] - シグナル情報      │
│     ├─ copy_mm()                      [kernel/fork.c:1514] - メモリ空間       │
│     │    └─ dup_mm() → dup_mmap() (CLONE_VMがない場合)                        │
│     ├─ copy_namespaces()              [kernel/nsproxy.c] - 名前空間           │
│     ├─ copy_io()                      [block/blk-ioc.c] - I/Oコンテキスト      │
│     └─ copy_thread()                  [arch依存] - レジスタ/スレッド情報       │
│                                                                              │
│  6. PID割り当て                                                               │
│     └─ alloc_pid()                    [kernel/pid.c]                         │
│                                                                              │
│  7. cgroup処理                                                                │
│     ├─ cgroup_can_fork()                                                     │
│     └─ sched_cgroup_fork()            [kernel/sched/core.c:4748]             │
│                                                                              │
│  8. プロセスツリーへの追加                                                     │
│     ├─ klp_copy_process() - Live Patch                                       │
│     ├─ sched_core_fork()                                                     │
│     ├─ init_task_pid() - PID設定                                             │
│     ├─ attach_pid() - PIDハッシュ登録                                         │
│     └─ list_add_tail() - 親子/兄弟リスト追加                                   │
│                                                                              │
│  9. 後処理                                                                    │
│     ├─ sched_post_fork()                                                     │
│     ├─ cgroup_post_fork()                                                    │
│     └─ perf_event_fork()                                                     │
└──────────────────────────────────────────────────────────────────────────────┘

## 主要関数の位置

| 関数名                     | ファイル                | 行番号       |
|-------------------------|---------------------|-----------|
| SYSCALL_DEFINE0(fork)   | kernel/fork.c       | 2689      |
| SYSCALL_DEFINE0(vfork)  | kernel/fork.c       | 2705      |
| SYSCALL_DEFINE5(clone)  | kernel/fork.c       | 2718-2738 |
| SYSCALL_DEFINE2(clone3) | kernel/fork.c       | 2890      |
| kernel_clone()          | kernel/fork.c       | 2568      |
| copy_process()          | kernel/fork.c       | 1926      |
| dup_task_struct()       | kernel/fork.c       | 866       |
| copy_mm()               | kernel/fork.c       | 1514      |
| copy_files()            | kernel/fork.c       | 1573      |
| copy_fs()               | kernel/fork.c       | 1552      |
| copy_sighand()          | kernel/fork.c       | 1603      |
| copy_signal()           | kernel/fork.c       | 1652      |
| sched_fork()            | kernel/sched/core.c | 4678      |
| sched_cgroup_fork()     | kernel/sched/core.c | 4748      |
| wake_up_new_task()      | kernel/sched/core.c | 4813      |
```

## 3.4 分析例3: 特定の関数の影響範囲

**プロンプト:**
```
mutex_lock関数を変更した場合、どのコードに影響がありますか？
```

**Claude Codeの回答:**

```
mutex_lock 変更の影響範囲

## 影響の概要

mutex_lock() は Linuxカーネル全体で 23,243箇所 で使用されており、
関連API全体では 54,047箇所 に影響します。

## 実装ファイル

| ファイル                         | 行番号 | 設定                |
|------------------------------|-----|-------------------|
| kernel/locking/mutex.c       | 269 | 通常 (非 PREEMPT_RT) |
| kernel/locking/rtmutex_api.c | 601 | PREEMPT_RT        |

## mutex_lock() の内部呼び出し

mutex_lock(lock)
    │
    ├─ might_sleep()           // スリープ可能性チェック
    │
    └─ __mutex_trylock_fast()  [mutex.c:150] - ファストパス
         │
         ├─ 成功 → 即座にリターン
         │
         └─ 失敗 → __mutex_lock_slowpath() [mutex.c:1047]
                    └─ __mutex_lock() → スピン/スリープ待ち

## サブシステム別使用箇所

| サブシステム   | 使用箇所数  | 主な影響領域       |
|----------|--------|--------------|
| drivers/ | 18,499 | デバイスドライバ全般   |
| fs/      | 1,078  | ファイルシステム     |
| net/     | 823    | ネットワークスタック   |
| kernel/  | 708    | コア機能         |
| arch/    | 701    | アーキテクチャ依存コード |
| sound/   | 686    | オーディオサブシステム  |
| mm/      | 124    | メモリ管理        |
| block/   | 110    | ブロックデバイス     |

## drivers/ 内の内訳

| サブディレクトリ            | 使用箇所数 |
|---------------------|-------|
| drivers/net/        | 3,830 |
| drivers/gpu/        | 2,450 |
| drivers/media/      | 1,607 |
| drivers/iio/        | 895   |
| drivers/hwmon/      | 808   |
| drivers/usb/        | 720   |
| drivers/infiniband/ | 565   |
| drivers/scsi/       | 512   |

## kernel/ 内の内訳

| サブディレクトリ           | 使用箇所数 |
|--------------------|-------|
| kernel/trace/      | 196   |
| kernel/bpf/        | 64    |
| kernel/locking/    | 62    |
| kernel/events/     | 49    |
| kernel/workqueue.c | 47    |
| kernel/sched/      | 31    |
| kernel/cgroup/     | 29    |

## 関連API (同時に影響を受ける可能性)

| API                        | 使用箇所数   |
|----------------------------|---------|
| mutex_lock()               | 23,243  |
| mutex_unlock()             | ~23,000 |
| mutex_lock_nested()        | 約600    |
| mutex_lock_interruptible() | 約400    |
| mutex_lock_killable()      | 約100    |
| mutex_trylock()            | 約3,500  |

## 変更時の注意点

1. CONFIG_PREEMPT_RT: RTカーネルではrtmutexベースの実装を使用
2. CONFIG_DEBUG_LOCK_ALLOC: デバッグ時はmutex_lock_nested()へのマクロ展開
3. スリープ可能コンテキスト: might_sleep()によりアトミックコンテキストでの使用を検出
4. ロックデップ: デッドロック検出のための依存関係追跡

## テスト推奨範囲

変更内容に応じて:
- 全ドライバのストレステスト
- ファイルシステムI/Oテスト
- ネットワーク負荷テスト
- スケジューラ/コアのストレステスト
- lockdepを有効にしたビルド・テスト
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

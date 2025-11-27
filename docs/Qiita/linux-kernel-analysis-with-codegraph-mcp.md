---
title: 'CodeGraph MCPとVS CodeでLinuxカーネルのコードを分析してみた'
tags:
  - Linux
  - Kernel
  - MCP
  - VSCode
  - AI
private: false
updated_at: '2025-11-27'
id: null
organization_url_name: null
slide: false
---

# はじめに

Linuxカーネルは約3,000万行のCコードで構成される巨大なプロジェクトです。その構造を理解するのは容易ではありません。

本記事では、**CodeGraph MCP Server**を使って、AIコーディングアシスタント（GitHub Copilot）と連携しながらLinuxカーネルのコードを分析する方法を紹介します。

## この記事でわかること

- CodeGraph MCPでLinuxカーネルをインデックスする方法
- VS Code + GitHub CopilotでカーネルコードをAIに質問する方法
- 実際の分析例（スケジューラ、プロセス管理など）

## 前提条件

- Python 3.11以上
- VS Code + GitHub Copilot
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
# カーネルソースをクローン（時間がかかります）
git clone --depth 1 https://github.com/torvalds/linux.git
cd linux
```

## 1.3 VS Code MCP設定

`.vscode/settings.json`に以下を追加：

```json
{
  "mcp.servers": {
    "codegraph": {
      "command": "codegraph-mcp",
      "args": ["serve", "--repo", "${workspaceFolder}"]
    }
  }
}
```

---

# 第2章 カーネルのインデックス作成

## 2.1 部分インデックス（推奨）

カーネル全体をインデックスすると時間がかかるため、まずは特定のサブシステムから始めることをお勧めします。

```bash
# kernel/ ディレクトリのみをインデックス
codegraph-mcp index ./kernel --full --no-community
```

**実行結果:**

```
Indexed 54,748 entities, 142,532 relations in 5.77s
```

| 項目 | 値 |
|------|------|
| ファイル数 | 596 |
| エンティティ数 | 54,748 |
| リレーション数 | 142,532 |
| 処理時間 | 5.77秒 |

## 2.2 他のサブシステム例

```bash
# メモリ管理
codegraph-mcp index ./mm --full --no-community

# ファイルシステム
codegraph-mcp index ./fs --full --no-community

# ネットワーク
codegraph-mcp index ./net --full --no-community

# ドライバ（大規模）
codegraph-mcp index ./drivers --full --no-community
```

## 2.3 フルインデックス（上級者向け）

カーネル全体をインデックスする場合：

```bash
# 警告: 数分〜十数分かかります
codegraph-mcp index . --full --no-community
```

> **注意**: コミュニティ検出（`--no-community`を外す）を有効にすると、さらに時間がかかります。大規模コードベースでは無効化を推奨します。

---

# 第3章 MCPサーバーの起動

```bash
# バックグラウンドで起動
codegraph-mcp start --repo /path/to/linux

# 状態確認
codegraph-mcp status

# 停止する場合
codegraph-mcp stop
```

VS Codeを開き、GitHub Copilotが利用可能な状態にします。

---

# 第4章 分析例

## 4.1 スケジューラの関数を探す

**質問:**
```
Linuxカーネルのスケジューラに関連する関数を教えて
```

**Copilotの回答（CodeGraph MCPツール使用）:**

```
query_codebase ツールを使用して検索しました。

スケジューラ関連の主要な関数:
1. schedule() - kernel/sched/core.c:6847
   - メインのスケジューリング関数
   
2. __schedule() - kernel/sched/core.c:6780
   - 実際のコンテキストスイッチを行う内部関数
   
3. scheduler_tick() - kernel/sched/core.c:5765
   - タイマー割り込みから呼ばれる
   
4. wake_up_process() - kernel/sched/core.c:4534
   - プロセスを起床させる
   
5. try_to_wake_up() - kernel/sched/core.c:4234
   - wake_up_process の内部実装
```

## 4.2 fork システムコールの実装を追跡

**質問:**
```
forkシステムコールの実装を追跡して、関連する関数を教えて
```

**Copilotの回答:**

```
find_callers と find_callees ツールを使用しました。

fork の呼び出しチェーン:
1. sys_fork() - kernel/fork.c
   └── kernel_clone()
       ├── copy_process()
       │   ├── dup_task_struct()
       │   ├── copy_files()
       │   ├── copy_fs()
       │   ├── copy_mm()
       │   └── copy_thread()
       └── wake_up_new_task()

合計で100以上の関連エンティティが見つかりました。
```

## 4.3 特定の関数のソースコードを取得

**質問:**
```
copy_process関数のソースコードを見せて
```

**Copilotの回答:**

```
get_code_snippet ツールを使用しました。

// kernel/fork.c
static __latent_entropy struct task_struct *copy_process(
    struct pid *pid,
    int trace,
    int node,
    struct kernel_clone_args *args)
{
    int pidfd = -1, retval;
    struct task_struct *p;
    struct multiprocess_signals delayed;
    struct file *pidfile = NULL;
    const u64 clone_flags = args->flags;
    ...
}
```

## 4.4 依存関係の分析

**質問:**
```
schedule関数が依存している関数を教えて
```

**Copilotの回答:**

```
find_dependencies ツールを使用しました。

schedule() の依存先（深さ2）:
├── __schedule()
│   ├── pick_next_task()
│   ├── context_switch()
│   ├── update_rq_clock()
│   └── deactivate_task()
├── preempt_disable()
├── preempt_enable()
└── sched_submit_work()
```

## 4.5 プロジェクト構造の理解

**質問:**
```
kernel/ディレクトリの主要なコンポーネントを説明して
```

**Copilotの回答:**

```
analyze_module_structure と global_search ツールを使用しました。

kernel/ の主要コンポーネント:

1. **スケジューラ** (kernel/sched/)
   - プロセススケジューリング
   - CFS、リアルタイムスケジューラ
   - CPU負荷分散

2. **プロセス管理** (kernel/fork.c, kernel/exit.c)
   - プロセス生成・終了
   - シグナル処理

3. **時間管理** (kernel/time/)
   - タイマー、クロック
   - hrtimer、タイムキーピング

4. **同期プリミティブ** (kernel/locking/)
   - mutex、spinlock、rwlock
   - RCU

5. **割り込み処理** (kernel/irq/)
   - IRQ管理
   - softirq、tasklet
```

---

# 第5章 実践的なユースケース

## 5.1 バグ調査

特定の関数を変更した場合の影響範囲を調べる：

```
mutex_lock関数を変更した場合、影響を受けるコードは？
```

## 5.2 コードレビュー支援

新しいパッチがどの部分に影響するか確認：

```
このパッチはどのサブシステムに影響しますか？
関連するテストファイルはありますか？
```

## 5.3 オンボーディング

カーネル開発初心者が構造を理解する：

```
メモリアロケータの仕組みを説明して
主要な関数と、それらがどう呼び出されるか教えて
```

---

# 第6章 パフォーマンスTips

## 6.1 インデックス戦略

| シナリオ | 推奨設定 |
|----------|----------|
| 特定サブシステムの分析 | 該当ディレクトリのみインデックス |
| 全体構造の把握 | `--no-community`で高速インデックス |
| 詳細なクラスタ分析 | コミュニティ検出を有効化 |

## 6.2 クエリの最適化

```python
# 効率的: エンティティタイプでフィルタ
query_codebase(query="scheduler", entity_types=["function"])

# 効率的: 部分ID検索
find_callers(entity_id="schedule")  # フルパス不要

# 非効率: 広すぎるクエリ
query_codebase(query="kernel")  # 結果が多すぎる
```

## 6.3 増分インデックス

コードを変更した後は増分インデックスで高速更新：

```bash
# 変更ファイルのみ再インデックス
codegraph-mcp index . 
```

---

# 第7章 まとめ

## CodeGraph MCPの利点

1. **ゼロ構成**: pip installですぐに使える
2. **高速**: kernel/ディレクトリを6秒以下でインデックス
3. **AI連携**: GitHub Copilotから直接クエリ可能
4. **C言語対応**: v0.7.1でLinuxカーネル分析が可能に

## 活用シーン

- カーネルハッカーのコードナビゲーション
- バグ調査時の影響範囲分析
- 新人開発者のオンボーディング
- コードレビューの効率化

## リンク

- **CodeGraph MCP GitHub**: https://github.com/nahisaho/CodeGraphMCPServer
- **PyPI**: https://pypi.org/project/codegraph-mcp-server/
- **Linux Kernel**: https://github.com/torvalds/linux

---

# 参考資料

- [CodeGraph MCP 紹介記事](https://qiita.com/your-article)
- [Linux Kernel Documentation](https://www.kernel.org/doc/html/latest/)
- [Model Context Protocol](https://spec.modelcontextprotocol.io/)

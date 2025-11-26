"""
CLI Entry Point for CodeGraph MCP Server

Usage:
    codegraph-mcp start --repo /path/to/project    # Start server in background
    codegraph-mcp stop                              # Stop background server
    codegraph-mcp status                            # Check server status
    codegraph-mcp serve --repo /path/to/project    # Start server in foreground
    codegraph-mcp index /path/to/project           # Index repository
    codegraph-mcp query "find all functions"       # Execute query
    codegraph-mcp stats /path/to/project           # Show statistics
    codegraph-mcp --help

Requirements: REQ-CLI-001 ~ REQ-CLI-004
"""

import argparse
import os
import signal
import subprocess
import sys
from pathlib import Path

from codegraph_mcp import __version__


# Default PID file location
def get_pid_file() -> Path:
    """Get the PID file path."""
    return Path.home() / ".codegraph" / "server.pid"


def get_log_file() -> Path:
    """Get the log file path."""
    return Path.home() / ".codegraph" / "server.log"


def create_parser() -> argparse.ArgumentParser:
    """Create CLI argument parser."""
    parser = argparse.ArgumentParser(
        prog="codegraph-mcp",
        description="CodeGraph MCP Server - "
                    "Code graph analysis with GraphRAG",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )

    subparsers = parser.add_subparsers(
        dest="command",
        help="Available commands",
    )

    # start command - Start server in background
    start_parser = subparsers.add_parser(
        "start",
        help="Start MCP server in background",
    )
    start_parser.add_argument(
        "--repo",
        type=Path,
        default=Path.cwd(),
        help="Repository path to serve (default: current directory)",
    )
    start_parser.add_argument(
        "--transport",
        choices=["stdio", "sse"],
        default="sse",
        help="Transport protocol (default: sse for background)",
    )
    start_parser.add_argument(
        "--port",
        type=int,
        default=8080,
        help="Port for SSE transport (default: 8080)",
    )

    # stop command - Stop background server
    subparsers.add_parser("stop", help="Stop background MCP server")

    # status command - Check server status
    subparsers.add_parser("status", help="Check MCP server status")

    # serve command (REQ-CLI-001) - Foreground mode
    serve_parser = subparsers.add_parser(
        "serve",
        help="Start MCP server in foreground",
    )
    serve_parser.add_argument(
        "--repo",
        type=Path,
        default=Path.cwd(),
        help="Repository path to serve (default: current directory)",
    )
    serve_parser.add_argument(
        "--transport",
        choices=["stdio", "sse"],
        default="stdio",
        help="Transport protocol (default: stdio)",
    )
    serve_parser.add_argument(
        "--port",
        type=int,
        default=8080,
        help="Port for SSE transport (default: 8080)",
    )

    # index command (REQ-IDX-001)
    index_parser = subparsers.add_parser("index", help="Index a repository")
    index_parser.add_argument(
        "path",
        type=Path,
        help="Repository path to index",
    )
    index_parser.add_argument(
        "--incremental",
        action="store_true",
        default=True,
        help="Perform incremental indexing (default: True)",
    )
    index_parser.add_argument(
        "--full",
        action="store_true",
        help="Perform full re-indexing",
    )

    # query command (REQ-TLS-001)
    query_parser = subparsers.add_parser("query", help="Execute a graph query")
    query_parser.add_argument(
        "query",
        type=str,
        help="Query string",
    )
    query_parser.add_argument(
        "--repo",
        type=Path,
        default=Path.cwd(),
        help="Repository path (default: current directory)",
    )
    query_parser.add_argument(
        "--format",
        choices=["json", "text"],
        default="text",
        help="Output format (default: text)",
    )

    # stats command (REQ-RSC-004)
    stats_parser = subparsers.add_parser(
        "stats",
        help="Show repository statistics",
    )
    stats_parser.add_argument(
        "path",
        type=Path,
        nargs="?",
        default=Path.cwd(),
        help="Repository path (default: current directory)",
    )

    # community command (REQ-SEM-003)
    community_parser = subparsers.add_parser(
        "community",
        help="Detect communities in the code graph",
    )
    community_parser.add_argument(
        "path",
        type=Path,
        nargs="?",
        default=Path.cwd(),
        help="Repository path (default: current directory)",
    )
    community_parser.add_argument(
        "--algorithm",
        choices=["louvain"],
        default="louvain",
        help="Detection algorithm (default: louvain)",
    )
    community_parser.add_argument(
        "--resolution",
        type=float,
        default=1.0,
        help="Resolution parameter (default: 1.0)",
    )
    community_parser.add_argument(
        "--min-size",
        type=int,
        default=3,
        help="Minimum community size (default: 3)",
    )

    return parser


def cmd_start(args: argparse.Namespace) -> int:
    """Handle start command - Start server in background."""
    pid_file = get_pid_file()
    log_file = get_log_file()
    
    # Ensure directory exists
    pid_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Check if already running
    if pid_file.exists():
        try:
            pid = int(pid_file.read_text().strip())
            os.kill(pid, 0)  # Check if process exists
            print(f"Server is already running (PID: {pid})")
            return 1
        except (ProcessLookupError, ValueError):
            # Process not running, remove stale PID file
            pid_file.unlink()
    
    # Build command
    cmd = [
        sys.executable, "-m", "codegraph_mcp",
        "serve",
        "--repo", str(args.repo.resolve()),
        "--transport", args.transport,
        "--port", str(args.port),
    ]
    
    # Start server in background
    with open(log_file, "w") as log:
        process = subprocess.Popen(
            cmd,
            stdout=log,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )
    
    # Write PID file
    pid_file.write_text(str(process.pid))
    
    print("\u2705 Server started in background")
    print(f"   PID: {process.pid}")
    print(f"   Repository: {args.repo.resolve()}")
    print(f"   Transport: {args.transport}")
    if args.transport == "sse":
        print(f"   URL: http://localhost:{args.port}")
    print(f"   Log: {log_file}")
    print("\nUse 'codegraph-mcp stop' to stop the server")
    
    return 0


def cmd_stop(args: argparse.Namespace) -> int:
    """Handle stop command - Stop background server."""
    pid_file = get_pid_file()
    
    if not pid_file.exists():
        print("No server is running")
        return 1
    
    try:
        pid = int(pid_file.read_text().strip())
        os.kill(pid, signal.SIGTERM)
        
        # Wait for process to terminate
        import time
        for _ in range(10):
            try:
                os.kill(pid, 0)
                time.sleep(0.5)
            except ProcessLookupError:
                break
        
        pid_file.unlink()
        print(f"✅ Server stopped (PID: {pid})")
        return 0
        
    except ProcessLookupError:
        pid_file.unlink()
        print("Server was not running (stale PID file removed)")
        return 0
    except ValueError:
        print("Invalid PID file")
        pid_file.unlink()
        return 1


def cmd_status(args: argparse.Namespace) -> int:
    """Handle status command - Check server status."""
    pid_file = get_pid_file()
    log_file = get_log_file()
    
    if not pid_file.exists():
        print("❌ Server is not running")
        return 1
    
    try:
        pid = int(pid_file.read_text().strip())
        os.kill(pid, 0)  # Check if process exists
        
        print("\u2705 Server is running")
        print(f"   PID: {pid}")
        print(f"   Log: {log_file}")
        
        # Show last few log lines if available
        if log_file.exists():
            lines = log_file.read_text().strip().split("\n")
            if lines and lines[0]:
                print("\nRecent logs:")
                for line in lines[-5:]:
                    print(f"   {line}")
        
        return 0
        
    except ProcessLookupError:
        pid_file.unlink()
        print("❌ Server is not running (stale PID file removed)")
        return 1
    except ValueError:
        print("❌ Invalid PID file")
        return 1


def cmd_serve(args: argparse.Namespace) -> int:
    """Handle serve command."""
    from codegraph_mcp.server import run_server

    return run_server(
        repo_path=args.repo,
        transport=args.transport,
        port=args.port,
    )


def cmd_index(args: argparse.Namespace) -> int:
    """Handle index command."""
    import asyncio

    from codegraph_mcp.core.indexer import Indexer

    async def _index() -> int:
        indexer = Indexer()
        incremental = not args.full
        
        # Check if rich is available for progress display
        try:
            from rich.console import Console
            from rich.progress import (
                Progress,
                SpinnerColumn,
                TextColumn,
                BarColumn,
                TaskProgressColumn,
                TimeElapsedColumn,
            )
            from rich.table import Table
            
            console = Console()
            
            # Show start message
            mode = "Full" if args.full else "Incremental"
            console.print("\n[bold blue]\ud83d\udd0d CodeGraph Indexer[/bold blue]")
            console.print(f"Repository: [cyan]{args.path}[/cyan]")
            console.print(f"Mode: [yellow]{mode}[/yellow]\n")
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TaskProgressColumn(),
                TimeElapsedColumn(),
                console=console,
            ) as progress:
                # Add task for indexing
                task = progress.add_task(
                    "[cyan]Indexing files...",
                    total=None,  # Indeterminate at first
                )
                
                # Run indexer with progress callback
                result = await indexer.index_repository(
                    args.path,
                    incremental=incremental,
                    progress_callback=lambda current, total, file: (
                        progress.update(
                            task,
                            total=total,
                            completed=current,
                            description=(
                                f"[cyan]Processing: "
                                f"{file.name if file else '...'}"
                            ),
                        )
                    ),
                )
                
                # Complete the task
                progress.update(
                    task,
                    completed=result.files_indexed,
                    description="[green]Complete!",
                )
            
            # Show results in a nice table
            console.print()
            table = Table(title="📊 Indexing Results", show_header=False)
            table.add_column("Metric", style="cyan")
            table.add_column("Value", style="green")
            
            table.add_row("Entities", str(result.entities_count))
            table.add_row("Relations", str(result.relations_count))
            table.add_row("Files Indexed", str(result.files_indexed))
            table.add_row("Files Skipped", str(result.files_skipped))
            table.add_row("Duration", f"{result.duration_seconds:.2f}s")
            
            console.print(table)
            
            if result.errors:
                console.print(f"\n[red]\u26a0 Errors: {len(result.errors)}[/red]")
                for err in result.errors[:5]:
                    console.print(f"  [dim]- {err}[/dim]")
            else:
                msg = "\n[green]\u2705 Indexing completed successfully![/green]\n"
                console.print(msg)
            
            return 0 if result.success else 1
            
        except ImportError:
            # Fallback to simple output without rich
            result = await indexer.index_repository(
                args.path,
                incremental=incremental,
            )
            print(f"Indexed {result.entities_count} entities, "
                  f"{result.relations_count} relations in "
                  f"{result.duration_seconds:.2f}s")
            if result.errors:
                print(f"Errors: {len(result.errors)}")
                for err in result.errors[:5]:
                    print(f"  - {err}")
            return 0 if result.success else 1

    return asyncio.run(_index())


def cmd_query(args: argparse.Namespace) -> int:
    """Handle query command."""
    import asyncio

    from codegraph_mcp.core.graph import GraphEngine, GraphQuery

    async def _query() -> int:
        engine = GraphEngine(args.repo)
        await engine.initialize()
        try:
            query = GraphQuery(query=args.query)
            result = await engine.query(query)

            if args.format == "json":
                import json
                print(json.dumps(result.to_dict(), indent=2))
            else:
                print(f"Found {len(result.entities)} entities:")
                for entity in result.entities[:20]:
                    print(f"  - {entity.type.value}: {entity.qualified_name}")
                    print(f"    {entity.file_path}:{entity.start_line}")
            return 0
        finally:
            await engine.close()

    return asyncio.run(_query())


def cmd_stats(args: argparse.Namespace) -> int:
    """Handle stats command."""
    import asyncio

    from codegraph_mcp.core.graph import GraphEngine

    async def _stats() -> int:
        engine = GraphEngine(args.path)
        await engine.initialize()
        try:
            stats = await engine.get_statistics()

            print(f"Repository: {args.path}")
            print(f"Entities: {stats.entity_count}")
            print(f"Relations: {stats.relation_count}")
            print(f"Communities: {stats.community_count}")
            print(f"Files: {stats.file_count}")
            if stats.languages:
                print(f"Languages: {', '.join(stats.languages)}")
            if stats.entities_by_type:
                print("Entities by type:")
                for t, count in stats.entities_by_type.items():
                    print(f"  - {t}: {count}")
            return 0
        finally:
            await engine.close()

    return asyncio.run(_stats())


def cmd_community(args: argparse.Namespace) -> int:
    """Handle community command."""
    import asyncio

    from codegraph_mcp.core.graph import GraphEngine
    from codegraph_mcp.core.community import CommunityDetector

    async def _community() -> int:
        engine = GraphEngine(args.path)
        await engine.initialize()
        try:
            # Create detector with specified parameters
            detector = CommunityDetector(
                algorithm=args.algorithm,
                resolution=args.resolution,
                min_size=args.min_size,
            )

            # Detect communities
            result = await detector.detect(engine)

            print("Community Detection")
            print("=" * 40)
            print(f"Repository: {args.path}")
            print(f"Algorithm: {args.algorithm}")
            print(f"Resolution: {args.resolution}")
            print(f"Minimum size: {args.min_size}")
            print()
            print(f"Communities detected: {len(result.communities)}")
            print(f"Hierarchy levels: {result.levels}")
            print(f"Modularity: {result.modularity:.4f}")

            if result.communities:
                print("\nCommunity Details:")
                for comm in result.communities[:10]:
                    print(f"  Community {comm.id}:")
                    print(f"    Members: {comm.member_count}")
                    if comm.name:
                        print(f"    Name: {comm.name}")

            return 0
        finally:
            await engine.close()

    return asyncio.run(_community())


def main() -> int:
    """Main entry point."""
    parser = create_parser()
    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        return 0

    commands = {
        "start": cmd_start,
        "stop": cmd_stop,
        "status": cmd_status,
        "serve": cmd_serve,
        "index": cmd_index,
        "query": cmd_query,
        "stats": cmd_stats,
        "community": cmd_community,
    }

    handler = commands.get(args.command)
    if handler:
        try:
            return handler(args)
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1
    
    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())

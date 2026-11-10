#!/usr/bin/python3
"""
watch_builds.py — Live colorful grid monitor for Fedora Copr builds without triggering.

Displays an interactive, color-coded grid matrix of package builds across all chroots,
including live build elapsed times / total build durations.
Works standalone or continuously with auto-refresh.

Usage:
    ./watch_builds.py [options] [project]

Options:
    --project, -p <name>    Copr project name or username/project (default: artcraft-suites)
    --interval, -n <sec>    Auto-refresh interval in seconds (default: 5, set 0 for single-shot)
    --once                  Single snapshot then exit
    --compact               Display status using compact icons only (✔, ⚡, ⏳, ✖)
    --chroots <c1,c2,...>   Filter by specific chroots (comma-separated)
    --packages <p1,p2,...>  Filter by specific packages (comma-separated)
    -h, --help              Show this help message
"""

import sys
import os
import time
import argparse
import subprocess
import json
import shutil
import urllib.request
import urllib.error
from datetime import datetime

try:
    from rich.console import Console
    from rich.table import Table
    from rich.live import Live
    from rich.panel import Panel
    from rich.text import Text
    from rich import box
except ImportError as e:
    print(f"Error importing rich: {e}", file=sys.stderr)
    print("Error: 'rich' library is required. Install via: pip install rich (or dnf install python3-rich)", file=sys.stderr)
    sys.exit(1)

# Status styling and icons
STATE_STYLES = {
    "succeeded": ("bold green", "✔", "succeeded"),
    "forked": ("green", "✔", "forked"),
    "running": ("bold yellow", "⚡", "running"),
    "starting": ("yellow", "⏳", "starting"),
    "pending": ("dim yellow", "…", "pending"),
    "importing": ("cyan", "📥", "importing"),
    "waiting": ("dim white", "⏸", "waiting"),
    "failed": ("bold red", "✖", "failed"),
    "canceled": ("dim red", "⊘", "canceled"),
    "unknown": ("dim white", "-", "unknown"),
}

DEFAULT_PROJECT = "artcraft-suites"

def format_duration(seconds):
    """Format seconds into compact human-readable duration."""
    if seconds is None or seconds < 0:
        return "-"
    total = int(seconds)
    hours = total // 3600
    minutes = (total % 3600) // 60
    secs = total % 60
    if hours > 0:
        return f"{hours}h{minutes:02d}m"
    return f"{minutes}m{secs:02d}s"

def get_terminal_width():
    """Detect current terminal width, respecting COLUMNS if set."""
    cols = os.environ.get("COLUMNS")
    if cols and cols.isdigit():
        return int(cols)
    try:
        w, _ = shutil.get_terminal_size()
        if w > 0:
            return w
    except Exception:
        pass
    return 130

def get_copr_username():
    """Attempt to discover authenticated Copr username via copr-cli whoami."""
    try:
        res = subprocess.run(
            ["copr-cli", "whoami"],
            capture_output=True,
            text=True,
            check=False,
            timeout=5
        )
        if res.returncode == 0:
            user = res.stdout.strip()
            if user:
                return user
    except Exception:
        pass
    return None

def fetch_copr_monitor_data(project_spec):
    """Run `copr-cli monitor <project_spec>` and parse json."""
    cmd = ["copr-cli", "monitor", project_spec]
    try:
        res = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False,
            timeout=25
        )
        if res.returncode != 0:
            return None, res.stderr.strip() or res.stdout.strip() or f"Process returned exit code {res.returncode}"
        
        raw_output = res.stdout.strip()
        if not raw_output:
            return [], None
        
        data = json.loads(raw_output)
        return data, None
    except json.JSONDecodeError as e:
        return None, f"Failed to parse JSON from copr-cli: {e}\nOutput was: {raw_output[:200]}"
    except Exception as e:
        return None, str(e)

def fetch_build_times(project_spec):
    """
    Fetch timing info for recent builds from the Copr REST API.
    Returns a dict mapping build_id -> {
        'submitted_on': float,
        'started_on': float,
        'ended_on': float,
        'duration_str': str,
        'is_running': bool
    }
    """
    if "/" in project_spec:
        owner, proj = project_spec.split("/", 1)
    else:
        owner = get_copr_username() or "apicalshark"
        proj = project_spec

    url = f"https://copr.fedorainfracloud.org/api_3/build/list?ownername={owner}&projectname={proj}&limit=35"
    timing_map = {}
    now = time.time()

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "watch_builds/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            for item in data.get("items", []):
                bid = item.get("id")
                st = item.get("started_on")
                ed = item.get("ended_on")
                sub = item.get("submitted_on")
                state = item.get("state")
                
                duration = None
                is_running = False
                if st and ed:
                    duration = ed - st
                elif st:
                    duration = now - st
                    is_running = True
                elif sub:
                    duration = now - sub

                timing_map[bid] = {
                    "submitted_on": sub,
                    "started_on": st,
                    "ended_on": ed,
                    "duration": duration,
                    "duration_str": format_duration(duration),
                    "is_running": is_running,
                    "state": state,
                }
    except Exception:
        # Non-fatal if API request times out or is unreachable
        pass

    return timing_map

def build_status_cell(state, compact=False):
    """Return a formatted Rich Text object for a build state."""
    state_lower = (state or "unknown").lower()
    style, symbol, label = STATE_STYLES.get(state_lower, ("white", "?", state_lower))
    text = Text()
    text.append(symbol, style=style)
    if not compact:
        text.append(f" {label}", style=style)
    return text

def format_chroot_header(chroot, compact=False):
    """Format chroot string into a readable short column header."""
    s = chroot
    if s.startswith("fedora-"):
        s = s[len("fedora-"):]
    if s.startswith("rawhide"):
        s = s.replace("rawhide", "Raw")
    else:
        parts = s.split("-", 1)
        if len(parts) == 2 and parts[0].isdigit():
            s = f"F{parts[0]}-{parts[1]}"
    if compact:
        s = s.replace("-x86_64", "·x86").replace("-aarch64", "·arm").replace(" x86_64", "·x86").replace(" aarch64", "·arm")
    else:
        s = s.replace("-x86_64", " x86").replace("-aarch64", " arm")
    return s

def generate_renderable(data, timing_map, project_display, last_update, error_msg=None, chroot_filter=None, pkg_filter=None, compact_mode=False, console_width=None):
    """Generate the Rich table / panel layout."""
    
    if error_msg:
        panel_content = Text(f"Error fetching Copr build status:\n{error_msg}\n\nRetrying...", style="bold red")
        return Panel(
            panel_content,
            title=f"[bold cyan]Copr Build Monitor — {project_display}[/bold cyan]",
            subtitle=f"[dim]Last attempt: {last_update}[/dim]",
            border_style="red",
            box=box.ROUNDED,
        )

    if not data:
        return Panel(
            Text("No builds found for this project.", style="yellow"),
            title=f"[bold cyan]Copr Build Monitor — {project_display}[/bold cyan]",
            subtitle=f"[dim]Last update: {last_update}[/dim]",
            border_style="yellow",
            box=box.ROUNDED,
        )

    # Collect unique packages and chroots
    pkgs = {}
    all_chroots = set()

    for item in data:
        pkg_name = item.get("name")
        chroot = item.get("chroot")
        if not pkg_name or not chroot:
            continue

        if pkg_filter and pkg_name not in pkg_filter:
            continue
        if chroot_filter and chroot not in chroot_filter:
            continue

        if pkg_name not in pkgs:
            pkgs[pkg_name] = {
                "version": item.get("pkg_version") or "-",
                "build_id": item.get("build_id"),
                "chroots": {}
            }
        pkgs[pkg_name]["chroots"][chroot] = item.get("state")
        all_chroots.add(chroot)

    sorted_chroots = sorted(list(all_chroots))
    def chroot_sort_key(c):
        arch_rank = 0 if "x86_64" in c else 1
        return (c.rsplit("-", 1)[0], arch_rank, c)

    sorted_chroots.sort(key=chroot_sort_key)
    sorted_pkg_names = sorted(pkgs.keys())

    # Auto-adjust column layout based on available terminal width
    width = console_width or 120
    is_narrow = width < 130
    use_compact = compact_mode or is_narrow

    # Create the grid table
    grid = Table(
        title=f"Copr Project: [bold cyan]{project_display}[/bold cyan]",
        caption=f"[dim]Updated: {last_update} (Press Ctrl+C to exit)[/dim]",
        box=box.ROUNDED,
        header_style="bold bright_white on grey23",
        show_lines=True,
        title_style="bold",
    )

    grid.add_column("Package", style="bold white", no_wrap=True)
    if not is_narrow:
        grid.add_column("Version", style="dim cyan", no_wrap=True)
        grid.add_column("Build ID", style="dim magenta", justify="right", no_wrap=True)
    grid.add_column("Build Time", style="bold bright_yellow", justify="right", no_wrap=True)

    for chroot in sorted_chroots:
        header = format_chroot_header(chroot, compact=is_narrow)
        grid.add_column(header, justify="center", no_wrap=True)

    summary_counts = {k: 0 for k in STATE_STYLES.keys()}

    for pkg_name in sorted_pkg_names:
        info = pkgs[pkg_name]
        bid = info["build_id"]

        # Build time display
        time_text = "-"
        if bid and bid in timing_map:
            tinfo = timing_map[bid]
            dur_str = tinfo["duration_str"]
            if tinfo["is_running"]:
                time_text = f"⏱ [bold yellow]{dur_str}[/bold yellow]"
            else:
                time_text = f"[green]{dur_str}[/green]"

        row = [f"[bold]{pkg_name}[/bold]"]
        if not is_narrow:
            row.append(str(info["version"]))
            row.append(f"#{bid}" if bid else "-")
        row.append(time_text)

        for chroot in sorted_chroots:
            st = info["chroots"].get(chroot, "unknown")
            st_lower = st.lower()
            if st_lower in summary_counts:
                summary_counts[st_lower] += 1
            else:
                summary_counts["unknown"] += 1
            row.append(build_status_cell(st, compact=use_compact))
        grid.add_row(*row)

    # Summary footer text
    summary_parts = []
    if summary_counts.get("succeeded", 0) > 0:
        summary_parts.append(f"[bold green]✔ {summary_counts['succeeded']} succeeded[/bold green]")
    if summary_counts.get("running", 0) > 0:
        summary_parts.append(f"[bold yellow]⚡ {summary_counts['running']} running[/bold yellow]")
    if summary_counts.get("starting", 0) + summary_counts.get("pending", 0) > 0:
        p_count = summary_counts.get("starting", 0) + summary_counts.get("pending", 0)
        summary_parts.append(f"[yellow]⏳ {p_count} queued[/yellow]")
    if summary_counts.get("failed", 0) > 0:
        summary_parts.append(f"[bold red]✖ {summary_counts['failed']} failed[/bold red]")
    if summary_counts.get("canceled", 0) > 0:
        summary_parts.append(f"[dim red]⊘ {summary_counts['canceled']} canceled[/dim red]")

    summary_bar = "  |  ".join(summary_parts) if summary_parts else "[dim]No active build counts[/dim]"

    return Panel(
        grid,
        subtitle=f"Status: {summary_bar}",
        box=box.ROUNDED,
        border_style="blue",
        padding=(0, 1),
    )

def main():
    parser = argparse.ArgumentParser(
        description="Watch Copr package build statuses in a live color-coded grid table with build times without triggering builds."
    )
    parser.add_argument(
        "project",
        nargs="?",
        default=None,
        help=f"Target Copr project or username/project (default: {DEFAULT_PROJECT})"
    )
    parser.add_argument(
        "-p", "--project-opt",
        dest="project_opt",
        default=None,
        help="Target Copr project name"
    )
    parser.add_argument(
        "-n", "--interval",
        type=float,
        default=5.0,
        help="Refresh interval in seconds (default: 5.0). Set to 0 to run once."
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Render current status once and exit (no continuous live watch)."
    )
    parser.add_argument(
        "--compact",
        action="store_true",
        help="Display status using compact icons only (e.g. ✔, ⚡, ⏳, ✖) to fit smaller screens."
    )
    parser.add_argument(
        "--chroots",
        help="Filter chroots by comma-separated list (e.g. fedora-44-x86_64,fedora-rawhide-x86_64)"
    )
    parser.add_argument(
        "--packages",
        help="Filter packages by comma-separated list (e.g. photocraft,wordcraft)"
    )

    args = parser.parse_args()

    project = args.project_opt or args.project or DEFAULT_PROJECT
    if "/" not in project:
        user = get_copr_username()
        project_spec = f"{user}/{project}" if user else project
    else:
        project_spec = project

    chroot_filter = set([c.strip() for c in args.chroots.split(",")]) if args.chroots else None
    pkg_filter = set([p.strip() for p in args.packages.split(",")]) if args.packages else None

    # Setup rich console with terminal auto-detection
    term_width = get_terminal_width()
    console = Console(width=term_width)

    if args.once or args.interval <= 0:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        data, err = fetch_copr_monitor_data(project_spec)
        timing_map = fetch_build_times(project_spec) if not err else {}
        renderable = generate_renderable(
            data, timing_map, project_spec, timestamp, err, chroot_filter, pkg_filter,
            compact_mode=args.compact, console_width=console.width
        )
        console.print(renderable)
        sys.exit(0 if err is None else 1)

    try:
        with Live(console=console, screen=True, refresh_per_second=2) as live:
            while True:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                data, err = fetch_copr_monitor_data(project_spec)
                timing_map = fetch_build_times(project_spec) if not err else {}
                renderable = generate_renderable(
                    data, timing_map, project_spec, timestamp, err, chroot_filter, pkg_filter,
                    compact_mode=args.compact, console_width=console.width
                )
                live.update(renderable)
                time.sleep(max(1.0, args.interval))
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    main()

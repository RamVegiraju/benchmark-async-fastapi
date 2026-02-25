import re
import shlex
import subprocess
from dataclasses import dataclass
from typing import Optional


@dataclass
class HeyResult:
    name: str
    total_s: float
    rps: float
    avg_s: float
    fastest_s: float
    slowest_s: float
    p10_s: Optional[float] = None
    p25_s: Optional[float] = None
    p50_s: Optional[float] = None
    p75_s: Optional[float] = None
    p90_s: Optional[float] = None
    p95_s: Optional[float] = None
    p99_s: Optional[float] = None
    status_ok: Optional[int] = None
    status_other: Optional[int] = None
    raw: str = ""


def _run(cmd: str) -> str:
    proc = subprocess.run(
        shlex.split(cmd),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        check=False,
    )
    return proc.stdout


def _f(m: Optional[re.Match], idx: int = 1) -> Optional[float]:
    if not m:
        return None
    return float(m.group(idx))


def parse_hey(name: str, out: str) -> HeyResult:
    # Basic section
    total = _f(re.search(r"Total:\s+([0-9.]+)\s+secs", out)) or 0.0
    slowest = _f(re.search(r"Slowest:\s+([0-9.]+)\s+secs", out)) or 0.0
    fastest = _f(re.search(r"Fastest:\s+([0-9.]+)\s+secs", out)) or 0.0
    avg = _f(re.search(r"Average:\s+([0-9.]+)\s+secs", out)) or 0.0
    rps = _f(re.search(r"Requests/sec:\s+([0-9.]+)", out)) or 0.0

    # Latency distribution (percentiles)
    def pct(p: int) -> Optional[float]:
        return _f(re.search(rf"{p}%+\s+in\s+([0-9.]+)\s+secs", out))

    p10 = pct(10)
    p25 = pct(25)
    p50 = pct(50)
    p75 = pct(75)
    p90 = pct(90)
    p95 = pct(95)
    p99 = pct(99)

    # Status codes: count 200 vs others (best-effort)
    status_lines = re.findall(r"\[(\d{3})\]\s+(\d+)\s+responses", out)
    ok = None
    other = None
    if status_lines:
        ok = sum(int(n) for code, n in status_lines if code == "200")
        other = sum(int(n) for code, n in status_lines if code != "200")

    return HeyResult(
        name=name,
        total_s=total,
        rps=rps,
        avg_s=avg,
        fastest_s=fastest,
        slowest_s=slowest,
        p10_s=p10,
        p25_s=p25,
        p50_s=p50,
        p75_s=p75,
        p90_s=p90,
        p95_s=p95,
        p99_s=p99,
        status_ok=ok,
        status_other=other,
        raw=out,
    )


def fmt_s(x: Optional[float]) -> str:
    return "-" if x is None else f"{x:.4f}s"


def fmt_num(x: Optional[float]) -> str:
    return "-" if x is None else f"{x:.2f}"


def print_table(a: HeyResult, b: HeyResult) -> None:
    # a vs b, plus deltas (b - a)
    rows = [
        ("Requests/sec", f"{a.rps:.2f}", f"{b.rps:.2f}", f"{(b.rps - a.rps):+.2f}"),
        ("Avg latency", fmt_s(a.avg_s), fmt_s(b.avg_s), f"{(b.avg_s - a.avg_s):+.4f}s"),
        ("p50", fmt_s(a.p50_s), fmt_s(b.p50_s), "-" if (a.p50_s is None or b.p50_s is None) else f"{(b.p50_s - a.p50_s):+.4f}s"),
        ("p95", fmt_s(a.p95_s), fmt_s(b.p95_s), "-" if (a.p95_s is None or b.p95_s is None) else f"{(b.p95_s - a.p95_s):+.4f}s"),
        ("p99", fmt_s(a.p99_s), fmt_s(b.p99_s), "-" if (a.p99_s is None or b.p99_s is None) else f"{(b.p99_s - a.p99_s):+.4f}s"),
        ("Slowest", fmt_s(a.slowest_s), fmt_s(b.slowest_s), f"{(b.slowest_s - a.slowest_s):+.4f}s"),
        ("Total time", fmt_s(a.total_s), fmt_s(b.total_s), f"{(b.total_s - a.total_s):+.4f}s"),
        ("200 OK", str(a.status_ok) if a.status_ok is not None else "-", str(b.status_ok) if b.status_ok is not None else "-", "-"),
        ("Non-200", str(a.status_other) if a.status_other is not None else "-", str(b.status_other) if b.status_other is not None else "-", "-"),
    ]

    col1 = max(len(r[0]) for r in rows)
    col2 = max(len(r[1]) for r in rows + [("", a.name, "", "")])
    col3 = max(len(r[2]) for r in rows + [("", b.name, "", "")])
    col4 = max(len(r[3]) for r in rows)

    print()
    print(f"{'Metric'.ljust(col1)}  {a.name.ljust(col2)}  {b.name.ljust(col3)}  {'Δ (B-A)'.ljust(col4)}")
    print("-" * (col1 + col2 + col3 + col4 + 6))
    for m, va, vb, d in rows:
        print(f"{m.ljust(col1)}  {va.ljust(col2)}  {vb.ljust(col3)}  {d.ljust(col4)}")
    print()


def main() -> None:
    # Edit these if you want
    n = 200
    c = 50
    base = "http://localhost:8000"
    url_async = f"{base}/inference_async?x=5"
    url_sync = f"{base}/inference_sync?x=5"

    # Commands
    cmd_async = f'hey -n {n} -c {c} -m POST "{url_async}"'
    cmd_sync = f'hey -n {n} -c {c} -m POST "{url_sync}"'

    print("Running:")
    print("  " + cmd_async)
    out_async = _run(cmd_async)

    print("Running:")
    print("  " + cmd_sync)
    out_sync = _run(cmd_sync)

    a = parse_hey("async", out_async)
    b = parse_hey("sync", out_sync)

    print_table(a, b)

    # Optional: uncomment to dump raw outputs if you want
    # print("=== RAW ASYNC ===\n", out_async)
    # print("=== RAW SYNC ===\n", out_sync)


if __name__ == "__main__":
    main()
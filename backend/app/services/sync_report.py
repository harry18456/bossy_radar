"""Per-source sync result tracking for fail-loud CLI commands.

Sync services return a SyncReport; the CLI prints render_summary() and exits
non-zero when has_failures is true (BACKEND_AUDIT M11).
"""

from dataclasses import dataclass, field


@dataclass
class SourceResult:
    name: str
    success: bool
    rows_written: int = 0
    rows_skipped: int = 0
    error: str | None = None


@dataclass
class SyncReport:
    results: list[SourceResult] = field(default_factory=list)
    # Set when a circuit breaker aborted the run (bounded-retries spec).
    circuit_broken: bool = False

    def add(self, result: SourceResult) -> None:
        self.results.append(result)

    @property
    def has_failures(self) -> bool:
        return self.circuit_broken or any(not r.success for r in self.results)

    def render_summary(self) -> str:
        lines = ["=== Sync Summary ==="]
        for r in self.results:
            if r.success:
                lines.append(
                    f"  {r.name}: OK (written={r.rows_written}, "
                    f"skipped={r.rows_skipped})"
                )
            else:
                lines.append(f"  {r.name}: FAILED - {r.error or 'unknown error'}")
        if self.circuit_broken:
            lines.append("  !! circuit breaker tripped - run aborted early")
        return "\n".join(lines)

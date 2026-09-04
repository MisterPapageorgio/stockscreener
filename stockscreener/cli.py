from __future__ import annotations

from .pipeline import run_scan


def main() -> None:
    result = run_scan()
    print(result[["ticker", "dip_score", "quality_score", "valuation_score", "overall_score"]].to_string(index=False))


if __name__ == "__main__":
    main()

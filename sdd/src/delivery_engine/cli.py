from __future__ import annotations

import argparse
import sys


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="delivery-engine",
        description="Portfolio Delivery & Economic Flow Governance Engine",
    )
    # Flat-CSV mode (single self-contained file)
    parser.add_argument(
        "--flat-csv",
        help="Path to a flat delivery CSV (ticket_id, workstream, team, …). "
             "Builds the portfolio automatically; --portfolio and --events are not needed.",
    )
    # Standard mode
    parser.add_argument("--portfolio", help="Path to portfolio.json")
    parser.add_argument("--events", help="Path to work_item_events.csv")
    parser.add_argument("--output-dir", required=True, help="Directory for output files")
    args = parser.parse_args()

    from delivery_engine.engine import DeliveryAnalyticsEngine
    from delivery_engine.io.exporter import ReportExporter
    from delivery_engine.io.loader import DataLoader
    import os

    if args.flat_csv:
        portfolio, _ = DataLoader.load_from_flat_csv(args.flat_csv)
    elif args.portfolio and args.events:
        portfolio = DataLoader.load_portfolio(args.portfolio)
        work_items = DataLoader.load_work_items(args.events, portfolio)
        portfolio.work_items = work_items
    else:
        parser.error("Provide either --flat-csv or both --portfolio and --events.")

    engine = DeliveryAnalyticsEngine(portfolio)
    report = engine.calculate_all()

    exporter = ReportExporter()
    csv_files = exporter.export_csv(report, output_dir=args.output_dir)
    dashboard_path = exporter.export_dashboard(
        report,
        output_path=os.path.join(args.output_dir, "dashboard.html"),
    )

    for path in csv_files:
        print(path)
    print(dashboard_path)


if __name__ == "__main__":
    main()

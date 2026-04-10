from __future__ import annotations

import csv
import os


class ReportExporter:

    def export_csv(self, report, output_dir: str) -> list[str]:
        os.makedirs(output_dir, exist_ok=True)
        written: list[str] = []
        written.extend(self._write_flow_efficiency(report, output_dir))
        written.extend(self._write_cost_of_delay(report, output_dir))
        written.extend(self._write_cycle_time(report, output_dir))
        written.extend(self._write_roi_scatter(report, output_dir))
        return written

    def export_dashboard(self, report, output_path: str) -> str:
        from delivery_engine.dashboard.static import build_static_html

        output_path = os.path.abspath(output_path)
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        html = build_static_html(report)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html)
        return output_path

    # ------------------------------------------------------------------
    # US1: flow_efficiency.csv
    # ------------------------------------------------------------------

    def _write_flow_efficiency(self, report, output_dir: str) -> list[str]:
        path = os.path.join(output_dir, "flow_efficiency.csv")
        fieldnames = [
            "workstream_id", "workstream_name", "flow_efficiency_pct",
            "active_time_days", "total_lead_time_days", "below_threshold",
            "threshold_pct",
        ]
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for r in report.flow_efficiency:
                writer.writerow({
                    "workstream_id": r.workstream_id,
                    "workstream_name": r.workstream_name,
                    "flow_efficiency_pct": r.flow_efficiency_pct,
                    "active_time_days": r.active_time_days,
                    "total_lead_time_days": r.total_lead_time_days,
                    "below_threshold": r.below_threshold,
                    "threshold_pct": r.threshold_pct,
                })
        return [path]

    # ------------------------------------------------------------------
    # US2: cost_of_delay.csv
    # ------------------------------------------------------------------

    def _write_cost_of_delay(self, report, output_dir: str) -> list[str]:
        path = os.path.join(output_dir, "cost_of_delay.csv")
        fieldnames = [
            "team_id", "team_name", "workstream_name",
            "work_item_id", "title", "priority",
            "wait_time_days", "resource_daily_rate", "cost_of_delay",
        ]
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for team_result in report.cost_of_delay:
                for entry in team_result.breakdown:
                    writer.writerow({
                        "team_id": team_result.team_id,
                        "team_name": team_result.team_name,
                        "workstream_name": team_result.workstream_name,
                        "work_item_id": entry.work_item_id,
                        "title": entry.title,
                        "priority": entry.priority,
                        "wait_time_days": entry.wait_time_days,
                        "resource_daily_rate": entry.resource_daily_rate,
                        "cost_of_delay": entry.cost_of_delay,
                    })
                # Team total summary row
                writer.writerow({
                    "team_id": team_result.team_id,
                    "team_name": team_result.team_name,
                    "workstream_name": team_result.workstream_name,
                    "work_item_id": "",
                    "title": "",
                    "priority": "",
                    "wait_time_days": "",
                    "resource_daily_rate": "",
                    "cost_of_delay": team_result.total_cost_of_delay,
                })
        return [path]

    # ------------------------------------------------------------------
    # US3: cycle_time.csv
    # ------------------------------------------------------------------

    def _write_cycle_time(self, report, output_dir: str) -> list[str]:
        path = os.path.join(output_dir, "cycle_time.csv")
        fieldnames = ["priority", "median_days", "iqr_days", "high_variance", "sample_count"]
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for r in report.cycle_time:
                writer.writerow({
                    "priority": r.priority,
                    "median_days": r.median_days,
                    "iqr_days": r.iqr_days,
                    "high_variance": r.high_variance,
                    "sample_count": r.sample_count,
                })
        return [path]

    # ------------------------------------------------------------------
    # US4: roi_scatter.csv
    # ------------------------------------------------------------------

    def _write_roi_scatter(self, report, output_dir: str) -> list[str]:
        path = os.path.join(output_dir, "roi_scatter.csv")
        fieldnames = [
            "work_item_id", "title", "priority", "business_value",
            "lead_time_days", "team_name", "workstream_name",
        ]
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for r in report.roi_scatter:
                writer.writerow({
                    "work_item_id": r.work_item_id,
                    "title": r.title,
                    "priority": r.priority,
                    "business_value": r.business_value,
                    "lead_time_days": r.lead_time_days,
                    "team_name": r.team_name,
                    "workstream_name": r.workstream_name,
                })
        return [path]

"""
Generates a fully self-contained HTML dashboard from an EngineReport.
Uses plotly.io.to_html() so no server or CDN is required.
"""
from __future__ import annotations


def build_static_html(report) -> str:
    import plotly.graph_objects as go
    import plotly.express as px
    import plotly.io as pio

    summary = report.summary

    # ---------------------------------------------------------------
    # Tab 1: Flow Efficiency
    # ---------------------------------------------------------------
    fe = report.flow_efficiency
    fe_fig = go.Figure()
    if fe:
        fe_fig.add_trace(go.Bar(
            x=[r.flow_efficiency_pct for r in fe],
            y=[r.workstream_name for r in fe],
            orientation="h",
            marker_color=["#E74C3C" if r.below_threshold else "#27AE60" for r in fe],
            customdata=[[r.flow_efficiency_pct, r.threshold_pct] for r in fe],
            hovertemplate=(
                "<b>%{y}</b><br>"
                "Flow Efficiency: %{x:.1f}%<br>"
                "Threshold: %{customdata[1]:.1f}%<extra></extra>"
            ),
        ))
        avg_threshold = sum(r.threshold_pct for r in fe) / len(fe)
        fe_fig.add_vline(
            x=avg_threshold,
            line_dash="dash",
            line_color="orange",
            annotation_text=f"Avg threshold {avg_threshold:.0f}%",
        )
    fe_fig.update_layout(
        title="Flow Efficiency by Workstream",
        xaxis_title="Flow Efficiency (%)",
        xaxis_range=[0, 100],
        margin={"l": 200},
        height=400,
    )

    # ---------------------------------------------------------------
    # Tab 2: Cost of Delay
    # ---------------------------------------------------------------
    cod = report.cost_of_delay
    cod_fig = go.Figure()
    if cod:
        cod_fig.add_trace(go.Bar(
            x=[r.team_name for r in cod],
            y=[r.total_cost_of_delay for r in cod],
            marker_color="#C0392B",
            hovertemplate="<b>%{x}</b><br>CoD: $%{y:,.0f}<extra></extra>",
        ))
    cod_fig.update_layout(
        title="Cost of Delay by Team (sorted by total CoD)",
        yaxis_title="Cost of Delay ($)",
        height=400,
    )

    # ---------------------------------------------------------------
    # Tab 3: Cycle Time
    # ---------------------------------------------------------------
    ct = report.cycle_time
    ct_fig = go.Figure()
    for r in ct:
        color = "#E74C3C" if r.high_variance else "#3498DB"
        ct_fig.add_trace(go.Box(
            name=r.priority,
            median=[r.median_days],
            q1=[max(r.median_days - r.iqr_days / 2, 0)],
            q3=[r.median_days + r.iqr_days / 2],
            lowerfence=[max(r.median_days - r.iqr_days, 0)],
            upperfence=[r.median_days + r.iqr_days * 1.5],
            marker_color=color,
            hovertemplate=(
                f"<b>{r.priority}</b><br>"
                f"Median: {r.median_days:.1f}d<br>"
                f"IQR: {r.iqr_days:.1f}d<br>"
                f"Samples: {r.sample_count}<extra></extra>"
            ),
        ))
    ct_fig.update_layout(
        title="Cycle Time Distribution by Priority (red = high variance)",
        yaxis_title="Cycle Time (days)",
        showlegend=False,
        height=400,
    )

    # ---------------------------------------------------------------
    # Tab 4: ROI Scatter
    # ---------------------------------------------------------------
    roi = report.roi_scatter
    roi_fig = go.Figure()
    if roi:
        import pandas as pd
        df = pd.DataFrame([{
            "work_item_id": p.work_item_id,
            "title": p.title,
            "priority": p.priority,
            "business_value": p.business_value,
            "lead_time_days": p.lead_time_days,
            "team_name": p.team_name,
            "workstream_name": p.workstream_name,
        } for p in roi])
        roi_fig = px.scatter(
            df,
            x="lead_time_days",
            y="business_value",
            color="priority",
            hover_data=["title", "business_value", "lead_time_days"],
            labels={
                "lead_time_days": "Lead Time (days)",
                "business_value": "Business Value (0–100)",
            },
            title="Value vs. Lead Time (ROI Scatter)",
        )
    roi_fig.update_layout(height=400)

    # ---------------------------------------------------------------
    # Render each figure to HTML div (include JS only in first)
    # ---------------------------------------------------------------
    fe_html = pio.to_html(fe_fig, full_html=False, include_plotlyjs=True)
    cod_html = pio.to_html(cod_fig, full_html=False, include_plotlyjs=False)
    ct_html = pio.to_html(ct_fig, full_html=False, include_plotlyjs=False)
    roi_html = pio.to_html(roi_fig, full_html=False, include_plotlyjs=False)

    generated_at = report.generated_at.strftime("%Y-%m-%d %H:%M UTC")

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{report.portfolio_name} — Delivery Dashboard</title>
<style>
  body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
          margin: 0; background: #f5f5f5; color: #333; }}
  .header {{ background: #fff; padding: 24px 32px 16px; border-bottom: 1px solid #e0e0e0; }}
  .header h1 {{ margin: 0 0 4px; font-size: 1.5rem; }}
  .header p  {{ margin: 0 0 16px; color: #888; font-size: 0.9rem; }}
  .kpis {{ display: flex; gap: 24px; flex-wrap: wrap; }}
  .kpi  {{ background: #f8f8f8; border-radius: 6px; padding: 12px 20px; min-width: 160px; }}
  .kpi h3 {{ margin: 0 0 2px; font-size: 1.1rem; color: #222; }}
  .kpi p  {{ margin: 0; font-size: 0.8rem; color: #888; }}
  .tabs {{ display: flex; gap: 0; padding: 0 32px;
           background: #fff; border-bottom: 2px solid #e0e0e0; }}
  .tab-btn {{ padding: 12px 24px; cursor: pointer; border: none; background: none;
              font-size: 0.95rem; color: #666; border-bottom: 3px solid transparent;
              margin-bottom: -2px; }}
  .tab-btn.active {{ color: #2980B9; border-bottom-color: #2980B9; font-weight: 600; }}
  .tab-btn:hover {{ color: #333; }}
  .tab-content {{ display: none; padding: 24px 32px; background: #fff;
                  margin: 16px 32px; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,.1); }}
  .tab-content.active {{ display: block; }}
</style>
</head>
<body>

<div class="header">
  <h1>{report.portfolio_name}</h1>
  <p>Generated: {generated_at}</p>
  <div class="kpis">
    <div class="kpi">
      <h3>${summary.total_portfolio_cod:,.0f}</h3>
      <p>Total Portfolio CoD</p>
    </div>
    <div class="kpi">
      <h3>{summary.worst_flow_efficiency_workstream}</h3>
      <p>Worst Flow Efficiency</p>
    </div>
    <div class="kpi">
      <h3>{summary.highest_cod_team}</h3>
      <p>Highest CoD Team</p>
    </div>
    <div class="kpi">
      <h3>{summary.most_variable_priority_tier}</h3>
      <p>Most Variable Priority Tier</p>
    </div>
  </div>
</div>

<div class="tabs">
  <button class="tab-btn active" onclick="showTab('fe', this)">Flow Efficiency</button>
  <button class="tab-btn" onclick="showTab('cod', this)">Cost of Delay</button>
  <button class="tab-btn" onclick="showTab('ct', this)">Cycle Time</button>
  <button class="tab-btn" onclick="showTab('roi', this)">ROI Scatter</button>
</div>

<div id="tab-fe" class="tab-content active">{fe_html}</div>
<div id="tab-cod" class="tab-content">{cod_html}</div>
<div id="tab-ct" class="tab-content">{ct_html}</div>
<div id="tab-roi" class="tab-content">{roi_html}</div>

<script>
function showTab(name, btn) {{
  document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
  document.querySelectorAll('.tab-btn').forEach(el => el.classList.remove('active'));
  document.getElementById('tab-' + name).classList.add('active');
  btn.classList.add('active');
}}
</script>
</body>
</html>
"""

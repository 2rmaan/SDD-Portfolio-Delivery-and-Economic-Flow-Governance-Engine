from __future__ import annotations

from dash import dcc, html


def build_flow_efficiency_tab(results) -> dcc.Tab:
    import plotly.graph_objects as go

    workstream_names = [r.workstream_name for r in results]
    pct_values = [r.flow_efficiency_pct for r in results]
    colors = ["#E74C3C" if r.below_threshold else "#27AE60" for r in results]
    thresholds = [r.threshold_pct for r in results]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=pct_values,
        y=workstream_names,
        orientation="h",
        marker_color=colors,
        customdata=list(zip(pct_values, thresholds)),
        hovertemplate=(
            "<b>%{y}</b><br>"
            "Flow Efficiency: %{x:.1f}%<br>"
            "Threshold: %{customdata[1]:.1f}%<extra></extra>"
        ),
    ))

    if results:
        avg_threshold = sum(thresholds) / len(thresholds)
        fig.add_vline(
            x=avg_threshold,
            line_dash="dash",
            line_color="orange",
            annotation_text=f"Avg threshold {avg_threshold:.0f}%",
            annotation_position="top right",
        )

    fig.update_layout(
        title="Flow Efficiency by Workstream",
        xaxis_title="Flow Efficiency (%)",
        xaxis_range=[0, 100],
        yaxis_title="Workstream",
        margin={"l": 160},
    )

    return dcc.Tab(
        label="Flow Efficiency",
        children=[dcc.Graph(figure=fig, id="flow-efficiency-chart")],
    )


def build_cost_of_delay_tab(results, app=None) -> dcc.Tab:
    import plotly.express as px

    team_names = [r.team_name for r in results]
    cod_values = [r.total_cost_of_delay for r in results]

    fig = px.bar(
        x=team_names,
        y=cod_values,
        labels={"x": "Team", "y": "Cost of Delay ($)"},
        title="Cost of Delay by Team",
        color=cod_values,
        color_continuous_scale="Reds",
    )
    fig.update_layout(coloraxis_showscale=False)

    table_placeholder = html.Div(id="cod-drill-down-table")

    tab_content: list = [
        dcc.Graph(
            figure=fig,
            id="cod-chart",
            clickData=None,
        ),
        table_placeholder,
    ]

    return dcc.Tab(
        label="Cost of Delay",
        children=tab_content,
    )


def build_cycle_time_tab(results, work_items=None, app=None) -> dcc.Tab:
    import plotly.graph_objects as go

    fig = go.Figure()

    for r in results:
        color = "#E74C3C" if r.high_variance else "#3498DB"
        fig.add_trace(go.Box(
            name=r.priority,
            median=[r.median_days],
            q1=[max(r.median_days - r.iqr_days / 2, 0)],
            q3=[r.median_days + r.iqr_days / 2],
            lowerfence=[max(r.median_days - r.iqr_days, 0)],
            upperfence=[r.median_days + r.iqr_days * 1.5],
            marker_color=color,
            hovertemplate=(
                f"<b>{r.priority}</b><br>"
                f"Median: {r.median_days:.1f} days<br>"
                f"IQR: {r.iqr_days:.1f} days<br>"
                f"Samples: {r.sample_count}<extra></extra>"
            ),
        ))

    fig.update_layout(
        title="Cycle Time Distribution by Priority",
        yaxis_title="Cycle Time (days)",
        showlegend=False,
    )

    team_options: list[dict] = []
    if work_items:
        teams = sorted({wi.team_id for wi in work_items})
        team_options = [{"label": t, "value": t} for t in teams]

    return dcc.Tab(
        label="Cycle Time",
        children=[
            dcc.Dropdown(
                id="cycle-time-team-filter",
                options=team_options,
                multi=True,
                placeholder="Filter by team…",
                style={"marginBottom": "12px"},
            ),
            dcc.Graph(figure=fig, id="cycle-time-chart"),
        ],
    )


def build_roi_scatter_tab(points, app=None) -> dcc.Tab:
    import plotly.express as px

    if points:
        import pandas as pd
        data = pd.DataFrame([
            {
                "work_item_id": p.work_item_id,
                "title": p.title,
                "priority": p.priority,
                "business_value": p.business_value,
                "lead_time_days": p.lead_time_days,
                "team_name": p.team_name,
                "workstream_name": p.workstream_name,
            }
            for p in points
        ])
        fig = px.scatter(
            data,
            x="lead_time_days",
            y="business_value",
            color="priority",
            hover_data=["title", "business_value", "lead_time_days"],
            title="Value vs. Lead Time (ROI Scatter)",
            labels={
                "lead_time_days": "Lead Time (days)",
                "business_value": "Business Value (0–100)",
            },
        )
    else:
        import plotly.graph_objects as go
        fig = go.Figure()
        fig.update_layout(title="Value vs. Lead Time (no scored items)")

    priorities = sorted({p.priority for p in points}) if points else []
    priority_options = [{"label": p, "value": p} for p in priorities]

    return dcc.Tab(
        label="ROI Scatter",
        children=[
            dcc.Dropdown(
                id="roi-priority-filter",
                options=priority_options,
                multi=True,
                placeholder="Filter by priority…",
                style={"marginBottom": "12px"},
            ),
            dcc.Graph(figure=fig, id="roi-scatter-chart"),
        ],
    )


def build_dashboard(report, app=None):
    from dash import Dash

    if app is None:
        app = Dash(__name__)

    fe_tab = build_flow_efficiency_tab(report.flow_efficiency)
    cod_tab = build_cost_of_delay_tab(report.cost_of_delay, app=app)
    ct_tab = build_cycle_time_tab(report.cycle_time, work_items=None, app=app)
    roi_tab = build_roi_scatter_tab(report.roi_scatter, app=app)

    summary = report.summary
    kpi_style = {
        "display": "inline-block",
        "margin": "0 24px",
        "textAlign": "center",
    }
    header = html.Div([
        html.H2(report.portfolio_name, style={"margin": "0 0 4px 0"}),
        html.P(
            f"Generated: {report.generated_at.strftime('%Y-%m-%d %H:%M UTC')}",
            style={"color": "#666", "margin": "0 0 16px 0"},
        ),
        html.Div([
            html.Div([
                html.H4(f"${summary.total_portfolio_cod:,.0f}", style={"margin": 0}),
                html.P("Total Portfolio CoD", style={"margin": 0, "color": "#888"}),
            ], style=kpi_style),
            html.Div([
                html.H4(summary.worst_flow_efficiency_workstream, style={"margin": 0}),
                html.P("Worst Flow Efficiency", style={"margin": 0, "color": "#888"}),
            ], style=kpi_style),
            html.Div([
                html.H4(summary.highest_cod_team, style={"margin": 0}),
                html.P("Highest CoD Team", style={"margin": 0, "color": "#888"}),
            ], style=kpi_style),
            html.Div([
                html.H4(summary.most_variable_priority_tier, style={"margin": 0}),
                html.P("Most Variable Priority", style={"margin": 0, "color": "#888"}),
            ], style=kpi_style),
        ], style={"backgroundColor": "#f8f8f8", "padding": "16px", "borderRadius": "6px"}),
    ], style={"padding": "24px 24px 0 24px"})

    workstream_options = [
        {"label": ws_name, "value": ws_name}
        for ws_name in sorted({r.workstream_name for r in report.flow_efficiency})
    ]

    app.layout = html.Div([
        header,
        html.Div([
            dcc.DatePickerRange(id="global-date-range", style={"marginRight": "16px"}),
            dcc.Dropdown(
                id="global-workstream-filter",
                options=workstream_options,
                multi=True,
                placeholder="Filter by workstream…",
                style={"minWidth": "240px", "display": "inline-block"},
            ),
        ], style={"padding": "12px 24px", "display": "flex", "alignItems": "center"}),
        dcc.Tabs([fe_tab, cod_tab, ct_tab, roi_tab], id="main-tabs"),
    ])

    # Register global filter callback (server-mode only; static HTML shows initial state)
    _register_global_filter_callback(app, report)
    _register_cod_drilldown_callback(app, report)

    return app


def _register_global_filter_callback(app, report) -> None:
    from dash import Input, Output, callback_context

    @app.callback(
        Output("flow-efficiency-chart", "figure"),
        Output("cycle-time-chart", "figure"),
        Output("roi-scatter-chart", "figure"),
        Input("global-workstream-filter", "value"),
        Input("global-date-range", "start_date"),
        Input("global-date-range", "end_date"),
        prevent_initial_call=True,
    )
    def refresh_all_tabs(ws_filter, start_date, end_date):
        from delivery_engine.calculators.cycle_time import CycleTimeAnalyzer, InsufficientDataError
        from delivery_engine.calculators.flow_efficiency import FlowEfficiencyCalculator
        from delivery_engine.calculators.roi_scatter import ROIScatterAnalyzer
        import plotly.graph_objects as go

        # Filter work items by workstream name if requested
        wi = report._work_items if hasattr(report, "_work_items") else []
        fe_results = report.flow_efficiency
        ct_results = report.cycle_time
        roi_results = report.roi_scatter

        if ws_filter:
            ws_names = set(ws_filter)
            fe_results = [r for r in fe_results if r.workstream_name in ws_names]
            roi_results = [r for r in roi_results if r.workstream_name in ws_names]

        # Rebuild figures
        import plotly.express as px

        # Flow efficiency
        import plotly.graph_objects as go
        fe_fig = go.Figure()
        if fe_results:
            fe_fig.add_trace(go.Bar(
                x=[r.flow_efficiency_pct for r in fe_results],
                y=[r.workstream_name for r in fe_results],
                orientation="h",
                marker_color=["#E74C3C" if r.below_threshold else "#27AE60" for r in fe_results],
            ))
        fe_fig.update_layout(title="Flow Efficiency by Workstream", xaxis_range=[0, 100])

        # Cycle time
        ct_fig = go.Figure()
        for r in ct_results:
            color = "#E74C3C" if r.high_variance else "#3498DB"
            ct_fig.add_trace(go.Box(
                name=r.priority,
                median=[r.median_days],
                q1=[max(r.median_days - r.iqr_days / 2, 0)],
                q3=[r.median_days + r.iqr_days / 2],
                lowerfence=[max(r.median_days - r.iqr_days, 0)],
                upperfence=[r.median_days + r.iqr_days * 1.5],
                marker_color=color,
            ))
        ct_fig.update_layout(title="Cycle Time Distribution by Priority")

        # ROI scatter
        if roi_results:
            import pandas as pd
            data = pd.DataFrame([{
                "title": p.title, "priority": p.priority,
                "business_value": p.business_value, "lead_time_days": p.lead_time_days,
            } for p in roi_results])
            roi_fig = px.scatter(data, x="lead_time_days", y="business_value",
                                 color="priority", hover_data=["title"])
        else:
            roi_fig = go.Figure()

        return fe_fig, ct_fig, roi_fig


def _register_cod_drilldown_callback(app, report) -> None:
    from dash import Input, Output
    from dash import dash_table

    @app.callback(
        Output("cod-drill-down-table", "children"),
        Input("cod-chart", "clickData"),
        prevent_initial_call=True,
    )
    def show_cod_drilldown(click_data):
        if not click_data:
            return []
        team_name = click_data["points"][0]["x"]
        team_result = next((r for r in report.cost_of_delay if r.team_name == team_name), None)
        if team_result is None:
            return []
        rows = [
            {
                "Work Item": e.work_item_id,
                "Title": e.title,
                "Priority": e.priority,
                "Wait Days": round(e.wait_time_days, 1),
                "Daily Rate": f"${e.resource_daily_rate:,.0f}",
                "CoD": f"${e.cost_of_delay:,.0f}",
            }
            for e in team_result.breakdown
        ]
        return dash_table.DataTable(
            data=rows,
            columns=[{"name": c, "id": c} for c in rows[0].keys()],
            style_table={"marginTop": "16px"},
        )

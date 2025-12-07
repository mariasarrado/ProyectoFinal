from dash import Dash, dcc, html, Input, Output
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import textwrap
import os

# ============================
# 1. CARGA Y PREPROCESADO
# ============================

df = pd.read_csv("DataExtract.csv")

cols = [
    "Country", "Year", "Air Pollutant", "Air Pollutant Description",
    "Data Aggregation Process", "Spatial Resolution Description",
    "Temporal Resolution", "Meteorology", "Chemistry", "Emissions", "Topography",
    "Assessment Type", "Administration Level", "Model Application"
]

data = df[cols].copy()
data = data.dropna(subset=["Country", "Year", "Air Pollutant"])
data["Year"] = pd.to_numeric(data["Year"], errors="coerce")
data = data.dropna(subset=["Year"])
data["Year"] = data["Year"].astype(int)

for c in ["Country", "Air Pollutant", "Data Aggregation Process"]:
    data[c] = data[c].astype(str).str.strip()

pollutants = sorted(data["Air Pollutant"].dropna().unique().tolist())
countries = ["Todos los países"] + sorted(data["Country"].dropna().unique().tolist())

ymin, ymax = int(data["Year"].min()), int(data["Year"].max())

# ============================
# 2. ESTILO GLOBAL
# ============================

GRAPH_CONFIG = {
    "displaylogo": False,
    "modeBarButtonsToRemove": [
        "zoom2d", "pan2d", "select2d", "lasso2d",
        "autoScale2d", "resetScale2d"
    ],
    "toImageButtonOptions": {
        "format": "png",
        "filename": "eea_air_quality_dashboard",
        "height": 600,
        "width": 1000,
        "scale": 2,
    },
}

def style_fig(fig, title=None):
    fig.update_layout(
        title=title or fig.layout.title.text,
        template="plotly_white",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=40, r=20, t=70, b=40),
        font=dict(
            family="Segoe UI, system-ui, -apple-system, sans-serif",
            size=12,
            color="#212529",
        ),
        title_font=dict(
            size=18,
            family="Segoe UI, system-ui, -apple-system, sans-serif",
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.25,
            xanchor="left",
            x=0,
        ),
        hoverlabel=dict(
            bgcolor="white",
            bordercolor="#9ca3af",
            font_size=12,
            font_family="Segoe UI, system-ui, -apple-system, sans-serif",
        ),
    )
    return fig


def format_int(n):
    try:
        return f"{int(n):,}".replace(",", ".")
    except Exception:
        return "0"

# ============================
# 3. APP
# ============================

app = Dash(__name__)
server = app.server     # <- Necesario para Render

app.title = "EEA Air Quality Models"

CARD_STYLE = {
    "background": "white",
    "borderRadius": "14px",
    "padding": "16px 18px",
    "boxShadow": "0 4px 10px rgba(15, 23, 42, 0.06)",
}

KPI_CARD_STYLE = {
    **CARD_STYLE,
    "textAlign": "center",
    "padding": "16px 8px",
}

# ============================
# 4. LAYOUT
# ============================

app.layout = html.Div(
    style={
        "minHeight": "100vh",
        "background": "linear-gradient(135deg, #e0f7fa 0%, #e8f5e9 45%, #bbdefb 100%)",
        "padding": "24px 12px",
    },
    children=[
        html.Div(
            style={"maxWidth": "1300px", "margin": "0 auto"},
            children=[

                # CABECERA
                html.Div(
                    style={"marginBottom": "10px"},
                    children=[
                        html.H1(
                            "EEA Air Quality Models Dashboard",
                            style={
                                "fontFamily": "Segoe UI, system-ui, -apple-system, sans-serif",
                                "fontSize": "32px",
                                "marginBottom": "4px",
                                "color": "#0f172a",
                                "letterSpacing": "0.02em",
                            },
                        ),
                        html.P(
                            "Explora cómo los países europeos modelizan la calidad del aire por contaminante, año y tipo de proceso.",
                            style={
                                "margin": "0",
                                "color": "#1e293b",
                                "fontSize": "14px",
                                "maxWidth": "780px",
                            },
                        ),
                    ],
                ),

                html.Hr(style={"borderColor": "#d1d5db", "margin": "8px 0 18px"}),

                # FILTROS
                html.Div(
                    style={
                        "display": "flex",
                        "gap": "16px",
                        "flexWrap": "wrap",
                        "marginBottom": "18px",
                    },
                    children=[

                        # Dropdown contaminantes
                        html.Div(
                            style={**CARD_STYLE, "flex": "1 1 260px"},
                            children=[
                                html.Label(
                                    [
                                        "Contaminantes ",
                                        html.Span(
                                            "ⓘ",
                                            title="Selecciona uno o varios contaminantes declarados en los modelos EEA.",
                                            style={
                                                "cursor": "help",
                                                "color": "#6b7280",
                                                "fontSize": "11px",
                                            },
                                        ),
                                    ],
                                    style={
                                        "fontWeight": "600",
                                        "fontSize": "13px",
                                        "color": "#6b7280",
                                    },
                                ),
                                dcc.Dropdown(
                                    id="dd-pol",
                                    options=[{"label": p, "value": p} for p in pollutants],
                                    value=[pollutants[0]],
                                    multi=True,
                                    clearable=False,
                                    style={"marginTop": "6px"},
                                ),
                            ],
                        ),

                        # Slider años
                        html.Div(
                            style={**CARD_STYLE, "flex": "1 1 260px"},
                            children=[
                                html.Label(
                                    [
                                        "Rango de años ",
                                        html.Span(
                                            "ⓘ",
                                            title="Acota el periodo temporal de los modelos incluidos.",
                                            style={
                                                "cursor": "help",
                                                "color": "#6b7280",
                                                "fontSize": "11px",
                                            },
                                        ),
                                    ],
                                    style={
                                        "fontWeight": "600",
                                        "fontSize": "13px",
                                        "color": "#6b7280",
                                    },
                                ),
                                dcc.RangeSlider(
                                    id="sl-year",
                                    min=ymin,
                                    max=ymax,
                                    step=1,
                                    value=[max(ymin, ymax - 10), ymax],
                                    marks={
                                        y: str(y)
                                        for y in range(
                                            ymin,
                                            ymax + 1,
                                            max(1, (ymax - ymin) // 5 or 1),
                                        )
                                    },
                                    tooltip={"placement": "bottom"},
                                    allowCross=False,
                                ),
                            ],
                        ),

                        # Dropdown país
                        html.Div(
                            style={**CARD_STYLE, "flex": "1 1 260px"},
                            children=[
                                html.Label(
                                    [
                                        "País ",
                                        html.Span(
                                            "ⓘ",
                                            title="Filtra la vista para un país concreto o analiza todos en conjunto.",
                                            style={
                                                "cursor": "help",
                                                "color": "#6b7280",
                                                "fontSize": "11px",
                                            },
                                        ),
                                    ],
                                    style={
                                        "fontWeight": "600",
                                        "fontSize": "13px",
                                        "color": "#6b7280",
                                    },
                                ),
                                dcc.Dropdown(
                                    id="dd-country",
                                    options=[{"label": c, "value": c} for c in countries],
                                    value="Todos los países",
                                    clearable=False,
                                    style={"marginTop": "6px"},
                                ),
                            ],
                        ),
                    ],
                ),

                # KPIs
                html.Div(
                    style={
                        "display": "flex",
                        "gap": "16px",
                        "flexWrap": "wrap",
                        "marginBottom": "22px",
                    },
                    children=[
                        # KPI tarjetas
                        html.Div(
                            style={**KPI_CARD_STYLE, "flex": "1 1 180px"},
                            children=[
                                html.P(
                                    "Modelos",
                                    style={
                                        "margin": "0 0 4px",
                                        "fontSize": "12px",
                                        "textTransform": "uppercase",
                                        "letterSpacing": "0.12em",
                                        "color": "#9ca3af",
                                        "fontWeight": "600",
                                    },
                                ),
                                html.H2(
                                    id="kpi-models",
                                    style={
                                        "margin": "0",
                                        "fontSize": "30px",
                                        "color": "#111827",
                                    },
                                ),
                                html.P(
                                    "Total de registros de modelos",
                                    style={
                                        "margin": "4px 0 0",
                                        "fontSize": "11px",
                                        "color": "#9ca3af",
                                    },
                                ),
                            ],
                        ),

                        # Segundo KPI
                        html.Div(
                            style={**KPI_CARD_STYLE, "flex": "1 1 180px"},
                            children=[
                                html.P(
                                    "Países",
                                    style={
                                        "margin": "0 0 4px",
                                        "fontSize": "12px",
                                        "textTransform": "uppercase",
                                        "letterSpacing": "0.12em",
                                        "color": "#9ca3af",
                                        "fontWeight": "600",
                                    },
                                ),
                                html.H2(
                                    id="kpi-countries",
                                    style={
                                        "margin": "0",
                                        "fontSize": "30px",
                                        "color": "#111827",
                                    },
                                ),
                                html.P(
                                    "Países con modelos registrados",
                                    style={
                                        "margin": "4px 0 0",
                                        "fontSize": "11px",
                                        "color": "#9ca3af",
                                    },
                                ),
                            ],
                        ),

                        # Tercer KPI
                        html.Div(
                            style={**KPI_CARD_STYLE, "flex": "1 1 180px"},
                            children=[
                                html.P(
                                    "Contaminantes",
                                    style={
                                        "margin": "0 0 4px",
                                        "fontSize": "12px",
                                        "textTransform": "uppercase",
                                        "letterSpacing": "0.12em",
                                        "color": "#9ca3af",
                                        "fontWeight": "600",
                                    },
                                ),
                                html.H2(
                                    id="kpi-pollutants",
                                    style={
                                        "margin": "0",
                                        "fontSize": "30px",
                                        "color": "#111827",
                                    },
                                ),
                                html.P(
                                    "Tipos de contaminantes modelizados",
                                    style={
                                        "margin": "4px 0 0",
                                        "fontSize": "11px",
                                        "color": "#9ca3af",
                                    },
                                ),
                            ],
                        ),
                    ],
                ),

                # =====================================
                # TABS PRINCIPALES
                # =====================================
                dcc.Tabs(
                    id="tabs-main",
                    value="tab-overview",
                    colors={
                        "border": "#e5e7eb",
                        "primary": "#0ea5e9",
                        "background": "transparent",
                    },
                    children=[

                        # ================================
                        # TAB 1 — ANÁLISIS DESCRIPTIVO
                        # ================================
                        dcc.Tab(
                            label="Análisis descriptivo",
                            value="tab-overview",
                            style={"padding": "10px 16px", "fontWeight": "500"},
                            selected_style={
                                "padding": "10px 16px",
                                "fontWeight": "600",
                                "borderBottom": "3px solid #0ea5e9",
                                "background": "rgba(255,255,255,0.7)",
                            },
                            children=[

                                # -----------------------------
                                # FILA 1 — MAPA + RANKING
                                # -----------------------------
                                html.Div(
                                    style={
                                        "display": "flex",
                                        "gap": "16px",
                                        "flexWrap": "wrap",
                                        "marginTop": "18px",
                                        "marginBottom": "18px",
                                    },
                                    children=[
                                        # MAPA
                                        html.Div(
                                            style={**CARD_STYLE, "flex": "1 1 48%"},
                                            children=[
                                                dcc.Loading(
                                                    type="circle",
                                                    children=[
                                                        dcc.Graph(
                                                            id="fig-map",
                                                            style={"height": "420px"},
                                                            config=GRAPH_CONFIG,
                                                        )
                                                    ],
                                                )
                                            ],
                                        ),

                                        # RANKING
                                        html.Div(
                                            style={
                                                **CARD_STYLE,
                                                "flex": "1 1 48%",
                                                "maxHeight": "440px",
                                                "overflowY": "auto",
                                            },
                                            children=[
                                                dcc.Loading(
                                                    type="circle",
                                                    children=[
                                                        dcc.Graph(
                                                            id="fig-ranking",
                                                            style={"height": "420px"},
                                                            config=GRAPH_CONFIG,
                                                        )
                                                    ],
                                                )
                                            ],
                                        ),
                                    ],
                                ),

                                # -----------------------------
                                # FILA 2 — EVOLUCIÓN TEMPORAL
                                # -----------------------------
                                html.Div(
                                    style={
                                        **CARD_STYLE,
                                        "flex": "1 1 100%",
                                        "marginBottom": "18px",
                                    },
                                    children=[
                                        dcc.Loading(
                                            type="circle",
                                            children=[
                                                dcc.Graph(
                                                    id="fig-trend",
                                                    style={"height": "380px"},
                                                    config=GRAPH_CONFIG,
                                                )
                                            ],
                                        )
                                    ],
                                ),

                                # -----------------------------
                                # FILA 3 — PROCESOS DE AGREGACIÓN
                                # -----------------------------
                                html.Div(
                                    style={
                                        **CARD_STYLE,
                                        "flex": "1 1 100%",
                                        "marginBottom": "18px",
                                    },
                                    children=[
                                        dcc.Loading(
                                            type="circle",
                                            children=[
                                                dcc.Graph(
                                                    id="fig-process",
                                                    style={"height": "420px"},
                                                    config=GRAPH_CONFIG,
                                                )
                                            ],
                                        )
                                    ],
                                ),
                            ],
                        ),

                        # ================================
                        # TAB 2 — MODELO DE SEGMENTACIÓN
                        # ================================
                        dcc.Tab(
                            label="Modelo de segmentación",
                            value="tab-model",
                            style={"padding": "10px 16px", "fontWeight": "500"},
                            selected_style={
                                "padding": "10px 16px",
                                "fontWeight": "600",
                                "borderBottom": "3px solid #0ea5e9",
                                "background": "rgba(255,255,255,0.7)",
                            },
                            children=[
                                html.Div(
                                    style={"marginTop": "18px"},
                                    children=[

                                        # Config segmentación
                                        html.Div(
                                            style={**CARD_STYLE, "marginBottom": "16px"},
                                            children=[
                                                html.H3(
                                                    "Modelo de segmentación por intensidad de modelización",
                                                    style={
                                                        "marginTop": "0",
                                                        "marginBottom": "8px",
                                                        "fontSize": "18px",
                                                        "color": "#111827",
                                                    },
                                                ),
                                                html.P(
                                                    "Se calcula un score por país combinando número de modelos y "
                                                    "diversidad de contaminantes. Luego se agrupan en k segmentos.",
                                                    style={
                                                        "fontSize": "13px",
                                                        "color": "#4b5563",
                                                        "marginBottom": "10px",
                                                    },
                                                ),

                                                html.Label(
                                                    "Nº de segmentos (k)",
                                                    style={
                                                        "fontWeight": "600",
                                                        "fontSize": "13px",
                                                        "color": "#6b7280",
                                                    },
                                                ),
                                                dcc.Slider(
                                                    id="sl-k",
                                                    min=2,
                                                    max=6,
                                                    step=1,
                                                    value=3,
                                                    marks={k: str(k) for k in range(2, 7)},
                                                ),
                                            ],
                                        ),

                                        # Gráfico de clusters
                                        html.Div(
                                            style={**CARD_STYLE, "marginBottom": "16px"},
                                            children=[
                                                dcc.Loading(
                                                    type="circle",
                                                    children=[
                                                        dcc.Graph(
                                                            id="fig-cluster",
                                                            style={"height": "420px"},
                                                            config=GRAPH_CONFIG,
                                                        )
                                                    ],
                                                )
                                            ],
                                        ),

                                        # Explicación de los clústers
                                        html.Div(
                                            style={**CARD_STYLE},
                                            children=[html.Div(id="txt-k-explanation")],
                                        ),
                                    ],
                                )
                            ],
                        ),

                        # ======================================
                        # TAB 3 — TREEMAP: COMPOSICIÓN DE MODELOS
                        # ======================================
                        dcc.Tab(
                            label="Composición de modelos",
                            value="tab-tree",
                            style={"padding": "10px 16px", "fontWeight": "500"},
                            selected_style={
                                "padding": "10px 16px",
                                "fontWeight": "600",
                                "borderBottom": "3px solid #0ea5e9",
                                "background": "rgba(255,255,255,0.7)",
                            },
                            children=[
                                html.Div(
                                    style={**CARD_STYLE, "marginTop": "18px"},
                                    children=[
                                        html.H3(
                                            "Mapa de árbol de contaminantes y países",
                                            style={
                                                "marginTop": "0",
                                                "marginBottom": "8px",
                                                "fontSize": "18px",
                                                "color": "#111827",
                                            },
                                        ),
                                        html.P(
                                            "El treemap muestra cómo se reparte el número de modelos entre "
                                            "los distintos contaminantes y países declarantes.",
                                            style={
                                                "fontSize": "13px",
                                                "color": "#4b5563",
                                                "marginBottom": "10px",
                                            },
                                        ),
                                        dcc.Loading(
                                            type="circle",
                                            children=[
                                                dcc.Graph(
                                                    id="fig-treemap",
                                                    style={"height": "520px"},
                                                    config=GRAPH_CONFIG,
                                                )
                                            ],
                                        ),
                                    ],
                                )
                            ],
                        ),

                        # ================================
                        # TAB 4 — METODOLOGÍA
                        # ================================
                        dcc.Tab(
                            label="Metodología",
                            value="tab-method",
                            style={"padding": "10px 16px", "fontWeight": "500"},
                            selected_style={
                                "padding": "10px 16px",
                                "fontWeight": "600",
                                "borderBottom": "3px solid #0ea5e9",
                                "background": "rgba(255,255,255,0.7)",
                            },
                            children=[
                                html.Div(
                                    style={**CARD_STYLE, "marginTop": "18px"},
                                    children=[
                                        html.H3(
                                            "Cómo interpretar este dashboard",
                                            style={
                                                "marginTop": "0",
                                                "marginBottom": "8px",
                                                "fontSize": "18px",
                                                "color": "#111827",
                                            },
                                        ),
                                        dcc.Markdown(
                                            """
- **Mapa:** visualiza el volumen relativo de modelos reportados por país.
- **Ranking:** ordena los países por número de modelos.
- **Evolución temporal:** muestra si aumenta, se mantiene o cae la modelización.
- **Procesos:** compara tipos de proceso más utilizados en los países más activos.
- **Segmentación:** k-means simplificado basado en score de intensidad.
- **Treemap:** composición contaminante–país del total de modelos declarados.

Datos procedentes del repositorio de *EEA Air Quality Models*.
                                            """,
                                            style={"fontSize": "13px", "color": "#4b5563"},
                                        ),
                                    ],
                                )
                            ],
                        ),
                    ],
                ),

                # FOOTER
                html.Div(
                    style={
                        "marginTop": "24px",
                        "fontSize": "11px",
                        "color": "#6b7280",
                        "textAlign": "right",
                    },
                    children=[
                        html.Span(
                            "Fuente de datos: EEA Air Quality Models · Dashboard académico."
                        )
                    ],
                ),
            ],
        )
    ],
)
# ============================================================
# 5. CALLBACKS
# ============================================================

@app.callback(
    [
        Output("kpi-models", "children"),
        Output("kpi-countries", "children"),
        Output("kpi-pollutants", "children"),
        Output("fig-map", "figure"),
        Output("fig-ranking", "figure"),
        Output("fig-trend", "figure"),
        Output("fig-process", "figure"),
        Output("fig-cluster", "figure"),
        Output("fig-treemap", "figure"),
        Output("txt-k-explanation", "children"),
    ],
    [
        Input("dd-pol", "value"),
        Input("sl-year", "value"),
        Input("dd-country", "value"),
        Input("sl-k", "value"),
    ],
)
def update_dashboard(pol_list, year_range, country, k):

    empty_fig = style_fig(go.Figure(), "Sin datos")
    empty_explanation = [
        html.P(
            "Ajusta los filtros y selecciona un valor de k para ver la segmentación.",
            style={"fontSize": "13px", "color": "#6b7280", "margin": "0"},
        )
    ]

    if not pol_list or year_range is None or k is None:
        return (
            "0", "0", "0",
            empty_fig, empty_fig, empty_fig, empty_fig, empty_fig, empty_fig,
            empty_explanation
        )

    y0, y1 = int(year_range[0]), int(year_range[1])
    d = data[
        (data["Air Pollutant"].isin(pol_list))
        & (data["Year"].between(y0, y1))
    ].copy()

    if country != "Todos los países":
        d = d[d["Country"] == country]

    # =======================
    # KPIs
    # =======================
    n_models = len(d)
    n_countries = d["Country"].nunique()
    n_polls = d["Air Pollutant"].nunique()

    # =======================
    # MAPA
    # =======================
    geo = d.groupby("Country").size().reset_index(name="Model Count")

    if geo.empty:
        fig_map = style_fig(go.Figure(), "Sin datos para mapa")
    else:
        fig_map = px.choropleth(
            geo,
            locations="Country",
            locationmode="country names",
            color="Model Count",
            color_continuous_scale=px.colors.sequential.YlGnBu,
            scope="europe",
        )
        fig_map = style_fig(fig_map, "Distribución europea de modelos")
        fig_map.update_layout(coloraxis_colorbar=dict(title="Modelos"))
        fig_map.update_traces(
            hovertemplate="<b>%{location}</b><br>Modelos: %{z}<extra></extra>"
        )

    # =======================
    # RANKING
    # =======================
    rank = (
        d.groupby("Country")
        .size()
        .reset_index(name="Model Count")
        .sort_values("Model Count", ascending=False)
        .head(20)
    )

    if rank.empty:
        fig_rank = style_fig(go.Figure(), "Sin datos para ranking")
    else:
        fig_rank = px.bar(
            rank,
            x="Model Count",
            y="Country",
            orientation="h",
        )
        fig_rank.update_layout(yaxis={"categoryorder": "total ascending"})
        fig_rank = style_fig(fig_rank, "Ranking de países por número de modelos")
        fig_rank.update_traces(
            hovertemplate="<b>%{y}</b><br>Modelos: %{x}<extra></extra>"
        )

    # =======================
    # EVOLUCIÓN TEMPORAL
    # =======================
    trend = (
        d.groupby(["Year", "Air Pollutant"])
        .size()
        .reset_index(name="Model Count")
    )

    if trend.empty:
        fig_trend = style_fig(go.Figure(), "Sin datos para evolución")
    else:
        fig_trend = px.line(
            trend,
            x="Year",
            y="Model Count",
            color="Air Pollutant",
            markers=True,
        )
        fig_trend.update_layout(
            xaxis=dict(dtick=max(1, (y1 - y0) // 10 or 1)),
            hovermode="x unified",
        )
        fig_trend = style_fig(fig_trend, "Evolución del número de modelos por año")
        fig_trend.update_traces(
            hovertemplate="<b>Año %{x}</b><br>Modelos: %{y}<extra></extra>"
        )

    # =======================
    # PROCESOS
    # =======================
    if "Data Aggregation Process" in d.columns:
        proc = (
            d.groupby(["Country", "Data Aggregation Process"])
            .size()
            .reset_index(name="Count")
        )

        if proc.empty:
            fig_proc = style_fig(go.Figure(), "Sin datos de procesos")
        else:
            top_countries = (
                proc.groupby("Country")["Count"]
                .sum()
                .sort_values(ascending=False)
                .head(10)
                .index
            )
            proc = proc[proc["Country"].isin(top_countries)]

            process_totals = (
                proc.groupby("Data Aggregation Process")["Count"]
                .sum()
                .sort_values(ascending=False)
            )

            top_processes = process_totals.head(5).index

            proc["ProcessGroup"] = proc["Data Aggregation Process"].where(
                proc["Data Aggregation Process"].isin(top_processes),
                "Otros procesos",
            )

            proc["ProcessLabel"] = proc["ProcessGroup"].apply(
                lambda s: "<br>".join(textwrap.wrap(str(s), width=18))
            )

            proc_plot = (
                proc.groupby(["Country", "ProcessLabel"])["Count"]
                .sum()
                .reset_index()
            )

            fig_proc = px.bar(
                proc_plot,
                x="Count",
                y="Country",
                color="ProcessLabel",
                barmode="stack",
            )
            fig_proc = style_fig(
                fig_proc,
                "Procesos de agregación por país (Top 10)",
            )
            fig_proc.update_layout(
                xaxis_title="Número de modelos",
                yaxis_title="País",
                yaxis={"categoryorder": "total ascending"},
                legend_title="Proceso",
                margin=dict(l=80, r=230, t=70, b=40),
            )
            fig_proc.update_traces(
                hovertemplate="<b>%{y}</b><br>Proceso: %{legendgroup}<br>Modelos: %{x}<extra></extra>"
            )
    else:
        fig_proc = style_fig(go.Figure(), "Columna no encontrada")

    # =======================
    # TREEMAP
    # =======================
    tm = d[["Air Pollutant", "Country"]].dropna()

    if tm.empty:
        fig_treemap = style_fig(go.Figure(), "Sin datos para treemap")
    else:
        tm_group = (
            tm.groupby(["Air Pollutant", "Country"])
            .size()
            .reset_index(name="Count")
        )

        fig_treemap = px.treemap(
            tm_group,
            path=["Air Pollutant", "Country"],
            values="Count",
            color="Air Pollutant",
            color_discrete_sequence=px.colors.qualitative.Set3,
        )
        fig_treemap = style_fig(
            fig_treemap,
            "Composición de modelos por contaminante y país",
        )

    # =======================
    # SEGMENTACIÓN DE PAÍSES
    # =======================
    seg = (
        d.groupby("Country")
        .agg(
            Model_Count=("Country", "size"),
            Pollutant_Count=("Air Pollutant", "nunique"),
        )
        .reset_index()
    )

    if seg.empty or seg["Country"].nunique() < 2:
        fig_cluster = style_fig(go.Figure(), "No hay suficientes datos")
        explanation_children = empty_explanation

    elif seg["Country"].nunique() < k:
        fig_cluster = style_fig(go.Figure(), "No hay suficientes países para ese k")
        explanation_children = empty_explanation

    else:
        seg["Model_Count_norm"] = seg["Model_Count"] / seg["Model_Count"].max()
        seg["Pollutant_Count_norm"] = seg["Pollutant_Count"] / seg["Pollutant_Count"].max()
        seg["Score"] = 0.7 * seg["Model_Count_norm"] + 0.3 * seg["Pollutant_Count_norm"]

        labels = [f"Segmento {i+1}" for i in range(k)]
        seg["Segment"] = pd.qcut(
            seg["Score"],
            q=k,
            labels=labels,
            duplicates="drop",
        )

        cats = list(seg["Segment"].cat.categories)
        counts = seg["Segment"].value_counts().reindex(cats, fill_value=0)
        total_countries = counts.sum()

        fig_cluster = px.choropleth(
            seg,
            locations="Country",
            locationmode="country names",
            color="Segment",
            scope="europe",
            color_discrete_sequence=px.colors.qualitative.Set3,
        )
        fig_cluster = style_fig(
            fig_cluster,
            f"Segmentación de países (k = {len(cats)})",
        )
        fig_cluster.update_traces(
            hovertemplate="<b>%{location}</b><br>Segmento: %{z}<extra></extra>"
        )

        items = []
        for i, label in enumerate(cats, start=1):
            n_in_segment = int(counts[label])
            pct = round(100 * n_in_segment / total_countries, 1) if total_countries else 0

            if i == 1:
                desc = "baja intensidad: pocos modelos y poca diversidad."
            elif i == len(cats):
                desc = "alta intensidad: muchos modelos y alta diversidad."
            else:
                desc = "intensidad intermedia."

            items.append(
                html.Li(
                    f"{label}: {n_in_segment} países (~{pct}%) — {desc}",
                    style={"fontSize": "13px", "color": "#4b5563", "marginBottom": "4px"},
                )
            )

        explanation_children = [
            html.H4(
                "Interpretación de segmentos",
                style={
                    "marginTop": "0",
                    "marginBottom": "6px",
                    "fontSize": "16px",
                    "color": "#111827",
                },
            ),
            html.Ul(items),
        ]

    return (
        format_int(n_models),
        format_int(n_countries),
        format_int(n_polls),
        fig_map,
        fig_rank,
        fig_trend,
        fig_proc,
        fig_cluster,
        fig_treemap,
        explanation_children,
    )

# ============================================================
# 6. EJECUCIÓN DEL SERVIDOR (RENDER)
# ============================================================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))

    app.run_server(host="0.0.0.0", port=port, debug=False)

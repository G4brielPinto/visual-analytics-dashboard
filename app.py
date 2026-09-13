import os
import re
import json
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
import dash
from dash import dcc, html, ctx
from dash.dependencies import Input, Output
import plotly.io as pio
pio.templates.default = "plotly_dark"
# === Add at the top ===
from dash.dependencies import ALL, State

# === CONFIGURATION ===
BASE_DIR = os.environ.get("VAD_DATA_DIR", os.path.join(os.path.dirname(__file__), "data"))
CATEGORIES = ['Employment', 'Population', 'Wages']

# === UTILITY FUNCTIONS ===
def extract_year(filename):
    match = re.search(r'(\d{4})', filename)
    return match.group(1) if match else "UnknownYear"

def load_data(base_dir, categories):
    data_dict = {}
    feature_dict = {}
    for cat in categories:
        path = os.path.join(base_dir, f"CrimeX{cat}")
        if not os.path.exists(path): continue
        data_dict[cat] = {}
        feature_set = set()
        for file in os.listdir(path):
            if not file.endswith(".csv"): continue
            year = extract_year(file)
            df = pd.read_csv(os.path.join(path, file))
            for col in df.columns:
                if col not in ['Lat', 'Long', 'Crime Count'] and not col.startswith("City"):
                    df[col] = pd.to_numeric(df[col], errors='coerce')
            df["Crime Count"] = pd.to_numeric(df["Crime Count"], errors='coerce')
            data_dict[cat][year] = df
            numeric = df.select_dtypes(include='number').columns
            features = [col for col in numeric if col not in {'Lat', 'Long', 'Crime Count'}]
            feature_set.update(features)
        feature_dict[cat] = sorted(feature_set)
    return data_dict, feature_dict

# === LOAD DATA ===
data_by_category_and_year, all_features_by_category = load_data(BASE_DIR, CATEGORIES)

# === DASH INITIALIZATION ===
app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.CYBORG],  # or DARKLY, SLATE, etc.
    suppress_callback_exceptions=True
)
app.title = "UK Crime Data Explorer"

# Extrair categorias e anos disponíveis
available_categories = list(data_by_category_and_year.keys())
available_years = sorted({year for cat in data_by_category_and_year.values() for year in cat.keys()})

# === LAYOUT ===
app.layout = dbc.Container([
    dbc.Row([
        dbc.Col(html.H1("UK Crime Dashboard", className="text-center mb-4"), width=12)
    ]),

    dbc.Row([
        dbc.Col([
            dcc.Dropdown(
                id='category-selector',
                options=[{"label": cat, "value": cat} for cat in CATEGORIES],
                value=CATEGORIES[0],
                style={
                    "color": "black",
                    "minWidth": "200px",  # helps with responsiveness
                    "backgroundColor": "#121212",  # improves readability in dark themes
                },
                className="mb-3"
            ),
            html.Div([
                dbc.ButtonGroup(
                    id="year-selector-group",
                    children=[],
                    size="md",
                    className="mb-2",
                    style={"flexWrap": "wrap", "justifyContent": "center", "width": "100%", "gap": "10px"}
                )
            ]),
            dcc.Store(id="selected-year", data=None)  # 🔁 store for selected year
        ], width=12, className="d-flex flex-column align-items-center")
    ], className="mb-4"),


    dbc.Row([
        dbc.Col([
            html.H3("Crime Count vs Socio-economic Feature", className="text-white"),

            html.Div([
                dcc.RadioItems(
                    id='scatter-metric',
                    options=[
                        {'label': 'Crime Count', 'value': 'abs'},
                        {'label': 'Ratio (Crimes / Feature)',  'value': 'ratio'},
                    ],
                    value='abs',
                    labelStyle={'display': 'inline-block', 'marginRight': '20px'},
                    inputStyle={'marginRight': '5px'},
                    className="text-white mb-3"
                )
            ], style={'textAlign': 'center', 'marginBottom': '20px'}),

            dcc.Graph(id='scatter-plot')
        ])
    ], className="mb-5"),

    dbc.Row([
        dbc.Col([
            html.H3("Multifeature Comparison (Parallel Coordinates)", className="text-white"),
            dcc.Graph(id='parallel-coords-plot')
        ])
    ], className="mb-5"),

    html.H3("Crime Trend Over Time", className="text-white"),

    html.Div([
        dcc.RadioItems(
            id='trend-value-type',
            options=[
                {'label': 'Crime Count', 'value': 'Crime Count'},
                {'label': 'Category', 'value': 'Socioeconomic'}
            ],
            value='Crime Count',
            labelStyle={'display': 'inline-block', 'marginRight': '20px'},
            inputStyle={'marginRight': '5px'},
        )
    ], style={'textAlign': 'center', 'marginBottom': '20px'}),

    dcc.Graph(id='crime-trend-plot'),

    html.H3("Top & Bottom 10 Cities by", className="text-white"),

    html.Div([
        dcc.RadioItems(
            id='top-bar-mode',
            options=[
                {'label': 'Crime Count',          'value': 'crime_abs'},
                {'label': 'Socioeconomical Feature','value': 'feature_abs'},
                {'label': 'Ratio: Crimes / Feature',        'value': 'ratio'},
            ],
            value='crime_abs',
            labelStyle={'display':'block', 'marginBottom':'8px'},
            inputStyle={'marginRight':'8px'},
            className="text-white mb-4"
        )
    ], style={'textAlign':'center'}),



    dcc.Graph(id='top-cities-bar'),


    html.H3("Rose Diagram", className="text-white"),

    html.Div([
        dcc.RadioItems(
            id='rose-mode',
            options=[
                {'label': 'Crime Count',           'value': 'crime_abs'},
                {'label': 'Socioeconomical Feature','value': 'feature_abs'},
                {'label': 'Ratio: Crimes / Feature',         'value': 'ratio'},
            ],
            value='crime_abs',
            labelStyle={'display':'block','marginBottom':'8px'},
            inputStyle={'marginRight':'8px'},
            className="text-white mb-4"
        )
    ], style={'textAlign':'center'}),

    dcc.Graph(id='rose-diagram'),


    html.H3("Interactive maps", className="text-white"),

    dbc.Row([
        dbc.Col([
            dcc.Tabs(
                id="map-tabs",
                value="heat",  # podes manter 'heat' como pre-selecionado
                children=[
                    dcc.Tab(label="Heatmap",   value="heat",    className="custom-tab", selected_className="custom-tab--selected", style={"color":"white","backgroundColor":"#121212"}),
                    dcc.Tab(label="Layered",   value="layered",  className="custom-tab", selected_className="custom-tab--selected", style={"color":"white","backgroundColor":"#121212"}),
                    dcc.Tab(label="Dorling",   value="dorling",  className="custom-tab", selected_className="custom-tab--selected", style={"color":"white","backgroundColor":"#121212"}),
                ]
            ),
            html.Div(id="tabs-content", className="mt-4")
        ])
    ]),

], fluid=True, style={"backgroundColor": "#121212", "padding": "30px"})

# === CALLBACKS ===

@app.callback(
    [Output('year-selector-group', 'children'),
     Output('selected-year', 'data')],
    [Input('category-selector', 'value'),
     Input({'type': 'year-btn', 'index': ALL}, 'n_clicks')],
    [State({'type': 'year-btn', 'index': ALL}, 'id'),
     State('selected-year', 'data')]
)
def manage_year_buttons(category, n_clicks_list, ids, current_selected_year):
    years = sorted(data_by_category_and_year[category].keys())

    # Generate year buttons
    buttons = []
    for year in years:
        is_selected = str(year) == str(current_selected_year)
        buttons.append(
            dbc.Button(
                str(year),
                id={'type': 'year-btn', 'index': str(year)},
                n_clicks=0,
                color="primary" if is_selected else "secondary",
                outline=not is_selected,
                className="me-2 mb-2"
            )
        )

    # Detect button click
    if ctx.triggered_id and isinstance(ctx.triggered_id, dict) and ctx.triggered_id.get('type') == 'year-btn':
        new_selected_year = ctx.triggered_id['index']
    else:
        new_selected_year = years[0] if years else None

    return buttons, new_selected_year

@app.callback(
    Output('scatter-plot', 'figure'),
    [
        Input('category-selector', 'value'),
        Input('selected-year', 'data'),
        Input('scatter-metric', 'value')
    ]
)
def update_scatter(category, year, metric):
    if category is None or year is None:
        return go.Figure()
    df = data_by_category_and_year.get(category, {}).get(year)
    if df is None or df.empty:
        return go.Figure()

    feature = all_features_by_category[category][0]
    city_col = next((c for c in df.columns if c.startswith("City")), None)

    if metric == 'abs':
        y_col = 'Crime Count'
        title_suffix = "Crime Count"
    else:
        ratio = df['Crime Count'] / df[feature].replace({0: np.nan})
        df = df.assign(Ratio=ratio)
        y_col = 'Ratio'
        title_suffix = f"Ratio Crimes/{feature}"

    # Paleta vibrante: verde-limão, amarelo, ciano, laranja, vermelho
    bright_colors = [
        "#00FF00", "#ADFF2F", "#FFFF00", "#00FFFF",
        "#FFA500", "#FF4500", "#FF0000"
    ]

    fig = px.scatter(
        df,
        x=feature,
        y=y_col,
        hover_name=city_col,
        title=f"{feature} vs {title_suffix} ({year})",
        trendline="ols",
        color=y_col,
        color_continuous_scale=bright_colors
    )
    fig.update_traces(marker=dict(size=10, opacity=0.85))
    fig.update_layout(
        template="plotly_dark",
        height=700,
        xaxis_title=feature,
        yaxis_title=title_suffix
    )
    return fig

@app.callback(
    Output("tabs-content", "children"),
    [Input("map-tabs", "value"),
     Input('category-selector', 'value'),
     Input('selected-year', 'data')]
)
def update_map(tab, category, year):
    if category is None or year is None:
        return go.Figure()  # or {} if you're okay with an empty dict

    if category not in data_by_category_and_year:
        return go.Figure()

    df = data_by_category_and_year[category].get(year)
    if df is None or df.empty:
        return go.Figure()

    elif tab == "heat":
        df_all = pd.concat([df.assign(Year=yr) for yr, df in data_by_category_and_year[category].items()])
        fig = px.density_mapbox(df_all, lat="Lat", lon="Long", z="Crime Count", radius=30,
                                animation_frame="Year", mapbox_style="carto-darkmatter", zoom=5,
                                center={"lat": df["Lat"].mean(), "lon": df["Long"].mean()},
                                color_continuous_scale="Hot")
        fig.update_layout(margin=dict(l=0, r=0, t=40, b=0), height=800)
        return dcc.Graph(figure=fig)

    elif tab == "layered":
        # Combine all years and add a Year column
        df_all = pd.concat([df.assign(Year=yr) for yr, df in data_by_category_and_year[category].items()])

        # Filter only for selected year
        df_current = df_all[df_all["Year"] == year]

        # Get min and max for the slider
        min_crime = float(df_current["Crime Count"].min())
        max_crime = float(df_current["Crime Count"].max())

        return html.Div([
            dcc.Graph(id="layered-map"),  # ✅ Map appears first
            html.Div([
                html.P("Filter Crime Count Range:", style={"marginTop": "20px"}),
                dcc.RangeSlider(
                    id="layered-slider",
                    min=min_crime,
                    max=max_crime,
                    step=1,
                    value=[min_crime, max_crime],
                    marks={int(v): str(int(v)) for v in np.linspace(min_crime, max_crime, 5)}
                )
            ]),
            html.Div(id="selected-data", style={"marginTop": "20px", "fontStyle": "italic"})
        ])

    elif tab == "dorling":
        # chama a tua função existente
        fig_dorling = update_dorling_map(category, year)
        # se update_dorling_map devolve um Figure:
        return dcc.Graph(figure=fig_dorling)

    else:
        return html.Div("Invalid tab selected.")

@app.callback(
    Output("layered-map", "figure"),
    [Input("layered-slider", "value"),
     Input("category-selector", "value"),
     Input("selected-year", "data")]
)
def update_layered_map(range_vals, category, year):
    if category is None or year is None:
        return go.Figure()  # or {} if you're okay with an empty dict

    if category not in data_by_category_and_year:
        return go.Figure()

    df = data_by_category_and_year[category].get(year)
    if df is None or df.empty:
        return go.Figure()

    df_filtered = df[(df["Crime Count"] >= range_vals[0]) & (df["Crime Count"] <= range_vals[1])]
    if df_filtered.empty: return {}
    city_col = next((col for col in df_filtered.columns if col.startswith("City")), None)
    fig = go.Figure([
        go.Densitymapbox(lat=df_filtered["Lat"], lon=df_filtered["Long"],
                         z=df_filtered["Crime Count"], radius=30, colorscale="Hot", name="Density", opacity=0.6),
        go.Scattermapbox(lat=df_filtered["Lat"], lon=df_filtered["Long"],
                         mode="markers", marker=dict(size=10, color=df_filtered["Crime Count"],
                         colorscale="Turbo", showscale=True), text=df_filtered[city_col], name="Points")
    ])
    fig.update_layout(mapbox_style="carto-darkmatter", mapbox_zoom=5,
                      mapbox_center={"lat": df_filtered["Lat"].mean(), "lon": df_filtered["Long"].mean()},
                      margin=dict(l=0, r=0, t=40, b=0), height=600)
    return fig

@app.callback(
    Output("selected-data", "children"),
    [Input("layered-map", "selectedData")]
)
def display_selected_data(selected_data):
    if not selected_data or "points" not in selected_data:
        return html.Div("🧐 No points selected. Use Box or Lasso Select on the map.")

    points = selected_data["points"]
    if not points:
        return html.Div("😕 No cities found in selection.")

    selected_cities = [pt.get("text", "Unknown City") for pt in points]
    return html.Div([
        html.P("✅ Selected Cities:"),
        html.Ul([html.Li(city) for city in selected_cities])
    ])


@app.callback(
    Output('parallel-coords-plot', 'figure'),
    [Input('category-selector', 'value'),
     Input('selected-year', 'data')]
)
def update_parallel_coords(category, year):
    if category is None or year is None:
        return go.Figure()

    try:
        year_int = int(str(year).strip())
    except (ValueError, TypeError):
        return go.Figure()

    dfs = []
    for cat, year_dict in data_by_category_and_year.items():
        df_cat = year_dict.get(year)
        if df_cat is not None:
            dfs.append(df_cat)

    if not dfs:
        return go.Figure()

    from functools import reduce
    df_merged = reduce(lambda left, right: pd.merge(left, right, on=[col for col in left.columns if col.startswith('City')][0], how='outer'), dfs)
    df_merged = df_merged.dropna()

    feature_cols = []
    for cat in all_features_by_category:
        feature_cols += all_features_by_category[cat]

    feature_cols = list(dict.fromkeys(feature_cols))  # remove duplicatas

    if year_int == 2024:
        feature_cols = [col for col in feature_cols if col != "Population"]

    feature_cols = feature_cols[:4]

    city_col = next((col for col in df_merged.columns if col.startswith("City")), None)
    if city_col is None or 'Crime Count' not in df_merged.columns or len(feature_cols) == 0:
        return go.Figure()

    df_filtered = df_merged[[city_col] + feature_cols + ['Crime Count']].dropna()

    normalized_df = df_filtered.copy()
    for col in feature_cols + ['Crime Count']:
        normalized_df[col] = (df_filtered[col] - df_filtered[col].min()) / (df_filtered[col].max() - df_filtered[col].min())

    city_list = df_filtered[city_col].unique().tolist()
    city_map = {city: i for i, city in enumerate(city_list)}
    normalized_df['CityEncoded'] = df_filtered[city_col].map(city_map)

    dimensions = [
        dict(label="City", values=normalized_df['CityEncoded'],
             tickvals=list(city_map.values()),
             ticktext=list(city_map.keys()))
    ] + [
        dict(label=col, values=normalized_df[col]) for col in feature_cols + ['Crime Count']
    ]

    fig = go.Figure(data=go.Parcoords(
        line=dict(color=normalized_df['Crime Count'], colorscale='Tealrose', showscale=True),
        dimensions=dimensions
    ))

    fig.update_layout(title=f"Multifeature Comparison ({year})", height=900)
    return fig





@app.callback(
    Output('crime-trend-plot', 'figure'),
    [Input('category-selector', 'value'),
     Input('trend-value-type', 'value')]  # novo input para escolher entre crime ou socioeconómica
)
def update_trend_line(category, value_type):
    if category is None:
        return go.Figure()

    all_years_data = []
    for year, df in data_by_category_and_year[category].items():
        city_col = next((col for col in df.columns if col.startswith("City")), None)
        if city_col:
            if value_type == "Crime Count":
                grouped = df.groupby(city_col)["Crime Count"].sum().reset_index()
            else:
                # procura pela primeira variável socioeconómica válida associada à categoria
                features = all_features_by_category.get(category, [])
                socio_feature = features[0] if features else None
                if socio_feature not in df.columns:
                    continue
                grouped = df.groupby(city_col)[socio_feature].mean().reset_index()
                grouped.rename(columns={socio_feature: "Value"}, inplace=True)

            grouped["Year"] = year
            all_years_data.append(grouped)

    if not all_years_data:
        return go.Figure()

    df_all = pd.concat(all_years_data)

    y_column = "Crime Count" if value_type == "Crime Count" else "Value"
    title = f"📈 Crime Trend by City" if value_type == "Crime Count" else f"📈 Socioeconomic Trend by City ({category})"

    fig = px.line(df_all, x="Year", y=y_column, color=city_col,
                  title=title, markers=True)
    fig.update_layout(height=850)
    return fig



@app.callback(
    Output('top-cities-bar', 'figure'),
    [
        Input('category-selector', 'value'),
        Input('selected-year',   'data'),
        Input('top-bar-mode',    'value')
    ]
)
def update_top_cities_bar(category, year, mode):
    # Guard clauses
    if not category or not year:
        return go.Figure()

    df = data_by_category_and_year[category].get(year)
    if df is None or df.empty:
        return go.Figure()

    city_col = next(c for c in df.columns if c.startswith("City"))
    feature  = all_features_by_category[category][0]

    # Decidir qual a métrica
    if mode == 'crime_abs':
        df2 = df.assign(Value = df['Crime Count'])
        y_label = 'Crime Count'
    elif mode == 'feature_abs':
        df2 = df.assign(Value = df[feature])
        y_label = feature
    else:  # ratio
        ratio = df['Crime Count'] / df[feature].replace({0: np.nan})
        df2   = df.assign(Value=ratio)
        y_label = f"Crimes per {feature}"

    # Agrupar e obter Top/Bottom 10
    grouped   = df2.groupby(city_col)['Value'].mean().reset_index()
    top10     = grouped.nlargest(10, 'Value').assign(Ranking='Top 10')
    bottom10  = grouped.nsmallest(10, 'Value').assign(Ranking='Bottom 10')
    combined  = pd.concat([bottom10, top10]).sort_values('Value', ascending=False)

    # Construir o gráfico
    fig = px.bar(
        combined,
        x='Value',
        y=city_col,
        color='Ranking',
        orientation='h',
        title=f"{y_label} — Top & Bottom 10 Cities ({year})",
        color_discrete_map={'Top 10':'crimson','Bottom 10':'steelblue'},
        labels={'Value': y_label, city_col:'City'}
    )
    fig.update_layout(
        template="plotly_dark",
        height=700,
        yaxis={'categoryorder':'total ascending'}
    )
    return fig


@app.callback(
    Output('rose-diagram', 'figure'),
    [
        Input('category-selector', 'value'),
        Input('selected-year', 'data'),
        Input('rose-mode', 'value')   # ⬅️ o novo input
    ]
)
def update_rose_diagram(category, year, mode):
    if not category or not year:
        return px.scatter(title="Selecione uma categoria e um ano.")

    df = data_by_category_and_year.get(category, {}).get(year)
    if df is None or df.empty:
        return px.scatter(title="Sem dados disponíveis para esta combinação.")

    city_col = next((c for c in df.columns if c.startswith("City")), "City")
    feature = all_features_by_category[category][0]

    # construir 'Value' corretamente conforme modo
    if mode == 'crime_abs':
        df2 = df.assign(Value = df['Crime Count'])
        title = f"Crime Count by City ({year})"
    elif mode == 'feature_abs':
        df2 = df.assign(Value = df[feature])
        title = f"{feature} by City ({year})"
    else:  # ratio
        ratio = df['Crime Count'] / df[feature].replace({0: np.nan})
        df2 = df.assign(Value = ratio)
        title = f"Ratio: Crimes per {feature} by City ({year})"

    grouped_df = df2.groupby(city_col, as_index=False)['Value'].sum()

    fig = px.bar_polar(
        grouped_df,
        r="Value",    # <-- SEMPRE 'Value' aqui
        theta=city_col,
        color="Value",  # <-- Também
        color_continuous_scale='Reds',
        title=title,
        template='plotly_dark'
    )

    fig.update_layout(
        polar=dict(
            radialaxis=dict(showticklabels=True, ticks=''),
            angularaxis=dict(direction="clockwise")
        ),
        height=800,
    )

    return fig




@app.callback(
    Output('dorling-map', 'figure'),
    [Input('category-selector', 'value'),
     Input('selected-year', 'data')]
)

def update_dorling_map(category, year):
    if category is None or year is None:
        return go.Figure()

    df = data_by_category_and_year[category].get(year)
    if df is None or df.empty:
        return go.Figure()

    city_col = next((c for c in df.columns if c.startswith("City")), None)
    grouped = df.groupby(city_col).agg({
        'Crime Count': 'sum',
        category: 'mean',   # <- Valor da categoria socioeconómica (ex: Employment)
        'Lat': 'mean',
        'Long': 'mean'
    }).reset_index()

    # Escala de tamanho dos círculos pelo número de crimes
    size_scale = 100 / grouped["Crime Count"].max()
    grouped["Size"] = grouped["Crime Count"] * size_scale

    fig = go.Figure(go.Scattermapbox(
        lat=grouped["Lat"],
        lon=grouped["Long"],
        mode='markers',
        marker=go.scattermapbox.Marker(
            size=grouped["Size"],
            color=grouped[category],  # <- A cor representa o valor da categoria
            colorscale='Viridis',
            sizemode='diameter',
            opacity=0.7,
            showscale=True,
            colorbar=dict(title=f'{category} Value')
        ),
        text=grouped[city_col] + "<br>" +
             "Crimes: " + grouped["Crime Count"].astype(int).astype(str) + "<br>" +
             f"{category}: " + grouped[category].round(2).astype(str),
        hoverinfo='text'
    ))

    fig.update_layout(
        mapbox_style="carto-darkmatter",
        mapbox_zoom=5,
        mapbox_center={"lat": grouped["Lat"].mean(), "lon": grouped["Long"].mean()},
        height=700,
        margin={"r":0,"t":40,"l":0,"b":0}
    )

    return fig

@app.callback(
    Output('dorling-title', 'children'),
    Input('category-selector', 'value'),
    Input('selected-year', 'data')
)
def update_dorling_title(category, year):
    if not category or not year:
        return "📍 Dorling Map"
    return f"📍 Dorling Map - {category} vs Crime Count ({year})"


# === RUN APP ===
if __name__ == '__main__':
    app.run(debug=True)

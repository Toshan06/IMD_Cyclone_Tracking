from pathlib import Path
import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# PAGE CONFIGURATION

st.set_page_config(
    page_title="IMD Cyclone Track Explorer",
    page_icon="",
    layout="wide"
)

st.title("IMD Historical Cyclone Track Explorer")
st.caption("Historical Cyclone Analysis | 1982–2025")

BASE_DIR = Path(__file__).resolve().parent.parent

FILE_PATH = BASE_DIR / "data" / "IMD_Standardized.xlsx"

st.markdown("""
<style>
/* Remove hover background change and any transform effects */
.stButton button:hover {
    background-color: transparent !important;
    transform: none !important;
    box-shadow: none !important;
}
</style>
""", unsafe_allow_html=True)

# LOAD DATA

@st.cache_data
def load_data():
    xl = pd.ExcelFile(FILE_PATH)
    data = {}

    for sheet in xl.sheet_names:
        df = pd.read_excel(
            FILE_PATH,
            sheet_name=sheet
        )
        df.columns = df.columns.astype(str).str.strip()

        # Fill serial numbers
        df["Serial Number of system during year"] = (
            df["Serial Number of system during year"].ffill()
        )

        # Convert numerical columns
        numeric_columns = [
            "Latitude (lat.)",
            "Longitude (lon.)",
            "Maximum Sustained Surface Wind (kt)",
            'Pressure Drop (hPa) [or "delta P"]',
            'CI No [or "T. No"]'
        ]

        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(
                    df[col],
                    errors="coerce"
                )

        # Parse dates
        df["Date"] = pd.to_datetime(
            df["Date (DD-MM-YYYY)"],
            dayfirst=True,
            errors="coerce"
        )

        # Format UTC time
        def format_time(value):
            if pd.isna(value):
                return "0000"
            try:
                return str(int(float(value))).zfill(4)
            except (ValueError, TypeError):
                return str(value).strip().zfill(4)

        df["Time_String"] = df["Time (UTC)"].apply(
            format_time
        )

        # Construct datetime
        df["Datetime"] = pd.to_datetime(
            df["Date"].dt.strftime("%Y-%m-%d")
            + " "
            + df["Time_String"].str[:2]
            + ":"
            + df["Time_String"].str[2:],
            errors="coerce"
        )

        # Cyclone ID
        df["Cyclone_ID"] = (
            df["Serial Number of system during year"]
            .astype("Int64")
            .astype(str)
        )

        # Retain valid geographical observations
        df = df.dropna(
            subset=[
                "Latitude (lat.)",
                "Longitude (lon.)",
                "Datetime"
            ]
        )

        df = df[
            df["Latitude (lat.)"].between(-90, 90)
            & df["Longitude (lon.)"].between(-180, 180)
        ]

        df = df[
            df["Cyclone_ID"] != "<NA>"
        ]

        data[str(sheet)] = df

    return data

data = load_data()

if not data:
    st.error("No worksheets were found in the Excel file.")
    st.stop()

# ==================================================
# SIDEBAR FILTERS
# ==================================================

st.sidebar.header("Dashboard Controls")

years = sorted(
    data.keys(),
    key=int
)

selected_year = st.sidebar.selectbox(
    "Select Year",
    years,
    index=len(years) - 1
)

year_data = data[selected_year].copy()

basins = (
    year_data["Basin of origin"]
    .dropna()
    .astype(str)
    .str.strip()
)

basins = sorted(basins.unique())

basin_options = ["All Basins"] + basins

selected_basin = st.sidebar.selectbox(
    "Select Basin",
    basin_options
)

# Filter according to selected basin
if selected_basin != "All Basins":

    year_data = year_data[
        year_data["Basin of origin"]
        .astype(str)
        .str.strip() == selected_basin
    ].copy()

# Cyclone IDs
cyclone_ids = sorted(
    year_data["Cyclone_ID"].unique(),
    key=lambda x: int(x)
)

# ==================================================
# CYCLONE NAME MAPPING
# ==================================================

cyclone_names = {}

for cid in cyclone_ids:
    names = (
        year_data.loc[
            year_data["Cyclone_ID"] == cid,
            "Name"
        ]
        .dropna()
        .astype(str)
        .str.strip()
    )

    names = names[
        ~names.str.lower().isin(
            ["", "nan", "none", "-", "n/a"]
        )
    ]

    if len(names) > 0:
        cyclone_names[cid] = names.iloc[0]
    else:
        cyclone_names[cid] = "Unnamed Cyclone"


name_counts = pd.Series(
    list(cyclone_names.values())
).value_counts()

cyclone_labels = {}
label_to_id = {}

for cid in cyclone_ids:
    name = cyclone_names[cid]
    if name_counts[name] > 1 or name == "Unnamed Cyclone":
        label = f"{name} (ID: {cid})"
    else:
        label = name
    cyclone_labels[cid] = label
    label_to_id[label] = cid

cyclone_options = ["All Cyclones"] + [
    cyclone_labels[cid]
    for cid in cyclone_ids
]

selected_cyclone = st.sidebar.selectbox(
    "Select Cyclone",
    cyclone_options
)

# ==================================================
# FILTER DATA
# ==================================================

if selected_cyclone == "All Cyclones":
    filtered_data = year_data.copy()

else:
    cyclone_number = label_to_id[selected_cyclone]
    filtered_data = year_data[
        year_data["Cyclone_ID"] == cyclone_number
    ].copy()

filtered_data = filtered_data.sort_values(
    "Datetime"
)

# ==================================================
# DASHBOARD STATISTICS
# ==================================================

total_cyclones = filtered_data["Cyclone_ID"].nunique()

max_wind = filtered_data[
    "Maximum Sustained Surface Wind (kt)"
].max()

max_wind = 0 if pd.isna(max_wind) else max_wind

if selected_cyclone == "All Cyclones":
    display_name = "Multiple"
else:
    cyclone_number = label_to_id[selected_cyclone]
    display_name = cyclone_names[cyclone_number]

col1, col2, col3, col4 = st.columns(
    [1, 1, 1.8, 1],
    gap="large"
)

col1.metric("Selected Year", selected_year)
col2.metric("Cyclones", total_cyclones)
col3.metric("Cyclone Name", display_name)
col4.metric("Maximum Wind Speed", f"{max_wind:g} kt")

st.divider()

# ==================================================
# COLOUR PALETTE
# ==================================================

colors = [
    "#636EFA",
    "#EF553B",
    "#00CC96",
    "#AB63FA",
    "#FFA15A",
    "#19D3F3",
    "#FF6692",
    "#B6E880",
    "#FF97FF",
    "#FECB52"
]

# ==================================================
# ANIMATED GEOGRAPHICAL MAP
# ==================================================

animation_data = filtered_data.dropna(
    subset=[
        "Datetime",
        "Latitude (lat.)",
        "Longitude (lon.)"
    ]
).copy()

animation_data = animation_data.sort_values("Datetime")

# Map and CI graph side by side
map_col, ci_col = st.columns(
    [1.5, 1],
    gap="large"
)

with map_col:
    st.markdown(
        "<h3 style='text-align: center;'>Cyclone Trajectory Map</h3>",
        unsafe_allow_html=True
    )
    if animation_data.empty:

        st.warning(
            "No valid geographical observations available."
        )
    else:
        timestamps = sorted(
            animation_data["Datetime"].unique()
        )
        cyclone_groups = {
            cid: group.sort_values("Datetime")
            for cid, group in animation_data.groupby(
                "Cyclone_ID",
                sort=False
            )
        }
        cyclone_order = list(cyclone_groups.keys())

        # --------------------------------------------------
        # INITIAL TRACES
        # --------------------------------------------------

        initial_traces = []

        for i, cid in enumerate(cyclone_order):
            group = cyclone_groups[cid]
            color = colors[i % len(colors)]
            name = cyclone_labels[cid]

            current = group[
                group["Datetime"] <= timestamps[0]
            ]
            if current.empty:

                lon_values = []
                lat_values = []
                marker_lon = []
                marker_lat = []
                hover_data = []
            else:

                lon_values = current["Longitude (lon.)"].tolist()
                lat_values = current["Latitude (lat.)"].tolist()
                latest = current.iloc[-1]
                marker_lon = [latest["Longitude (lon.)"]]
                marker_lat = [latest["Latitude (lat.)"]]
                hover_data = [[
                    str(latest["Datetime"]),
                    latest["Maximum Sustained Surface Wind (kt)"],
                    latest["Grade (text)"]
                ]]

            # Track line: one legend entry per cyclone
            initial_traces.append(
                go.Scattergeo(
                    lon=lon_values,
                    lat=lat_values,
                    mode="lines",
                    line=dict(
                        width=2.5,
                        color=color
                    ),
                    name=name,
                    legendgroup=str(cid),
                    showlegend=False,
                    hoverinfo="skip"
                )
            )

            # Moving marker: no duplicate legend entry
            initial_traces.append(
                go.Scattergeo(
                    lon=marker_lon,
                    lat=marker_lat,
                    mode="markers",
                    marker=dict(
                        size=11,
                        color=color,
                        line=dict(
                            width=1,
                            color="white"
                        )
                    ),
                    customdata=hover_data,
                    name=name,
                    legendgroup=str(cid),
                    showlegend=False,
                    hovertemplate=(
                        f"<b>{name}</b><br>"
                        "Latitude: %{lat:.2f}°<br>"
                        "Longitude: %{lon:.2f}°<br>"
                        "Date/Time: %{customdata[0]}<br>"
                        "Wind: %{customdata[1]} kt<br>"
                        "Grade: %{customdata[2]}"
                        "<extra></extra>"
                    )
                )
            )

        # --------------------------------------------------
        # ANIMATION FRAMES
        # --------------------------------------------------

        frames = []

        for frame_index, timestamp in enumerate(timestamps):
            frame_traces = []
            for i, cid in enumerate(cyclone_order):
                group = cyclone_groups[cid]
                # Only observations up to this frame's time
                current = group[
                    group["Datetime"] <= timestamp
                ]
                color = colors[i % len(colors)]
                name = cyclone_labels[cid]

                if current.empty:
                    lon_values = []
                    lat_values = []
                    marker_lon = []
                    marker_lat = []
                    hover_data = []

                else:
                    lon_values = current[
                        "Longitude (lon.)"
                    ].tolist()
                    lat_values = current[
                        "Latitude (lat.)"
                    ].tolist()
                    latest = current.iloc[-1]
                    marker_lon = [
                        latest["Longitude (lon.)"]
                    ]
                    marker_lat = [
                        latest["Latitude (lat.)"]
                    ]
                    hover_data = [[
                        str(latest["Datetime"]),
                        latest["Maximum Sustained Surface Wind (kt)"],
                        latest["Grade (text)"]
                    ]]

                frame_traces.append(
                    go.Scattergeo(
                        lon=lon_values,
                        lat=lat_values,
                        mode="lines",
                        line=dict(
                            width=2.5,
                            color=color
                        ),
                        name=name,
                        legendgroup=str(cid),
                        showlegend=False,
                        hoverinfo="skip"
                    )
                )

                frame_traces.append(
                    go.Scattergeo(
                        lon=marker_lon,
                        lat=marker_lat,
                        mode="markers",
                        marker=dict(
                            size=11,
                            color=color,
                            line=dict(
                                width=1,
                                color="white"
                            )
                        ),
                        customdata=hover_data,
                        name=name,
                        legendgroup=str(cid),
                        showlegend=False,
                        hovertemplate=(
                            f"<b>{name}</b><br>"
                            "Latitude: %{lat:.2f}°<br>"
                            "Longitude: %{lon:.2f}°<br>"
                            "Date/Time: %{customdata[0]}<br>"
                            "Wind: %{customdata[1]} kt<br>"
                            "Grade: %{customdata[2]}"
                            "<extra></extra>"
                        )
                    )
                )

            frames.append(
                go.Frame(
                    name=str(frame_index),
                    data=frame_traces,
                    traces=list(range(len(frame_traces))),
                )
            )

        # --------------------------------------------------
        # TIMELINE SLIDER
        # --------------------------------------------------

        slider_steps = []

        for i, timestamp in enumerate(timestamps):
            slider_steps.append(
                dict(
                    method="animate",
                    label=pd.Timestamp(timestamp).strftime(
                        "%d-%m %H:%M"
                    ),
                    args=[
                        [str(i)],
                        dict(
                            mode="immediate",
                            frame=dict(
                                duration=0,
                                redraw=True
                            ),
                            transition=dict(duration=0)
                        )
                    ]
                )
            )

        # --------------------------------------------------
        # FIGURE
        # --------------------------------------------------

        fig = go.Figure(
            data=initial_traces,
            frames=frames
        )

        # ==================================================
        # OFFICIAL INDIA BOUNDARY
        # ==================================================

        import geopandas as gpd

        india_gdf = gpd.read_file(
            BASE_DIR / "data" / "Outline_of_India" / "Outline_of_India.shp"
        ).to_crs("EPSG:4326")

        for geometry in india_gdf.geometry:
            if geometry is None:
                continue
            polygons = (
                list(geometry.geoms)
                if geometry.geom_type == "MultiPolygon"
                else [geometry]
            )

            for polygon in polygons:
                boundary_coords = list(polygon.exterior.coords)
                fig.add_trace(
                    go.Scattergeo(
                        lon=[point[0] for point in boundary_coords],
                        lat=[point[1] for point in boundary_coords],
                        mode="lines",
                        line=dict(
                            color="#7189C5",
                            width=2
                        ),
                        showlegend=False,
                        hoverinfo="skip"
                    )
                )

        # ==================================================
        # STATIC LEGEND TRACES
        # ==================================================

        for i, cid in enumerate(cyclone_order):

            fig.add_trace(
                go.Scattergeo(
                    lon=[None],
                    lat=[None],
                    mode="lines+markers",
                    name=cyclone_labels[cid],
                    line=dict(
                        width=2.5,
                        color=colors[i % len(colors)]
                    ),
                    marker=dict(
                        size=7,
                        color=colors[i % len(colors)]
                    ),
                    showlegend=True,
                    legendgroup=str(cid),
                    hoverinfo="skip"
                )
            )

        fig.update_geos(
            projection_type="natural earth",
        
            lonaxis=dict(
                range=[67, 100],
                showgrid=True,
                gridwidth=0.5,
                gridcolor="lightgrey"
            ),

            lataxis=dict(
                range=[5, 38.5],
                showgrid=True,
                gridwidth=0.5,
                gridcolor="lightgrey"
            ),

            # Keep land and ocean backgrounds
            showland=True,
            landcolor="rgb(235,235,235)",

            showocean=True,
            oceancolor="rgb(215,235,245)",

            # REMOVE OLD BUILT-IN BOUNDARIES
            showcoastlines=False,
            showcountries=False,

            # No additional administrative boundaries
            showsubunits=False
        )

        # --------------------------------------------------
        # PLAY / PAUSE BUTTONS AND LEGEND
        # --------------------------------------------------

        fig.update_layout(
            height=620,
            margin=dict(
                l=0,
                r=180,
                t=60,
                b=170
            ),
            updatemenus=[
                dict(
                    type="buttons",
                    direction="left",
                    x=0.5,
                    xanchor="center",
                    y=-0.13,
                    yanchor="top",
                    bgcolor="#000000",
                    bordercolor="#002C7E",
                    borderwidth=1.5,
                    font=dict(
                        color="#00A53A",
                        size=15
                    ),

                    buttons=[
                        # PLAY
                        dict(
                            label="▶ Play",
                            method="animate",
                            args=[
                                None,
                                dict(
                                    fromcurrent=True,
                                    mode="immediate",
                                    frame=dict(
                                        duration=700,
                                        redraw=True
                                    ),
                                    transition=dict(duration=0)
                                )
                            ]
                        ),

                        # PAUSE
                        dict(
                            label="⏸ Pause",
                            method="animate",
                            args=[
                                [None],
                                dict(
                                    mode="immediate",
                                    frame=dict(
                                        duration=0,
                                        redraw=True
                                    ),
                                    transition=dict(duration=0)
                                )
                            ]
                        ),

                        # 4X SPEED
                        dict(
                            label="⏩ 4×",
                            method="animate",
                            args=[
                                None,
                                dict(
                                    fromcurrent=True,
                                    mode="immediate",
                                    frame=dict(
                                        duration=175,
                                        redraw=True
                                    ),
                                    transition=dict(duration=0)
                                )
                            ]
                        )
                    ]
                )
            ],

            sliders=[
                dict(
                    active=0,
                    x=0.05,
                    y=-0.30,
                    len=0.90,
                    currentvalue=dict(
                        prefix="Observation Time (UTC): ",
                        visible=True,
                        font=dict(size=11)
                    ),

                    steps=slider_steps
                )
            ],

            # Legend stays below the map, aligned left.
            # Each cyclone has its own legend entry.
            legend=dict(
            title="Cyclone",
            orientation="v",
            x=1.02,
            xanchor="left",
            y=1,
            yanchor="top",
            font=dict(size=10),
            tracegroupgap=2,
            itemsizing="constant"
        )
        )

        st.plotly_chart(
            fig,
            use_container_width=True,
            key="animated_cyclone_map"
        )

# ==================================================
# CI NUMBER GRAPH BESIDE MAP
# ==================================================

with ci_col:
    st.subheader('CI Number [or "T. No"]')
    ci_data = filtered_data.dropna(
        subset=[
            "Datetime",
            'CI No [or "T. No"]'
        ]
    ).copy()
    ci_fig = go.Figure()

    for i, (cid, group) in enumerate(
        ci_data.groupby("Cyclone_ID")
    ):
        group = group.sort_values("Datetime")
        ci_fig.add_trace(
            go.Scatter(
                x=group["Datetime"],
                y=group['CI No [or "T. No"]'],
                mode="lines+markers",
                name=cyclone_labels[cid],
                marker=dict(size=5),
                line=dict(
                    width=2,
                    color=colors[i % len(colors)]
                ),
                connectgaps=False,
                hovertemplate=(
                    "<b>%{fullData.name}</b><br>"
                    "Date: %{x|%d-%m-%Y %H:%M} UTC<br>"
                    "CI Number: %{y}"
                    "<extra></extra>"
                )
            )
        )

    ci_fig.update_layout(
        height=620,
        xaxis_title="Date / Time (UTC)",
        yaxis_title="CI Number",
        hovermode="closest",
        margin=dict(
            l=40,
            r=20,
            t=30,
            b=50
        ),
        legend=dict(
            title="Cyclone",
            orientation="h",
            yanchor="top",
            y=-0.20,
            xanchor="center",
            x=0.5
        )
    )

    ci_fig.update_xaxes(
        showgrid=True,
        gridcolor="lightgrey"
    )

    ci_fig.update_yaxes(
        showgrid=True,
        gridcolor="lightgrey"
    )

    st.plotly_chart(
        ci_fig,
        use_container_width=True,
        key="ci_number_graph"
    )

# ==================================================
# METEOROLOGICAL ANALYSIS
# ==================================================

st.divider()

st.subheader("Cyclone Meteorological Analysis")
plot_data = filtered_data.sort_values(
    "Datetime"
).copy()

# Convert numerical values
plot_data["Maximum Sustained Surface Wind (kt)"] = pd.to_numeric(
    plot_data["Maximum Sustained Surface Wind (kt)"],
    errors="coerce"
)

plot_data['Pressure Drop (hPa) [or "delta P"]'] = pd.to_numeric(
    plot_data['Pressure Drop (hPa) [or "delta P"]'],
    errors="coerce"
)

wind_col, pressure_col = st.columns(
    2,
    gap="large"
)

# ==================================================
# WIND SPEED GRAPH
# ==================================================

with wind_col:
    st.markdown("### Maximum Sustained Surface Wind")
    wind_fig = go.Figure()

    for i, (cid, group) in enumerate(
        plot_data.groupby("Cyclone_ID")
    ):
        group = group.sort_values("Datetime")
        wind_fig.add_trace(
            go.Scatter(
                x=group["Datetime"],
                y=group["Maximum Sustained Surface Wind (kt)"],
                mode="lines+markers",
                name=cyclone_labels[cid],
                marker=dict(size=5),
                line=dict(
                    width=2,
                    color=colors[i % len(colors)]
                ),
                connectgaps=False,
                hovertemplate=(
                    "<b>%{fullData.name}</b><br>"
                    "Date: %{x|%d-%m-%Y %H:%M} UTC<br>"
                    "Wind Speed: %{y} kt"
                    "<extra></extra>"
                )
            )
        )

    wind_fig.update_layout(
        height=450,
        xaxis_title="Date / Time (UTC)",
        yaxis_title="Wind Speed (kt)",
        hovermode="closest",
        margin=dict(
            l=20,
            r=20,
            t=30,
            b=20
        )
    )

    wind_fig.update_yaxes(
        rangemode="tozero",
        showgrid=True,
        gridcolor="lightgrey"
    )

    wind_fig.update_xaxes(
        showgrid=True,
        gridcolor="lightgrey"
    )

    st.plotly_chart(
        wind_fig,
        use_container_width=True
    )

# ==================================================
# PRESSURE DROP GRAPH
# ==================================================

with pressure_col:
    st.markdown("### Pressure Drop")
    pressure_fig = go.Figure()

    for i, (cid, group) in enumerate(
        plot_data.groupby("Cyclone_ID")
    ):
        group = group.sort_values("Datetime")
        # Drop missing pressure observations from this trace.
        # This avoids hover points being generated for missing values.
        pressure_group = group.dropna(
            subset=[
                'Pressure Drop (hPa) [or "delta P"]'
            ]
        )

        if pressure_group.empty:
            continue

        pressure_fig.add_trace(
            go.Scatter(
                x=pressure_group["Datetime"],
                y=pressure_group[
                    'Pressure Drop (hPa) [or "delta P"]'
                ],
                mode="lines+markers",
                name=cyclone_labels[cid],
                marker=dict(size=5),
                line=dict(
                    width=2,
                    color=colors[i % len(colors)]
                ),
                connectgaps=False,
                hovertemplate=(
                    "<b>%{fullData.name}</b><br>"
                    "Date: %{x|%d-%m-%Y %H:%M} UTC<br>"
                    "Pressure Drop: %{y} hPa"
                    "<extra></extra>"
                )
            )
        )

    pressure_fig.update_layout(
        height=450,
        xaxis_title="Date / Time (UTC)",
        yaxis_title="Pressure Drop (hPa)",
        hovermode="closest",
        margin=dict(
            l=20,
            r=20,
            t=30,
            b=20
        )
    )

    pressure_fig.update_yaxes(
        rangemode="tozero",
        showgrid=True,
        gridcolor="lightgrey"
    )

    pressure_fig.update_xaxes(
        showgrid=True,
        gridcolor="lightgrey"
    )

    st.plotly_chart(
        pressure_fig,
        use_container_width=True
    )

# ==================================================
# END OF DASHBOARD
# ==================================================

st.divider()

st.caption(
    "IMD Historical Cyclone Track Explorer | "
    "Data source: IMD Standardized Historical Records"
)
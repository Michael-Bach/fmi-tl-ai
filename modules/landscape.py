import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from data.landscape_data import CAPABILITY_AREAS, CAPABILITY_MATRIX, ORG_NAMES, ORGANISATIONS


def render():
    st.header("Nordic/NATO M&S Landscape")

    st.subheader("Organisations")
    df = pd.DataFrame(ORGANISATIONS)
    st.dataframe(df, use_container_width=True, hide_index=True)

    st.subheader("Capability Coverage")

    fig = go.Figure(data=go.Heatmap(
        z=CAPABILITY_MATRIX,
        x=ORG_NAMES,
        y=CAPABILITY_AREAS,
        colorscale=[
            [0.0, "#0d1117"],
            [0.5, "#196c2e"],
            [1.0, "#39d353"],
        ],
        zmin=0,
        zmax=2,
        text=CAPABILITY_MATRIX,
        texttemplate="%{text}",
        textfont=dict(family="Courier New", size=13, color="#c9d1d9"),
        showscale=True,
        colorbar=dict(
            tickvals=[0, 1, 2],
            ticktext=["None", "Partial", "Strong"],
            tickfont=dict(family="Courier New", color="#c9d1d9"),
            bgcolor="#0d1117",
            bordercolor="#21262d",
        ),
    ))

    fig.update_layout(
        title=dict(
            text="Capability Coverage — Nordic/NATO M&S Landscape",
            font=dict(color="#c9d1d9", family="Courier New"),
        ),
        plot_bgcolor="#0d1117",
        paper_bgcolor="#0d1117",
        font=dict(color="#c9d1d9", family="Courier New"),
        xaxis=dict(side="bottom", tickfont=dict(family="Courier New", color="#c9d1d9")),
        yaxis=dict(tickfont=dict(family="Courier New", color="#c9d1d9")),
        margin=dict(l=180, r=20, t=60, b=80),
        height=420,
    )

    st.plotly_chart(fig, use_container_width=True)

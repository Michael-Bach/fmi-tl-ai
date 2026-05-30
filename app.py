import streamlit as st

st.set_page_config(
    page_title="EW M&S Foundation",
    layout="wide",
    page_icon="🛡️",
)

st.markdown(
    """
    <style>
    html, body, [class*="css"] {
        background-color: #0d1117;
        color: #c9d1d9;
    }
    .stApp {
        background-color: #0d1117;
    }
    .stMetric label, .stMetric div[data-testid="stMetricValue"] {
        font-family: 'Courier New', monospace !important;
    }
    .stDataFrame, .stDataFrame td, .stDataFrame th {
        font-family: 'Courier New', monospace !important;
    }
    .stSelectbox label, .stSlider label, .stExpander summary p {
        font-family: 'Courier New', monospace !important;
    }
    [data-testid="metric-container"] {
        font-family: 'Courier New', monospace !important;
    }
    .stSidebar [data-testid="stMarkdownContainer"] p {
        font-family: 'Courier New', monospace !important;
        color: #c9d1d9;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.markdown(
        """
        ```
        Role:         Team Lead, AI Modellering
                      og Simulering
        Organisation: FMI — TEW
        ```
        """
    )

st.title("EW M&S Foundation — FMI TEW")

from modules import vision, simulation, landscape, intelligence

tab1, tab2, tab3, tab4 = st.tabs(["🗺️ Vision", "📡 Simulation", "🌐 Landscape", "🔍 Intelligence"])

with tab1:
    vision.render()

with tab2:
    simulation.render()

with tab3:
    landscape.render()

with tab4:
    intelligence.render()

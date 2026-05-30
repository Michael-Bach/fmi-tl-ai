import streamlit as st
from data.roadmap import ROADMAP


def render():
    st.header("TEW Capability Roadmap — Year 1")

    for i, q in enumerate(ROADMAP):
        with st.expander(f"{q['id']} ({q['period']}) — {q['headline']}", expanded=(i == 0)):
            st.markdown(f"**{q['headline']}**")
            for point in q["points"]:
                st.markdown(f"- {point}")
            st.markdown(f":orange[**Deliverable:** {q['deliverable']}]")

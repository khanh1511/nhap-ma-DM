import streamlit as st
import pandas as pd

if "selected" not in st.session_state:
    st.session_state.selected = 2

df = pd.DataFrame({
    "A": [1, 2, 3, 4, 5],
    "B": ["a", "b", "c", "d", "e"]
})

def highlight(row):
    if row.name == st.session_state.selected:
        return ["background-color: yellow"] * len(row)
    return [""] * len(row)

styled = df.style.apply(highlight, axis=1)

event = st.dataframe(styled, on_select="rerun", selection_mode="single-row")

st.write("Selected row in UI:", event.selection.rows)
if event.selection.rows:
    st.session_state.selected = event.selection.rows[0]
    st.write("Set state to:", event.selection.rows[0])

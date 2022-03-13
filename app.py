from webbrowser import get
import streamlit as st
import pandas as pd
import numpy as np

from get_data import get_games

games = get_games()
teams = pd.read_csv("./2021_teams.csv")
num_games = len(games)
num_teams = len(teams)

# Set options for parameters
method = st.selectbox("Choose a ranking method", [
                      "Colley", "Massey"], index=0, format_func=lambda x: x + " (accounts for point differential)" if x == "Massey" else x)
home_win_weight = st.slider(
    "Home win weight", value=1.0, min_value=0.0, max_value=10.0, step=0.1)
away_win_weight = st.slider(
    "Away win weight", value=1.0, min_value=0.0, max_value=10.0, step=0.1)
neutral_win_weight = st.slider(
    "Neutral win weight", value=1.0, min_value=0.0, max_value=10.0, step=0.1)

use_time_weights = st.checkbox("Use time-based weights", value=True)

if use_time_weights:
    with st.expander("Time-based Weights", expanded=True):
        st.write("""
          These weights will be applied to games based on the day in which they were played during the season. The season is split into segments according to the number of weights that you specify here.
        """)
        num_time_weights = st.number_input(
            "Number of time weights", value=2, min_value=2, max_value=10)
        time_weights = np.array([1] * int(num_time_weights))
        for i in range(int(num_time_weights)):
            time_weights[i] = st.slider(
                f"Time weight {i+1}", value=1, min_value=0, max_value=10)

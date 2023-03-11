import streamlit as st
from data import get_data, get_teams, get_team_by_id, get_games_by_team_id
from time_weighting import input_time_weights

# Configure the streamlit app
st.set_page_config(
    page_title="March Madness",
    layout="wide"
)

st.title("March Madness")
"""
Welcome to the 2023 March Madness ranking app.
"""

st.header("Ranking Parameters")

form_col_1, form_col_2 = st.columns(2)
method = form_col_1.selectbox(
    "Choose a ranking method",
    ["Colley", "Massey"],
    index=0,
    format_func=lambda x:
        x + " (accounts for point differential)" if x == "Massey" else x)
home_win_weight = form_col_2.slider(
    "Home win weight", value=1.0, min_value=0.0, max_value=2.0, step=0.01)
away_win_weight = form_col_2.slider(
    "Away win weight", value=1.0, min_value=0.0, max_value=2.0, step=0.01)
neutral_win_weight = form_col_2.slider(
    "Neutral win weight",
    value=1.0,
    min_value=0.0,
    max_value=2.0,
    step=0.01
)

use_time_weights = form_col_1.checkbox("Use time-based weights", value=True)

if use_time_weights:
    with form_col_1.expander("Time-based Weights", expanded=True):
        st.write("""
            These weights will be applied to games based on the day in which
            they were played during the season. The season is split
            into segments according to the number of weights
            that you specify here.
        """)
        num_time_weights = st.number_input(
            "Number of time weights", value=2, min_value=2, max_value=10)
        time_weights = [1] * int(num_time_weights)
        for i in range(int(num_time_weights)):
            time_weights[i] = st.slider(
                f"Time weight {i+1}",
                value=1.0,
                min_value=0.0,
                max_value=2.0,
                step=0.01
            )

opts = {
    "weight_home_win": home_win_weight,
    "weight_away_win": away_win_weight,
    "weight_neutral_win": neutral_win_weight,
    "use_time_weights": use_time_weights,
    "segment_weights": time_weights if use_time_weights else [1],
}


data = get_data()

st.dataframe(data)

st.json(data.loc[0, :].to_dict())

# Plot a chart of the count of games played by day
st.header("Games Played by Day")
st.bar_chart(data["date"].value_counts())

# Plot a line chart of the average winning score by day
st.header("Average Winning Score by Day")
st.line_chart(data.groupby("date")[["winning_score", "losing_score"]].mean())


st.header("Teams")
teams = get_teams()
st.dataframe(teams)

st.write(get_team_by_id(1))


# Team Selector
selected_team = st.selectbox(
    "Select a team",
    teams["team_id"],
    format_func=get_team_by_id
)

st.dataframe(get_games_by_team_id(selected_team))

input_time_weights()

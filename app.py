import streamlit as st
from data import get_data, get_teams
from bracket import get_bracket_games, BRACKET_URL_2022
from time_weighting import input_time_weights
import pandas as pd
import numpy as np

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
    form_col_1.caption("Note: the dates shown in this table should not be edited — only the weights themselves.")
    time_weight_df = input_time_weights(parent=form_col_1)
    time_weights = time_weight_df["weight"].to_list()

opts = {
    "weight_home_win": home_win_weight,
    "weight_away_win": away_win_weight,
    "weight_neutral_win": neutral_win_weight,
    "use_time_weights": use_time_weights,
    "segment_weights": time_weights if use_time_weights else [1],
}


data = get_data()

st.dataframe(data)

# Plot a chart of the count of games played by day
st.header("Games Played by Day")
st.bar_chart(data["date"].value_counts())

# Plot a line chart of the average winning score by day
st.header("Average Winning Score by Day")
st.line_chart(data.groupby("date")[["winning_score", "losing_score"]].mean())


bracket = get_bracket_games(BRACKET_URL_2022)

# Make team_1_name and team_2_name columns null if round != 1
bracket.loc[bracket["round"] != 1, [
    "team_1_seed",
    "team_1_name",
    "team_2_seed",
    "team_2_name"]] = None


def decide_by_seeds(row):
    if row["team_1_seed"] < row["team_2_seed"]:
        return 1
    elif row["team_2_seed"] < row["team_1_seed"]:
        return 2
    else:
        return np.random.choice([1, 2])


# Play the bracket
decision_func = decide_by_seeds
for i in range(len(bracket)):
    row = bracket.iloc[i]
    winning_team = decision_func(row)

    which_spot = 1 if row["round_game_number"] % 2 == 1 else 2

    if row["next_round"] == 5:
        which_spot = 1 if row["region_name"] in ["WEST", "MIDWEST"] else 2

    bracket.loc[i, ["team_1_win", "team_2_win"]] = (
        True if winning_team == 1 else False,
        True if winning_team == 2 else False
    )

    if np.isnan(row["next_game_index"]):
        continue
    bracket.loc[row["next_game_index"], [
        f"team_{which_spot}_seed",
        f"team_{which_spot}_name",
    ]] = row[f"team_{winning_team}_seed"], row[f"team_{winning_team}_name"]


st.dataframe(bracket)

st.write(f"""
The winner of the tournament is **{
    bracket.iloc[-1, :][
        "team_1_name" if bracket.iloc[-1, :]["team_1_win"] else "team_2_name"
    ]
}**!
""")
         

distinct_bracket_teams = sorted(list(set(
    bracket["team_1_name"].dropna().unique().tolist() +
    bracket["team_2_name"].dropna().unique().tolist()
)))

teams = pd.DataFrame({"bracket_teams": distinct_bracket_teams})
all_teams = get_teams()
teams = teams.merge(
    all_teams,
    how="left",
    left_on="bracket_teams",
    right_on="team_name"
)
st.dataframe(teams)
st.dataframe(all_teams)

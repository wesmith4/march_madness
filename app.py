import streamlit as st
from data import get_data, get_teams
from bracket import get_bracket_games, get_team_seeds, BRACKET_URL
from time_weighting import input_time_weights
from ranker import ColleyRanker, MasseyRanker, RankingOptions
import pandas as pd
import numpy as np

# Configure the streamlit app
st.set_page_config(
    page_title="March Madness",
    layout="wide"
)

st.title("March Madness 2023")
"""
This app provides a frontend for using the [Colley](https://en.wikipedia.org/wiki/Colley_Matrix) and [Massey](https://masseyratings.com/theory/massey.htm) ranking algorithms to inform selection of the outcomes of the NCAA March Madness bracket. The Colley algorithm is a simple ranking algorithm that does not account for point differential, while the Massey algorithm does. The Massey algorithm is more accurate, but it is also more computationally expensive. The Colley algorithm is much faster, but it is less accurate. The Massey algorithm is also more sensitive to the weights assigned to home, away, and neutral wins.

The app also allows you to input weights for different parts of the season. For example, you can assign a weight of 1.0 to the first half of the season, and a weight of 0.5 to the second half of the season. This allows you to account for the fact that teams tend to play better in the first half of the season than in the second half of the season.

#### How to use
- Select a ranking method from the dropdown menu.
- Adjust the weights for home, away, and neutral wins.
- (Optionally) Check the box to enable time-based weights.
- (If time-based weights are enabled) Adjust the weights for each segment of the season.
- The app will automatically update the ratings in the background, and the Predicted Game Results table will show their predicted outcome for each game, ordered by region and round.

#### Resources
- [Data: Masseyratings.com](https://masseyratings.com/scores.php?s=500054&sub=11590&all=1&mode=3)
- [Bracket: NCAA.com](https://www.ncaa.com/march-madness-live/bracket)
"""

st.header("Ranking Parameters")

form_col_1, form_col_2 = st.columns(2)
method = form_col_1.selectbox(
    "Choose a ranking method",
    ["Colley", "Massey"],
    index=0,
    format_func=lambda x:
        x + " (accounts for point differential)" if x == "Massey" else x
)
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

use_time_weights = form_col_1.checkbox("Use time-based weights", value=True,help="If checked, the ranking algorithm will use time-based weights. If unchecked, all games will be weighted equally.")

if use_time_weights:
    form_col_1.caption("Note: the dates shown in this table should not be edited — only the weights themselves.")
    time_weight_df = input_time_weights(parent=form_col_1)
    time_weights = time_weight_df["weight"].to_list()


opts = RankingOptions(
    weight_home_win=home_win_weight,
    weight_away_win=away_win_weight,
    weight_neutral_win=neutral_win_weight,
    use_time_weights=use_time_weights,
    segment_weights=time_weights if use_time_weights else [1],
)
data = get_data()
teams = get_teams()

# Ranking Algorithms
colley = ColleyRanker(data, teams, opts)
colley_results = colley.process()
massey = MasseyRanker(data, teams, opts)
massey_results = massey.process()

ALGO_MAP = {
    "Colley": colley_results,
    "Massey": massey_results,
}

bracket = get_bracket_games(BRACKET_URL)

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


def decide_by_algorithm(row):
    results = ALGO_MAP[method]

    team_1_name = row["team_1_name"].split("/")[0] if "/" in row["team_1_name"] else row["team_1_name"]
    team_2_name = row["team_2_name"].split("/")[0] if "/" in row["team_2_name"] else row["team_2_name"]

    team_1_rating = results.loc[results["team"] == team_1_name, "rating"].values[0]
    team_2_rating = results.loc[results["team"] == team_2_name, "rating"].values[0]

    return 1 if team_1_rating > team_2_rating else 2


# Play the bracket

for i in range(len(bracket)):
    row = bracket.iloc[i]
    winning_team = decide_by_algorithm(row)

    which_spot = 1 if row["round_game_number"] % 2 == 1 else 2

    if row["next_round"] == 5:
        which_spot = 1 if row["region_name"] in ["South", "Midwest"] else 2

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


"""
## Predicted Game Results

You can use the game outcomes in the dataframe below to fill out your bracket region-by-region, round-by-round, and then complete the Final Four.
"""

st.dataframe(bracket, height=1500)

st.write(f"""
The winner of the tournament is **{
    bracket.iloc[-1, :][
        "team_1_name" if bracket.iloc[-1, :]["team_1_win"] else "team_2_name"
    ]
}**!
""")
         

seeded_teams = get_team_seeds()

rating_results = pd.merge(
    seeded_teams,
    ALGO_MAP[method],
    how="left",
    on="team"
)
rating_results.sort_values(by="rating", ascending=False, inplace=True)

"""
### Rating results

The table below shows the actual rating values assigned to each team in the bracket by the algorithm and set of parameters you specified.
"""
st.dataframe(rating_results)


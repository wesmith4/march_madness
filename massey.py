from pyparsing import col
import streamlit as st
import numpy as np
import pandas as pd
from math import ceil


@st.cache
def massey(games, teams, opts={
    "weight_home_win": 1,
    "weight_away_win": 1,
    "weight_neutral_win": 1,
    "use_time_weights": True,
    "segment_weights": [1]
}):
    num_games = len(games)
    num_teams = len(teams)

    massey_matrix = np.zeros((num_teams, num_teams))
    b = np.zeros(num_teams)

    day_before_season = games.loc[0, 'days_since_timestart'] - 1
    last_day_of_season = games.loc[len(games) - 1, 'days_since_timestart']

    for i in range(num_games):
        [current_day, date, team_1_id, team_1_homefield, team_1_score,
            team_2_id, team_2_homefield, team_2_score] = games.loc[i, :].values

        team_1_index = team_1_id - 1
        team_2_index = team_2_id - 1

        num_segments = len(opts["segment_weights"])

        weight_index = ceil(num_segments*((current_day - day_before_season) /
                            (last_day_of_season-day_before_season))) - 1
        time_weight = opts["segment_weights"][weight_index]

        if team_1_score > team_2_score:
            if team_1_homefield == 1:
                game_weight = opts["weight_home_win"] * time_weight
            elif team_1_homefield == -1:
                game_weight = opts["weight_away_win"] * time_weight
            else:
                game_weight = opts["weight_neutral_win"] * time_weight
        else:
            if team_2_homefield == 1:
                game_weight = opts["weight_home_win"] * time_weight
            elif team_2_homefield == -1:
                game_weight = opts["weight_away_win"] * time_weight
            else:
                game_weight = opts["weight_neutral_win"] * time_weight

        # Update the colley matrix
        massey_matrix[team_1_index, team_1_index] += game_weight
        massey_matrix[team_2_index, team_2_index] += game_weight
        massey_matrix[team_1_index, team_2_index] -= game_weight
        massey_matrix[team_2_index, team_1_index] -= game_weight

        point_differential = game_weight * abs(team_1_score - team_2_score)

        if team_1_score > team_2_score:
            b[team_1_index] += point_differential
            b[team_2_index] -= point_differential
        else:
            b[team_1_index] -= point_differential
            b[team_2_index] += point_differential

    massey_matrix[-1, :] = np.ones((1, num_teams))
    b[-1] = 0

    # Solve the system of equations
    r = np.linalg.solve(massey_matrix, b)
    iSort = np.argsort(-r)

    massey_ratings = pd.DataFrame(columns=['rank', 'team', 'rating'])
    for i in range(num_teams):
        massey_ratings.loc[i, :] = [
            i+1, teams.loc[iSort[i], 'team'], r[iSort[i]]]
    return massey_ratings

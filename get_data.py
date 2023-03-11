import pandas as pd
import streamlit as st

@st.cache
def get_games():
    games_url = "https://masseyratings.com/scores.php?s=379387&sub=11590&all=1&mode=3&format=1"
    games = pd.read_csv(games_url, header=None, index_col=None)
    games.rename(columns={
      0: "days_since_timestart",
      1: "date",
      2: "team_1_id",
      3: "team_1_homefield",
      4: "team_1_score",
      5: "team_2_id",
      6: "team_2_homefield",
      7: "team_2_score",
    }, inplace=True)
    return games

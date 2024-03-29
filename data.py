import streamlit as st
import pandas as pd
from datetime import datetime as dt
import pytz
import re

# Disable flake8 warning about line length
TEAMS_ENDPOINT = "https://masseyratings.com/scores.php\
?s=500054&sub=11590&all=1&mode=3&format=2"
GAMES_ENDPOINT = "https://masseyratings.com/scores.php\
?s=500054&sub=11590&all=1&mode=3&format=1"


def format_team_name(team_name: str) -> str:
    TEAM_NAME_MAPPINGS = {
        "Miami OH": "Miami (OH)",
        "Miami FL": "Miami (FL)",
        "Loyola-Chicago": "Loyola Chicago",
        "St Mary's CA": "Saint Mary's",
        "St Peter's": "Saint Peter's",
        "S Dakota St.": "South Dakota St.",
        "TX Southern": "Texas Southern",
        "Connecticut": "UConn",
        "CS Fullerton": "Cal State Fullerton",
        "Col Charleston": "Col of Charleston",
        "FL Atlantic": "FAU",
        "Kennesaw": "Kennesaw St.",
        "Kent": "Kent St.",
        "UC Santa Barbara": "UCSB",
        "TAM C. Christi": "Texas A&M-CC",
        "F Dickinson": "F. Dickinson",
        "Pittsburgh": "Pitt",
    }

    team_name = team_name.strip()

    team_name = team_name.replace("_", " ")

    # Regex replace St at the end of a string with St.
    team_name = re.sub(r"St$", "St.", team_name)

    # Replace team name with a mapping if it exists
    if team_name in TEAM_NAME_MAPPINGS:
        team_name = TEAM_NAME_MAPPINGS[team_name]

    return team_name


@st.cache_data
def get_teams() -> pd.DataFrame:

    teams_df = pd.read_csv(TEAMS_ENDPOINT, header=None, index_col=None)
    teams_df.columns = ["team_id", "team_name"]
    teams_df["team_id"] = teams_df["team_id"].astype(int)
    teams_df["raw_team_name"] = teams_df["team_name"].copy()
    teams_df["team_name"] = teams_df["team_name"].apply(format_team_name)
    return teams_df


def get_team_by_id(team_id: int) -> str:
    teams_df = get_teams()
    return teams_df["team_name"][team_id - 1]


def get_team_id_by_name(team_name: str) -> int:
    teams_df = get_teams()
    return teams_df[teams_df["team_name"] == team_name]["team_id"].values[0]


@st.cache_data
def get_games() -> pd.DataFrame:
    games = pd.read_csv(GAMES_ENDPOINT, header=None, index_col=None)
    games.columns = [
        "days_since_timestart",
        "date",
        "team_1_id",
        "team_1_homefield",
        "team_1_score",
        "team_2_id",
        "team_2_homefield",
        "team_2_score",
    ]

    # Make the homefield column a binary, instead of 1 and -1
    games["team_1_homefield"] = games["team_1_homefield"].apply(
        lambda x: 1 if x == 1 else 0
    )
    games["team_2_homefield"] = games["team_2_homefield"].apply(
        lambda x: 1 if x == 1 else 0
    )

    # Convert the date column to a datetime object
    games["date"] = games["date"].apply(
        lambda x: dt.strptime(str(x), "%Y%m%d")
        .astimezone(pytz.timezone("US/Eastern"))
    )

    return games


@st.cache_data
def get_data() -> pd.DataFrame:
    teams = get_teams()
    games = get_games()

    # Bring in two new columns team_1_name and team_2_name
    #  by joining in the teams df twice
    games = games.merge(
        teams,
        left_on="team_1_id",
        right_on="team_id",
        how="left"
    )
    games = games.merge(
        teams,
        left_on="team_2_id",
        right_on="team_id",
        how="left"
    )

    # Drop the extra team_id columns
    games.drop(columns=["team_id_x", "team_id_y"], inplace=True)

    # Rename the team_name columns
    games.rename(
        columns={"team_name_x": "team_1_name", "team_name_y": "team_2_name"},
        inplace=True
    )

    # Trim any string whitespace from any string columns
    games = games.applymap(
        lambda x: x.strip() if isinstance(x, str) else x
    )

    games.loc[:, "team_1_win"] = games["team_1_score"] > games["team_2_score"]
    games.loc[:, "team_2_win"] = games["team_2_score"] > games["team_1_score"]
    games.loc[:, "winning_score"] = games[
        ["team_1_score", "team_2_score"]
    ].max(axis=1)
    games.loc[:, "losing_score"] = games[
        ["team_1_score", "team_2_score"]
    ].min(axis=1)

    return games[[
        "days_since_timestart",
        "date",
        "team_1_id",
        "team_1_name",
        "team_1_homefield",
        "team_1_score",
        "team_1_win",
        "team_2_id",
        "team_2_name",
        "team_2_homefield",
        "team_2_score",
        "team_2_win",
        "winning_score",
        "losing_score"
    ]]


def get_games_by_team_id(team_id: int) -> pd.DataFrame:
    df = get_data()
    return df[
        (df["team_1_id"] == team_id) | (df["team_2_id"] == team_id)
    ]


if __name__ == "__main__":
    df = get_data()
    print(df.columns)
    print(df.head())

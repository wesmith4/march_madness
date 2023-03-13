import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np

BRACKET_URL = "https://www.ncaa.com/brackets/basketball-men/d1/2023"
BRACKET_URL_2022 = "https://www.ncaa.com/brackets/basketball-men/d1/2022"


PLAY_IN_SEED_MAP = {
    "1": "16",
    "6": "11"
}


@st.cache_data
def get_bracket_games(url=BRACKET_URL, save_to_file=False):
    r = requests.get(url)
    soup = BeautifulSoup(r.text, "html.parser")

    regions = soup.find_all("div", {"class": "region"})

    # Filter regions to include only the ones that have a round-1 div
    regions = [region for region in regions
               if region.find("div", {"class": "region-round round-1"})]

    df = pd.DataFrame(columns=[
        "id",
        "region_name",
        "round",
        "round_game_number",
        "team_1_seed",
        "team_1_name",
        "team_1_win",
        "team_2_seed",
        "team_2_name",
        "team_2_win"
    ])
    ind = 0
    for region in regions:
        region_name = region.find("span", {"class": "subtitle"}).text
        for i in range(1, 5):
            game_counter = 1
            round_div = region.find("div", {"class": f"region-round round-{i}"})
            if not round_div:
                continue
            games = round_div.find_all("a", {"class": "game-pod"})
            for game in games:
                teams = game.find_all("div", {"class": "team"})
                df.loc[ind] = [
                    int(game["id"]),
                    region_name,
                    i,
                    game_counter,
                    int(teams[0].find("span", {"class": "overline"}).text) if len(teams[0].find("span", {"class": "overline"}).text) > 0 else None,
                    teams[0].find("p", {"class": "body"}).text if len(teams[0].find("p", {"class": "body"}).text) > 0 else None,
                    None,
                    int(teams[1].find("span", {"class": "overline"}).text) if len(teams[1].find("span", {"class": "overline"}).text) > 0 else None,
                    teams[1].find("p", {"class": "body"}).text if len(teams[1].find("p", {"class": "body"}).text) > 0 else None,
                    None
                ]

                if len(teams[0].find("span", {"class": "overline"}).text) > 0 and not teams[0].find("span", {"class": "overline"}).text.isnumeric():
                    df.loc[ind, "team_2_seed"] = int(PLAY_IN_SEED_MAP[str(df.loc[ind, "team_1_seed"])])
                    df.loc[ind, "team_2_name"] = str(np.random.randint(1, 10))

                game_counter += 1
                ind += 1


    # Modifications to include next game info
    df.loc[:, "next_round"] = df["round"] + 1
    df.loc[:, "next_game_number"] = df.loc[:, "round_game_number"].apply(
        lambda x: int(np.ceil(x / 2))
    )
    cols_to_keep = df.columns
    df.sort_values(by=["round", "region_name", "round_game_number"])
    df.reset_index(inplace=True, drop=True)
    copy = df.copy()
    copy.reset_index(inplace=True)
    df = df.merge(
        copy,
        how="left",
        left_on=["region_name", "next_round", "next_game_number"],
        right_on=["region_name", "round", "round_game_number"],
        suffixes=("", "_next")
    )
    df = df[cols_to_keep.to_list() + ["index", "id_next"]]
    df.rename(columns={
        "id_next": "next_game_id",
        "index": "next_game_index"
    }, inplace=True)
    df["next_game_id"] = df["next_game_id"].astype("Int64")
    # df["next_game_index"] = df["next_game_index"].astype("Int64")

    final_four_games = soup.find("div", {"class": "final-four"})\
        .find_all("a", {"class": "game-pod"})
    ff = pd.DataFrame(columns=df.columns)
    for raw_game in final_four_games:
        teams = raw_game.find_all("div", {"class": "team"})
        ff.loc[len(ff)] = [
            int(raw_game["id"]),
            "FINAL FOUR" if raw_game["id"][0] == "6" else "CHAMPIONSHIP",
            int(str(raw_game["id"][0])) - 1,
            int(str(raw_game["id"][-1])),
            None,
            None,
            None,
            None,
            None,
            None,
            6 if raw_game["id"][0] == "6" else None,
            1 if raw_game["id"][0] == "6" else None,
            62 if raw_game["id"][0] == "6" else np.nan,
            701 if raw_game["id"][0] == "6" else None,
        ]
    ff.sort_values(by="id", inplace=True)
    ff.reset_index(inplace=True, drop=True)

    df = pd.concat([df, ff], ignore_index=True)

    df.loc[
        (df["region_name"].isin(["South", "East"])) & (df["round"] == 4),
        ["next_game_number", "next_game_index", "next_game_id"]
    ] = [1, np.float64(60.0), 601]
    df.loc[
        (df["region_name"].isin(["Midwest", "West"])) & (df["round"] == 4),
        ["next_game_number", "next_game_index", "next_game_id"]
    ] = [2, np.float64(61.0), 602]


    # First Four
    REGION_INDICATOR_MAP = {
        "S": "South",
        "E": "East",
        "MW": "Midwest",
        "W": "West"
    }
    first_four = soup.find("div", {"class": "first-four"})
    first_four_pods = first_four.find_all("div", {"class": "game-pod"})
    for pod in first_four_pods:
        region = REGION_INDICATOR_MAP[pod.find("span", {"class": "subtitle"}).text]
        seed = int(pod.find("span", {"class": "overline"}).text)
        teams = "/".join([
            team.find("p", {"class": "body"}).text for team in pod.find_all("div", {"class": "team"})
        ])
        df.loc[
            (df["region_name"] == region) &
            (df["round"] == 1) &
            (df["team_2_seed"].isnull()),
            ["team_2_seed", "team_2_name"]
        ] = [seed, teams]

    if save_to_file:
        df.to_csv("bracket.csv", index=False)
    return df


@st.cache_data
def get_team_seeds():
    bracket_games = get_bracket_games()
    bracket_games = bracket_games[bracket_games["round"] == 1]
    df = pd.concat([
        pd.DataFrame(bracket_games[["team_1_seed", "team_1_name"]].values, columns=["seed", "team"]),
        pd.DataFrame(bracket_games[["team_2_seed", "team_2_name"]].values, columns=["seed", "team"])
    ])

    # Get rows where team contains "/"
    split_teams = df[df["team"].str.contains("/")].copy()

    for i, row in split_teams.iterrows():
        team_1, team_2 = row["team"].split("/")
        seed = row["seed"]
        df.loc[len(df)] = [seed, team_1]
        df.loc[len(df)] = [seed, team_2]

    df = df[~df["team"].str.contains("/")]
    df.drop_duplicates(inplace=True)
    df.sort_values(by=["seed", "team"], inplace=True)
    df.reset_index(inplace=True, drop=True)
    df["seed"] = df["seed"].astype("Int64")
    return df


if __name__ == "__main__":
    get_bracket_games(save_to_file=True)

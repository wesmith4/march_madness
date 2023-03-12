import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np

BRACKET_URL = "https://www.ncaa.com/brackets/basketball-men/d1/2023"
BRACKET_URL_2022 = "https://www.ncaa.com/brackets/basketball-men/d1/2022"


@st.cache_data
def get_bracket_games(url=BRACKET_URL_2022, save_to_file=False):
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
        "team_2_seed",
        "team_2_name",
        "team_1_win",
        "team_2_win"
    ])
    ind = 0
    for region in regions:
        region_name = region.find("h3").text
        for i in range(1, 5):
            game_counter = 1
            round_div = region.find("div", {"class": f"region-round round-{i}"})
            if not round_div:
                continue
            games = round_div.find_all("div", {"class": "game-pod"})
            for game in games:
                teams = game.find_all("div", {"class": "team"})
                df.loc[ind] = [
                    int(game["id"]),
                    region_name,
                    i,
                    game_counter,
                    int(teams[0].find("span", {"class": "seed"}).text),
                    teams[0].find("span", {"class": "name"}).text,
                    int(teams[1].find("span", {"class": "seed"}).text),
                    teams[1].find("span", {"class": "name"}).text,
                    None,
                    None
                ]
                game_counter += 1
                ind += 1

    # Modifications to include next game info
    df.loc[:, "next_round"] = df["round"] + 1
    df.loc[:, "next_game_number"] = df.loc[:, "round_game_number"].apply(
        lambda x: int(np.ceil(x / 2))
    )
    cols_to_keep = df.columns
    df.sort_values(by=["round","region_name", "round_game_number"])
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

    if save_to_file:
        df.to_csv("bracket.csv", index=False)
    return df


if __name__ == "__main__":
    get_bracket_games(save_to_file=True)

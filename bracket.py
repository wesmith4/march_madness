import streamlit as st
import requests
from bs4 import BeautifulSoup
import json

BRACKET_URL = "https://www.ncaa.com/brackets/basketball-men/d1/2023"
BRACKET_URL_2022 = "https://www.ncaa.com/brackets/basketball-men/d1/2022"


@st.cache_data
def get_bracket_games(save_to_file=False):
    r = requests.get(BRACKET_URL_2022)
    soup = BeautifulSoup(r.text, "html.parser")

    games = []
    # Get all div.game-pod that are children of a div.region-round.round-1
    region_divs = soup.find_all("div", {"class": "region"})

    print(len(region_divs))

    for region_div in region_divs:

        # Find the div.region-round.round-1 div
        region_round_1 = region_div.find(
            "div",
            {"class": "region-round round-1"}
        )
        if not region_round_1:
            continue

        region_name = region_div.find("h3").text
        region_games = region_round_1.find_all("div", {"class": "game-pod"})
        for game in region_games:
            raw_teams = game.find_all("div", {"class": "team"})
            teams = []
            for team in raw_teams:
                name = team.find("span", {"class": "name"}).text
                seed = team.find("span", {"class": "seed"}).text
                teams.append({
                    "name": name,
                    "seed": int(seed)
                })

            games.append({
                "region": region_name,
                "teams": teams
            })

    if save_to_file:
        json.dump(games, open("bracket.json", "w"), indent=4)

    return games


if __name__ == "__main__":
    get_bracket_games(save_to_file=True)

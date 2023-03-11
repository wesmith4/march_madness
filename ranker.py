import pandas as pd
import numpy as np
from math import ceil


class RankingOptions:
    def __init__(
            self,
            weight_home_win: float = 1,
            weight_away_win: float = 1,
            weight_neutral_win: float = 1,
            use_time_weights: bool = True,
            segment_weights: list[float] = [1],
    ):
        self.weight_home_win = weight_home_win
        self.weight_away_win = weight_away_win
        self.weight_neutral_win = weight_neutral_win
        self.use_time_weights = use_time_weights
        self.segment_weights = segment_weights


class Ranker:
    def __init__(
            self,
            games: pd.DataFrame,
            teams: pd.DataFrame,
            options: RankingOptions
    ):
        self.games = games
        self.teams = teams
        self.options = options
        self.num_games = len(games)
        self.num_teams = len(teams)

        self.day_before_season = games.loc[
            0, 'days_since_timestart'] - 1
        self.last_day_of_season = games.loc[
            len(games) - 1, 'days_since_timestart']

    @property
    def matrix():
        raise NotImplementedError

    def process(self):
        raise NotImplementedError


class ColleyRanker(Ranker):

    @property
    def matrix(self):
        return 2 * np.diag(np.ones(self.num_teams))

    def process(self):

        b = np.ones(self.num_teams)

        for i in range(self.num_games):
            [
                current_day,
                date,
                team_1_id,
                team_1_homefield,
                team_1_score,
                team_2_id,
                team_2_homefield,
                team_2_score
            ] = self.games.loc[i, :].values

            team_1_index = team_1_id - 1
            team_2_index = team_2_id - 1

            num_segments = len(self.options.segment_weights)

            weight_index = ceil(
                num_segments * ((
                     current_day - self.day_before_season) / (
                    self.last_day_of_season - self.day_before_season
                ))) - 1
            time_weight = self.options.segment_weights[weight_index]

            if team_1_score > team_2_score:
                if team_1_homefield == 1:
                    game_weight = self.options.weight_home_win * time_weight
                elif team_1_homefield == -1:
                    game_weight = self.options.weight_away_win * time_weight
                else:
                    game_weight = self.options.weight_neutral_win * time_weight
            else:
                if team_2_homefield == 1:
                    game_weight = self.options.weight_home_win * time_weight
                elif team_2_homefield == -1:
                    game_weight = self.options.weight_away_win * time_weight
                else:
                    game_weight = self.options.weight_neutral_win * time_weight

            self.matrix[team_1_index, team_1_index] += game_weight
            self.matrix[team_2_index, team_2_index] += game_weight
            self.matrix[team_1_index, team_2_index] -= game_weight
            self.matrix[team_2_index, team_1_index] -= game_weight

            if team_1_score > team_2_score:
                b[team_1_index] += game_weight
                b[team_2_index] -= game_weight
            else:
                b[team_1_index] -= game_weight
                b[team_2_index] += game_weight

        r = np.linalg.solve(self.matrix, b)
        i_sort = np.argsort(-r)

        ratings = pd.DataFrame(columns=['rank', 'team', 'rating'])
        for i in range(self.num_teams):
            ratings.loc[i, :] = [
                i+1,
                self.teams.loc[i_sort[i], 'team'],
                r[i_sort[i]]
            ]

        return ratings


class MasseyRanker(Ranker):

    @property
    def matrix(self):
        return np.zeros((self.num_teams, self.num_teams))

    def process(self):

        b = np.zeros(self.num_teams)

        for i in range(self.num_games):
            [
                current_day,
                date,
                team_1_id,
                team_1_homefield,
                team_1_score,
                team_2_id,
                team_2_homefield,
                team_2_score
            ] = self.games.loc[i, :].values

            team_1_index = team_1_id - 1
            team_2_index = team_2_id - 1

            num_segments = len(self.options.segment_weights)

            weight_index = ceil(
                num_segments * ((
                    current_day - self.day_before_season
                ) / (
                    self.last_day_of_season-self.day_before_season
                ))) - 1

            time_weight = self.options.segment_weights[weight_index]

            if team_1_score > team_2_score:
                if team_1_homefield == 1:
                    game_weight = self.options.weight_home_win * time_weight
                elif team_1_homefield == -1:
                    game_weight = self.options.weight_away_win * time_weight
                else:
                    game_weight = self.options.weight_neutral_win * time_weight
            else:
                if team_2_homefield == 1:
                    game_weight = self.options.weight_home_win * time_weight
                elif team_2_homefield == -1:
                    game_weight = self.options.weight_away_win * time_weight
                else:
                    game_weight = self.options.weight_neutral_win * time_weight

            self.matrix[team_1_index, team_1_index] += game_weight
            self.matrix[team_2_index, team_2_index] += game_weight
            self.matrix[team_1_index, team_2_index] -= game_weight
            self.matrix[team_2_index, team_1_index] -= game_weight

            point_differential = game_weight * abs(team_1_score - team_2_score)

            if team_1_score > team_2_score:
                b[team_1_index] += point_differential
                b[team_2_index] -= point_differential
            else:
                b[team_1_index] -= point_differential
                b[team_2_index] += point_differential

        self.matrix[-1, :] = np.ones((1, self.num_teams))
        b[-1] = 0

        r = np.linalg.solve(self.matrix, b)
        i_sort = np.argsort(-r)

        ratings = pd.DataFrame(columns=['rank', 'team', 'rating'])
        for i in range(self.num_teams):
            ratings.loc[i, :] = [
                i+1,
                self.teams.loc[i_sort[i], 'team'],
                r[i_sort[i]]
            ]
        return ratings

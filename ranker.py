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

    def process(self):
        raise NotImplementedError


class ColleyRanker(Ranker):

    def process(self):

        matrix = 2 * np.diag(np.ones(self.num_teams))

        b = np.ones(self.num_teams)

        for i in range(self.num_games):
            [
                days_since_timestart,
                date,
                team_1_id,
                team_1_name,
                team_1_homefield,
                team_1_score,
                team_1_win,
                team_2_id,
                team_2_name,
                team_2_homefield,
                team_2_score,
                team_2_win,
                winning_score,
                losing_score
            ] = self.games.loc[i, :].values

            team_1_index = team_1_id - 1
            team_2_index = team_2_id - 1

            num_segments = len(self.options.segment_weights)

            weight_index = ceil(
                num_segments * ((
                     days_since_timestart - self.day_before_season) / (
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

            matrix[team_1_index, team_1_index] += game_weight
            matrix[team_2_index, team_2_index] += game_weight
            matrix[team_1_index, team_2_index] -= game_weight
            matrix[team_2_index, team_1_index] -= game_weight

            if team_1_score > team_2_score:
                b[team_1_index] += game_weight
                b[team_2_index] -= game_weight
            else:
                b[team_1_index] -= game_weight
                b[team_2_index] += game_weight

        r = np.linalg.solve(matrix, b)
        i_sort = np.argsort(-r)

        ratings = pd.DataFrame(columns=['rank', 'team', 'rating'])
        for i in range(self.num_teams):
            ratings.loc[i, :] = [
                i+1,
                self.teams.loc[i_sort[i], 'team_name'],
                r[i_sort[i]]
            ]

        self.ratings = ratings
        return self.ratings


class MasseyRanker(Ranker):

    def process(self):

        matrix = np.zeros((self.num_teams, self.num_teams))

        b = np.zeros(self.num_teams)

        for i in range(self.num_games):
            [
                days_since_timestart,
                date,
                team_1_id,
                team_1_name,
                team_1_homefield,
                team_1_score,
                team_1_win,
                team_2_id,
                team_2_name,
                team_2_homefield,
                team_2_score,
                team_2_win,
                winning_score,
                losing_score
            ] = self.games.loc[i, :].values

            team_1_index = team_1_id - 1
            team_2_index = team_2_id - 1

            num_segments = len(self.options.segment_weights)

            weight_index = ceil(
                num_segments * ((
                    days_since_timestart - self.day_before_season
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

            matrix[team_1_index, team_1_index] += game_weight
            matrix[team_2_index, team_2_index] += game_weight
            matrix[team_1_index, team_2_index] -= game_weight
            matrix[team_2_index, team_1_index] -= game_weight

            point_differential = game_weight * abs(team_1_score - team_2_score)

            if team_1_score > team_2_score:
                b[team_1_index] += point_differential
                b[team_2_index] -= point_differential
            else:
                b[team_1_index] -= point_differential
                b[team_2_index] += point_differential

        matrix[-1, :] = np.ones((1, self.num_teams))
        b[-1] = 0

        r = np.linalg.solve(matrix, b)
        i_sort = np.argsort(-r)

        ratings = pd.DataFrame(columns=['rank', 'team', 'rating'])
        for i in range(self.num_teams):
            ratings.loc[i, :] = [
                i+1,
                self.teams.loc[i_sort[i], 'team_name'],
                r[i_sort[i]]
            ]

        self.ratings = ratings
        return self.ratings

import pandas as pd
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.tree import DecisionTreeRegressor
from xgboost import XGBRegressor
from joblib import dump, load


class XP_Model:
    def __init__(self, player_dict, current_gw, team_id_mapping):
        self.player_dict = player_dict
        self.current_gw = current_gw
        self.team_id_mapping = team_id_mapping

    def build_data(self) -> dict[int, int]:
        output = {}
        for player in self.player_dict.values():
            rolling_pts_list = [
                gameweekdata.points
                for gw, gameweekdata in player.historic_data.history.items()
                if gw <= self.current_gw and gw >= self.current_gw - 3
            ]
            if rolling_pts_list:
                rolling_pts = sum(rolling_pts_list) / len(rolling_pts_list)
            else:
                rolling_pts = 0
            output[player.id] = rolling_pts
        return output

    def get_xp(self) -> dict[int, int]:
        output = {}
        player_data_as_list = []
        for player in self.player_dict.values():
            for gwd_list in player.historic_data.history.values():
                for gwd in gwd_list:
                    row_as_dict = gwd.__dict__
                    row_as_dict["player_name"] = player.name
                    player_data_as_list.append(row_as_dict)
        df = pd.DataFrame(player_data_as_list)
        df = df.sort_values(by="round_number")
        new_df = pd.DataFrame()
        for key, player_df in df.groupby("player_id"):
            for column in ["points", "creativity", "threat", "influence", "bps"]:
                player_df[f"rolling_{column}_avg"] = (
                    player_df[column].rolling(4, 0).mean()
                )
            # player_df["expected_points"] = player_df["rolling_pts_avg"].shift(
            #     1
            # )  # rolling average after that row's points are added
            # try:
            #     expected_points = player_df[
            #         player_df.round_number == self.current_gw
            #     ].rolling_pts_avg.values[0]
            # except IndexError:
            #     expected_points = 0

            new_df = pd.concat([new_df, player_df])
            # output[key] = expected_points if expected_points == expected_points else 0
        # return output
        new_df = new_df[new_df["round_number"] <= self.current_gw].copy()
        zero_preds = new_df[new_df.value.isna()].copy()
        zero_preds["preds"] = 0
        rest_of_df = new_df[~new_df.value.isna()].copy()
        categorical_columns = ["was_home"]  # , "opposition_team_id"]
        for column in categorical_columns:
            new_cols = pd.get_dummies(rest_of_df[[column]].astype("str"))
            rest_of_df = pd.concat([rest_of_df, new_cols], axis=1)
        model_fit_df = rest_of_df[
            (rest_of_df.points != 0)
        ].copy()  # & (new_df.round_number != 1)]

        model = Ridge()
        ignore_cols = [
            "points",
            "player_name",
            "player_id",
            "round_number",
            "value",
            "was_home",
            "opposition_team_id",
            "threat",
            "creativity",
            "influence",
            "bps",
        ]
        X_train = model_fit_df.drop(ignore_cols, axis=1).copy()
        y_train = model_fit_df.points.copy()
        model.fit(X_train, y_train)
        # dump(model, "model.joblib")
        # model = load("model.joblib")
        preds = model.predict(rest_of_df.drop(ignore_cols, axis=1))
        rest_of_df["preds"] = preds
        new_df = pd.concat([rest_of_df, zero_preds])

        # sum up the points for this GW
        filtered = (
            new_df[new_df.round_number == self.current_gw][["player_id", "preds"]]
            .groupby("player_id")
            .sum()
            .reset_index()
        )

        output = dict(zip(filtered.player_id, filtered.preds))

        return output

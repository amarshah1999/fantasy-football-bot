from pulp import *

from config import max_players, max_players_per_team
from players import Player


class Optimiser:
    def __init__(self, player_dict, team, unlimited_transfers):
        self.player_dict = player_dict
        self.var_dict = {
            id_: LpVariable(str(id_), cat=LpBinary) for id_ in self.player_dict
        }

        self.previous_team_ids = [p.id for p in team.players if p.is_starting]
        self.budget = team.budget
        self.max_players = max_players
        self.pos_constraint_dict = team.pos_constraints_dict
        self.max_players_per_team = max_players_per_team
        self.num_transfers = team.num_transfers
        self.bench = [player_dict[p.id] for p in team.players if not p.is_starting]
        self.unlimited_transfers = unlimited_transfers or False

    def get_cost(self):
        return sum(
            self.player_dict[id].cost * self.var_dict[id]
            for id in self.player_dict.keys()
        )

    def get_num_players(self):
        return sum(x for x in self.var_dict.values())

    def get_num_pos(self, pos: str):
        return sum(
            x for k, x in self.var_dict.items() if self.player_dict[k].position == pos
        )

    def get_total_points(self, type="XP"):
        if type == "XP":
            return sum(
                self.player_dict[k].expected_points * x
                for k, x in self.var_dict.items()
            )
        # elif type == "XP_Rolling":
        #     return sum(
        #         (
        #             self.player_dict[k].get_xp_for_gw(self.gw)
        #             + 1 * self.player_dict[k].get_xp_for_gw(self.gw + 1)
        #         )
        #         * x
        #         for k, x in self.var_dict.items()
        #     )
        # return sum(
        #     self.player_dict[k].get_points_for_gw(self.gw) * x
        #     for k, x in self.var_dict.items()
        # )

    def get_num_players_for_team(self, team):
        return sum(
            x for k, x in self.var_dict.items() if self.player_dict[k].team == team
        )

    def get_team_similarity(self):
        return sum(self.var_dict.get(k, 0) for k in self.previous_team_ids)

    def create_model(self):
        # init problem
        self.model = LpProblem("TeamPicker", LpMaximize)

    def add_objective(self):
        # objective
        self.model += self.get_total_points(type="XP"), "total_points"

    def add_constraints(self):
        # constraints
        self.model += self.get_cost() <= self.budget
        self.model += self.get_num_players() == self.max_players
        for pos, bounds_dict in self.pos_constraint_dict.items():
            self.model += self.get_num_pos(pos) >= bounds_dict["min"]
            self.model += self.get_num_pos(pos) <= bounds_dict["max"]

        if not self.unlimited_transfers:
            self.model += (
                self.get_team_similarity() >= self.max_players - self.num_transfers
            )

        for team in sorted(set(x.team for x in self.player_dict.values())):
            self.model += self.get_num_players_for_team(
                team
            ) <= self.max_players_per_team - len(
                [p for p in self.bench if p.team == team]
            )

    def solve_model(self):
        # solve
        self.model.solve(PULP_CBC_CMD(msg=False))
        # print(LpStatus[model.status])

    def get_new_team(self) -> list[Player]:
        return [
            self.player_dict[k] for k, v in self.var_dict.items() if v.varValue == 1
        ]

    def create_and_solve_model(self):
        self.create_model()
        self.add_objective()
        self.add_constraints()
        self.solve_model()

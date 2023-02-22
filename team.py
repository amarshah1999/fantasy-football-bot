from optimiser import Optimiser
from players import Player
from team_status import TeamStatus


class Team:
    def __init__(self, player_dict, player_list, current_team: TeamStatus) -> None:
        self.players: list[Player] = player_list
        self.player_dict = player_dict

        self.budget = current_team.budget
        self.num_transfers = current_team.num_transfers
        self.pos_constraints_dict = current_team.pos_constraints_dict
        self.current_team = current_team

    # TODO Build this
    def build_initial_team(self) -> None:
        pass

    def build_team_for_gw(self) -> list[Player]:
        unlimited_transfers = (
            True if self.current_team.transfer_status == "unlimited" else False
        )
        opt = Optimiser(
            self.player_dict, team=self, unlimited_transfers=unlimited_transfers
        )
        opt.create_and_solve_model()
        new_team = opt.get_new_team()
        return new_team

    @property
    def total_cost(self):
        return sum(player.cost for player in self.players)

    @property
    def total_points(self):
        return sum(player.total_points for player in self.players)

    def get_team_points_for_gw(self, gw):
        return sum(player.get_points_for_gw(gw) for player in self.players)

    @property
    def get_team_as_ids(self):
        return [player.id for player in self.players]

    @property
    def formation(self):
        return {
            "GKS": sum(1 for player in self.players if player.position == "GK"),
            "DEFS": sum(1 for player in self.players if player.position == "DEF"),
            "MIDS": sum(1 for player in self.players if player.position == "MID"),
            "FWDS": sum(1 for player in self.players if player.position == "FWD"),
        }


# class TeamForGameWeek(Team):
#     def __init__(self, GameWeekTeamData):
#         super().__init__()
#         self.players=[player['element'] for player in GameWeekTeamData['picks']]

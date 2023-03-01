from dataclasses import dataclass
from collections import defaultdict
from config import pos_mapping


@dataclass
class GameWeekData:
    player_id: int
    round_number: int
    points: int
    goals_scored: int
    opposition_team_id: int
    was_home: bool
    value: int
    influence: float
    threat: float
    bps: float
    creativity: float
    minutes: int


class HistoricData:
    def __init__(self, player_id, player_round_history, live_gw):
        self.history: defaultdict[int, list[GameWeekData]] = defaultdict(list)
        for gameweek in player_round_history["history"]:
            round_number = gameweek["round"]
            points = gameweek["total_points"]
            goals_scored = gameweek["goals_scored"]
            opposition_team_id = gameweek["opponent_team"]
            was_home = gameweek["was_home"]
            value = gameweek["value"]
            influence = gameweek["influence"]
            threat = gameweek["threat"]
            bps = gameweek["bps"]
            creativity = gameweek["creativity"]
            minutes = gameweek["minutes"]

            self.history[round_number].append(
                GameWeekData(
                    player_id,
                    round_number,
                    points,
                    goals_scored,
                    opposition_team_id,
                    was_home,
                    value,
                    influence,
                    threat,
                    bps,
                    creativity,
                    minutes,
                )
            )
        # fill in the blank gameweeks
        for gameweek in range(1, live_gw + 1):
            if not self.history.get(gameweek):
                self.history[gameweek].append(
                    GameWeekData(
                        player_id, gameweek, 0, None, None, None, None, 0, 0, 0, 0, 0
                    )
                )


@dataclass
class Player:
    name: str
    id: int
    team: str
    position: str
    cost: int
    historic_data: HistoricData
    numeric_position: int | None = None
    expected_points: int = 0
    is_starting: bool = False
    selling_price: int = None

    def __repr__(self):
        return f"{self.name}"  # {self.position} COST: {self.cost} XP: {self.expected_points}"

    def __hash__(self):
        return hash(self.name)


def get_player_dict(player_data, player_historic, team_id_mapping, live_gw):
    player_dict = {}
    for data_dict in player_data:
        player_id = data_dict["id"]
        player_round_history = player_historic[player_id]
        player_dict[player_id] = Player(
            name=data_dict["first_name"] + " " + data_dict["second_name"],
            id=player_id,
            cost=data_dict["now_cost"],
            position=pos_mapping[data_dict["element_type"]],
            team=team_id_mapping[data_dict["team"]],
            historic_data=HistoricData(player_id, player_round_history, live_gw),
            expected_points=float(data_dict["ep_next"]),
        )
    return player_dict

import pickle

from api import API
from config import is_live, num_games, pos_mapping
from players import get_player_dict
from team import Team
from team_status import TeamStatus
from xp_model import XP_Model

if __name__ == "__main__":

    api = API()
    player_data = api.get_player_data()
    team_id_mapping = api.get_team_id_mapping()

    # with open('player_historic.pickle', 'rb') as file:
    #     player_historic = pickle.load(file)

    with open("player_dict.pickle", "rb") as file:
        player_dict = pickle.load(file)
    current_team = api.get_historic_team_for_gw(1)
    current_team = TeamStatus(current_team)

    player_list = []
    for player_api_data in current_team.picks:
        player_id = player_api_data["element"]
        player = player_dict[player_id]
        player.numeric_position = player_api_data["position"]
        player.is_starting = True if player.numeric_position < 12 else False
        player_dict[player_id] = player
        player_list.append(player)
    current_team.player_list = player_list

    def update_team_attributes(current_team: TeamStatus, wildcard: bool = False):
        bank = 1000 - sum(p.cost for p in current_team.player_list)
        budget = sum(
            player.cost for player in current_team.player_list if player.is_starting
        )
        num_transfers = 1  # TODO change this
        pos_constraints_dict = {}
        for position in pos_mapping.values():
            constraint_value = len(
                [
                    p
                    for p in current_team.player_list
                    if p.is_starting and p.position == position
                ]
            )
            pos_constraints_dict[position] = {
                "max": constraint_value,
                "min": constraint_value,
            }

        current_team.set_team_attributes_from_overrides(
            bank=bank,
            budget=budget,
            num_transfers=num_transfers,
            pos_constraints_dict=pos_constraints_dict,
            player_list=player_list,
            transfer_status="unlimited" if wildcard else None,
        )

    update_team_attributes(current_team)

    amar_total = 0
    fpl_bot_total = 0
    wildcard_week = 5
    for round_number in range(2, 22):
        update_team_attributes(current_team, wildcard_week == round_number)

        current_gw = round_number - 1
        amar_points = api.get_historic_team_for_gw(round_number)["entry_history"][
            "points"
        ]
        print(f"in gameweek {round_number} Amar scored : {amar_points}")
        amar_total += amar_points
        active_players = player_dict.copy()
        # Update player with any changed attributes
        for player in player_dict.values():
            hist_data = player.historic_data.history.get(current_gw)

            if hist_data and hist_data.value:
                player.cost = player.selling_price = hist_data.value  # this is wrong

        model = XP_Model(active_players, round_number - 1, team_id_mapping)

        xp_dict1 = model.get_xp()

        for player_id in active_players:
            player_dict[player_id].expected_points = xp_dict1[player_id]

        t1 = Team(player_dict, player_list=player_list, current_team=current_team)
        new_team = t1.build_team_for_gw()

        players_out = sorted(
            set(p for p in t1.players if p.is_starting) - set(p for p in new_team),
            key=lambda p: p.position,
        )
        players_in = sorted(
            set(p for p in new_team) - set(p for p in player_list),
            key=lambda p: p.position,
        )
        for p_out, p_in in zip(players_out, players_in):
            # print("OUT: ", p_out, p_out.expected_points, "IN: ", p_in, p_in.expected_points)
            player_dict[p_in.id].is_starting = True
            current_team.player_list.remove(player_dict[p_out.id])
            current_team.player_list.append(player_dict[p_in.id])
            p_in.numeric_position = p_out.numeric_position
        # new_players_as_ids = [p.id for p in current_team.player_list if p.is_starting]
        captain_id = max(
            [p for p in current_team.player_list if p.is_starting],
            key=lambda p: p.expected_points,
        ).id

        # logic to calculate the points we would have scored in that week
        def check_player_satisfies_position_constraints(
            player, team, pos_constraints_dict
        ):
            pos = player.position
            return (
                pos_constraints_dict[pos]["max"]
                - len([p for p in team if p.position == pos])
                > 0
            )

        bot_points = 0
        players_counted = []
        for player in sorted(
            current_team.player_list, key=lambda p: p.numeric_position
        ):
            gameweek_data = player.historic_data.history[round_number]
            if gameweek_data.minutes > 0 & check_player_satisfies_position_constraints(
                player, players_counted, current_team.pos_constraints_dict
            ):
                players_counted.append(player)
                bot_points += gameweek_data.points
                if player.id == captain_id:
                    bot_points += gameweek_data.points
            if len(players_counted) > 10:
                break

        print(
            f"in gameweek {round_number} FPLBot scores with captain {player_dict[captain_id]}: {bot_points}"
        )
        fpl_bot_total += bot_points
        # print(
        #     f"Team for gameweek {round_number} , {sorted([(p.name, p.cost, p.numeric_position, p.historic_data.history[round_number].points) for p in current_team.player_list], key = lambda p: p[2])}"
        # )
    print(fpl_bot_total, amar_total)

import pickle

from api import API
from players import get_player_dict
from team import Team
from team_status import TeamStatus
from xp_model import XP_Model

if __name__ == "__main__":
    api = API()
    current_gw = api.current_gw  # 1 less than the gw we are planning for
    player_data = api.get_player_data()

    team_id_mapping = api.get_team_id_mapping()
    # player_historic = api.load_player_historic([player["id"] for player in player_data])
    # with open("player_historic.pickle", "rb") as file:
    #     player_historic = pickle.load(file)

    # player_dict = get_player_dict(
    #     player_data, player_historic, team_id_mapping, current_gw
    # )
    # with open("player_dict.pickle", "wb") as file:
    #     pickle.dump(player_dict, file)

    with open("player_dict.pickle", "rb") as file:
        player_dict = pickle.load(file)

    # model.get_xp()

    # xp_dict = model.build_data()
    # for player_id in player_dict:
    #     player_dict[player_id].expected_points = xp_dict[player_id]
    api.login()

    current_team = TeamStatus(api.get_current_team())
    # updates player dict with actual values like selling price
    current_team.update_player_dict(player_dict)
    current_team.set_team_attributes_from_live_data()
    player_list = current_team.player_list
    model = XP_Model(player_dict, current_gw, team_id_mapping)
    xp_dict1 = model.get_xp()
    # if player_id not in xp_dict will just fallback to FPL provided value
    for player_id in xp_dict1:
        player_dict[player_id].expected_points = xp_dict1[player_id]

    t1 = Team(player_dict, player_list=player_list, current_team=current_team)
    new_team = t1.build_team_for_gw()

    players_out = sorted(
        set(p for p in t1.players if p.is_starting) - set(p for p in new_team),
        key=lambda p: p.position,
    )
    players_in = sorted(
        set(p for p in new_team) - set(p for p in player_list), key=lambda p: p.position
    )
    for p_out, p_in in zip(players_out, players_in):
        print("OUT: ", p_out, p_out.expected_points, "IN: ", p_in, p_in.expected_points)
    breakpoint()
    print(sum([p.expected_points for p in new_team]))
    print(sum([p.expected_points for p in t1.players if p.is_starting]))

    transfer_payload = api.create_transfer_payload(list(players_out), list(players_in))
    print(transfer_payload)
    # if is_live:
    #     api.make_transfer(transfer_payload)

    # print("Building team")
    # # t1.build_initial_team()
    # total_score = 0
    # team_history = {0: None}
    # for i in range(1, num_games + 1):
    #     t1.build_team_for_gw(gw=i, previous_team_ids=team_history[i - 1])
    #     team_history[i] = t1.get_team_as_ids
    #     total_score += t1.get_team_points_for_gw(i)
    #     if i == 1:
    #         print(t1.players)
    #     # else:
    #     #     added_player = player_dict[list(set(team_history[i])-set(team_history[i-1]))[0]]
    #     #     removed_player = player_dict[list(set(team_history[i-1])-set(team_history[i]))[0]]
    #     #     print(f'IN {added_player.name} {added_player.gw_data[i]["points"]} OUT {removed_player.name} {removed_player.gw_data[i]["points"]}')
    #     #     print(t1.total_cost)
    #     # print(t1.formation)
    # print("TOTAL: ", total_score)

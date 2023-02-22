from pathlib import Path

ROOT_DIRECTORY = Path.cwd()  # .parent
season = "2022-23"
num_games = 6
gw_data_path = ROOT_DIRECTORY / "data" / season / "gws" / "merged_gw.csv"
id_dict_path = ROOT_DIRECTORY / "data" / season / "id_dict.csv"
individual_player_folders_path = ROOT_DIRECTORY / "data" / season / "players"


max_players = 11

max_players_per_team = 3

pos_mapping = {
    1: "GK",
    2: "DEF",
    3: "MID",
    4: "FWD",
}
is_live = False

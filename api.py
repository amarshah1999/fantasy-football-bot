import getpass
import json
import os
import time

import requests
from dotenv import load_dotenv


class API:
    # methods mostly from https://github.com/vaastav/Fantasy-Premier-League
    # and https://github.com/amosbastian/fpl
    def __init__(self):
        self.session = requests.Session()
        load_dotenv()
        self.username = os.getenv("USERNAME")
        self.team_id = os.getenv("TEAM_ID")
        self.load_base_data()

    def login(self):
        self.password = getpass.getpass()
        headers = {
            "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 5.1; PRO 5 Build/LMY47D)"
        }

        data = {
            "password": self.password,
            "login": self.username,
            "app": "plfpl-web",
            "redirect_uri": "https://fantasy.premierleague.com/",
        }

        url = "https://users.premierleague.com/accounts/login/"

        self.session.post(url, data=data, headers=headers)

    def get_current_team(self):
        team_url = f"https://fantasy.premierleague.com/api/my-team/{self.team_id}/"
        res = self.session.get(team_url)
        return json.loads(res.content)

    def get_historic_team_for_gw(self, gw: int):
        team_url = f"https://fantasy.premierleague.com/api/entry/{self.team_id}/event/{gw}/picks/"
        res = self.session.get(team_url)
        return json.loads(res.content)

    def load_base_data(self):
        """Retrieve the fpl player data from the hard-coded url"""
        response = requests.get(
            "https://fantasy.premierleague.com/api/bootstrap-static/"
        )
        if response.status_code != 200:
            raise Exception("Response was code " + str(response.status_code))
        response_as_str = response.text
        self.data_dict = json.loads(response_as_str)
        self.current_gw = int(
            [x["id"] for x in self.data_dict["events"] if x["is_current"]][0]
        )

    def get_individual_player_data(self, player_id):
        """Retrieve the player-specific detailed data
        Args:
            player_id (int): ID of the player whose data is to be retrieved
        """
        base_url = "https://fantasy.premierleague.com/api/element-summary/"
        full_url = base_url + str(player_id) + "/"
        response = ""
        while response == "":
            try:
                response = requests.get(full_url)
            except:
                time.sleep(5)
        if response.status_code != 200:
            raise Exception("Response was code " + str(response.status_code))
        data = json.loads(response.text)
        return data

    def load_player_historic(self, list_of_player_ids: list[int]):
        player_historic_dict = {}

        for id in list_of_player_ids:
            player_historic_dict[id] = self.get_individual_player_data(id)

        return player_historic_dict

    def get_base_data(self):
        return self.data_dict

    def get_player_data(self):
        return self.data_dict["elements"]

    def get_team_id_mapping(self):
        team_data = self.data_dict["teams"]
        return {team["id"]: team["name"] for team in team_data}

    def create_transfer_payload(self, players_out, players_in):
        # credit to https://github.com/amosbastian/fpl/ for figuring this out
        transfer_payload = {
            "confirmed": False,
            "entry": int(self.team_id),
            "event": self.current_gw + 1,
            "transfers": [],
            "wildcard": False,  # TODO add chip features
            "freehit": False,
        }

        for player_out, player_in in zip(players_out, players_in):
            transfer_payload["transfers"].append(
                {
                    "element_in": player_in.id,
                    "element_out": player_out.id,
                    "purchase_price": player_in.cost,
                    "selling_price": player_out.selling_price,
                }
            )

        return transfer_payload

    def make_transfer(self, transfer_payload):
        response = self.session.post(
            "https://fantasy.premierleague.com/api/transfers/",
            json.dumps(transfer_payload),
            headers={
                "Content-Type": "application/json; charset=UTF-8",
                "X-Requested-With": "XMLHttpRequest",
                "Referer": "https://fantasy.premierleague.com/a/squad/transfers",
            },
        )

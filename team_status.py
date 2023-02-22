from config import pos_mapping


class TeamStatus:
    def __init__(self, current_team) -> None:
        self.current_team = current_team
        self.picks = self.current_team["picks"]

    def update_player_dict(self, player_dict):
        self.player_list = []
        # Modify the player_dict player objects for players in my current starting XI
        for player_api_data in self.picks:
            player_id = player_api_data["element"]
            player = player_dict[player_id]
            player.numeric_position = player_api_data["position"]
            player.is_starting = True if player.numeric_position < 12 else False

            player.selling_price = player_api_data["selling_price"]
            player.cost = player_api_data[
                "selling_price"
            ]  # This is because the cost of buying a player we already own is just his selling price
            self.player_list.append(player)

    def set_team_attributes_from_live_data(self):
        self.bank = self.current_team["transfers"]["bank"]
        self.budget = self.bank + sum(
            [p.selling_price for p in self.player_list if p.is_starting]
        )
        self.num_transfers = (
            self.current_team["transfers"]["limit"]
            - self.current_team["transfers"]["made"]
        )  # not sure if this is correct
        self.pos_constraints_dict = {}
        for position in pos_mapping.values():
            constraint_value = len(
                [
                    p.selling_price
                    for p in self.player_list
                    if p.is_starting and p.position == position
                ]
            )
            self.pos_constraints_dict[position] = {
                "max": constraint_value,
                "min": constraint_value,
            }
        self.transfer_status = self.current_team["transfers"]["status"]

    def set_team_attributes_from_overrides(
        self,
        bank=None,
        budget=None,
        num_transfers=None,
        pos_constraints_dict=None,
        transfer_status=None,
        player_list=None,
    ):
        self.bank = bank
        self.budget = budget
        self.num_transfers = num_transfers
        self.pos_constraints_dict = pos_constraints_dict
        self.transfer_status = transfer_status
        if player_list:
            self.player_list = player_list

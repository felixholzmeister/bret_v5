from . import *


class PlayerBot(Bot):

    cases = ['always_bomb', 'never_bomb']

    def play_round(self):
        if INSTRUCTIONS and self.player.round_number == 1:
            yield Instructions
        boxes_collected = 2
        yield (
            Game,
            dict(
                bomb_row=1,
                bomb_col=1,
                boxes_collected=boxes_collected,
                bomb=1 if self.case == 'always_bomb' else 0,
            ),
        )
        expected_round_result = (
            0 if self.case == 'always_bomb' else BOX_VALUE * boxes_collected
        )
        expect(self.player.round_result, expected_round_result)
        if RESULTS and self.player.round_number == NUM_ROUNDS:
            # 1 round is chosen randomly
            expect(self.participant.bret_payoff, expected_round_result)
            yield Results

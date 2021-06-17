import random

from otree.api import *

from . import config
from .config import *
from settings import LANGUAGE_CODE

if LANGUAGE_CODE == 'de':
    from .lexicon_de import Lexicon
else:
    from .lexicon_en import Lexicon

author = 'Felix Holzmeister & Armin Pfurtscheller'
doc = """
Bomb Risk Elicitation Task (BRET) à la Crosetto/Filippin (2013), Journal of Risk and Uncertainty (47): 31-65.
"""

which_language = {'en': False, 'de': False}  # noqa
which_language[LANGUAGE_CODE] = True

BOX_VALUE = cu(BOX_VALUE)


def dict_from_module(module):
    context = {}
    for setting in dir(module):
        # you can write your filter here
        if not setting.startswith('_') and setting.isupper():
            context[setting] = getattr(module, setting)

    return context


config_dict = dict_from_module(config)


class Constants(BaseConstants):
    name_in_url = 'bret'
    num_rounds = config.NUM_ROUNDS
    players_per_group = None
    results_1_round_template = __name__ + '/results_1_round.html'
    results_multi_round_template = __name__ + '/results_multi_round.html'
    instructions_template = __name__ + '/instructions.html'


class Subsession(BaseSubsession):
    pass


class Group(BaseGroup):
    pass


class Player(BasePlayer):
    # whether bomb is collected or not
    # store as integer because it's easier for interop with JS
    bomb = models.IntegerField()
    bomb_row = models.IntegerField()
    bomb_col = models.IntegerField()
    boxes_collected = models.IntegerField()
    pay_this_round = models.BooleanField()
    round_result = models.CurrencyField()


# FUNCTIONS
def set_payoff(player: Player):
    participant = player.participant
    round_number = player.round_number

    # determine round_result as (potential) payoff per round
    if player.bomb:
        player.round_result = cu(0)
    else:
        player.round_result = player.boxes_collected * BOX_VALUE
    if round_number == 1:
        participant.vars['round_to_pay'] = random.randint(1, NUM_ROUNDS)
    if RANDOM_PAYOFF:
        if round_number == participant.vars['round_to_pay']:
            player.pay_this_round = True
            player.payoff = player.round_result
        else:
            player.pay_this_round = False
            player.payoff = cu(0)
    else:
        player.payoff = player.round_result


class Instructions(Page):
    @staticmethod
    def is_displayed(player: Player):
        return INSTRUCTIONS and player.round_number == 1

    @staticmethod
    def vars_for_template(player: Player):
        return dict(
            num_boxes=NUM_ROWS * NUM_COLS,
            num_nobomb=NUM_ROWS * NUM_COLS - 1,
            Lexicon=Lexicon,
            **which_language,
            **config_dict,
        )


class Game(Page):
    # form fields on player level
    form_model = 'player'
    form_fields = [
        'bomb',
        'boxes_collected',
        'bomb_row',
        'bomb_col',
    ]

    @staticmethod
    def vars_for_template(player: Player):
        return dict(Lexicon=Lexicon, num_boxes=NUM_ROWS * NUM_COLS, **which_language)

    @staticmethod
    def js_vars(player: Player):
        participant = player.participant
        reset = participant.vars.pop('reset', False)
        if DYNAMIC:
            input = False
        else:
            input = not DEVILS_GAME
        return dict(reset=reset, input=input, **config_dict)

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        player.participant.vars['reset'] = True
        set_payoff(player)


class Results(Page):
    @staticmethod
    def is_displayed(player: Player):
        return RESULTS and player.round_number == NUM_ROUNDS

    @staticmethod
    def vars_for_template(player: Player):
        participant = player.participant
        total_payoff = sum([p.payoff for p in player.in_all_rounds()])
        participant.vars['bret_payoff'] = total_payoff
        return dict(
            player_in_all_rounds=player.in_all_rounds(),
            box_value=BOX_VALUE,
            boxes_total=NUM_ROWS * NUM_COLS,
            boxes_collected=player.boxes_collected,
            bomb=player.bomb,
            bomb_row=player.bomb_row,
            bomb_col=player.bomb_col,
            round_result=player.round_result,
            round_to_pay=participant.vars['round_to_pay'],
            payoff=player.payoff,
            total_payoff=total_payoff,
            Lexicon=Lexicon,
            **config_dict,
            **which_language,
        )


page_sequence = [Instructions, Game, Results]

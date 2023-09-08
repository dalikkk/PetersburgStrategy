import sys
import json

USERNAME = 'ddd'
PASSWORD = 'd'
HOST = 'http://localhost:5000'
PLAY_ENDPOINT = '/game/api/'
STATUS_ENDPOINT = '/game/api/session/'
SESSION = '16'

# interface with server
ARGS = None
SESSION_DATA = None
CARDLIST = None


"""
Function that sends move to server.
"""
def play(args):
    print(args)
    global ARGS
    ARGS = args

"""
Simple strategy that you should beat easily. You can use it as a template or
for testing.
"""

def strategy(session_data):
    if session_data['actual_phase'] == "worker":
        buy_cheapest(session_data, 'worker')
    elif session_data['actual_phase'] == "upgrade":
        play({
            'action': 'pass'
        })
    else:
        buy_most_expensive(session_data, session_data['actual_phase'])


def buy_cheapest(session_data, phase):
    cheapest_card = None
    actual_player = actual_player_info(session_data)
    for card in session_data['board']:
        if card['card_type'] == phase:
            if (cheapest_card is None or
                cheapest_card['price'] > card['price'])\
               and card['price'] <= actual_player['money']:
                cheapest_card = card
    if cheapest_card is not None:
        play({
            'action': 'buy',
            'card_id': cheapest_card['id']
        })
    else:
        play({
            'action': 'pass'
        })

def buy_most_expensive(session_data, phase):
    most_expensive_card = None
    actual_player = actual_player_info(session_data)
    for card in session_data['board']:
        if card['card_type'] == phase:
            if (most_expensive_card is None or
                most_expensive_card['price'] < card['price'])\
               and card['price'] <= actual_player['money']:
                most_expensive_card = card
    if most_expensive_card is not None:
        play({
            'action': 'buy',
            'card_id': most_expensive_card['id']
        })
    else:
        play({
            'action': 'pass'
        })


def actual_player_info(session_data):
    actual_player = None
    for player in session_data['players']:
        if player['actual_player']:
            return player
    return None

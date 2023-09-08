import requests
import sys
import json


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
Simple strategy that you should beat quite easily. Has cash reserve for aristocrats.
"""

def strategy(session_data):
    if session_data['actual_phase'] == "worker":
        buy_cheapest(session_data, 'worker')
    elif session_data['actual_phase'] == "upgrade":
        play({
            'action': 'pass'
        })
    elif session_data['actual_phase'] == "building":
        if cards_remaining(session_data) >= 18:
            # save money for aristocrats/workers
            play({'action': 'pass'})
        elif cards_remaining(session_data) >= 14:
            buy_most_expensive(
                session_data,
                session_data['actual_phase'],
                limit = actual_player_info(session_data)['money'] - 18
            )
        else:
           buy_most_expensive(session_data, session_data['actual_phase']) 
    else:
        buy_most_expensive(session_data, session_data['actual_phase'])


def buy_cheapest(session_data, phase, limit = None):
    actual_player = actual_player_info(session_data)
    if limit is None:
        limit = actual_player['money']
    assert limit <= actual_player['money']

    cheapest_card = None

    for card in session_data['board']:
        if card['card_type'] == phase:
            if (cheapest_card is None or
                cheapest_card['price'] > card['price'])\
               and card['price'] <= limit:
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

def buy_most_expensive(session_data, phase, limit = None, filter_useless=True):
    actual_player = actual_player_info(session_data)

    if limit is None:
        limit = actual_player['money']
    assert limit <= actual_player['money']
    most_expensive_card = None

    for card in session_data['board']:
        if card['card_type'] == phase:
            if (most_expensive_card is None or
                most_expensive_card['price'] < card['price'])\
               and card['price'] <= limit:
                if not filter_useless \
                   or card['money_income'] > 0 \
                   or card['point_income'] > 0:
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


def cards_remaining(session_data):
    """
    Function to determine stage of the game
    """
    
    workers = session_data['worker_count']
    buildings = session_data['building_count']
    aristocrats = session_data['aristocrat_count']
    upgrade = session_data['upgrade_count']

    if session_data['actual_phase'] == 'worker':
        buildings -= 8 - len(session_data['board'])
    elif session_data['actual_phase'] == 'building':
        aristocrats -= 8 - len(session_data['board'])
    elif session_data['actual_phase'] == 'aristocrat':
        upgrade -= 8 - len(session_data['board'])

    return min(workers, buildings, aristocrats, upgrade)

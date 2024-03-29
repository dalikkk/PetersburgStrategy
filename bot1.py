import requests
import sys
import json

# these are assigned for test user
# feel free to create your own user (wia web interface)
USERNAME = 'dd'
PASSWORD = 'd'

HOST = 'http://localhost:5000'
PLAY_ENDPOINT = '/game/api/'
STATUS_ENDPOINT = '/game/api/session/'
SESSION = '10'


"""
Function that sends move to server.
"""
def play(args):
    print(args)
    args['name'] = USERNAME
    args['password'] = PASSWORD
    
    resp = requests.post(
        HOST + PLAY_ENDPOINT + SESSION,
        data=args,
    )

    if resp.status_code != 200:
        print(resp, file=sys.stderr)
        print(resp.json())
        #exit(1)
    if resp.json().get('error'):
        print(resp.json()["error"], file=sys.stderr)
        #exit(1)

def get_session_data(session_id=SESSION):
    resp = requests.get(HOST + STATUS_ENDPOINT + session_id)
    if resp.status_code != 200:
        print(resp.json()["error"], file=sys.stderr)
        exit(1)
    return resp.json()


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

from time import sleep
import requests
import sys
import threading
import importlib.util

HOST = 'http://localhost:5000'
CREATE_GAME_ENDPOINT = '/api/game/new/'

import bot1 as bot
#BOTS = ['bot1', 'bot2', 'bot3', 'bot4', 'bot5', 'bot6']
OPPONENT_BOT = ['bot1']


def play(bot):
    while True:
        session_data = bot.get_session_data(bot.SESSION)
        player = bot.actual_player_info(session_data)
        if player is None:
            break
        if player['name'] == bot.USERNAME:
            print('turn', bot.USERNAME)
            bot.strategy(session_data)
        print('sleep', bot.USERNAME)
        sleep(0.1)


def create_game():
    resp = requests.get(HOST + CREATE_GAME_ENDPOINT,
                        params={
                            'player1': bot.USERNAME,
                            'player2': OPPONENT_BOT}
                        )
    if resp.status_code != 200:
        print(resp.json()["error"], file=sys.stderr)
        exit(1)
    if resp.json().get('error'):
        print(resp.json()['error'], file=sys.stderr)
    return resp.json()['session']

def main():
    session = create_game()
    bot.SESSION = str(session)
    play(bot)

    session_data = bot.get_session_data(session)
    my_points = session_data['players'][0]['points']
    opponent_points = session_data['players'][1]['points']
    if my_points < opponent_points:
        print("you lose")
    elif my_points == opponent_points:
        print("you draw")
    else:
        print("you win")


if __name__ == '__main__':
    main()

        

        



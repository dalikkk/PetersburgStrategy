from time import sleep
import requests
import sys
import threading
import importlib.util

HOST = 'http://localhost:5000'
CREATE_GAME_ENDPOINT = '/api/game/new/'

BOTS = ['bot1', 'bot2', 'bot3', 'bot4', 'bot5', 'bot6']


def play(bot):
    while True:
        session_data = bot.get_session_data()
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
                        params={'player1': 'dd', 'player2': 'ddd'}
                        )
    if resp.status_code != 200:
        print(resp.json()["error"], file=sys.stderr)
        exit(1)
    if resp.json().get('error'):
        print(resp.json()['error'], file=sys.stderr)
    return resp.json()['session']



sessions = []

for i in range(len(BOTS)):
    session_row = []
    for j in range(i + 1, len(BOTS)):
        session = create_game()
        session_row.append(session)
        P1_SPEC = importlib.util.find_spec(BOTS[i])
        P2_SPEC = importlib.util.find_spec(BOTS[j])
        p1 = importlib.util.module_from_spec(P1_SPEC)
        p2 = importlib.util.module_from_spec(P2_SPEC)
        P1_SPEC.loader.exec_module(p1)
        P2_SPEC.loader.exec_module(p2)

        # just in case you would need also to list in modules
        # sys.modules['p1'] = p1
        del P1_SPEC
        del P2_SPEC

        p1.SESSION = str(session)
        p2.SESSION = str(session)
        p1.USERNAME = 'dd'
        p2.USERNAME = 'ddd'
        # they share predefined password 'd'

        jobs = []
        t1 = threading.Thread(target=lambda:play(p1))
        jobs.append(t1)
        t2 = threading.Thread(target=lambda:play(p2))
        jobs.append(t2)

        for j in jobs:
            j.start()
        for j in jobs:
            j.join()

        print('================== Game', session, 'finished =================')
    sessions.append(session_row)



    

        

        



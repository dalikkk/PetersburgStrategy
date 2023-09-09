import requests

HOST = 'http://localhost:5000'
CREATE_GAME_ENDPOINT = '/api/game/new/'
STATUS_ENDPOINT = '/game/api/session/'

BOTS = ['bot1', 'bot2', 'bot3', 'bot4', 'bot5', 'bot6']

matrix = []

for i in range(6):
    m = []
    for j in range(6):
        m.append(0)
    matrix.append(m)

def main():
    sessions = []
    for i in range(len(BOTS)):
        for j in range(i + 1, len(BOTS)):
            for k in range(10):
                session = create_game(BOTS[i], BOTS[j])
                session_data = get_session_data(session)
                print(i + 1, j + 1,
                    session_data['players'][0]['points'] < \
                    session_data['players'][1]['points']
                )
                if session_data['players'][0]['points'] < \
                    session_data['players'][1]['points']:
                    matrix[i][j] += 1
    for row in matrix:
        print(row)

def get_session_data(session_id):
    resp = requests.get(HOST + STATUS_ENDPOINT + str(session_id))
    if resp.status_code != 200:
        print(resp.json()["error"], file=sys.stderr)
        exit(1)
    return resp.json()


def create_game(p1='dd', p2='ddd'):
    resp = requests.get(HOST + CREATE_GAME_ENDPOINT,
                        params={'player1': p1, 'player2': p2}
                        )
    if resp.status_code != 200:
        print(resp.json()["error"], file=sys.stderr)
        exit(1)
    if resp.json().get('error'):
        print(resp.json()['error'], file=sys.stderr)
    return resp.json()['session']

if __name__ == "__main__":
    main()




    

        

        



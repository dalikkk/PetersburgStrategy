import requests
import sys
import json

USERNAME = 'ddd'
PASSWORD = 'd'
HOST = 'http://localhost:5000'
PLAY_ENDPOINT = '/game/api/'
STATUS_ENDPOINT = '/game/api/session/'
CARDLIST_ENDPOINT = '/api/cardlist/'
SESSION = '28'

# interface with server
ARGS = None
SESSION_DATA = None
CARDLIST = None


"""
Function that sends move to server.
"""
def play(args):
    global ARGS
    ARGS = args


"""
Little advanced strategy. With simpler implementation.
"""

def strategy(session_data):
    if session_data['actual_phase'] == "worker":
        if worker_buy(session_data, session_data['board']):
            return
        if worker_buy(session_data, actual_player_info(session_data)['hand']):
            return
        play({"action": "pass"})
    elif session_data['actual_phase'] == "building":
        if upgrade_buy(session_data, session_data['board']):
            return
        if upgrade_buy(session_data, actual_player_info(session_data)['hand']):
            return
        if cards_remaining(session_data) >= 18:
            # save money for aristocrats/workers
            play({'action': 'pass'})
            return
        elif cards_remaining(session_data) >= 14:
            if buy_most_expensive(
                session_data,
                session_data['actual_phase'],
                limit = actual_player_info(session_data)['money'] - 18
            ):
                return
        elif buy_most_expensive(session_data, session_data['actual_phase']):
            return

        play({
            'action': 'pass'
        })
    elif session_data['actual_phase'] == "aristocrat":
        if buy_most_expensive(session_data, session_data['actual_phase']):
            return
        if upgrade_buy(session_data, session_data['board']):
            return
        if upgrade_buy(session_data, actual_player_info(session_data)['hand']):
            return
        play({
            'action': 'pass'
        })
    elif session_data['actual_phase'] == "upgrade":
        actual_player = actual_player_info(session_data)
        if cards_remaining(session_data) == 0:
            play({
                'action': 'pass'
            })
            return
        elif len(actual_player['hand']) < 3 and upgrade_hold(session_data):
            return
        else:
            play({
                'action': 'pass'
            })
    else:
        print("Unknown phase:",
              session_data['actual_phase'],
              file=sys.stderr
        )

def worker_buy(session_data, card_options, hold=False):
    actual_player = actual_player_info(session_data)
    cheapest_card = None
    for card in card_options:
        if card['card_type'] == 'worker':
            discounted_price, upgrade_actual_from = discounted_card_price(session_data, card, hold)
            if cheapest_card is not None:
                discounted_cheapest_price, _ = discounted_card_price(session_data, cheapest_card, hold)
            if (cheapest_card is None or
                discounted_price < discounted_cheapest_price)\
                and (
                   (hold and len(actual_player['hand']) < 3)
                   or
                   (not hold and discounted_price <= actual_player['money'])
                ):
                cheapest_card = card
                upgrade_from = upgrade_actual_from
    if cheapest_card is not None:
        args = {'action': 'buy', 'card_id': cheapest_card['id']}
        if hold:
            args['action'] = 'hold'
    
        if cheapest_card['card_type'] == 'upgrade':
            # find card from upgrade
            args['upgrade_from'] = upgrade_from['id']
        discounted_price, _ = discounted_card_price(session_data, cheapest_card)
        
        cards_rem = cards_remaining(session_data)
        if hold:
            # one turn less
            cards_rem -= 3

        if session_data['board'] == card_options:
            # need to buy anyway even if not bargain
            play(args)
            return True
        
        if cards_rem >= 8 or cheapest_card['card_type'] == 'upgrade':
            play(args)
            return True
        elif cards_rem >= 6 and cheapest_card['name'] != 'Czar and carpenter':
            play(args)
            return True
        elif cards_rem >= 2 and discounted_price < 6:
            play(args)
            return True
        elif discounted_price <= 3:
            play(args)
            return True
    return False


def upgrade_buy(session_data, card_options):
    actual_player = actual_player_info(session_data)
    if session_data['actual_phase'] in ['building', 'aristocrat']:
        # find cheapest building to replace
        for upgrade in card_options:
            if upgrade['card_type'] != 'upgrade' \
               or upgrade['upgrade_type'] != session_data['actual_phase']:
                continue
            discounted_price = upgrade['price']
            if upgrade['discounted']:
                discounted_price -= 1
            cheapest_building = None
            for buil_ar in actual_player['board']:
                if buil_ar['card_type'] != session_data['actual_phase']:
                    continue
                if buil_ar['price'] > upgrade['price']:
                    continue
                upgrade_cost = discounted_price - buil_ar['price']
                if upgrade_cost < 1:
                    upgrade_cost = 1
                if upgrade_cost < actual_player['money']:
                    play({
                        'action': 'buy',
                        'card_id': upgrade['id'],
                        'upgrade_from': buil_ar['id']
                    })
                    return True
    return False

def upgrade_hold(session_data):
    cheapest_upgrade = None
    actual_player = actual_player_info(session_data)
    if len(actual_player['board']) == 3:
        return False
    for upgrade in session_data['board']:
        if upgrade['card_type'] != 'upgrade':
            continue
        if upgrade['upgrade_type'] != 'aristocrat':
            continue
        if cheapest_upgrade is None:
            cheapest_upgrade = upgrade
        elif cheapest_upgrade['price'] > upgrade['price']:
            cheapest_upgrade = upgrade
    if cheapest_upgrade is not None:
        play({'action': 'hold', 'card_id': cheapest_upgrade['id']})
        return True

    # again for non aristocrat upgrades
    for upgrade in session_data['board']:
        if upgrade['card_type'] != 'upgrade':
            continue
        if cheapest_upgrade is None:
            cheapest_upgrade = upgrade
        elif cheapest_upgrade['price'] > upgrade['price']:
            cheapest_upgrade = upgrade

    if cheapest_upgrade is not None:
        play({'action': 'hold', 'card_id': cheapest_upgrade['id']})
        return True
    return False
        


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
    actual_player = actual_player_info(session_data)
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
        return True
    else:
        return False


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

def discounted_card_price(session_data,
                          card,
                          consider_hold = False, # second round where there is not enough money
                          check_compatibility = True, # third round if compatible worker not found
                          cardlist = None
                          ):
    """
    Discounts card price of card.
    For worker upgrade return discount from upgraded card (of same type).
    Not defined for other upgrades.
    """
    if cardlist is None:
        cardlist = CARDLIST
    price = card['price']
    actual_player = actual_player_info(session_data)
    upgrade_from = None
    upgrade_discount = None
    for board_card in actual_player['board']:
        if card['name'] == board_card['name'] and not consider_hold:
            price -= 1

    if card['card_type'] == 'upgrade':
        # discount by card type
        if card['upgrade_type'] == 'worker':
            if card['price'] < 8:
                # try firstly direct upgrade then consider czar and carpenter
                for board_card in actual_player['board']:
                    if board_card.get('upgrade_limitation') == card['name']:
                        upgrade_discount = board_card['price']
                        upgrade_from = board_card
                        break
                # if price is high or board does not have an upgrade consider czar and carpenter
                discounted_price = None
                if upgrade_discount is not None:
                    discounted_price = price - upgrade_discount
                    if discounted_price < 1:
                        discounted_price = 1
                if upgrade_discount is None or discounted_price > actual_player['money']:
                    for board_card in actual_player['board']:
                        if board_cardcard['name'] == 'Czar and carpenter':
                            upgrade_discount = board_card['price'] # 8
                            upgrade_from = board_card
                            break
            else:
                # try firstly czar and carpenter then other card
                # here is buy and hold preference the same
                for board_card in actual_player['board']:
                    if board_card['name'] == 'Czar and carpenter':
                        upgrade_discount = board_card['price'] # 8
                        upgrade_from = board_card
                        break

                if upgrade_discount is None:
                    for board_card in actual_player['board']:
                        if board_card.get('upgrade_limitation') == card['name']:
                            upgrade_discount = board_card['price']
                            upgrade_from = board_card
                            break
                
            if upgrade_discount is None and consider_hold:
                # second round of strategy when holding cards no need to have worker card on board
                for card_prototype in cardlist:
                    # only direct upgrade, not czar and carpenter
                    if card_prototype.get('upgrade_limitation') == card['name']:
                        upgrade_discount = card_prototype['price']
                        # upgrade from is irelevant -> we are holding upgrade

    if upgrade_discount is not None:
        price -= upgrade_discount

    if price < 1:
        price = 1
    return price, upgrade_from

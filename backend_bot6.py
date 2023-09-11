import requests
import sys
import json
from collections import Counter

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
Simple strategy that you should beat easily. You can use it as a template or
for testing.
"""

def strategy(session_data):
    if session_data['actual_phase'] == "worker":
        worker_strategy(session_data)
    elif session_data['actual_phase'] == "building":
        building_strategy(session_data)
    elif session_data['actual_phase'] == "aristocrat":
        aristocrat_strategy(session_data)
    elif session_data['actual_phase'] == "upgrade":
        upgrade_strategy(session_data)
    else:
        print("No such phase found", file=sys.stderr)


def worker_strategy(session_data):
    # based on buy cheapest strategy but consider upgrades
    actual_player = actual_player_info(session_data)
    cards_rem = cards_remaining(session_data)
    upgrade_from = None

    # first round buy from row
    if worker_buy(session_data, session_data['board']):
        return

    # cannot buy from board and hand is full
    if len(actual_player['hand']) == 3:
        if worker_buy(session_data, actual_player['hand']):
            return

    # try hold card to protect point loss
    if cards_rem <= 3 and len(actual_player):
        # try fix upgrades in hand
        for upgrade in actual_player['hand']:
            if upgrade['card_type'] != 'upgrade' or upgrade['upgrade_type'] != 'worker':
                continue
            ok_upgrade = False
            for card in actual_player['hand'] + actual_player['board']:
                if card['card_type'] == 'worker':
                    if card.get('upgrade_limitation') is None \
                       or card.get('upgrade_limitation') == upgrade['name']:
                        ok_upgrade = True
                        break
            if not ok_upgrade:
                # try find coresponding worker
                for card in session_data['board']:
                    if card.get('upgrade_limitation') == upgrade['name']:
                        play({"action": "hold", "card_id": card['id']})
                        return True
                # try find Czar and carpenter
                for card in session_data['board']:
                    if card['card_type'] == 'worker' and card.get('upgrade_limitation') is None:
                        play({"action": "hold", "card_id": card['id']})
                        return True

    # hold cheap workers
    if len(actual_player['hand']) < 3 and worker_buy(session_data, session_data['board'], True):
        return
            

    # card not holded try buy from hand when no worker card can be holded
    if worker_buy(session_data, actual_player['hand']):
        return

    # general heuristic to try hold a good card
    if try_buy_or_hold_good_card(session_data):
        return

    play({"action": "pass"})
    return
    
            

def worker_buy(session_data, card_options, hold=False):
    actual_player = actual_player_info(session_data)
    cheapest_card = None
    upgrade_from = None
    for card in card_options:
        if card['card_type'] == 'worker' or (card['card_type'] == 'upgrade'
                                             and card['upgrade_type'] == 'worker'):
            discounted_price, upgrade_actual_from = discounted_card_price(session_data, card, hold)
            if not hold and card['card_type'] == 'upgrade' \
               and card['upgrade_type'] == 'worker'\
               and upgrade_actual_from is None:
                continue
            if cheapest_card is not None:
                discounted_cheapest_price, _ = discounted_card_price(session_data, cheapest_card, hold)
            if (cheapest_card is None or
                discounted_price < discounted_cheapest_price)\
                and (
                        (
                            (hold and len(actual_player['hand']) < 3)
                            or
                            (
                                not hold
                                and discounted_price <= actual_player['money']
                            )
                        )
                   ):
                cheapest_card = card
                upgrade_from = upgrade_actual_from
    if cheapest_card is not None:
        args = {'action': 'buy', 'card_id': cheapest_card['id']}
        if hold:
            args['action'] = 'hold'

        discounted_price, upgrade_from = discounted_card_price(session_data, cheapest_card)
        
        if cheapest_card['card_type'] == 'upgrade' and args['action'] != 'hold':
            # find card from upgrade
            args['upgrade_from'] = upgrade_from['id']

        
        cards_rem = cards_remaining(session_data)
        if hold:
            # one turn less
            cards_rem -= 3

        if session_data['board'] == card_options:
            # need to buy anyway even if not bargain
            play(args)
            return True

        if discounted_price > actual_player['money']:
            return False
        
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


def building_strategy(session_data):
    """
    Buildings are considered as weakest card type. Main approach is to get ready to aristocrat
    phase.
    """
    actual_player = actual_player_info(session_data)
    # by default prefer aristocrats and upgrades over buildings
    if try_buy_or_hold_good_card(session_data):
        return True

    if actual_player['money'] >= 60:
        if buy_most_expensive(session_data, 'building'):
            return True

    
    if cards_remaining(session_data) > 8:
        # try get card that earns money
        for card in session_data['board']:
            discounted_price, _ = discounted_card_price(session_data, card)
            if card['card_type'] == 'building' \
               and card['money_income'] > 0 \
               and discounted_price <= actual_player['money']:
                play({'action': 'buy', 'card_id': card['id']})
                return True
    
    if attack_building_discount(session_data, session_data['board']):
        return True

    if attack_building_discount(session_data, actual_player['hand']):
        return True

    if actual_player['money'] >= 25:
        # play most expensive from hand
        
        buildings = list(filter(
            lambda card: card['card_type'] == 'building',
            actual_player['hand']
        ))

        buildings.sort(
            key=lambda building: building['price'],
            reverse=actual_player['money'] >= 40
        )
        
        if len(buildings) > 0:
            play({'action': 'buy', 'card_id': buildings[0]['id']})
            return

    if open_hold_buy(session_data):
        return True
    play({"action": "pass"})


def aristocrat_strategy(session_data):
    actual_player = actual_player_info(session_data)
    for deck in [session_data['board'], actual_player['hand']]:
        aristocrats = list(filter(
            lambda card: card['card_type'] == 'aristocrat',
            session_data['board']
        ))
        aristocrats.sort(key=lambda card: card['price'], reverse = True)
        for card in aristocrats:
            discounted_price, _ = discounted_card_price(session_data, card)
            if discounted_price <= actual_player['money']:
                play({"action": "buy", "card_id": card['id']})
                return
            if len(actual_player['hand']) < 3:
                play({'action': 'hold', 'card_id': card['id']})
                return

    # try to use aristocrats that we have more than one time
    for deck in [session_data['board'], actual_player['hand']]:
        upgrades = list(filter(
            lambda card: card['card_type'] == 'upgrade' \
                and card['upgrade_type'] == 'aristocrat',
            deck
        ))
        upgrades.sort(key=lambda card: card['price'])
        aristocrats = list(filter(
            lambda card: card['card_type'] == 'aristocrat',
            session_data['board']
        ))
        aristocrats.sort(key=lambda card: card['price'])
        counter = Counter(map(lambda card: card['name'], aristocrats))
        duplicit_names = filter(lambda card: counter[card['name']] > 1, aristocrats)
        duplicits = list(filter(lambda card: card['name'] in duplicit_names, aristocrats))
        duplicits.sort(key=lambda card: card['price'])

        for upgrade in upgrades:
            for duplicity in duplicits:
                if upgrade['price'] >= duplicity['price']:
                    if upgrade['price'] - duplicity['price'] <= actual_player['money'] \
                       and actual_player['money'] > 0:
                        play({
                            "action": "buy",
                            "card_id": upgrade['id'],
                            "upgrade_from": duplicity['id']
                        })
                        return

            for aristocrat in aristocrats:
                if not economic_upgrade(session_data, aristocrat, upgrade, deck):
                    continue
                play({
                    'action': 'buy',
                    'card_id': upgrade['id'],
                    "upgrade_from": aristocrat['id']
                })

            if len(actual_player['hand']) < 3 and deck == session_data['board']:
                play({
                    "action": "hold",
                    "card_id": upgrade['id']
                })
                return
    play({'action': 'pass'})
    return

def economic_upgrade(session_data, aristocrat, upgrade, deck):
    actual_player = actual_player_info(session_data)
    if aristocrat['price'] >= upgrade['price'] - 5:
        return False
    if aristocrat['price'] >= 16 and upgrade['price'] <= 12:
        return False
    if aristocrat['price'] >= upgrade['price'] and deck == actual_player['hand']:
        return False
    return True


def upgrade_strategy(session_data):
    actual_player = actual_player_info(session_data)
    # count aristocrats and space in hand
    if cards_remaining(session_data) == 0:
        if actual_player['money'] == 0:
            play({'action': 'pass'})
            return
        for deck in [session_data['board'], actual_player['hand']]:
            if deck == actual_player['hand']:
                # first get rid of aristocrats may generate duplicities
                aristocrats = list(filter(
                    lambda card: card['card_type'] == 'aristocrat',
                    actual_player['hand']
                ))
                for aristocrat in aristocrats:
                    discounted_price, _ = discounted_card_price(session_data, aristocrat)
                    if discounted_price < actual_player['money']:
                        play({"action": "buy", "card_id": aristocrat['id']})
                        return
            upgrades = list(filter(
                lambda card: card['card_type'] == 'upgrade' \
                    and card['upgrade_type'] == 'aristocrat',
                deck
            ))
            upgrades.sort(key=lambda card: card['price'], reverse=deck==actual_player['hand'])
            aristocrats = list(filter(
                lambda card: card['card_type'] == 'aristocrat',
                actual_player['board']
            ))
            aristocrats.sort(key=lambda card: card['price'], reverse=deck==actual_player['hand'])
            counter = Counter(map(lambda card: card['name'], aristocrats))
            duplicits = list(filter(lambda card: counter[card['name']] > 1, aristocrats))
            #duplicits = list(filter(lambda card: card['name'] in duplicit_names, aristocrats))
            duplicits.sort(key=lambda card: card['price'], reverse=deck==actual_player['hand'])

            for upgrade in upgrades:
                for duplicity in duplicits:
                    if upgrade['price'] >= duplicity['price']:
                        if upgrade['price'] - duplicity['price'] <= actual_player['money']:
                            play({
                                "action": "buy",
                                "card_id": upgrade['id'],
                                "upgrade_from": duplicity['id']
                            })
                            return

                for aristocrat in aristocrats:
                    if len(actual_player['hand']) < 3 and deck == session_data['board']:
                        play({
                            "action": "hold",
                            "card_id": upgrade['id'],
                            "upgrade_from": aristocrat['id']
                        })
                        return

        # get rid of other cards in hand
        for card in actual_player['hand']:
            discounted_price, _ = discounted_card_price(session_data, card)
            if card['card_type'] == 'upgrade':
                continue
            if discounted_price < actual_player['money']:
                play({"action": "buy", "card_id": card['id']})
                return
        
        upgrades = list(filter(
            lambda card: card['card_type'] == 'upgrade',
            actual_player['hand']
        ))
        upgrades.sort(key=lambda card: card['price'], reverse=True)

        for upgrade in upgrades:
            if upgrade['upgrade_type'] == 'worker':
                discounted_price, upgrade_from = discounted_card_price(session_data, card)
                if discounted_price <= actual_player['money'] \
                   and upgrade_from is not None:
                    play({
                        'action': 'buy',
                        'card_id': upgrade['id'],
                        'upgrade_from': upgrade_from['id']
                    })
                    return
            cards = list(filter(
                lambda card: card['card_type'] == upgrade['upgrade_type'],
                actual_player['board']
            ))

            cards.sort(key=lambda card: card['price'], reverse=True)
            for card in cards:
                if upgrade['price'] - card['price'] <= actual_player['money']\
                   and actual_player['money'] >= 1:
                    play({
                        'action': 'buy',
                        'card_id': upgrade['id'],
                        'upgrade_from': card['id']
                    })
                    return
                        
        play({"action": "pass"})
        return
    else:
        if try_buy_or_hold_good_card(session_data):
            return

        # worker phase following
        upgrades = list(filter(
            lambda card: card['card_type'] == 'upgrade' \
            and card['upgrade_type'] == 'worker',
            session_data['board']
        ))


        for upgrade in upgrades:
            discounted_price, upgrade_from = discounted_card_price(
                session_data, upgrade
            )

            buy = discounted_price <= actual_player['money'] and \
                  upgrade_from is not None and \
                  (
                      upgrade['discounted'] or
                      len(actual_player['hand']) == 3
                  )
            hold = len(actual_player['hand']) < 3 and\
                   (
                       upgrade_from is not None or
                       cards_remaining(session_data) >= 5
                   )

            if buy:
                play({
                    'action': 'buy',
                    'card_id': upgrade['id'],
                    'upgrade_from': upgrade_from['id']
                })
                return
            if hold:
                play({
                    'action': 'hold',
                    'card_id': upgrade['id']
                })
                return


        if cards_remaining(session_data) >= 5:
            if open_hold_buy(session_data):
                return
        play({"action": 'pass'})
        return


def buy_most_expensive(session_data, phase, limit = None, filter_useless=True):
    actual_player = actual_player_info(session_data)
    if limit is None:
        limit = actual_player['money']
    assert limit <= actual_player['money']
    most_expensive_card = None
    actual_player = actual_player_info(session_data)
    for card in session_data['board'] + actual_player['hand']:
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

def open_hold_buy(session_data):
    print("open_hold")
    assert session_data['actual_phase'] in ['building', 'upgrade']
    next_phase = None
    if session_data['actual_phase'] == 'building':
        next_phase = 'aristocrat'
    elif session_data['actual_phase'] == 'upgrade':
        next_phase = 'worker'
    # count order of following phase
    actual_player = actual_player_info(session_data)
    actual_player_index = session_data['players'].index(actual_player)
    # player of following phase
    next_starting_player = None
    for player in session_data['players']:
        for token in player['starting_tokens']:
            if token == next_phase:
                next_starting_player = player
    next_starting_player_index = session_data['players'].index(
        next_starting_player
    )
    if session_data['actual_phase'] == 'upgrade':
        # after upgrade starting tokens rotate
        next_starting_player_index += 1
    card_offset = actual_player_index - next_starting_player_index
    card_offset %= len(session_data['players'])
    if session_data['actual_phase'] == 'building':
        card_spots = (8 - len(session_data['board']))
    else:
        cards = 0
        for card in session_data['board']:
            if not card['discounted']:
                cards += 1
        card_spots = 8 - cards

    if card_offset != card_spots % len(session_data['players']):
        # taking would open to someone else
        return False

    if session_data['actual_phase'] == 'upgrade':
        # easy case dont want to hold workers
        # hold by default
        if len(actual_player['hand']) == 3:
            if card_spots // len(session_data['players']) == 0:
                # try buy cheapest
                cheapest_card = get_cheapest_card(
                    session_data,
                    deny_discounted=True,
                    allow_hand=True
                )

                discounted_cheapest_price, upgrade_from = discounted_card_price(session_data, card)

                if cheapest_card is not None \
                   and discounted_cheapest_price is not None\
                   and discounted_cheapest_price <= actual_player['money'] - 7:
                    args = {"action": "buy", "card_id": cheapest_card['id']}
                    if upgrade_from is not None:
                        args['upgrade_from'] = upgrade_from['id']
                    play({"action": "buy", "card_id": cheapest_card['id']})
                    return True
                else:
                    play({"action": "pass"})
                    return True
                    
                
            else:
                play({"action": "pass"})
                return True
        else:
            if actual_player['money'] < 7:
                # just pass
                play({"action": "pass"})
                return True
            # hold cheapest card
            cheapest_card = get_cheapest_card(
                session_data,
                deny_discounted=True,
                allow_hand=False
            )

            if cheapest_card is not None:
                play({"action": "hold", "card_id": cheapest_card['id']})
                return True
            else:
                play({"action": "pass"})
                return True
    else:
        # building try to get aristocrats
        # dont mind to hold them
        offsetted_cards = card_spots - card_offset
        cards_for_me = offsetted_cards // len(session_data['players'])
        hand_space = len(actual_player['hand']) - cards_for_me
        if hand_space >= -2:
            play({"action": "pass"})
            return True
        if hand_space == -1:
            if actual_player['money'] > 20:
                cheapest_card = get_cheapest_card(session_data, allow_hand=False)
                if cheapest_card['price'] < actual_player['money'] - 30:
                    play({"action": "buy", "card_id": cheapest_card['id']})
                    return True
            play({"action": "pass"})
            return True
        if hand_space == 0:
            cheapest_card = get_cheapest_card(session_data, allow_hand=False)
            if cheapest_card['price'] < actual_player['money'] - 18:
                play({"action": "buy", "card_id": cheapest_card['id']})
            else:
                play({"action": "pass"})
            return True
        if hand_space == 1:
            cheapest_card = get_cheapest_card(session_data, allow_hand=True)
            if cheapest_card['price'] <= 8 \
               and cheapest_card['price'] <= actual_player['money']:
                play({"action": "buy", "card_id": cheapest_card['id']})
                return True
            elif actual_player['money'] >= 18:
                cheapest_card = get_cheapest_card(session_data, allow_hand=False)
                play({"action": "hold", "card_id": cheapest_card['id']})
                return True
            else:
                play({"action": "pass"})
                return True
        if hand_space >= 2:
            cheapest_card = get_cheapest_card(session_data, allow_hand=True)
            if cheapest_card['price'] <= actual_player['money'] - 18:
                play({"action": "buy", "card_id": cheapest_card['id']})
            else:
                cheapest_card = get_cheapest_card(session_data, allow_hand=False)
                play({"action": "hold", "card_id": cheapest_card['id']})
            return True
    return False
    

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
            upgrade_discount = None
            if card['price'] < 8:
                # try firstly direct upgrade then consider czar and carpenter
                for board_card in actual_player['board']:
                    if board_card.get('upgrade_limitation') == card['name']:
                        upgrade_discount = card['price'] - board_card['price']
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
                        if board_card['name'] == 'Czar and carpenter':
                            upgrade_discount = board_card['price'] # 8
                            upgrade_from = board_card
                            break
            else:
                # try firstly czar and carpenter then other card
                # here is buy and hold preference the same
                for board_card in actual_player['board']:
                    if card['name'] == 'Czar and carpenter':
                        upgrade_discount = card['price'] # 8
                        upgrade_from = board_card
                        break

                if upgrade_discount is None:
                    for board_card in actual_player['board']:
                        if board_card.get('upgrade_limitation') == card['name']:
                            upgrade_discount = card['price'] - board_card['price']
                            upgrade_from = board_card
                            break
                
            if upgrade_discount is None and consider_hold:
                # second round of strategy when holding cards no need to have worker card on board
                for card_prototype in cardlist:
                    # only direct upgrade, not czar and carpenter
                    if card_prototype.get('upgrade_limitation') == card['name']:
                        upgrade_discount = card['price'] - board_card['price']
                        # upgrade from is irelevant -> we are holding upgrade

    if upgrade_discount is not None:
        price -= upgrade_discount

    if price < 1:
        price = 1
    return price, upgrade_from


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

def try_buy_or_hold_good_card(session_data):
    """
    General heuristic for buyng / holding aristocracy and aristocracy upgrades.
    """

    for card in session_data['board']:
        if card['card_type'] == 'upgrade' and card['upgrade_type'] == 'aristocrat':
            if card['price'] != 24: # Czar is expensive, prefer aristocrats
                if buy_hold_decision(session_data, card):
                    return True

    if cards_remaining(session_data) >= 7:
        for card in session_data['board']:
            if card['card_type'] == 'upgrade' \
               and card['card_type'] == 'building' \
               and card['money_income'] >= 4:
                if buy_hold_decision(session_data, card):
                    return True
    most_expensive_aristocrat = None
    for card in session_data['board']:
        if card['card_type'] == 'aristocrat':
            if most_expensive_aristocrat is None or most_expensive_aristocrat['price'] < card['price']:
                most_expensive_aristocrat = card
    if most_expensive_aristocrat is not None:
        if buy_hold_decision(session_data, most_expensive_aristocrat):
            return True

    # cannot hold, try buy
    for card in session_data['board']:
        if card['card_type'] == 'aristocrat':
            if buy_hold_decision(session_data, card):
                return True
        
    if cards_remaining(session_data) >= 2:
        for card in session_data['board']:
            if card['card_type'] == 'upgrade' \
               and card['card_type'] == 'building':
                if buy_hold_decision(session_data, card):
                    return True


"""
Try to search if exist in this mess more accurate function.
"""

def get_cheapest_card(session_data, deny_discounted = False, allow_hand = True):
    actual_player = actual_player_info(session_data)
    cheapest_card = None
    discounted_cheapest_price = None
    board = session_data['board']
    if allow_hand:
        board += actual_player['hand']
    for card in board:
        if card['discounted'] and deny_discounted:
            continue
        if card['card_type'] == 'upgrade':
            continue
        if cheapest_card is not None:
            discounted_cheapest_price, _ = discounted_card_price(
                session_data,
                cheapest_card
            )

        discounted_price, _ = discounted_card_price(
            session_data,
            card
        )
        if cheapest_card is None \
           or discounted_cheapest_price > discounted_price:
            cheapest_card = card
            discounted_cheapest_price = discounted_price
    return cheapest_card
                

def buy_hold_decision(session_data, card):
    actual_player = actual_player_info(session_data)
    if session_data['actual_phase'] == 'upgrade':
        if len(actual_player['hand']) < 3:
            play({'action': 'hold', 'card_id': card['id']})
            return True
        if actual_player['money'] == 0:
            play({'action': 'pass'})
            return True
        if card['card_type'] == 'upgrade':
            # code is copied below be careful with changes
            best_c = None
            for c in actual_player['board']:
                if c['card_type'] == card['upgrade_type']:
                    if best_c is None or abs(card['price'] - c['price'] - 3) < \
                       abs(card['price'] - best_c['price'] - 3):
                        discounted_price, upgrade_from = discounted_card_price(session_data, card)
                        if upgrade_from is not None:
                            # want to grab since it is right before worker phase
                            if dicounted_price <= actual_player['money']:
                                play({
                                    'action': 'buy',
                                    'card_id': card['id'],
                                    'upgrade_from': upgrade_from['id']
                                })
                                return True
                            return False
                        if upgrade_from is None and card['upgrade_type'] == 'worker':
                            # full hand and cannot buy
                            return False
                        if discounted_price - c['price'] < actual_player['money']:
                            best_c = c
            if best_c is None:
                return False
            if best_c['name'] == 'Ministress':
                if card['price'] < 18:
                    return False
            if best_c['name'] == 'Judge':
                if card['price'] < 16:
                    return False
            if card['price'] - best_c['price'] <= actual_player['money']:
                if card['price'] - best_c['price'] <= 5:
                    play({'action': 'buy', 'card_id': card['id'], 'upgrade_from': best_c['id']})
                    return True
        return False

    discounted_price, upgrade_from = discounted_card_price(session_data, card)
    prefer_buy = True
    if card['card_type'] == 'upgrade' and card['upgrade_type'] != 'aristocrat'\
       and session_data['actual_phase'] == 'aristocrat':
        prefer_buy = False
    if card['card_type'] in ['worker', 'building'] \
       and session_data['actual_phase'] == 'aristocrat':
        prefer_buy = False
    if (card['card_type'] == 'worker' or card.get('upgrade_type') == 'worker') \
       and session_data['actual_phase'] == 'building':
        prefer_buy = False
    if prefer_buy == False and len(actual_player['hand']) < 3:
        play({'action': 'hold', 'card_id': card['id']})
        return True

    if card['card_type'] == 'upgrade':
        # just copied code dont blame me
        best_c = None
        for c in actual_player['board']:
            if c['card_type'] == card['upgrade_type']:
                if best_c is None or \
                   abs(card['price'] - c['price'] - 3) < \
                   abs(card['price'] - best_c['price'] - 3):
                    discounted_price, upgrade_from = discounted_card_price(session_data, card)
                    if upgrade_from is not None:
                        # want to grab since it is right before worker phase
                        if dicounted_price <= actual_player['money']:
                            play({
                                'action': 'buy',
                                'card_id': card['id'],
                                'upgrade_from': upgrade_from['id']
                            })
                            return True
                        return False
                if upgrade_from is None and card['upgrade_type'] == 'worker':
                    # full hand and cannot buy
                    return False
                if discounted_price - c['price'] < actual_player['money']:
                    best_c = c
        if best_c is None:
                return False
        if best_c['name'] == 'Ministress':
            if card['price'] < 18:
                return False
        if best_c['name'] == 'Judge':
            if card['price'] < 16:
                return False
        if card['price'] - best_c['price'] <= actual_player['money']:
            if card['price'] - best_c['price'] <= 5:
                play({'action': 'buy', 'card_id': card['id'], 'upgrade_from': best_c['id']})
                return True
    else:
        if discounted_price <= actual_player['money']:
            play({'action': 'buy', 'card_id': card['id']})
            return True

    if len(actual_player['hand']) < 3:
        play({'action': 'hold', 'card_id': card['id']})
        return True
    return False

def attack_building_discount(session_data, board):
    """
    Market and Customs house are frequent cards in buildings. Sometimes it can be benefitial to
    buy them at discount. They are also good as upgrade base.
    """
    actual_player = actual_player_info(session_data)
    if actual_player['money'] < 6:
        return False
    aristocrat_start = False
    for token in actual_player['starting_tokens']:
        if token == 'aristocrat':
            aristocrat_start = True
    discounted_buildings = list(filter(
        lambda card: card['card_type'] == 'building' and card['discounted'],
        board
    ))

    other_buildings = list(filter(
        lambda card: card['card_type'] == 'building' and not card['discounted'],
        board
    ))

    for building in discounted_buildings + other_buildings:
        discounted_price, _ = discounted_card_price(session_data, building)
        if discounted_price > actual_player['money']:
            continue
        if building['price'] <= 8:
            if building['price'] - discounted_price - int(aristocrat_start) >= 2:
                play({"action": "buy", 'card_id': building['id']})
                return True
            if actual_player['money'] >= 26:
                if building['price'] > discounted_price:
                    play({"action": "buy", 'card_id': building['id']})
                    return True
        if building['price'] <= 11:
            if discounted_price <= 9 and actual_player['money'] >= 20:
                play({"action": "buy", 'card_id': building['id']})
                return True
        if building['price'] == 14:
            if discounted_price <= 11 and actual_player['money'] >= 22:
                play({"action": "buy", 'card_id': building['id']})
                return True

    

def actual_player_info(session_data):
    actual_player = None
    for player in session_data['players']:
        if player['actual_player']:
            return player
    return None

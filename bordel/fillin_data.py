import sys
sys.path.append("..")
from server import db, app, CardPrototype, Users, BOT_USERNAMES, TEST_USERS


def create_cards_prototypes():
    cards = []
  
    cards.append(CardPrototype(
        name = "Lumberjack",
        price = 3,
        money_income = 3,
        point_income = 0,
        card_type = 'worker',
        # upgrade limitation will be fixed below
        deck_count = 6
    ))

    
    cards.append(CardPrototype(
        name = "Gold digger",
        price = 4,
        money_income = 3,
        point_income = 0,
        card_type = 'worker',
        # upgrade limitation will be fixed below
        deck_count = 6
    ))

    cards.append(CardPrototype(
        name = "Shepherd",
        price = 5,
        money_income = 3,
        point_income = 0,
        card_type = 'worker',
        # upgrade limitation will be fixed below
        deck_count = 6
    ))

    cards.append(CardPrototype(
        name = "Fur trapper",
        price = 6,
        money_income = 3,
        point_income = 0,
        card_type = 'worker',
        # upgrade limitation will be fixed below
        deck_count = 6
    ))

    cards.append(CardPrototype(
        name = "Ship builder",
        price = 7,
        money_income = 3,
        point_income = 0,
        card_type = 'worker',
        # upgrade limitation will be fixed below
        deck_count = 6
    ))

    cards.append(CardPrototype(
        name = "Czar and carpenter",
        price = 8,
        money_income = 3,
        point_income = 0,
        card_type = 'worker',
        # no upgrade limitation
        deck_count = 1
    ))

    cards.append(CardPrototype(
        name = "Market",
        price = 5,
        money_income = 0,
        point_income = 1,
        card_type = 'building',
        deck_count = 5
    ))

    cards.append(CardPrototype(
        name = "Customs house",
        price = 8,
        money_income = 0,
        point_income = 2,
        card_type = 'building',
        deck_count = 5
    ))

    cards.append(CardPrototype(
        name = "Fire house",
        price = 11,
        money_income = 0,
        point_income = 3,
        card_type = 'building',
        deck_count = 3
    ))

    cards.append(CardPrototype(
        name = "Hospital",
        price = 14,
        money_income = 0,
        point_income = 4,
        card_type = 'building',
        deck_count = 3
    ))

    cards.append(CardPrototype(
        name = "Library",
        price = 17,
        money_income = 0,
        point_income = 5,
        card_type = 'building',
        deck_count = 3
    ))

    cards.append(CardPrototype(
        name = "Theater",
        price = 20,
        money_income = 0,
        point_income = 6,
        card_type = 'building',
        deck_count = 2
    ))

    cards.append(CardPrototype(
        name = "Academy",
        price = 23,
        money_income = 0,
        point_income = 7,
        card_type = 'building',
        deck_count = 1
    ))

    cards.append(CardPrototype(
        name = "Potjomkin's village",
        price = 1,
        money_income = 0,
        point_income = 0,
        card_type = 'building',
        deck_count = 2
    ))

    cards.append(CardPrototype(
        name = "Restaurant",
        price = 3,
        money_income = 1,
        point_income = 0,
        card_type = 'building',
        deck_count = 2
    ))

    cards.append(CardPrototype(
        name = "Steak house",
        price = 7,
        money_income = 1,
        point_income = 1,
        card_type = 'building',
        deck_count = 2
    ))

    cards.append(CardPrototype(
        name = "Author",
        price = 4,
        money_income = 1,
        point_income = 0,
        card_type = 'aristocrat',
        deck_count = 6
    ))

    cards.append(CardPrototype(
        name = "Administrator",
        price = 7,
        money_income = 2,
        point_income = 0,
        card_type = 'aristocrat',
        deck_count = 5
    ))

    cards.append(CardPrototype(
        name = "Warehouse manager",
        price = 10,
        money_income = 3,
        point_income = 0,
        card_type = 'aristocrat',
        deck_count = 5
    ))

    cards.append(CardPrototype(
        name = "Secretary",
        price = 12,
        money_income = 4,
        point_income = 0,
        card_type = 'aristocrat',
        deck_count = 4
    ))

    cards.append(CardPrototype(
        name = "Controller",
        price = 12,
        money_income = 4,
        point_income = 1,
        card_type = 'aristocrat',
        deck_count = 3
    ))

    cards.append(CardPrototype(
        name = "Judge",
        price = 16,
        money_income = 5,
        point_income = 2,
        card_type = 'aristocrat',
        deck_count = 2
    ))

    cards.append(CardPrototype(
        name = "Ministress",
        price = 18,
        money_income = 6,
        point_income = 3,
        card_type = 'aristocrat',
        deck_count = 2
    ))

    cards.append(CardPrototype(
        name = "Workshop",
        price = 4,
        money_income = 4,
        point_income = 0,
        card_type = 'upgrade',
        upgrade_type = 'worker',
        deck_count = 1
    ))

    cards.append(CardPrototype(
        name = "Gold smelter",
        price = 6,
        money_income = 5,
        point_income = 0,
        card_type = 'upgrade',
        upgrade_type = 'worker',
        deck_count = 1
    ))

    cards.append(CardPrototype(
        name = "Weaving mill",
        price = 8,
        money_income = 6,
        point_income = 0,
        card_type = 'upgrade',
        upgrade_type = 'worker',
        deck_count = 2
    ))

    cards.append(CardPrototype(
        name = "Fur shop",
        price = 10,
        money_income = 3,
        point_income = 2,
        card_type = 'upgrade',
        upgrade_type = 'worker',
        deck_count = 3
    ))

    cards.append(CardPrototype(
        name = "Wharf",
        price = 12,
        money_income = 6,
        point_income = 1,
        card_type = 'upgrade',
        upgrade_type = 'worker',
        deck_count = 3
    ))

    cards.append(CardPrototype(
        name = "Cheap theater",
        price = 10,
        money_income = 5,
        point_income = 0,
        card_type = 'upgrade',
        upgrade_type = 'building',
        deck_count = 1
    ))

    cards.append(CardPrototype(
        name = "Bank",
        price = 13,
        money_income = 5,
        point_income = 1,
        card_type = 'upgrade',
        upgrade_type = 'building',
        deck_count = 1
    ))

    cards.append(CardPrototype(
        name = "Petegrof",
        price = 14,
        money_income = 4,
        point_income = 2,
        card_type = 'upgrade',
        upgrade_type = 'building',
        deck_count = 1
    ))

    cards.append(CardPrototype(
        name = "St. Isaac Cathedral",
        price = 15,
        money_income = 3,
        point_income = 3,
        card_type = 'upgrade',
        upgrade_type = 'building',
        deck_count = 1
    ))

    cards.append(CardPrototype(
        name = "Harbor",
        price = 16,
        money_income = 5,
        point_income = 2,
        card_type = 'upgrade',
        upgrade_type = 'building',
        deck_count = 1
    ))

    cards.append(CardPrototype(
        name = "Big Cathedral",
        price = 16,
        money_income = 2,
        point_income = 4,
        card_type = 'upgrade',
        upgrade_type = 'building',
        deck_count = 1
    ))

    cards.append(CardPrototype(
        name = "Smolny Cathedral",
        price = 17,
        money_income = 1,
        point_income = 5,
        card_type = 'upgrade',
        upgrade_type = 'building',
        deck_count = 1
    ))

    cards.append(CardPrototype(
        name = "Cathedral4",
        price = 17,
        money_income = 4,
        point_income = 3,
        card_type = 'upgrade',
        upgrade_type = 'building',
        deck_count = 1
    ))

    cards.append(CardPrototype(
        name = "Hermitrage",
        price = 18,
        money_income = 3,
        point_income = 4,
        card_type = 'upgrade',
        upgrade_type = 'building',
        deck_count = 1
    ))

    cards.append(CardPrototype(
        name = "Winter palace",
        price = 19,
        money_income = 3,
        point_income = 5,
        card_type = 'upgrade',
        upgrade_type = 'building',
        deck_count = 1
    ))

    cards.append(CardPrototype(
        name = "Pope",
        price = 6,
        money_income = 1,
        point_income = 1,
        card_type = 'upgrade',
        upgrade_type = 'aristocrat',
        deck_count = 1
    ))

    cards.append(CardPrototype(
        name = "Weapon master",
        price = 8,
        money_income = 4,
        point_income = 0,
        card_type = 'upgrade',
        upgrade_type = 'aristocrat',
        deck_count = 1
    ))

    cards.append(CardPrototype(
        name = "Chamber maid",
        price = 8,
        money_income = 0,
        point_income = 2,
        card_type = 'upgrade',
        upgrade_type = 'aristocrat',
        deck_count = 1
    ))

    cards.append(CardPrototype(
        name = "Builder",
        price = 10,
        money_income = 5,
        point_income = 0,
        card_type = 'upgrade',
        upgrade_type = 'aristocrat',
        deck_count = 1
    ))

    cards.append(CardPrototype(
        name = "Senator",
        price = 12,
        money_income = 2,
        point_income = 2,
        card_type = 'upgrade',
        upgrade_type = 'aristocrat',
        deck_count = 1
    ))

    cards.append(CardPrototype(
        name = "Patriarch",
        price = 16,
        money_income = 0,
        point_income = 4,
        card_type = 'upgrade',
        upgrade_type = 'aristocrat',
        deck_count = 1
    ))

    cards.append(CardPrototype(
        name = "Tax man",
        price = 17,
        money_income = 8,
        point_income = 0,
        card_type = 'upgrade',
        upgrade_type = 'aristocrat',
        deck_count = 1
    ))

    cards.append(CardPrototype(
        name = "Admiral",
        price = 18,
        money_income = 3,
        point_income = 3,
        card_type = 'upgrade',
        upgrade_type = 'aristocrat',
        deck_count = 1
    ))

    cards.append(CardPrototype(
        name = "Minister",
        price = 20,
        money_income = 2,
        point_income = 4,
        card_type = 'upgrade',
        upgrade_type = 'aristocrat',
        deck_count = 1
    ))

    cards.append(CardPrototype(
        name = "Czar",
        price = 24,
        money_income = 0,
        point_income = 6,
        card_type = 'upgrade',
        upgrade_type = 'aristocrat',
        deck_count = 1
    ))

    for card in cards:
        db.session.add(card)
    db.session.commit()

    # set upgrade limitation on cards
    limitations = [
        ("Lumberjack", "Workshop"),
        ("Gold digger", "Gold smelter"),
        ("Shepherd", "Weaving mill"),
        ("Fur trapper", "Fur shop"),
        ("Ship builder", "Wharf")
    ]

    for limitation in limitations:
        worker_name, upgrade_name = limitation
        
        worker = CardPrototype.query.filter_by(name=worker_name).first()
        upgrade = CardPrototype.query.filter_by(name=upgrade_name).first()
        worker.upgrade_limitation = upgrade.id

    db.session.commit()


def create_users():
    users = []
    for bot_username in BOT_USERNAMES:
        users.append(Users(
            name=bot_username,
            password=bot_username
        ))
    for test_user in TEST_USERS.keys():
        users.append(Users(
            name=test_user,
            password=TEST_USERS[test_user]
        ))

    for user in users:
        db.session.add(user)
    db.session.commit()

if __name__ == "__main__":
    with app.app_context():
        create_cards_prototypes()
        create_users()

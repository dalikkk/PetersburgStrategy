from flask import Flask, render_template, request, flash
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, SelectField
from wtforms.validators import DataRequired
from flask_sqlalchemy import SQLAlchemy
from flask_bootstrap import Bootstrap5
from datetime import datetime
from sqlalchemy.orm import mapped_column
import random
from collections import Counter

import backend_bot1, backend_bot2, backend_bot3, backend_bot4, backend_bot5, backend_bot6
BOTS = [backend_bot1, backend_bot2, backend_bot3, backend_bot4, backend_bot5, backend_bot6]
BOT_USERNAMES = ['bot1', 'bot2', 'bot3', 'bot4', 'bot5', 'bot6']
assert len(BOTS) == len(BOT_USERNAMES)

TEST_USERS = {'dd':'d', 'ddd': 'd'}

app = Flask(__name__)

app.config['SECRET_KEY'] = "secret key lalal"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
#app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:1234@localhost/test'

CARD_TYPES = ['worker', 'building', 'aristocrat', 'upgrade']
# Initialize db
db = SQLAlchemy(app)
bootstrap = Bootstrap5(app)

class Users(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String(200), nullable = False, unique = True)
    password = db.Column(db.String(200), nullable = False)
    date_added = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return '<Name %r>' % self.name


class CardPrototype(db.Model):
    __tablename__ = 'card_prototype'
    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String(50), nullable = False, unique = True)
    price = db.Column(db.Integer, nullable = False)
    money_income = db.Column(db.Integer, nullable = False)
    point_income = db.Column(db.Integer, nullable = False)
    card_type = db.Column(db.String(20), nullable = False)
    upgrade_type = db.Column(db.String(20))
    upgrade_limitation = db.Column(
        db.Integer,
        db.ForeignKey('card_prototype.id', ondelete="CASCADE")
    )
    deck_count = db.Column(db.Integer, nullable = False)


class Session(db.Model):
    __tablename__ = 'session'
    id = db.Column(db.Integer, primary_key = True)
    player1 = db.Column(
        db.Integer,
        db.ForeignKey('user.id', ondelete="CASCADE"),
        nullable = False
    )
    player2 = db.Column(
        db.Integer,
        db.ForeignKey('user.id', ondelete="CASCADE"),
        nullable = False
    )

    player3 = db.Column(
        db.Integer,
        db.ForeignKey('user.id', ondelete="CASCADE")
    )

    player4 = db.Column(
        db.Integer,
        db.ForeignKey('user.id', ondelete="CASCADE")
    )

    # None is finished game
    actual_player = db.Column(
        db.Integer,
        db.ForeignKey('user.id', ondelete="CASCADE")
    )

    actual_player_index = db.Column(
        db.Integer
    )

    actual_phase = db.Column(
        db.String,
        default = CARD_TYPES[0]
    )

class PlayerInfo(db.Model):
    __tablename__ = 'player_info'
    id = db.Column(db.Integer, primary_key = True)
    index = db.Column(db.Integer, nullable = False)
    session_id = db.Column(
        db.Integer,
        db.ForeignKey('session.id')
    )
    player_id = db.Column(
        db.Integer,
        db.ForeignKey('user.id', ondelete="CASCADE"),
        nullable = False
    )
    money = db.Column(db.Integer, nullable = False)
    points = db.Column(db.Integer, nullable = False)
    hand_id = db.Column(
        db.Integer,
        db.ForeignKey('deck.id'),
        nullable = False
    )
    # build cards
    deck_id = db.Column(
        db.Integer,
        db.ForeignKey('deck.id', ondelete="CASCADE"),
        nullable = False
    )

    had_passed = db.Column(
        db.Boolean,
        default = False
    )

class Deck(db.Model):
    __tablename__ = 'deck'
    id = db.Column(db.Integer, primary_key = True)
    session_id = db.Column(
        db.Integer,
        db.ForeignKey('session.id', ondelete="CASCADE"),
        nullable = False
    )
    deck_type = db.Column(db.String(20))


class StartToken(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    token_type = db.Column(db.String(20))
    player_info = db.Column(
        db.Integer,
        db.ForeignKey('player_info.id'),
        nullable = False
    )
    

class CardInstance(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    prototype_id = db.Column(
        db.Integer,
        db.ForeignKey('card_prototype.id')
    )
    deck_id = db.Column(
        db.Integer,
        db.ForeignKey('deck.id')
    )
    deck_order = db.Column(db.Integer)
    discounted = db.Column(db.Boolean, default = False, nullable = False)

class UserForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Submit")


class NewGameForm(FlaskForm):
    player1 = SelectField('Player 1', coerce=str, validators=[DataRequired()])
    player2 = SelectField('Player 2', coerce=str, validators=[DataRequired()])
    player3 = SelectField('Player 3', coerce=str)
    player4 = SelectField('Player 4', coerce=str)
    submit = SubmitField("Submit")

def create_game(p1_id, p2_id, p3_id = None, p4_id = None):
    assert p1_id is not None
    assert p2_id is not None
    assert p3_id is not None or p4_id is None

    player_ids = [p1_id, p2_id]
    for p_id in [p3_id, p4_id]:
        if p_id is not None:
            player_ids.append(p_id)

    players_count = 2
    if p3_id is not None:
        players_count += 1
    if p4_id is not None:
        players_count += 1



    # create decks
    session = Session(
        player1=p1_id,
        player2=p2_id,
        player3=p3_id,
        player4=p4_id,
        actual_player=None
    )

    db.session.add(session)
    db.session.commit()
    start_token_distribution = distribute_tokens(players_count)

    deck = Deck(
        session_id = session.id,
        deck_type = "board"
    )
    db.session.add(deck)

    for i, p_id in enumerate(player_ids):
        player = Users.query.filter_by(id=p_id).first()
        if player is None:
            print("No user found with id:", p_id)
            return None

        deck = Deck(
            session_id = session.id,
            deck_type = "player board"
        )
        db.session.add(deck)

        hand = Deck(
            session_id = session.id,
            deck_type = "hand"
        )
        db.session.add(hand)
        db.session.commit()
        player_info = PlayerInfo(
            index=i,
            session_id = session.id,
            player_id = p_id,
            money = 25,
            points = 0,
            hand_id = hand.id,
            deck_id = deck.id
        )
        


        db.session.add(player_info)
        db.session.commit()
        
        for start_token_type in start_token_distribution[i]:
            start_token = StartToken(
                token_type = start_token_type,
                player_info=player_info.id
            )
            db.session.add(start_token)
        db.session.commit()

    # create cards
    for type in CARD_TYPES:
        deck = Deck(
            session_id = session.id,
            deck_type = type
        )

        db.session.add(deck)

        prototypes = CardPrototype.query.filter_by(card_type=type)
        for prototype in prototypes:
            for i in range(prototype.deck_count):
                card = CardInstance(
                    prototype_id = prototype.id,
                    deck_id = deck.id,
                    # shuffle the cards
                    deck_order = random.randint(0, 100000)
                )
                db.session.add(card)
    db.session.commit()

    # initial card distribution
    get_cards_from_deck(CARD_TYPES[0], session.id, 2*players_count)
    set_active_player(session.id)
    db.session.commit()
    if session.actual_player is not None and session.actual_player <= len(BOTS):
        bot = BOTS[session.actual_player - 1]
        if bot.CARDLIST is None:
            bot.CARDLIST = api_cards()
        bot.strategy(session_data(session.id))
        print("bot.ARGS", bot.ARGS)
        move(session.id, session.actual_player, bot.ARGS)
    return session
    

def set_active_player(session_id):
    session = Session.query.filter_by(id=session_id).one()
    for i, player_id in enumerate([
        session.player1,
        session.player2,
        session.player3,
        session.player4
    ]):
        if player_id is None:
            break
        player_info = PlayerInfo.query\
                      .filter_by(
                          session_id=session_id,
                          index=i,
                          player_id=player_id
                      )\
                      .one()

        token = StartToken.query\
                .filter_by(
                    token_type=session.actual_phase,
                    player_info=player_info.id
                ).first()
        if token is not None:
            session.actual_player = player_id
            session.actual_player_index = i

        #token = StartToken.query\
        #        .join(PlayerInfo, StartToken.player_info == PlayerInfo.id)\
        #        .add_column(PlayerInfo.player_id)\
        #        .filter_by(StartToken.token_type==session.actual_phase)\
        #        .one()
        # session.actual_player = token.player_id


def get_cards_from_deck(deck_type, session_id, limit = None):
    board = Deck.query.filter_by(
        deck_type='board',
        session_id=session_id
    ).one()

    if limit is None:
        card_count = CardInstance.query.filter_by(deck_id=board.id).count()
        limit = 8 - card_count
    assert limit >= 0

    deck = Deck.query.filter_by(
        deck_type=deck_type,
        session_id=session_id
    ).one()
        
    cards = CardInstance.query\
            .filter_by(deck_id=deck.id)\
            .order_by(CardInstance.deck_order)\
            .limit(limit)\
            .all()

    for card in cards:
        db.session.add(card)
        card.discounted = False
        card.deck_id = board.id
    db.session.commit()

def distribute_tokens(player_count):
    assert player_count >= 2
    assert player_count <= 4

    types = CARD_TYPES[0:4]
    distribution = []
    for i in range(player_count):
        j = random.randint(0, len(types) - 1)
        card_type = types.pop(j)
        distribution.append([card_type])

    if player_count == 3:
        # choose player with two tokens
        player_position = random.randint(0, 2)
        distribution[player_position].append(types[0])
    if player_count == 2:
        j = random.randint(0, len(types) - 1)
        card_type = types.pop(j)
        distribution[0].append(card_type)

        distribution[1].append(types.pop())
    return distribution
        

@app.route('/')
def index():
    return render_template(
        "index.html"
    )

@app.route('/user/add/', methods=['GET', 'POST'])
def add_user():
    form = UserForm()
    name = None
    exists_user = False
    bot_name = False
    if form.validate_on_submit():
        name=form.name.data
        if form.name.data.startswith("bot"):
            bot_name = True
        else:
            user = Users.query.filter_by(name=form.name.data).first()
            if user is None:
                user = Users(name=form.name.data, password = form.password.data)
                db.session.add(user)
                db.session.commit()

                name = form.name.data
                form.name.data = ''
                form.password.data = ''
            else:
                exists_user = True

    our_users = Users.query.order_by(Users.date_added)
    return render_template(
        "add_user.html",
        name=name,
        form=form,
        our_users=list(our_users),
        bot_name = bot_name,
        exists_user=exists_user
    )


@app.route('/api/cardlist/')
def api_cards():
    cards = CardPrototype.query.order_by(CardPrototype.id)
    return list(map(card_to_dict, cards))

def card_to_dict(card):
    dictionary = dict()
    dictionary['id'] = card.id
    dictionary['name'] = card.name
    dictionary['price'] = card.price
    dictionary['money_income'] = card.money_income
    dictionary['point_income'] = card.point_income
    dictionary['deck_count'] = card.deck_count
    if card.upgrade_limitation is not None:
        dictionary['upgrade_limitation'] = get_card_upgrade_limitation_name(card)
    return dictionary


def get_card_upgrade_limitation_name(card):
    if card.upgrade_limitation is not None:
        prototype = CardPrototype.query\
                    .filter_by(id=card.upgrade_limitation)\
                    .one()
        return prototype.name


@app.route('/cardlist/')
def cards():
    cards = list(CardPrototype.query.order_by(CardPrototype.id))
    for card in cards:
        card.upgrade_limitation_name = get_card_upgrade_limitation_name(card)
    return render_template(
        "card_list.html",
        cards=cards
    )

def new_game(p1, p2, p3, p4):
    ids = []

    for p in [p1, p2]:
        player = Users.query.filter_by(name=p).first()
        if player is None:
            return {"error": "No such user."}
        ids.append(player.id)
    for p in [p3, p4]:
        if p:
            player = Users.query.filter_by(name=p).first()
            if player is None:
                return {"error": "No such user."}
            ids.append(player.id)
        else:
            ids.append(None)

    p1_id, p2_id, p3_id, p4_id = tuple(ids)
    if p3_id is None and p4_id is not None:
        return {"error": "Player3 is not defined but player4 is."}
    session = create_game(p1_id, p2_id, p3_id, p4_id)
    return {"session": session.id}

@app.route('/api/game/new/')
def new_game_api():
    p1 = request.args.get("player1")
    p2 = request.args.get("player2")
    p3 = request.args.get("player3")
    p4 = request.args.get("player4")
    return new_game(p1, p2, p3, p4)


@app.route('/game/new/', methods=['GET', 'POST'])
def new_game_view():
    user_choices = list(map(
        lambda user: (user.name, user.name),
        Users.query.order_by(Users.date_added)
    ))

    form = NewGameForm()
    for x in [form.player1, form.player2]:
        x.choices = user_choices
    for x in [form.player3, form.player4]:
        x.choices = [('', 'Select player')] + user_choices

    if form.validate_on_submit():
        result = new_game(
            form.player1.data,
            form.player2.data,
            form.player3.data,
            form.player4.data
        )
        if result.get('session'):
            flash(
                "New game created. Session id: " + str(result['session']),
                'success'
            )
            form.player1.data = ''
            form.player2.data = ''
            form.player3.data = ''
            form.player4.data = ''
        else:
            flash(result['error'], 'error')
    return render_template(
        'new_game.html',
        form=form
    )

@app.route('/game/api/session/<session_id>')
def session_data(session_id):
    data = {}
    session = Session.query.filter_by(id=session_id).first()
    if session is None:
        return {"error": "No such session found"}

    data['session_id'] = session.id
    data['actual_phase'] = session.actual_phase

    board = Deck.query.filter_by(session_id=session_id, deck_type='board').one()
    board_cards = CardInstance.query\
                  .filter_by(deck_id=board.id)
    data['board'] = list(map(card_data, board_cards))

    players_data = []
    data['players'] = players_data

    for i, player_id in enumerate([
        session.player1,
        session.player2,
        session.player3,
        session.player4
    ]):
        if player_id is None:
            continue
        user = Users.query.filter_by(id=player_id).one()
        player_info = PlayerInfo.query.filter_by(
            session_id=session_id,
            index=i,
            player_id=player_id
        ).one()
        player_card_deck = Deck.query.filter_by(id=player_info.deck_id).one()
        player_hand_deck = Deck.query.filter_by(id=player_info.hand_id).one()

        player_cards = CardInstance.query\
                       .filter_by(deck_id=player_card_deck.id)
        player_hand = CardInstance.query\
                      .filter_by(deck_id=player_hand_deck.id)

        tokens = StartToken.query.filter_by(player_info=player_info.id)

        player_data = {}
        player_data['name'] = user.name
        player_data['money'] = player_info.money
        player_data['points'] = player_info.points
        player_data['board'] = list(map(card_data, player_cards))
        player_data['hand'] = list(map(card_data, player_hand))
        player_data['had_passed'] = player_info.had_passed
        player_data['actual_player'] = (player_id == session.actual_player
                                        and player_info.index == \
                                        session.actual_player_index
                                        )
        player_data['starting_tokens'] = list(map(
            lambda token: token.token_type,
            tokens
        ))

        players_data.append(player_data)

    counts = remaining_counts(session_id)
    for i in range(4):
        # return count of cards
        data[CARD_TYPES[i] + '_count'] = counts[i]
    return data

@app.route('/game/api/<session_id>', methods=['POST'])
def play(session_id):
    session_id = int(session_id)
    args = request.get_json()
    print("Session id:", session_id)
    # authentication and authorization
    player_name = args.get('name')
    password = args.get('password')
    if player_name is None or password is None:
        return {"error": "Name or password not specified"}
    player = Users.query.filter_by(name=player_name).first()
    if player is None:
        return {"error": "No such user found"}
    if player.id <= len(BOTS):
        return {"error": "User is server bot."}
    if player.password != password:
        return {"error": "Invalid password"}
    session = Session.query.filter_by(id=session_id).first()
    if session is None:
        return {"error": "No such game session found"}
    if session.actual_player != player.id:
        return {"error": "Not your turn"}

    return move(session.id, player.id, args)
    
    
def move(session_id, player_id, args):
    action = args.get('action')
    session = Session.query\
              .filter_by(id=session_id)\
              .one()
    player_info = PlayerInfo.query.filter_by(
        session_id=session_id,
        index=session.actual_player_index,
        player_id=player_id
    ).one()

    
    if action == 'pass':
        player_info.had_passed = True
        if check_pass(session_id):
            next_phase(session_id)
        else:
            next_player(session_id)
    else:
        player_info.had_passed = False
        board = Deck.query.filter_by(
            session_id=session_id,
            deck_type='board'
        ).one()
        card_instance = CardInstance.query\
                        .filter_by(id=args.get('card_id'))\
                        .first()
        if card_instance is None:
            return {"error": "No such card defined"}
        card = CardPrototype.query\
               .filter_by(id=card_instance.prototype_id)\
               .one()
        hand = Deck.query\
               .filter_by(id=player_info.hand_id)\
               .one()
        player_board = Deck.query.filter_by(id=player_info.deck_id).one()
        
        if action == 'buy':
            if card_instance.deck_id in [hand.id, board.id]:
                discount = 0
                card_instance_from = None
                if card.card_type == CARD_TYPES[3]:
                    card_instance_from = CardInstance.query.filter_by(
                        id=args.get('upgrade_from')
                    ).first()
                    if card_instance_from is None:
                        return {
                            "error": "Not specified from which card to upgrade"
                        }
                    card_prototype_from = CardPrototype.query.filter_by(
                        id=card_instance_from.prototype_id
                    ).one()
                    discount += card_prototype_from.price
                if card_instance.discounted:
                    discount += 1
                discount += CardInstance.query\
                            .filter_by(
                                prototype_id=card_instance.prototype_id,
                                deck_id=player_board.id
                            )\
                            .count()
                price = card.price - discount
                if price < 1:
                    price = 1
                if price <= player_info.money:
                    player_info.money -= price
                    if card_instance_from is not None:
                        db.session.delete(card_instance_from)
                    card_instance.deck_id = player_board.id
                else:
                    return {"error": "Not enough money to buy this card."}
            else:
                return {"error": "Cannot buy this card " +
                        "(not on common board nor in your hand)."}
        elif action == 'hold':
            if card_instance.deck_id != board.id:
                return {"error": "Cannot hold this card (not on common board)."}
            card_hand_count = CardInstance.query\
                              .filter_by(
                                  deck_id=hand.id
                              )\
                              .count()
            if card_hand_count < 3:
                card_instance.deck_id = hand.id
                card_instance.discounted = False
            else:
                return {"error": "Full hand (max 3 cards in hand)."}
        else:
            return {"error": "Unknown action " + action + "."}
        next_player(session_id)
        
    db.session.commit()
    # autoplay if bot strategy required
    session = Session.query\
              .filter_by(id = session_id)\
              .one()

    if session.actual_player is not None and session.actual_player <= len(BOTS):
        bot = BOTS[session.actual_player - 1]
        if bot.CARDLIST is None:
            bot.CARDLIST = api_cards()
        bot.strategy(session_data(session_id))
        result = move(session_id, session.actual_player, bot.ARGS)
        if result is None or result.get('error'):
            raise Exception(result.get('error'))

    return {"message": "Move performed succesfuly."}

def check_pass(session_id):
    session = Session.query\
              .filter_by(id = session_id)\
              .one()
    for i, p_id in enumerate([
        session.player1,
        session.player2,
        session.player3,
        session.player4
    ]):
        if p_id is None:
            continue
        player_info = PlayerInfo.query\
                      .filter_by(
                          player_id = p_id,
                          index=i,
                          session_id = session_id
                      )\
                      .one()
        if not player_info.had_passed:
            return False
    return True

def next_player(session_id):
    session = Session.query\
              .filter_by(id=session_id)\
              .one()
    player_count = PlayerInfo.query\
                   .filter_by(session_id=session_id)\
                   .count()
    session.actual_player_index += 1
    session.actual_player_index %= player_count

    if session.actual_player_index == 0:
        session.actual_player = session.player1
    elif session.actual_player_index == 1:
        session.actual_player = session.player2
    elif session.actual_player_index == 2:
        session.actual_player = session.player3
    elif session.actual_player_index == 3:
        session.actual_player = session.player4


def next_phase(session_id):
    session = Session.query\
              .filter_by(id = session_id)\
              .one()
    player_info_ids = []
    player_infos = []
    tokens = []
    for i, p_id in enumerate([
        session.player1,
        session.player2,
        session.player3,
        session.player4
    ]):
        if p_id is None:
            continue
        player_info = PlayerInfo.query\
                      .filter_by(
                          player_id = p_id,
                          index=i,
                          session_id = session_id
                      )\
                      .one()
        player_info.had_passed = False
        player_info_ids.append(player_info.id)
        player_infos.append(player_info)
    phase = CARD_TYPES.index(session.actual_phase)
    if phase == 3:
        if check_game_end(session_id):
            game_end(session_id)
            return
        else:
            # rotate start tokens
            for player_info in player_infos:
                player_tokens = StartToken.query\
                                .filter_by(player_info=player_info.id)
                tokens += list(player_tokens)
            for token in tokens:
                index = player_info_ids.index(token.player_info)
                token.player_info = player_info_ids[(index + 1) % len(player_info_ids)]

            # discount cards on board
            board = Deck.query\
                    .filter_by(session_id=session_id, deck_type='board')\
                    .one()
            cards = CardInstance.query\
                    .filter_by(deck_id=board.id)
            for card in cards:
                if card.discounted:
                    db.session.delete(card)
                else:
                    card.discounted = True
            
    else:
        # add money and points
        for player_info in player_infos:
            for card in player_card_prototypes(player_info.id):
                if card.card_type == session.actual_phase or (
                    card.card_type == CARD_TYPES[3] and
                    card.upgrade_type == session.actual_phase
                ):
                    player_info.money += card.money_income
                    player_info.points += card.point_income
                
        
    session.actual_phase = CARD_TYPES[(phase + 1) % 4]
    get_cards_from_deck(session.actual_phase, session.id)
    set_active_player(session_id)
    db.session.commit()

def player_card_prototypes(player_info_id):
    player_info = PlayerInfo.query.filter_by(id = player_info_id).one()
    deck = Deck.query\
           .filter_by(id=player_info.deck_id, deck_type='player board')\
           .one()
    cards = CardInstance.query.filter_by(deck_id=deck.id)
    result = []
    for card in cards:
        card_prototype = CardPrototype.query\
                         .filter_by(id=card.prototype_id)\
                         .one()
        result.append(card_prototype)
    return result

def check_game_end(session_id):
    decks = Deck.query.filter_by(session_id=session_id)
    for deck in decks:
        if deck.deck_type in CARD_TYPES:
            count = CardInstance.query.filter_by(deck_id=deck.id).count()
            if count == 0:
                return True
    return False

def game_end(session_id):
    session = Session.query\
              .filter_by(id = session_id)\
              .one()
    for i, p_id in enumerate([
        session.player1,
        session.player2,
        session.player3,
        session.player4
    ]):
        if p_id is None:
            continue
        player_info = PlayerInfo.query\
                      .filter_by(
                          player_id = p_id,
                          index=i,
                          session_id = session_id
                      )\
                      .one()
        hand_deck = Deck.query\
                    .filter_by(id=player_info.hand_id, deck_type='hand')\
                    .one()
        hand_count = CardInstance.query\
                     .filter_by(deck_id=hand_deck.id)\
                     .count()
        player_info.points -= hand_count * 5

        count = len(Counter(
            filter(
                lambda card: card.card_type == 'aristocrat' or\
                (card.card_type == 'upgrade' \
                 and card.upgrade_type == 'aristocrat'
                ),
                player_card_prototypes(player_info.id)
                )).keys())
        if count > 10:
            count = 10
        print("points before", player_info.points)
        print("money before", player_info.money)
        print("count", count)
        player_info.points += count * (count + 1) // 2
        player_info.points += player_info.money // 10
        player_info.money %= 10
        print("points now", player_info.points)
    session.actual_player = None
    session.actual_player_index = None
    db.session.commit()
        

def remaining_counts(session_id):
    result = []
    for card_type in CARD_TYPES[0:4]:
        deck = Deck.query.filter_by(
            session_id=session_id,
            deck_type=card_type
        ).one()
        cards_remaining = CardInstance.query.filter_by(
            deck_id=deck.id
        ).count()
        result.append(cards_remaining)
    return result


def card_data(card_instance):
    prototype = CardPrototype.query\
                .filter_by(id=card_instance.prototype_id)\
                .one()
    data = {}
    data['id'] = card_instance.id
    data['discounted'] = card_instance.discounted
    data['name'] = prototype.name
    data['price'] = prototype.price
    data['money_income'] = prototype.money_income
    data['point_income'] = prototype.point_income
    data['card_type'] = prototype.card_type
    if prototype.upgrade_type:
        data['upgrade_type'] = prototype.upgrade_type
    if prototype.upgrade_limitation:
        upgrade_prototype = CardPrototype.query\
                            .filter_by(id=prototype.upgrade_limitation)\
                            .one()
        data['upgrade_limitation'] = upgrade_prototype.name
    return data
        

@app.route('/game/session/<session_id>')
def session_info(session_id):
    data = session_data(session_id)
    # TODO
    return render_template('game.html', data=data)





if __name__ == "__main__":
    app.run()

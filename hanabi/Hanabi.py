from random import shuffle
import sys
import itertools
import os
from termcolor import *

class Card(object):
  def __init__(self, color, num):
    self.card = (color, num)
    self.color = color
    self.number = num
    self.known_traits = []
  def __repr__(self):
    return colored(self.color + ' ' + str(self.number), self.color)

class Deck(object):
  def __init__(self, game):
    self.deck = []
    for color in game.colors:
      for num in range(0, 3):
        self.deck.append(Card(color, 1))
      for num in range(2, 5):
        self.deck.append(Card(color, num))
        self.deck.append(Card(color, num))
      self.deck.append(Card(color, 5))        
    shuffle(self.deck)

  def len(self):
    return len(self.deck)

  def __repr__(self):
    return self.deck.__repr__()

  def deal(self):
    if self.deck:
      return self.deck.pop()

class Player(object):
  def __init__(self, name):
    self.name = name
    self.hand = []

  def my_cards(self):
    k = 1
    cards = []
    while k <= len(self.hand):
      card_traits = self.hand[k-1].known_traits
      print_traits = ": " + ', '.join(card_traits)

      cards.append("Card {0} {1}".format(k, print_traits if card_traits else ''))
      k += 1
    print("My cards: [" + "] [".join(cards) + "]")

  def __repr__(self):
    return self.name + "'s hand is " + "[" + "] [".join(map(Card.__repr__, self.hand)) + "]"

  def draw_a_new_card(self, game, card):
    self.hand = [c for c in self.hand if c != card]
    self.hand.append(game.deck.deal())

  def play_card(self, game):
    index = game.get_valid_integer('Which card do you want to play? Choose a card number between 1 and ' + str(len(self.hand)) + ". ", range(1, len(self.hand) + 1))
    card = self.hand[index - 1]
    self.draw_a_new_card(game, card)

    if game.board.displayed[card.color].number == card.number - 1:
      game.board.displayed[card.color] = card
      message1 = self.name + " played a " + card.__repr__() + " on the board.\n" 
      self.message_to_journal(game, message1)

      game.board.important_discards = [x for x in game.board.important_discards if x.color != card.color or x.number >= card.number]

      if card.number == 5:
        if self.check_win(game):
          print("\n Congratulations! You have set off all the fireworks.")
          os._exit(1)
        game.hints += 1
        message2 = self.name + " completed the " + card.color + " firework."
        self.message_to_journal(game, message2)
    else:
      game.fuses -= 1
      
      if game.fuses > 0:
        message = self.name + " played a " + card.__repr__() + ", which cannot be placed on the board. You have " + str(game.fuses) + " more fuse{0}".format("s." if game.fuses > 1 else ".")
        self.message_to_journal(game, message)  
      elif game.fuses == 0:
        print("The fireworks exploded in your face. You lose.")
        os._exit(1)
      game.board.add_to_discard_pile(self, game, card)

  def discard_card(self, game):
    index = game.get_valid_integer('Which card do you want to discard? Choose a number between 1 and ' + str(len(self.hand)) + '. ', range(1, len(self.hand) + 1))
    card = self.hand[index - 1]
    self.draw_a_new_card(game, card)
    game.hints = min(game.hints + 1, game.max_hints)

    message = "{0} discarded a {1}.".format(self.name, card.__repr__()) #TODO: fix all of these into a format string.
    self.message_to_journal(game, message)

    game.board.add_to_discard_pile(self, game, card)

  def give_hint(self, game):
    receiving_player_name = game.get_valid_string('Which player would you like to give a hint to, ' + self.name + "? ", [x for x in game.player_names if x != self.name])

    receiving_player = game.get_player(receiving_player_name)
    hint_is_a_number = None #TODO: Charles: This is some terrible shit.
    hint_is_a_name = None

    hint = game.get_valid_string("Type in a color or a number to tell " + receiving_player_name + " about their cards. ", game.colors + map(str, range(1, 6)))
    try:
      int(hint)
      hint_is_a_number = True 
    except ValueError:
      hint_is_a_name = True 
    index = 0
    lst_of_cards = []
    game.hints -= 1 #TODO: stick this in a separate get_valid_string/int

    if hint_is_a_number: #TODO: change to type(hint)== int:
      for card in receiving_player.hand:
        if card.number == int(hint):
          lst_of_cards.append(index)
        index += 1

    if hint_is_a_name:
      for card in receiving_player.hand:
        if card.color == hint:
          lst_of_cards.append(index)
        index += 1

    if len(lst_of_cards) > 1:
      message = receiving_player.name + "'s cards in locations " + ', '.join(map(str, lst_of_cards)) + " are " + str(hint) + "."  #TODO: merge 1st and third branch. change to .format()
    elif len(lst_of_cards) == 0:
      message = "There are no " + str(hint) + " cards in " + receiving_player.name + "'s hand."
    else:
      message = receiving_player.name + "'s card in location " + str(lst_of_cards[0]) + " is " + str(hint) + "."
    message = self.name + " gave a hint: " + message
    self.message_to_journal(game, message)

    for each_card in lst_of_cards:
      if str(hint) not in receiving_player.hand[each_card].known_traits:
            receiving_player.hand[each_card].known_traits.append(str(hint))

  def message_to_journal(self, game, message):
    print(message)
    for x in game.journal:
      if x != self.name:
        game.journal[x].append(message) #TODO: add a global journal?
  def check_win(self, game):
    for card in game.board.displayed.values():
      if card.number < 5:
        return False 
    return True

class Board(object):
  def __init__(self, colors):
    self.displayed = {'red': Card('red', 0), 
                      'green': Card('green', 0), 
                      'blue': Card('blue', 0), 
                      'yellow': Card('yellow', 0), 
                      'white': Card('white', 0)}
    self.important_discards = []
    self.no_more = [] #TODO: rename.

  def __repr__(self):
    return "Board: " + "[" + "] [".join(map(Card.__repr__, self.displayed.values())) + "]"+ "\n" + "Discards: " + "[" + "] [".join(map(Card.__repr__, self.important_discards)) + "]"

  def add_to_discard_pile(self, person, game, card):
    if card.number != 1 and game.board.displayed[card.color].number < card.number:
      for important_discard in game.board.important_discards:
        if (card.color == important_discard.color and card.number == important_discard.number) or card.number == 5:
          message = "There are no more " + card.__repr__() + "s available in the game. It is now impossible to complete the " + card.color + " firework."
          self.no_more.append(card)
          person.message_to_journal(game, message)
          self.important_discards = [x for x in self.important_discards if x != important_discard] #TODO: Change to set. (add/remove) or use list(remove)
          return None
      self.important_discards.append(card)

class Game(object):
  def __init__(self):
    self.colors = ['red', 'green', 'blue', 'yellow', 'white']
    self.deck = Deck(self)
    self.player_names = []
    self.get_names()
    self.players = [Player(name) for name in self.player_names]
    self.hints = 8     
    self.max_hints = 8
    self.fuses = 3
    self.board = Board(self.colors)
    self.deal_cards()
    self.turns_left = len(self.players) #after last card.

    self.next_players = {}
    self.current = self.players[0] 
    self.make_next_player_names()
    
    self.journal = {}
    for player in self.player_names:
      self.journal[player] = []

    self.play()

    #do I need so many init statements?

  def get_names(self):
    while True:
      if len(self.player_names) >= 5:  #Should I do one at a time or ask for a list?
        break
      value = raw_input("Enter a player's name. If all player names have been entered, type done.")     
      if value == 'exit':
        os._exit(1)
      elif value == "done":
        if len(self.player_names) < 2:
          print("There must be at least 2 players.")
          continue
        break
      elif value in self.player_names:
        print("Each name must be unique. Try again.")
        continue
      else:
        self.player_names.append(value)


  def make_next_player_names(self):
    g = iter(list(range(1, len(self.player_names))))
    for player in self.players:
      try:
        self.next_players[player.name] = self.players[next(g)]
      except StopIteration:
        self.next_players[player.name] = self.players[0]

  def get_player(self, name):
    for player in self.players:
      if player.name == name:
        return player
    return None

  def deal_cards(self):
    for each in self.players:
      if len(self.players) <= 3:
        while len(each.hand) < 5:
          each.hand.append(self.deck.deal())
      else:
        while len(each.hand) < 4:  
          each.hand.append(self.deck.deal())

  def play(self):
    possible_actions = ['discard_card', 'play_card', 'give_hint']
    
    while self.turns_left > 0:
      self.print_board()

      if self.deck.len() == 0:
        self.turns_left -= 1
        print("\n There are no more cards to draw. This is your last turn.")
      
      if self.hints == 0:
        action = self.get_valid_integer("\n" + self.current.name + ': \n  [0] Discard \n  [1] Place a card. \n  There are no more hints left. \n \n', [0,1])

      if self.hints > 0:
        action = self.get_valid_integer("\n" + self.current.name + ': \n  [0] Discard \n  [1] Place a card \n  [2] Give a hint. \n \n', [0,1,2]) #Can you merge these two lines?

      getattr(self.current, possible_actions[action])(self)

      self.journal[self.current.name] = []
      self.current = self.next_players[self.current.name]
      print("Your turn is over.")
      self.clear_screen()
      print("Pass the computer to " + self.current.name + ". Tell me when you're ready.")
      self.clear_screen()

    final_score = sum([card.number for card in self.board.displayed.values()])
    print("Game over. Your final score is " + str(final_score) + ".")
    os._exit(1)


  def get_valid_integer(self, prompt, valid_answers):
    while True:
        try:
          g = raw_input(prompt)
          value = int(g)
        except (ValueError, NameError, SyntaxError, TypeError):
          if g == 'exit' or str(g) == 'exit':
            os._exit(1)
          self.invalid_answers(str(g), valid_answers)
          continue
        if value not in valid_answers:
          self.invalid_answers(str(g), valid_answers)
          continue
        else:
          break
    return value

  def get_valid_string(self, prompt, valid_answers):
    while True:
        value = raw_input(prompt)
        if value == 'exit':
          os._exit(1)
        if value not in valid_answers:
            self.invalid_answers(value, valid_answers)
            continue
        else:
            break
    return value

  def invalid_answers(self, value, valid_answers):
    os.system('clear')
    self.print_board()
    print("\n" + value + " is not a valid response. Please try: " + ', '.join(map(str, valid_answers)) + ".\n")
    

  def print_board(self):
    other_players = [x for x in self.players if x != self.current]

    if self.journal[self.current.name]:
      print("\n" + "Since you last played: ")
      for line in self.journal[self.current.name]:
        print(line) 
    print("\n" + self.board.__repr__())
    print("Hints available: " + str(self.hints))
    print("Fuses left: " + str(self.fuses) + "\n")
    if self.board.no_more:
      print("There are no more " + "[" + "] [".join(map(Card.__repr__, self.board.no_more)) + "] cards. \n")
    if self.turns_left > 1:
      print("The next player is " + self.next_players[self.current.name].name + ".")
    for x in other_players:
      print(x.__repr__())
    self.current.my_cards()
  
  def clear_screen(self):
    g = raw_input("Press Enter to continue...")
    if g == 'exit':
      os._exit(1)
    else:
      os.system('clear')
      pass

# make prettier lists with good grammar.
#global memory??
# offer a way to go back? if you want to change your action.
# print other players' boards in order that they will play next.


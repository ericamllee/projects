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
    k = 0
    cards = []
    while k < len(self.hand):
      card_traits = self.hand[k].known_traits
      print_traits = ": " + ", ".join(card_traits)

      cards.append("Card {0}{1}".format(k + 1, print_traits if card_traits else ''))
      k += 1
    print("My cards: [{0}]\n".format("] [".join(cards) + "]"))

  def __repr__(self):
    return "{0}'s hand is [{1}]".format(self.name, "] [".join(map(Card.__repr__, self.hand)))

  def draw_a_new_card(self, game, card):
    self.hand.remove(card)
    self.hand.append(game.deck.deal())

  def play_card(self, game):
    index = game.get_valid_string('Which card do you want to play? Choose a card number between 1 and {0}.\n'.format(len(self.hand)), map(str, range(1, len(self.hand) + 1)))
    card = self.hand[int(index) - 1]
    self.draw_a_new_card(game, card)

    if game.board.displayed[card.color].number == card.number - 1:
      game.board.displayed[card.color] = card
      message1 = "{0} played a {1} on the board.\n".format(self.name, card.__repr__()) 
      self.message_to_journal(game, message1)

      game.board.important_discards = [x for x in game.board.important_discards if x.color != card.color or x.number > card.number]

      if card.number == 5:
        if self.check_win(game):
          print("\n Congratulations! You have set off all the fireworks.")
          os._exit(1)
        game.hints += 1
        message2 = "{0} completed the {1} firework.".format(self.name, card.color)
        self.message_to_journal(game, message2)
    else:
      game.fuses -= 1
      
      if game.fuses > 0:
        message = "{0} played a {1}, which cannot be placed on the board. You have {2} more fuse{3}".format(
          self.name, card.__repr__(), str(game.fuses), "s." if game.fuses > 1 else ".")
        self.message_to_journal(game, message)  
      elif game.fuses == 0:
        print("The fireworks exploded in your face. You lose.")
        os._exit(1)
      game.board.add_to_discard_pile(self, game, card)

  def discard_card(self, game):
    index = game.get_valid_string('Which card do you want to discard? Choose a number between 1 and {0}.\n'.format(len(self.hand)), map(str, range(1, len(self.hand) + 1)))
    card = self.hand[int(index) - 1]
    self.draw_a_new_card(game, card)
    game.hints = min(game.hints + 1, game.max_hints)

    message = "{0} discarded a {1}.".format(self.name, card.__repr__())
    self.message_to_journal(game, message)

    game.board.add_to_discard_pile(self, game, card)

  def give_hint(self, game):
    receiving_player_name = game.get_valid_string('Which player would you like to give a hint to, {0}?\n'.format(self.name), [x for x in game.player_names if x != self.name])

    receiving_player = game.get_player(receiving_player_name)

    hint = game.get_valid_string("Type in a color or a number to tell {0} about their cards.\n".format(receiving_player_name), game.colors + map(str, range(1, 6)))

    index = 1
    lst_of_cards = []
    game.hints -= 1

    if hint in game.colors:
      for card in receiving_player.hand:
        if card.color == hint:
          lst_of_cards.append(index)
        index += 1
    else:
      for card in receiving_player.hand:
        if card.number == int(hint):
          lst_of_cards.append(index)
        index += 1

    if len(lst_of_cards) == 0:
      message = "There are no {0} cards in {1}'s hand.".format(hint, receiving_player_name)
    else:
      message = "{0}'s card{1} in location{1} {2} {3} {4}.".format(
        receiving_player_name, 
        's' if len(lst_of_cards) > 1 else '', 
        pretty_list_and(map(str, lst_of_cards)), 
        'is' if len(lst_of_cards) == 1 else 'are', 
        hint)

    self.message_to_journal(game, "{0} gave a hint: {1}".format(self.name, message))

    for each_card in lst_of_cards:
      if hint not in receiving_player.hand[each_card - 1].known_traits:
            receiving_player.hand[each_card - 1].known_traits.append(hint)

  def message_to_journal(self, game, message):
    print(message)
    for x in game.journal:
      if x != self.name:
        game.journal[x].append(message)
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
    self.no_more = []

  def __repr__(self):
    return "Board: [{0}] \nDiscards: [{1}]".format("] [".join(map(Card.__repr__, self.displayed.values())), "] [".join(map(Card.__repr__, self.important_discards)))

  def add_to_discard_pile(self, person, game, card):
    if card.number != 1 and game.board.displayed[card.color].number < card.number:
      for important_discard in game.board.important_discards:
        if (card.color == important_discard.color and card.number == important_discard.number) or card.number == 5:
          message = "There are no more {0}s available in the game. It is now impossible to complete the {1} firework.".format(card.__repr__(), card.color)  
          self.no_more.append(card)
          person.message_to_journal(game, message)
          self.important_discards.remove(important_discard)
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
    self.turns_left = len(self.players)

    self.next_players = {}
    self.current = self.players[0] 
    self.make_next_player_names()
    
    self.journal = {}
    for player in self.player_names:
      self.journal[player] = []

    self.play()

  def get_names(self):
    while True:
      if len(self.player_names) >= 5:
        break
      value = raw_input("Enter a player's name. If all player names have been entered, type done.\n")     
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
    possible_actions = ['empty', 'discard_card', 'play_card', 'give_hint']
    
    while self.turns_left > 0:
      self.print_board()

      if self.deck.len() == 0:
        self.turns_left -= 1
        print("\n There are no more cards to draw. This is your last turn.")
      
      if self.hints == 0:
        action = self.get_valid_string("\nPlayer {0}, choose an action: \n  [1] Discard \n  [2] Place a card. \n  There are no more hints left. \n \n".format(self.current.name), ['1', '2'])

      if self.hints > 0:
        action = self.get_valid_string("\nPlayer {0}, choose an action: \n  [1] Discard \n  [2] Place a card \n  [3] Give a hint. \n \n".format(self.current.name), ['1', '2' ,'3'])

      getattr(self.current, possible_actions[int(action)])(self)

      self.journal[self.current.name] = []
      self.current = self.next_players[self.current.name]
      print("Your turn is over.")
      self.clear_screen()
      print("Pass the computer to {0}. Tell me when you're ready.".format(self.current.name))
      self.clear_screen()

    final_score = sum([card.number for card in self.board.displayed.values()])
    print("Game over. Your final score is {0}.".format(final_score))
    os._exit(1)

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
    print("\n{0} is not a valid response. Please try: {1}.\n".format(value, pretty_list_or(map(str, valid_answers))))
    

  def print_board(self):
    if self.journal[self.current.name]:
      print("\nSince you last played: ")
      for line in self.journal[self.current.name]:
        print(line) 
    print("\n" + self.board.__repr__())
    print("Hints available: " + str(self.hints))
    print("Fuses left: {0}\n".format(str(self.fuses)))
    if self.board.no_more:
      print("There are no more [{0}] cards. \n".format("] [".join(map(Card.__repr__, self.board.no_more))))
    
    self.current.my_cards()
    other_player = self.next_players[self.current.name]
    while other_player != self.current:
      print(other_player.__repr__())
      other_player = self.next_players[other_player.name]
  
  def clear_screen(self):
    g = raw_input("Press Enter to continue...")
    if g == 'exit':
      os._exit(1)
    else:
      os.system('clear')
      pass


def pretty_list_or(valid_answers):
  return ", ".join(valid_answers[:-2] + [" or ".join(valid_answers[-2:])])

def pretty_list_and(valid_answers):
  return ", ".join(valid_answers[:-2] + [" and ".join(valid_answers[-2:])])


# offer a way to go back? if you want to change your action.


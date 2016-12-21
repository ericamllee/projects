from random import shuffle
import sys
import itertools
import os
from termcolor import colored

class Card(object):
  def __init__(self, color, num):
    self.card = (color, num)
    self.color = color
    self.number = num
  def __repr__(self):
    return colored(self.color + ' ' + str(self.number), self.color)

class Deck(object):
  def __init__(self, colors, number):
    self.deck = []
    for color in colors:
      for num in range(0, 3):
        self.deck.append(Card(color, 1))
      for num in range(2, number):
        self.deck.append(Card(color, num))
        self.deck.append(Card(color, num))
      self.deck.append(Card(color, number))        
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
    self.visible_cards = []
    try:
      int(self.name)
      print("Player names cannot be integers. Please try again.")
      os._exit(1)
    except ValueError:
      return None

  def __repr__(self):
    return self.name + "'s hand is " + "[" + "] [".join(map(Card.__repr__, self.hand)) + "]"

  def play_card(self, game):
      index = game.get_valid_integer('Which card do you want to play? ', list(range(0, len(self.hand))))
      card = self.hand[index]
      self.hand = [c for c in self.hand if c != card]
      self.hand.append(game.deck.deal())

      if game.board.displayed[card.color] == card.number - 1:
        game.board.displayed[card.color] = card.number
        message1 = self.name + " played a " + card.__repr__() + " on the board.\n" 
        self.message_to_journal(game, message1)

        game.board.important_discards = [x for x in game.board.important_discards if x.color != card.color or x.number >= card.number]

        if card.number == game.max_card:
          game.hints += 1
          message2 = self.name + " completed the " + card.color + " firework."
          self.message_to_journal(game, message2)
        game.board.__repr__()
      else:
        game.fuses -= 1
        
        if game.fuses > 1:
          message = self.name + " played a " + card.__repr__() + ", which cannot be placed on the board. You have " + str(game.fuses) + " more fuses."
          self.message_to_journal(game, message)
        elif game.fuses == 1: 
          message = self.name + " played a " + card.__repr__() + ", which cannot be placed on the board. You have " + str(game.fuses) + " more fuse."
          self.message_to_journal(game, message)    
        if game.fuses == 0:
          print("The fireworks exploded in your face. You lose.")
          os._exit(1)
        game.board.add_to_discard_pile(self, game, card)

  def discard_card(self, game):
    index = game.get_valid_integer('Which card do you want to discard? ', list(range(0, len(self.hand))))
    card = self.hand[index]
    self.hand = [c for c in self.hand if c != card]
    self.hand.append(game.deck.deal())
    self.hints = min(game.hints + 1, game.max_hints)

    message = self.name + " discarded a " + card.__repr__() + "."
    self.message_to_journal(game, message)

    game.board.add_to_discard_pile(self, game, card)

  def give_hint(self, game):
    receiving_player_name = game.get_valid_string('Which player would you like to give a hint to, ' + self.name + "? ", [x for x in game.player_names if x != self.name])

    receiving_player = game.get_player(receiving_player_name)
    hint_is_a_number = None
    hint_is_a_name = None

    hint = game.get_valid_string("Type in a color or a number to tell " + receiving_player_name + " about their cards. ", game.colors + map(str, range(1, game.max_card + 1)))
    try:
      int(hint)
      hint_is_a_number = True 
    except ValueError:
      hint_is_a_name = True 
    index = 0
    lst_of_cards = []
    game.hints -= 1

    if hint_is_a_number:
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
      message = receiving_player.name + "'s cards in locations " + str(lst_of_cards) + " are " + str(hint) + "."
    elif len(lst_of_cards) == 0:
      message = "There are no " + str(hint) + " cards in " + receiving_player.name + "'s hand."
    else:
      message = receiving_player.name + "'s card in location " + str(lst_of_cards) + " is " + str(hint) + "."
    message = self.name + " gave a hint: " + message
    self.message_to_journal(game, message)

  def message_to_journal(self, game, message):
    print(message)
    for x in game.journal:
      if x != self.name:
        game.journal[x].append(message)


  # def rearrange_cards(self, game):
  #   new_order = lst(input('List the new order of your cards.'))
  #   new_hand = [self.hand[f] for f in new_order]
  #   self.hand = new_hand

class Board(object):
  def __init__(self, colors):
    self.displayed = {}
    self.important_discards = []
    self.no_more = []
    for color in colors:          
      self.displayed[color] = 0
  def __repr__(self):
    return "Board: " + " ".join(['[{} {}]'.format(k,v) for k,v in self.displayed.iteritems()])+ "\n" + "Discards: " + "[" + "] [".join(map(Card.__repr__, self.important_discards)) + "]"

  def add_to_discard_pile(self, person, game, card):
    if card.number == 5:
      self.no_more.append(card)
      message = "There are no more " + card.__repr__() + "s available in the game. It is now impossible to complete the " + card.color + " firework."
      person.message_to_journal(game, message)
    if card.number != 1 and game.board.displayed[card.color] < card.number:
      for cards in game.board.important_discards:
        if card.color == cards.color and card.number == cards.number:
          message = "There are no more " + card.__repr__() + "s available in the game. It is now impossible to complete the " + card.color + " firework."
          self.no_more.append(card)
          person.message_to_journal(game, message)
          self.important_discards = [x for x in self.important_discards if x != cards]
          return None
      self.important_discards.append(card)

class Game(object):
  def __init__(self, names, colors = ['red', 'green', 'blue', 'yellow', 'white'], number = 5):
    self.deck = Deck(colors, number)
    self.players = [Player(name) for name in names]
    self.hints = 8
    self.fuses = 3
    self.board = Board(colors)
    self.deal_cards()
    self.max_card = number
    self.max_hints = 8
    self.turns_left = len(self.players) #after last card.
    self.generator = self.next_player()
    self.journal = {}
    self.player_names = names
    for player in self.player_names:
      self.journal[player] = []
    self.next_player_names = {}
    self.make_next_player_names(self.player_names)
    self.colors = colors
    self.current = self.generator.next()
    self.play()

  def make_next_player_names(self, lst):
    g = iter(list(range(1, len(self.player_names))))
    for player in lst:
      try:
        self.next_player_names[player] = self.player_names[next(g)]
      except StopIteration:
        self.next_player_names[player] = self.player_names[0]

  def get_player(self, name):
    for player in self.players:
      if player.name == name:
        return player
    return None

  def deal_cards(self):
    for each in self.players:
      if self.players <= 3:
        while len(each.hand) <= 5:
          each.hand.append(self.deck.deal())
      else:
        while len(each.hand) <= 4:  
          each.hand.append(self.deck.deal())
  def play(self):
    possible_actions = ['discard_card', 'play_card', 'give_hint']
    
    while self.turns_left > 0:
      self.print_board()

      if self.deck.len() == 0:
        self.turns_left -= 1
        print("\n There are no more cards to draw. This is your last turn.")

      # rearranging = input("I would like to rearrange my cards. True or False? ")
      # if rearranging: 
      #   current.rearrange_cards(self)
      
      if self.hints == 0:
        action = self.get_valid_integer("\n" + self.current.name + ': \n  [0] Discard \n  [1] Place a card. \n  There are no more hints left. \n \n', [0,1])

      if self.hints > 0:
        action = self.get_valid_integer("\n" + self.current.name + ': \n  [0] Discard \n  [1] Place a card \n  [2] Give a hint. \n \n', [0,1,2])

      getattr(self.current, possible_actions[action])(self)
      self.journal[self.current.name] = []

      self.current = self.generator.next()
      if self.check_win():
        print("\n Congratulations! You have set off all the fireworks.")
        os._exit(1)
      print("Your turn is over.")
      try: 
        input("Press Enter to continue...")
      except SyntaxError:
        pass
      os.system('clear')
      print("Pass the computer to " + self.current.name + ". Tell me when you're ready.")
      try:
        input("Press Enter to continue...")
      except SyntaxError:
        pass


    final_score = sum([value for key, value in self.board.displayed])
    print("You need to learn how to set off fireworks. Your final score is " + str(final_score) + ".")
    os._exit(1)

  def check_win(self):
    for color, value in self.board.displayed.iteritems():
      if value < self.max_card:
        return False
    return True

  def next_player(self):
    iterated_players = self.players[:]
    for player in itertools.cycle(iterated_players):
      yield player

  def get_valid_integer(self, prompt, valid_answers):
    while True:
        try:
          g = raw_input(prompt)
          value = int(g)
        except (ValueError, NameError, SyntaxError, TypeError):
          if g == 'exit' or str(g) == 'exit':
            os._exit(1)
          os.system('clear')
          print("Sorry, your response must be " + ', '.join(map(str, valid_answers)) + "\n")
          self.print_board()
          continue
        if value == 'exit':
          os._exit(1)
        if value not in valid_answers:
          os.system('clear')
          print("Sorry, your response must be " + ', '.join(map(str, valid_answers)) + "\n")
          self.print_board()
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
            os.system('clear')
            print("That is not a valid input. Please try: " + ', '.join(valid_answers) + "\n")
            self.print_board()
            continue
        else:
            break
    return value

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
      print("There are no more " + str(self.board.no_more) + " cards. \n")
    if self.turns_left > 1:
      print("The next player is " + self.next_player_names[self.current.name] + ".")
    for x in other_players:
      print(x.__repr__())

# rearranging cards--offer at the same time as actions.
#"press Enter to continue... " forces exit if you press anything else.
# make prettier lists with good grammar.
# colors
# fix instructions for discarding a card. make card values 1-5. explain that it shifts cards down. New cards are added in the 5th slot.
#start game with nothing, and then input players in order.
#ask whether to use normal parameters or to change them.
  #what to change? hint number, colors, arning numbers, makeup of deck?
#global memory. 
#press enter to continue-->can't exit from there.
#hints for locations look like a list.
#limit number of players.


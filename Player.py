import json

class Player:

  def __init__(self, name, cash, roundsWon):
    self.name = name
    self.cash = cash
    self.roundsWon = roundsWon

  def __eq__(self, other):
    if not isinstance(other, Player):
      # Don't attempt to compare against unrelated types
      return NotImplemented

    return self.name == other.name
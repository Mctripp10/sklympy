import discord
import os
import numpy as np

from replit import db

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

# Runs on start
@client.event
async def on_ready():
    print("{0.user} is now online!".format(client))

### Global variables ### 
  
season = "Winter"
year = 2023
startCash = 100
resetData = False

### Config ###

if resetData:
  db.clear()

### Methods ###

# Returns a string list of all players entered
def get_players():
    if "players" in db.keys():
      players = db["players"]
    else:
      return None
      
    list = ""
    for player in players:
        list += player + "\n"
    return list

# Adds user to list of players if not already entered
def add_player(player):
  if "players" in db.keys():
    players = db["players"]
    if player[0] in players:
      return False
    else:
      players[player[0]] = player
      db["players"] = players
      return True
  else:
    db["players"] = { player[0] : player }
    return True

# Used to update attributes of a specific player, such as current cash, etc.
def update_players(player):
  if "players" in db.keys():
    players = db["players"]
    players[player[0]] = player
    db["players"] = players

# Used to update attributes of a specific challenge, such as competitor names or winner
def update_challenges(challenge):
  if "challenges" in db.keys():
    challenges = db["challenges"]
    challenges[challenge[0]] = challenge
    db["challenges"] = challenges
  else:
    db["challenges"] = { challenge[0] : challenge }

# Function that will ensure the bot only records the user's message if sent in DMs, as well as ensure correct bet input
def check(m, message, playerCash, players, challenges, name):      
  
  if m.content.startswith("!sko"):
      print("exiting bet")
      return True, ""
  
  if isinstance(m.channel, discord.channel.DMChannel) and m.author == message.author:
      reply = m.content.split()
      print(reply)
      challengeNum = reply[0]
      betAmount = int(reply[1])
      betName = reply[2].lower().capitalize()
      if int(challengeNum) < 1:
          return False, "Invalid challenge number"
      elif betAmount > playerCash or betAmount < 1:
          return False, "Invalid bet amount"
      elif betName not in players.keys():
          return False, "Invalid player name"
      else:
        if challengeNum not in challenges:
            return False, "Challenge {} has not been started yet".format(challengeNum)
        else:
            challenge = challenges[challengeNum]
            bets = challenge[4]
            if name in bets:
              return False, "You have already bet on challenge {}".format(challengeNum)
            else:
              return True, ""
  else:
    return False, "Messaged in other channel"

# Method that compiles all bets into string printable format and calculates total pot value in the process
def bet_summary(bets):
  list = ""
  totalPot = 0
  for bet in bets:
    bet = bets[bet]
    name = bet[0]
    betAmount = int(bet[1])
    betName = bet[2]
    
    totalPot += betAmount
    list += ":point_right:" + name + " bet " + str(betAmount) + " on " + betName + "\n"
  return list, totalPot

# Method that calculates the return values for each player given their bet and winner of a challenge
def calc_returns(challenge):
  comp1 = challenge[1]
  winner = challenge[3]
  bets = challenge[4]

  comp1Bets = 0
  comp2Bets = 0
  
  for name in bets:
    bet = bets[name]
    betAmount = bet[1]
    betName = bet[2]
    if betName == comp1:
      comp1Bets += betAmount
    else:
      comp2Bets += betAmount

  totalBets = comp1Bets + comp2Bets
  if winner == comp1:
    winnerBets = comp1Bets
  else:
    winnerBets = comp2Bets

  for name in bets:
    bet = bets[name]
    name = bet[0]
    betAmount = bet[1]
    betName = bet[2]
    if betName == winner:
      returnVal = totalBets * (betAmount/winnerBets)
    else:
      returnVal = 0
    bet[3] = returnVal
    bets[name] = bet
    
  challenge[4] = bets
  update_challenges(challenge)

# Method that actually stores and adds the return values to the corresponding players money value given the results from a specific challenge
# Also returns a string list of what everyone got for printing purposes
def store_returns(challenge):
  bets = challenge[4]
  players = db["players"]
  list = ""

  for name in players:
    player = players[name]
    returnVal = bets[name][3]
    if returnVal != 0:
      player[1] += returnVal
      list += name + " won " + str(returnVal) + " moneys\n"
      update_players(player)
  return list

### Events ###

# Triggers anytime a message is sent by anyone
@client.event
async def on_message(message):
    msg = message.content
    author = message.author
    name = str(author).split("#")[0]

    if author == client.user:        # So Sklympy doesn't talk to himself
        return

    if msg.startswith("!sko"):
        msg = msg[5:len(msg)]        # Get command after !sko

        # Main switch (match) statement that decides what code to run based on varying commands
        match msg:

            # Enters player into the skylympics
            case "enter":
                player = [name, startCash, 0]
                if add_player(player):
                  await message.channel.send("Welcome {} to the {} {} Skylympics!".format(author.mention, year, season))
                else:
                  await message.channel.send("Hello again {}. You are already entered in the Skylympics :)".format(author.mention))

            # Lists all players currently entered
            case "players":
                list = get_players()
                if list != None:
                  await message.channel.send(list)
                else:
                  await message.channel.send("No players are currently entered in the {} {} Skylympics".format(year, season))

            # Shows the user their skylympics stats (or at least challenge day stats)
            case "stats":
                if "players" in db.keys():
                  players = db["players"]
                  if name in players:
                    player = players[name]
                    await message.channel.send("__**{}**__ :sunglasses:\nMoney: {}\nChallenges Won: {}".format(name, player[1], player[2]))
            
            
            # Privately DMs user to make their bet for the corresponding challenge and stores it
            case "bet":
                if "players" in db.keys() and "challenges" in db.keys():
                  players = db["players"]
                  challenges = db["challenges"]
                  
                  player = players[name]
                  playerCash = player[1]

                  
                  if (playerCash == 0):
                      await author.send("Haha. You're broke. No more betting for you :) :(")
                  else:
                      await author.send("__**You have {} money**__\nInput challenge #, bet amount, and who you are betting on (ex: 6 120 Speed2411)\nUse command *!sko players* to see player name list".format(playerCash))

                      exit = False
                      msg = await client.wait_for('message')
                      reply = msg.content.split()
                      challengeNum = reply[0]
                    
                      if not msg.content.startswith("!sko"):
                          cond, errorMessage  = check(msg, message, playerCash, players, challenges, name)
                          while not cond:
                              if errorMessage != "Messaged in other channel":
                                await author.send(errorMessage)
                                
                              msg = await client.wait_for('message')
                              reply = msg.content.split()
                              challengeNum = reply[0]
                              if not msg.content.startswith("!sko"):
                                cond, errorMessage  = check(msg, message, playerCash, players, challenges, name)
                              else:
                                exit = True
                                break
                          if not exit:
                            betAmount = int(reply[1])
                            betName = reply[2]
                            challenge = challenges[challengeNum]
                            returnVal = 0
                            bet = [name, betAmount, betName, returnVal]
                            bets = challenge[4]
                            
                            bets[name] = bet
                            challenge[4] = bets
                            update_challenges(challenge)
      
                            playerCash -= betAmount
                            player[1] = playerCash
                            update_players(player)
      
                            await author.send("Bet successful. Betting {} on {} in challenge #{}".format(betAmount, betName, challengeNum))
                else:
                  if "players" not in db.keys():
                    await message.channel.send("No players currently available to bet on")
                  else:
                    await message.channel.send("No challenges currently available to bet on")

            # Command used to start a challenge given the number and competitors
            case s if s.startswith("start challenge"):
              msg = msg.split()
              challengeNum = int(msg[2])
              update = True
              if "challenges" in db.keys():
                challenges = db["challenges"]
                if challengeNum in challenges:
                  await message.channel.send("Challenge {} has already been started".format(challengeNum))
                  update = False
                
              if update:
                competitor1 = msg[3].lower().capitalize()
                competitor2 = msg[5].lower().capitalize()
                winner = "TBD"
                bets = {}
  
                challenge = [challengeNum, competitor1, competitor2, winner, bets]
                update_challenges(challenge)
                await message.channel.send("Successfully started challenge {}: {} vs {}".format(challengeNum, competitor1, competitor2))
              
            # Command used to end a challenge given the number and winner
            case s if s.startswith("end challenge"):
              msg = msg.split()
              num = msg[2]
              winner = msg[3].lower().capitalize()

              if "challenges" in db.keys():
                challenges = db["challenges"]
                if num in challenges:
                  challenge = challenges[num]
                  if challenge[3] == "TBD":
                    challenge[3] = winner
                    
                    if "players" in db.keys():
                      players = db["players"]
                      if winner in players:
                        player = players[winner]
                        player[2] += 1
                        update_players(player)
                        update_challenges(challenge)
                        calc_returns(challenge)
                        results = store_returns(challenge)
                        await message.channel.send("{} has been declared winner of challenge {}\n\n__Challenge {} results__\n{}".format(winner, num, num, results))
                      else:
                        await message.channel.send("{} is not a player".format(winner))
                    else:
                      await message.channel.send("{} is not a player".format(winner))
                  else:
                    await message.channel.send("Challenge {} has already ended".format(num))
                else:
                  await message.channel.send("Challenge {} has not been started yet".format(num))
              else:
                await message.channel.send("No challenges have been started yet")

            # Allows user to view the results or current stats of a challenge
            case s if s.startswith("view challenge"):
              msg = msg.split()
              challengeNum = msg[2]

              if "challenges" in db.keys():
                challenges = db["challenges"]
                if challengeNum in challenges:
                  challenge = challenges[challengeNum]
                  bets = challenge[4]
                  winner = challenge[3]

                  summary, totalPot = bet_summary(bets)
                  await message.channel.send("__Challenge {}__\nTotal pot: {}\nWinner: {}\n\n{}".format(challengeNum, totalPot, winner, summary))
                else:
                  await message.channel.send("Challenge {} has not been started yet".format(challengeNum))
              else:
                await message.channel.send("No challenges have been started yet")

client.run(os.environ['TOKEN'])
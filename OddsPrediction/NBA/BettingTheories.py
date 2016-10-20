import MySQLdb, re, time, sys, datetime, math, signal
import matplotlib.pyplot as plt
import numpy as np
from config import CONFIG as config
import StatsDB


db = StatsDB.StatsDB("hockey")
book = "Pinnacle"
bankroll = 13270
rel_bet_size = .05
abs_bet_size = 700

####################### Theory 1 ###############################
### Use Pinnacle odds and threshold to make bets after line movements
#
# 1. For each game, get opening lines from Pinnacle
# 2. Remove margins such that probabilities add to 1
# 3. Select "edge" threshold that determines bets
# 4. Place bet if threshold is breached

def relative_bet_size(bank, rel):
	return bank*rel

def absolute_bet_size():
	global abs_bet_size
	return abs_bet_size

def place_bet(season,game_id,team,line):
	global bankroll
	# Put bet in escrow
	#bet_size = relative_bet_size(bankroll, rel_bet_size)
	bet_size = absolute_bet_size()
	bankroll -= bet_size
	# Check if the bet wins
	won = check_bet_outcome(season,game_id,team)

	if won: 
		bankroll += bet_size*line
		print "After betting ${0} on \'{1}\' and winning at {2}, your new bankroll is: ${3}".format(bet_size,team,line,bankroll)
	else:
		print "After betting ${0} on \'{1}\' and losing, your new bankroll is: ${2}".format(bet_size,team,bankroll)


def check_bet_outcome(season,game_id,team):
	#  Query DB to check bet outcome
	query = "SELECT winner FROM Games{0} WHERE gameID={1} AND team=\'{2}\'".format(season,game_id,team)
	winner = db.execute_query(query)[0][0]
	if winner == team: return 1
	return 0
	print "Winner ", winner




# Get game info for the season
season = 20152016
query = "SELECT gameID,team,opponent FROM Games{0} WHERE location='home' ORDER BY gameID;".format(season)
season_data = db.execute_query(query)
bet_count = 0

for game in season_data:
	gid = int(game[0])
	home_team = game[1]
	away_team = game[2]

	# 1. Get opening lines for each team
	home_odds = []
	away_odds = []
	query = "SELECT odds, opponentOdds FROM Moneylines{0} WHERE gameID={1} AND team=\'{2}\' AND bookName=\'{3}\';".format(season,gid,home_team,book)
	game_odds = db.execute_query(query)
	for odds in game_odds:
		home_odds.append(odds[0])
		away_odds.append(odds[1])
	if not home_odds or not away_odds: continue
	home_open = home_odds[0]
	away_open = away_odds[0]


	# 2. Remove margins from opening lines
	margin = 1/home_open + 1/away_open - 1
	home_open_fair = home_open + home_open*margin
	away_open_fair = away_open + away_open*margin

	# 3. Set threshold
	rel_thresh = 0.025
	home_thresh = home_open_fair + home_open_fair*rel_thresh
	away_thresh = away_open_fair + away_open_fair*rel_thresh

	# 4. Place bet if applicable
	for odd in home_odds:
		if odd >= home_thresh and odd < 2 and odd > 1.7:
			print "Game: ", gid
			print "Home thresh / home odds: ", home_thresh, " / ", odd
			place_bet(season,gid,home_team,odd)
			bet_count += 1
			break
	for odd in away_odds:
		if odd >= away_thresh and odd < 2 and odd > 1.7:
			print "Game: ", gid
			print "Away thresh / away odds: ", away_thresh, " / ", odd
			place_bet(season,gid,away_team,odd)
			bet_count += 1
			break

print bet_count




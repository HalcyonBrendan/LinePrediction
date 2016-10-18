import MySQLdb, re, time, sys, datetime, math, signal
import matplotlib.pyplot as plt
import numpy as np
from config import CONFIG as config
import StatsDB

####################### Theory 1 ###############################
### Use Pinnacle odds and threshold to make bets after line movements
#
# 1. For each game, get opening lines from Pinnacle
# 2. Remove margins such that probabilities add to 1
# 3. Select "edge" threshold that determines bets
# 4. Place bet if threshold is breached

class Bank(object):
	def __init__(self, sport='hockey', bankroll=1000, relative=.02, absolute=20, book="Pinnacle", use_relative_bet=True):
		self.db = StatsDB.StatsDB(sport)
		self.book = book
		self.bankroll = bankroll
		self.rel_bet_size = relative
		self.abs_bet_size = absolute
		self.use_relative_bet = use_relative_bet		

	def _bet_size(self):
		if self.use_relative_bet:
			return self.bankroll * self.rel_bet_size
		else:
			return self.abs_bet_size

	def place_bet(self, season, game_id, team, line):
		bet_size = self._bet_size()
		self.bankroll -= bet_size
		if self.check_bet_outcome(season, game_id, team):
			self.bankroll += bet_size * line
			print "After betting ${0} on \'{1}\' and winning at {2}, your new bankroll is: ${3}".format(bet_size, team, line, self.bankroll)
		else:
			print "After betting ${0} on \'{1}\' and losing, your new bankroll is: ${2}".format(bet_size,team, self.bankroll)

	def check_bet_outcome(self, season, game_id, team):
		#  Query DB to check bet outcome
		query = "SELECT winner FROM Games{0} WHERE gameID={1} AND team=\'{2}\'".format(season,game_id,team)
		winner = self.db.execute_query(query)[0][0]
		if winner == team: return 1
		return 0
		print "Winner ", winner


class Data(object):
	def __init__(self, bank, seasons=[20152016], threshold=0.02):
		if type(seasons) is not list: 
			seasons = [seasons]
		self.seasons = seasons
		self.threshold = threshold
		self.bank = bank
		self.season_datas = [self._season_data(season) for season in self.seasons]

	def _season_data(self, season):
		query = "SELECT gameID,team,opponent FROM Games{0} WHERE location='home' ORDER BY gameID;".format(season)
		return bank.db.execute_query(query)

	def _compute_thresholds(self, home_open, away_open):
		home_thresh = home_open + home_open*self.threshold
		away_thresh = away_open + away_open*self.threshold
		return home_thresh, away_thresh

	def _compute_thresholds2(self, home_open, away_open):
		home_thresh = 1/((1/home_open) - self.threshold)
		away_thresh = 1/((1/away_open) - self.threshold)
		return home_thresh, away_thresh

	def execute(self):
		bet_count = 0
		for season_data, season in zip(self.season_datas, self.seasons):
			for game in season_data:
				gid = int(game[0])
				home_team = game[1]
				away_team = game[2]

				# 1. Get opening lines for each team
				home_odds = []
				away_odds = []
				query = "SELECT odds, opponentOdds FROM Moneylines{0} WHERE gameID={1} AND team=\'{2}\' AND bookName=\'{3}\';".format(season, gid, home_team, self.bank.book)
				game_odds = self.bank.db.execute_query(query)
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
				#home_thresh, away_thresh = self._compute_thresholds(home_open_fair, away_open_fair)
				home_thresh, away_thresh = self._compute_thresholds2(home_open_fair, away_open_fair)

				# 4. Place bet if applicable
				for odd in home_odds:
					if odd >= home_thresh and odd < 5:
						print "Game: ", gid
						print "Home thresh / home odds: ", home_thresh, " / ", odd
						self.bank.place_bet(season,gid,home_team,odd)
						bet_count += 1
						break
				for odd in away_odds:
					if odd >= away_thresh and odd < 5:
						print "Game: ", gid
						print "Away thresh / away odds: ", away_thresh, " / ", odd
						self.bank.place_bet(season,gid,away_team,odd)
						bet_count += 1
						break
		print bet_count

bank = Bank(use_relative_bet=False)
data = Data(bank, seasons=[20152016])
data.execute()

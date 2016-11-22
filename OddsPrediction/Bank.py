import MySQLdb, re, time, sys, datetime, math, signal
import matplotlib.pyplot as plt
import numpy as np
import StatsDB

####################### Theory 1 ###############################
### Use Pinnacle odds and threshold to make bets after line movements
#
# 1. For each game, get opening lines from Pinnacle
# 2. Remove margins such that probabilities add to 1
# 3. Select "edge" threshold that determines bets
# 4. Place bet if threshold is breached

class Bank(object):
	def __init__(self, league='NHL', bankroll=1000, relative=.02, absolute=25, book="Pinnacle", use_relative_bet=True):
		self.db = StatsDB.StatsDB(league)
		self.league = league
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

	def place_bet(self, season, game_id, team, choice, line, thresh):
		bet_size = self._bet_size()
		self.bankroll -= bet_size
		outcome = self.check_bet_outcome(season, game_id, team, choice)
		if outcome == 1:
			#self.bankroll += bet_size * thresh
			self.bankroll += bet_size * line
			print "After betting ${0} on \'{1}\' and winning at {2}, your new bankroll is: ${3}".format(bet_size, choice, line, self.bankroll)
		elif outcome == -1:
			self.bankroll += bet_size
		else:
			print "After betting ${0} on \'{1}\' and losing, your new bankroll is: ${2}".format(bet_size, choice, self.bankroll)

	def check_bet_outcome(self, season, game_id, team, choice):
		#  Query DB to check bet outcome
		query = "SELECT winner FROM {0}_Moneylines{1} WHERE gameID={2} AND team=\'{3}\';".format(self.league,season,game_id,team)
		try:
			winner = self.db.execute_query(query)[0][0]
		except:
			print "Had problem finding winner. Returning bet amount to bankroll."
			time.sleep(2)
			return -1
		print "WINNER v CHOICE: ", winner, " ", choice
		if winner == choice: return 1
		return 0


class Data(object):
	def __init__(self, bank, hasDraws, seasons=[20152016], threshold=0.02):
		if type(seasons) is not list: 
			seasons = [seasons]
		self.seasons = seasons
		self.threshold = threshold
		self.bank = bank
		self.hasDraws = hasDraws
		self.season_datas = [self._season_data(season) for season in self.seasons]

	def _season_data(self, season):
		query = "SELECT gameID,homeTeam,awayTeam FROM gameIDs WHERE season={0} AND sport=\'{1}\' ORDER BY gameID;".format(season,self.bank.league)
		return bank.db.execute_query(query)

	def _compute_thresholds(self, home_open, away_open, draw_open=None):
		home_thresh = home_open + home_open*self.threshold
		away_thresh = away_open + away_open*self.threshold
		draw_thresh = None
		if not draw_open is None:
			draw_thresh = draw_open + draw_open*self.threshold

		return home_thresh, away_thresh, draw_thresh

	def _compute_thresholds2(self, home_open, away_open, draw_open=None):

		home_thresh = 1/((1/home_open) - self.threshold)
		away_thresh = 1/((1/away_open) - self.threshold)
		draw_thresh = None
		if not draw_open is None:
			draw_thresh = 1/((1/draw_open) - self.threshold)

		return home_thresh, away_thresh, draw_thresh

	def execute(self):
		bet_count = 0
		for season_data, season in zip(self.season_datas, self.seasons):
			for game in season_data:
				gid = int(game[0])
				home_team = game[1]
				away_team = game[2]

				if home_team == away_team: continue

				# 1. Get opening lines for each team
				home_odds = []
				away_odds = []
				draw_odds = []
				if not self.hasDraws:
					query = "SELECT odds, opponentOdds FROM {0}_Moneylines{1} WHERE gameID={2} AND team=\'{3}\' AND bookName=\'{4}\' ORDER BY pollTime;".format(self.bank.league,season, gid, home_team, self.bank.book)
					#query = "SELECT odds, opponentOdds FROM {0}_Moneylines{1} WHERE gameID={2} AND team=\'{3}\' AND bookName=\'{4}\';".format(self.bank.league,season, gid, home_team, self.bank.book)				
				else:
					query = "SELECT odds, opponentOdds, drawOdds FROM {0}_Moneylines{1} WHERE gameID={2} AND team=\'{3}\' AND bookName=\'{4}\' ORDER BY pollTime;".format(self.bank.league,season, gid, home_team, self.bank.book)
					#query = "SELECT odds, opponentOdds, drawOdds FROM {0}_Moneylines{1} WHERE gameID={2} AND team=\'{3}\' AND bookName=\'{4}\';".format(self.bank.league,season, gid, home_team, self.bank.book)
				game_odds = self.bank.db.execute_query(query)
				for odds in game_odds:
					home_odds.append(odds[0])
					away_odds.append(odds[1])
					if self.hasDraws: draw_odds.append(odds[2])
				if not home_odds or not away_odds: continue
				home_open = home_odds[0]
				away_open = away_odds[0]
				if self.hasDraws: draw_open = draw_odds[0]

				# 2. Remove margins from opening lines
				margin = 1./home_open + 1./away_open - 1.
				if self.hasDraws: margin = 1./home_open + 1./away_open +1./draw_open - 1.
				home_open_fair = home_open + home_open*margin
				away_open_fair = away_open + away_open*margin
				if self.hasDraws: draw_open_fair = draw_open + draw_open*margin
				else: draw_open_fair = None

				# 3. Set threshold
				#home_thresh, away_thresh = self._compute_thresholds(home_open_fair, away_open_fair)
				home_thresh, away_thresh, draw_thresh = self._compute_thresholds2(home_open_fair, away_open_fair, draw_open_fair)

				# 4. Place bet if applicable
				max_odd = 25
				min_odd = 1.01
				#print "home odds"
				'''
				for odd in home_odds:
					#print odd
					if odd >= home_thresh and odd < home_thresh*2 and odd > min_odd:
						print "Game: ", gid
						print "Home thresh / home odds: ", home_thresh, " / ", odd
						self.bank.place_bet(season,gid,home_team,home_team,odd, home_thresh)
						bet_count += 1
						break
				#print "away odds"
				for odd in away_odds:
					#print odd
					if odd >= away_thresh and odd < away_thresh*2 and odd > min_odd:
						print "Game: ", gid
						print "Away thresh / away odds: ", away_thresh, " / ", odd
						self.bank.place_bet(season,gid,away_team,away_team,odd,away_thresh)
						bet_count += 1
						break
				#print "draw odds"
				if self.hasDraws:
					#print odd
					for odd in draw_odds:
						if odd >= draw_thresh and odd < draw_thresh*2 and odd > min_odd:
							print "Game: ", gid
							print "Draw thresh / draw odds: ", draw_thresh, " / ", odd
							self.bank.place_bet(season,gid,home_team,"DRAW",odd,draw_thresh)
							bet_count += 1
							break
				'''
				self.bank.place_bet(season,gid,home_team,"DRAW",draw_odds[-1],draw_thresh)

		print bet_count

if __name__ == "__main__":
	# TO SET
	league = 'FRA'
	seasons = [20132014]
	hasDraws = 0
	if league in ['BPL','FRA']: hasDraws = 1

	bank = Bank(league=league,use_relative_bet=False)
	data = Data(bank, hasDraws, seasons=seasons)
	data.execute()

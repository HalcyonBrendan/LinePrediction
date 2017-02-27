"""
Run betting season simulations by randomly (and naively) guessing game winners, then determine
histogram of outcomes when optimal/anti-optimal/other-specified bets are made. This should provide
a better understanding of the impact that line shopping and time-(in)dependent arbitrage betting
is likely to have.
"""
import MySQLdb, re, time, sys, math, signal
import numpy as np
import pandas as pd
pd.set_option('display.max_rows', 100)
pd.set_option('display.max_columns', 20)
pd.set_option('display.width', 1000)
import HalcyonNHLdb
import GamesByDate
import Bookie


class SeasonData(object):

	def __init__(self,season,books=['Pinnacle']):
		self.db = HalcyonNHLdb.HalcyonNHLdb()
		self.season = season
		self.books = books
		self.odds_data = self.get_odds_data()
		self.homeaway_data = self.get_homeaway_data()
		self.games = GamesByDate.GamesByDate(season)

	def get_homeaway_data(self):
		query = "SELECT gameID, date, team as home, opponent as away, winner FROM Games{0} WHERE location=\"home\"".format(self.season)
		homeaway_data = pd.read_sql(query,con=self.db.get_connection())
		return homeaway_data

	def get_odds_data(self):
		# Get all data for the season
		if len(self.books) == 1:
			query = "SELECT gameID, date, team, max(odds) as max, min(odds) as min FROM Moneylines{0} WHERE bookName=\"{1}\" GROUP BY gameID,team,date;".format(self.season,self.books[0])
		else:
			query = "SELECT gameID, date, team, max(odds) as max, min(odds) as min FROM Moneylines{0} WHERE bookName in {1} GROUP BY gameID,team,date;".format(self.season,tuple(self.books))
		odds_data = pd.read_sql(query,con=self.db.get_connection())
		return odds_data


class SimulateSeason(object):

	def __init__(self,data,bookie,home_prob,goodness):
		self.data = data
		self.bookie = bookie
		self.home_prob = home_prob
		self.goodness = goodness

	def simulate(self):
		for game_date in self.data.games.game_dates:
			for game_id in self.data.games.gbd[game_date]:
				# Randomly select pick
				pick = self.select_pick(game_id)
				# Get odds you want (0=worst recorded, 1=best recorded)
				odds = self.select_odds(game_id,game_date,pick)
				if odds < 0:
					continue
				# Find out actual winner
				winner = self.get_winner(game_id,game_date)
				# Place bet
				self.bookie.place_bet(pick,winner,odds,1)

	def select_pick(self,game_id):
		home_winner = (np.random.uniform() < self.home_prob)
		if home_winner:
			team = self.data.homeaway_data.loc[self.data.homeaway_data["gameID"].isin([game_id]),"home"].values[0]
		else:
			team = self.data.homeaway_data.loc[self.data.homeaway_data["gameID"].isin([game_id]),"away"].values[0]
		return team

	def select_odds(self,game_id,game_date,pick):
		try:
			min_odds = float(self.data.odds_data.loc[(self.data.odds_data["gameID"].isin([game_id])) & (self.data.odds_data["date"].isin([game_date])) & (self.data.odds_data["team"].isin([pick])),"min"].values[0])
			max_odds = float(self.data.odds_data.loc[(self.data.odds_data["gameID"].isin([game_id])) & (self.data.odds_data["date"].isin([game_date])) & (self.data.odds_data["team"].isin([pick])),"max"].values[0])
		except:
			return -1
		odds = min_odds + self.goodness*(max_odds-min_odds)
		return odds

	def get_winner(self,game_id,game_date):
		winner = self.data.homeaway_data.loc[(self.data.homeaway_data["gameID"].isin([game_id])) & (self.data.homeaway_data["date"].isin([game_date])),"winner"].values[0]
		return winner

def execute(season,home_prob,goodness,silent,num_sims):

	sd = SeasonData(season)
	earnings = []
	for i in range(num_sims):
		print "Simulation", i+1, "of", num_sims
		bk = Bookie.Bookie(home_prob,goodness,silent=silent)
		ss = SimulateSeason(sd,bk,home_prob,goodness)
		ss.simulate()
		earnings.append(bk.balance)
		bk.summary()
	print "Average:", sum(earnings)/len(earnings), " Best:", max(earnings), " Worst:", min(earnings) 

if __name__ == "__main__":
	season = 20152016
	home_prob = .5
	goodness = 0.
	silent = True
	num_sims = 100
	execute(season,home_prob,goodness,silent,num_sims)



"""
Run betting season simulations by randomly (and naively) guessing game winners, then determine
histogram of outcomes when optimal/anti-optimal/other-specified bets are made. This should provide
a better understanding of the impact that line shopping and time-(in)dependent arbitrage betting
is likely to have.
"""
import MySQLdb, re, time, sys, math, signal
import numpy as np
import pandas as pd
pd.set_option('display.max_rows', 30)
pd.set_option('display.max_columns', 20)
pd.set_option('display.width', 1000)
import HalcyonNHLdb
import Bookie


class SeasonData(object):

	def __init__(self,season,books=['Pinnacle','SportsInteraction']):
		self.db = HalcyonNHLdb.HalcyonNHLdb()
		self.season = season
		self.books = books
		self.odds_data = self.get_odds_data()
		self.home_data = self.odds_data.loc[self.odds_data["team"]==self.odds_data["home"]]
		self.home_data = self.home_data.reset_index(drop=True)
		self.away_data = self.odds_data.loc[self.odds_data["team"]==self.odds_data["away"]]
		self.away_data = self.away_data.reset_index(drop=True)

	def get_odds_data(self):
		if len(self.books) == 1:
			query = "SELECT t2.gameID, t2.date, t2.team as team, t1.team as home, t1.opponent as away,\
				t1.winner as winner, t2.max as max, t2.min as min FROM (SELECT gameID, date, team,\
				opponent, winner FROM Games{0} WHERE location=\"home\") AS t1 RIGHT JOIN (SELECT\
				gameID, date, team, max(odds) AS max, min(odds) AS min FROM Moneylines{0} WHERE\
				bookName=\"{1}\" GROUP BY gameID, team, date) AS t2 ON t1.gameID=t2.gameID AND\
				t1.date=t2.date;".format(self.season,self.books[0])
		elif len(self.books) > 1:
			query = "SELECT t2.gameID, t2.date, t2.team as team, t1.team as home, t1.opponent as away,\
				t1.winner as winner, t2.max as max, t2.min as min FROM (SELECT gameID, date, team,\
				opponent, winner FROM Games{0} WHERE location=\"home\") AS t1 RIGHT JOIN (SELECT\
				gameID, date, team, max(odds) AS max, min(odds) AS min FROM Moneylines{0} WHERE\
				bookName in {1} GROUP BY gameID, team, date) AS t2 ON t1.gameID=t2.gameID AND\
				t1.date=t2.date;".format(self.season,tuple(self.books))
		data = pd.read_sql(query,con=self.db.get_connection())
		return data.dropna()


class SimulateSeason(object):

	def __init__(self,data,bookie,home_prob,goodness):
		self.data = data
		self.bookie = bookie
		self.home_prob = home_prob
		self.goodness = goodness
		self.simulate()

	def simulate(self):
		# Decife if we pick home team to win for each game in data
		pick_home = (np.random.uniform(size=len(self.data.odds_data.index)/2) < self.home_prob)
		# Get picks from corresponding rows of from home_data and away_data frames
		home_picks = self.data.home_data.loc[pick_home]
		away_picks = self.data.away_data.loc[~pick_home]
		picks = pd.concat([home_picks,away_picks])
		picks = picks.sort_values(["date","gameID"])
		# Calculate and add column of odds based on goodness of skill
		picks["odds"] = picks["min"] + self.goodness*(picks["max"]-picks["min"])
		# Place bets
		self.bookie.place_bets(picks["team"].values,picks["winner"].values,picks["odds"])


class BuildHistograms(object):

	def __init__(self,season,home_prob,goodness,silent,num_sims):
		self.data = SeasonData(season)
		self.home_prob = home_prob
		self.goodness = goodness
		self.silent = silent
		self.num_sims = num_sims
		self.earnings = []
		self.execute()

	def execute(self):
		for i in range(self.num_sims):
			print "Simulation", i+1, "of", self.num_sims,"\r",
			bk = Bookie.Bookie(home_prob,goodness,silent=silent)
			ss = SimulateSeason(self.data,bk,self.home_prob,self.goodness)
			self.earnings.append(bk.balance)
			#bk.summary()
		earnings = np.array(self.earnings)
		print "\nMean:", np.mean(earnings)
		print "Quintiles [0, 20, 40, 60, 80, 100]:"
		print np.percentile(earnings, np.arange(0, 120, 20))
		#print "Average:", sum(self.earnings)/len(self.earnings), " Best:", max(self.earnings), " Worst:", min(self.earnings),"\n" 

if __name__ == "__main__":
	season = 20152016
	home_prob = .5
	goodness = 1.
	silent = True
	num_sims = 10000
	BuildHistograms(season,home_prob,goodness,silent,num_sims)



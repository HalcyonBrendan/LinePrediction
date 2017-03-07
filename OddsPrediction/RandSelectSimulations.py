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

	def __init__(self,season,books=['Pinnacle','FiveDimes','SportsInteraction','Bet365']):
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
			query = 'SELECT t1.gameID, t1.date, t1.team, t0.team as home, t0.opponent as away, t0.winner, t2.openOdds, t3.closeOdds, t4.maxOdds\
				FROM (SELECT gameID, date, team, opponent, winner FROM Games{0} WHERE location="home") as t0\
				INNER JOIN (SELECT gameID, date, team, min(pollTime) as openTime, max(pollTime) as closeTime FROM Moneylines{0} WHERE bookName="{1}" GROUP BY gameID, team, date) as t1\
				ON (t0.gameID=t1.gameID AND t0.date=t1.date)\
				INNER JOIN (SELECT gameID, date, team, pollTime, max(odds) as openOdds FROM Moneylines{0} WHERE bookName="{1}" GROUP BY gameID, date, team, pollTime) as t2\
				ON (t1.gameID=t2.gameID AND t1.date=t2.date AND t1.team=t2.team AND t1.openTime=t2.pollTime)\
				INNER JOIN (SELECT gameID, date, team, pollTime, max(odds) as closeOdds FROM Moneylines{0} WHERE bookName="{1}" GROUP BY gameID, date, team, pollTime) as t3\
				ON t1.gameID=t3.gameID AND t1.date=t3.date AND t1.team=t3.team AND t1.closeTime=t3.pollTime\
				INNER JOIN (SELECT gameID, date, team, max(odds) AS maxOdds FROM Moneylines{0} WHERE bookName="{1}" GROUP BY gameID, team, date) as t4\
				ON t1.gameID=t4.gameID AND t1.date=t4.date AND t1.team=t4.team\
				ORDER BY t0.date, t0.gameID;'\
				.format(self.season,self.books[0])
		elif len(self.books) > 1:
			query = 'SELECT date, gameID, team, home, away, winner, max(openOdds) as openOdds, max(closeOdds) as closeOdds, max(maxOdds) as maxOdds\
				FROM (SELECT t1.gameID as gameID, t1.date as date, t1.team as team, t0.home as home, t0.away as away, t0.winner as winner, t1.bookName as bookName, t2.openOdds as openOdds, t3.closeOdds as closeOdds, t4.maxOdds as maxOdds\
				FROM (SELECT gameID, date, team as home, opponent as away, winner FROM Games{0} WHERE location="home") as t0\
				INNER JOIN (SELECT date, gameID, team, bookName, min(pollTime) as openTime, max(pollTime) as closeTime FROM Moneylines{0} WHERE bookName in {1} GROUP BY date, gameID, team, bookName) as t1\
				ON (t0.gameID=t1.gameID AND t0.date=t1.date)\
				INNER JOIN (SELECT gameID, date, team, bookName, pollTime, max(odds) as openOdds FROM Moneylines{0} WHERE bookName in {1} GROUP BY gameID, date, team, bookName, pollTime) as t2\
				ON (t1.gameID=t2.gameID AND t1.date=t2.date AND t1.team=t2.team AND t1.openTime=t2.pollTime AND t1.bookName=t2.bookName)\
				INNER JOIN (SELECT gameID, date, team, bookName, pollTime, max(odds) as closeOdds FROM Moneylines{0} WHERE bookName in {1} GROUP BY gameID, date, team, bookName, pollTime) as t3\
				ON (t1.gameID=t3.gameID AND t1.date=t3.date AND t1.team=t3.team AND t1.closeTime=t3.pollTime AND t1.bookName=t3.bookName)\
				INNER JOIN (SELECT gameID, date, team, max(odds) AS maxOdds FROM Moneylines{0} WHERE bookName in {1} GROUP BY gameID, team, date) as t4\
				ON (t1.gameID=t4.gameID AND t1.date=t4.date AND t1.team=t4.team)) as a1\
				GROUP BY a1.date, a1.gameID, a1.team, a1.home, a1.away, a1.winner;'\
				.format(self.season,tuple(self.books))
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
		picks["odds"] = picks["openOdds"] + self.goodness*(picks["maxOdds"]-picks["openOdds"])
		# Place bets
		self.bookie.place_bets(picks["team"].values,picks["winner"].values,picks["odds"])


class BuildHistograms(object):

	def __init__(self,season,books,home_prob,goodness,silent,num_sims):
		self.data = SeasonData(season,books=books)
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
		print "\n\nBooks:",self.data.books,"Home Prob.:",self.home_prob,"Goodness:",self.goodness,"Num. Games:",len(self.data.odds_data)/2
		print "Mean:", np.mean(earnings)
		quintiles = np.percentile(earnings, np.arange(0, 120, 20))
		print "Quintiles [0%: {0}, 20%: {1}, 40%: {2}, 60%: {3}, 80%: {4}, 100%: {5}]".format(quintiles[0],quintiles[1],quintiles[2],quintiles[3],quintiles[4],quintiles[5])
		print "\n"
		#print "Average:", sum(self.earnings)/len(self.earnings), " Best:", max(self.earnings), " Worst:", min(self.earnings),"\n" 

if __name__ == "__main__":
	season = 20152016
	home_prob = .5
	goodness = 0.
	silent = True
	num_sims = 5000
	books=['Pinnacle']
	BuildHistograms(season,books,home_prob,goodness,silent,num_sims)



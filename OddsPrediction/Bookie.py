import numpy as np

class Bookie(object):

	def __init__(self, home_prob, goodness, balance=0, silent=False,):
		self.balance = balance
		self.num_wins = 0
		self.num_losses = 0
		self.silent = silent
		self.home_prob = home_prob
		self.goodness = goodness

	def place_bet(self,pick,winner,odds,bet=1):
		"""
		For single bets.
		"""
		self.update_balance(-bet)
		if pick == winner:
			self.num_wins += 1
			self.update_balance(odds*bet)
			if not self.silent:
				print "W! Bet on:", pick, " Winner:", winner, " Odds:", odds, " Net:", odds*bet, " Balance:", self.balance
		elif pick != winner:
			self.num_losses += 1
			if not self.silent:
				print "L! Bet on:", pick, " Winner:", winner, " Odds:", odds, " Net:", -bet, " Balance:", self.balance

	def place_bets(self,picks,winners,odds,bet=1):
		"""
		For multiple, vectorized bets.
		"""
		wins = (picks == winners).astype(int)
		self.num_wins = sum(wins)
		self.num_losses = len(wins) - self.num_wins
		profits = np.multiply(np.multiply(wins,odds),bet)-bet
		self.update_balance(sum(profits))

	def update_balance(self,amount):
		self.balance += amount

	def summary(self):
		print "\n#######################################"
		print "Bet timing skill:", self.goodness
		print "Pick home prob.:", self.home_prob
		print "Final balance:", self.balance
		print "Number placed:", self.num_wins+self.num_losses
		print "Final wins:", self.num_wins
		print "Final losses:", self.num_losses
		print "#######################################\n"




class Bookie(object):

	def __init__(self, home_prob, goodness, balance=0, silent=False,):
		self.balance = balance
		self.wins = 0
		self.losses = 0
		self.silent = silent
		self.home_prob = home_prob
		self.goodness = goodness

	def place_bet(self,pick,winner,odds,bet):
		self.update_balance(-bet)
		if pick == winner:
			self.wins += 1
			self.update_balance(odds*bet)
			if not self.silent:
				print "W! Bet on:", pick, " Winner:", winner, " Odds:", odds, " Net:", odds*bet, " Balance:", self.balance
		elif pick != winner:
			self.losses += 1
			if not self.silent:
				print "L! Bet on:", pick, " Winner:", winner, " Odds:", odds, " Net:", -bet, " Balance:", self.balance

	def update_balance(self,amount):
		self.balance += amount

	def summary(self):
		print "\n#######################################"
		print "Bet timing skill:", self.goodness
		print "Pick home prob.:", self.home_prob
		print "Final balance:", self.balance
		print "Number placed:", self.wins+self.losses
		print "Final wins:", self.wins
		print "Final losses:", self.losses
		print "#######################################\n"


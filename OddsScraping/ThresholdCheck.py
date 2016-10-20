import MySQLdb, datetime, time
from config import CONFIG as config
import BettingDB


class ThresholdCheck():

	def __init__(self,thresh_book="Pinnacle",alpha=0.02):
		self.bets_DB = BettingDB.BettingDB()
		self.thresh_book = thresh_book
		self.alpha = alpha

	def run(self):
		print "Checking if lines have exceeded ", self.thresh_book, " initial thresholds...\n"
		# Find games that are still yet to occur
		curr_time = int(time.time())
		upcoming_games = self.find_upcoming_games(curr_time)

		# Determine betting thresholds for each game
		home_thresh = []
		away_thresh = []
		for gid in upcoming_games:
			home_thresh.append(self.determine_thresh(gid,"home"))
			away_thresh.append(self.determine_thresh(gid,"away"))

		# Check if latest moneyline exceeds threshold for each game
		for gid,ht,at in zip(upcoming_games,home_thresh,away_thresh):
			home_latest = self.get_line(gid,"home","latest")
			away_latest = self.get_line(gid,"away","latest")

			print "For game ", gid
			print "Latest home line: ", home_latest, " vs threshold ", ht
			print "Latest away line: ", away_latest, " vs threshold ", at, "\n"

			if  home_latest > ht:
				print "\n\n\n\n\a"
				print "Check out the HOME team in game ", gid, " !!!!!\n\n\n"
				print "\a"
			if  away_latest > at:
				print "\n\n\n\n\a"
				print "Check out the AWAY team in game ", gid, " !!!!!\n\n\n"
				print "\a"

	def find_upcoming_games(self,curr_time):
		query = "SELECT DISTINCT id FROM hockey_lines WHERE game_time>{0} AND site=\'{1}\';".format(curr_time,self.thresh_book)
		ids_temp = self.bets_DB.execute_query(query)
		ids = []
		for gid in ids_temp:
			ids.append(int(gid[0]))
		return ids

	def determine_thresh(self,gid,role):
		home_open = self.get_line(gid,"home","open")
		away_open = self.get_line(gid,"away","open")

		margin = 1/home_open + 1/away_open - 1
		home_open_fair = home_open + home_open*margin
		away_open_fair = away_open + away_open*margin

		home_thresh = 1/((1/home_open_fair) - self.alpha)
		away_thresh = 1/((1/away_open_fair) - self.alpha)

		if role == "home":
			return home_thresh
		if role == "away":
			return away_thresh


	def get_line(self,gid,role,epoch):
		if role=="home":
			query = "SELECT home_line FROM hockey_lines WHERE id={0} AND site=\'{1}\' ORDER BY poll_time;".format(gid,self.thresh_book)
			temp_lines = self.bets_DB.execute_query(query)
		elif role=="away":
			query = "SELECT away_line FROM hockey_lines WHERE id={0} AND site=\'{1}\' ORDER BY poll_time;".format(gid,self.thresh_book)
			temp_lines = self.bets_DB.execute_query(query)
		lines = []
		for line in temp_lines: lines.append(float(line[0]))
		if epoch == "open":
			return lines[0]
		elif epoch == "latest":
			return lines[-1]

if __name__ == "__main__":

	tc = ThresholdCheck()
	tc.run()



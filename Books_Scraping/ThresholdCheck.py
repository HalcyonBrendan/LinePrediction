import MySQLdb, datetime, time
from config import CONFIG as config
import BettingDB


class ThresholdCheck():

	def __init__(self,league="NHL",thresh_book="Pinnacle",alpha=0.02):
		self.bets_DB = BettingDB.BettingDB()
		self.league = league
		self.thresh_book = thresh_book
		self.alpha = alpha

	def run(self):
		print "Checking if lines have exceeded ", self.thresh_book, " initial thresholds...\n"
		# Find games that are still yet to occur
		curr_time = int(time.time())
		upcoming_games,home_teams,away_teams = self.find_upcoming_games(curr_time)

		# Determine betting thresholds for each game
		home_thresh = []
		away_thresh = []
		for gid in upcoming_games:
			home_thresh.append(self.determine_thresh(gid,"home"))
			away_thresh.append(self.determine_thresh(gid,"away"))

		# Check if latest moneyline exceeds threshold for each game
		for gid,ht,at,home_team,away_team in zip(upcoming_games,home_thresh,away_thresh,home_teams,away_teams):
			home_latest = self.get_line(gid,"home","latest")
			away_latest = self.get_line(gid,"away","latest")
			si_home_latest = self.get_line(gid,"home","latest","SportsInteraction")
			si_away_latest = self.get_line(gid,"away","latest","SportsInteraction")
			bod_home_latest = self.get_line(gid,"home","latest","bodog")
			bod_away_latest = self.get_line(gid,"away","latest","bodog")

			home_open = self.get_line(gid,"home","open")
			away_open = self.get_line(gid,"away","open")
			si_home_open = self.get_line(gid,"home","open","SportsInteraction")
			si_away_open = self.get_line(gid,"away","open","SportsInteraction")
			bod_home_open = self.get_line(gid,"home","open","bodog")
			bod_away_open = self.get_line(gid,"away","open","bodog")

			print "For game ", gid, " between ", away_team, " at ", home_team, ":"
			print "Away thresh:  ", at, "   Home thresh:  ", ht
			print "PIN away: ", away_latest, "  PIN home ", home_latest, " (vs open: ", away_open, "  ", home_open,")"
			print "SI away: ", si_away_latest, "  SI home ", si_home_latest, " (vs open: ", si_away_open, "  ", si_home_open,")"
			print "BOD away: ", bod_away_latest, "  BOD home ", bod_home_latest, " (vs open: ", bod_away_open, "  ", bod_home_open,")","\n"

			
			if  max(away_latest,si_away_latest,bod_away_latest) > at:
				print "\n\n\a"
				print "Check out the AWAY team in game ", gid, " !!!!!\n\n"
				print "\a"
			if  max(home_latest,si_home_latest,bod_home_latest) > ht:
				print "\n\n\a"
				print "Check out the HOME team in game ", gid, " !!!!!\n\n"
				print "\a"


	def find_upcoming_games(self,curr_time):
		query = "SELECT DISTINCT id,home_team,away_team FROM {0}_lines WHERE game_time>{1} AND site=\'{2}\';".format(self.league,curr_time,self.thresh_book)
		ids_temp = self.bets_DB.execute_query(query)
		ids = []
		home_teams = []
		away_teams = []
		for game in ids_temp:
			ids.append(int(game[0]))
			home_teams.append(str(game[1]))
			away_teams.append(str(game[2]))
		return ids,home_teams,away_teams

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


	def get_line(self,gid,role,epoch,book=None):
		if book is None: book = self.thresh_book
		if role=="home":
			query = "SELECT home_line FROM {0}_lines WHERE id={1} AND site=\'{2}\' ORDER BY poll_time;".format(self.league,gid,book)
			temp_lines = self.bets_DB.execute_query(query)
		elif role=="away":
			query = "SELECT away_line FROM {0}_lines WHERE id={1} AND site=\'{2}\' ORDER BY poll_time;".format(self.league,gid,book)
			temp_lines = self.bets_DB.execute_query(query)
		lines = []
		for line in temp_lines: lines.append(float(line[0]))
		if not lines:
			return -1
		elif epoch == "open":
			return lines[0]
		elif epoch == "latest":
			return lines[-1]

if __name__ == "__main__":

	tc = ThresholdCheck()
	tc.run()



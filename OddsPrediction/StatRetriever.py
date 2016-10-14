import MySQLdb
import OddsDB
import numpy as np


class StatRetriever():

	def __init__(self,sport,season):
		self.sport = sport
		self.season = season
		self.db = OddsDB.OddsDB(self.sport)


	def get_game_ids(self,team,start_date,end_date):
		query = "SELECT gameID FROM Games{0} WHERE team=\'{1}\' AND date>={2} AND date<={3} ORDER BY gameID;".format(self.season,team,start_date,end_date)
		temp_ids = self.db.execute_query(query)
		game_ids = []
		for gid in temp_ids: game_ids.append(int(gid[0]))
		return game_ids

	def get_team_stats(self,team,role,game_ids):
		curr_team = team
		team_stats = np.zeros((len(game_ids),5))
		game_count = 0
		for gid in game_ids:
			if role == "opp": 
				query = "SELECT opponent FROM Games{0} WHERE gameID={1} AND team=\'{2}\';".format(self.season,gid,team)
				curr_team = str(self.db.execute_query(query)[0][0])
			team_stats[game_count,0] = self.get_is_home(gid,curr_team,self.season)
			team_stats[game_count,1] = self.get_win_per_last_n(gid,curr_team,1,self.season)
			team_stats[game_count,2] = self.get_win_per_last_n(gid,curr_team,4,self.season)
			team_stats[game_count,3] = self.get_win_per_last_n(gid,curr_team,10,self.season)
			team_stats[game_count,4] = self.get_win_per_last_n(gid,curr_team,82,self.season)
			game_count += 1

		return team_stats

	def get_line_stats(self,team,role,game_ids):
		pass

	def get_win_per_last_n(self,game_id,team,n,season):
		query = "SELECT COUNT(*) FROM (SELECT * FROM Games{0} WHERE team=\'{1}\' AND gameID<{2} ORDER BY gameID DESC LIMIT {3}) AS tempTable WHERE result='W';".format(season,team,game_id,n)
		num_wins = int(self.db.execute_query(query)[0][0])
		query = "SELECT COUNT(*) FROM (SELECT * FROM Games{0} WHERE team=\'{1}\' AND gameID<{2} ORDER BY gameID DESC LIMIT {3}) AS tempTable".format(season,team,game_id,n)
		num_games = int(self.db.execute_query(query)[0][0])
		num_per = 1.*num_wins/num_games
		return num_per

	def get_is_home(self,game_id,team,season):
		query = "SELECT location FROM Games{0} WHERE gameID={1} AND team=\'{2}\';".format(season,game_id,team)
		is_home = int(str(self.db.execute_query(query)[0][0])=="home")
		return is_home

	# Given date in form yyyymmdd, increments date to next day
	def increment_date(self,curr_date):
		day = curr_date%100
		if day < 28: return curr_date + 1
		month = int((curr_date%10000-day)/100)
		year = int((curr_date-month*100-day)/10000)
		if month == 2:
			if day == 28 and year%4 == 0:
				return curr_date+1
			else:
				return int("{0}0301".format(year))
		if day < 30: return curr_date + 1
		if day == 30 and month in [1,3,5,7,8,10,12]: return curr_date +1
		if month == 12: return int("{0}0101".format(year+1))
		if month < 9: return int("{0}0{1}01".format(year,month+1))
		return int("{0}{1}01".format(year,month+1))

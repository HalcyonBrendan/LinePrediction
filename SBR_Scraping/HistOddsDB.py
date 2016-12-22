import MySQLdb, datetime, time
from config import CONFIG as config


class HistOddsDB():

	def __init__(self,league,season):
		self.db = MySQLdb.connect(passwd=config["mysql"]["pw"],host="localhost",user="root", db="halcyonlines")
		self.cursor = self.db.cursor()
		self.league = league
		self.season = season

	def execute_command(self, query_string):
		#print "{}\n".format(query_string)
		self.cursor.execute(query_string)
		self.db.commit()

	def execute_query(self, query_string):
		self.cursor.execute(query_string)
		sqlOut = self.cursor.fetchall()
		return sqlOut

	def add_game_to_DB(self,game):
		hasDraws = 0
		if self.league in ["BPL","FRA"]: hasDraws = 1
		if not self.moneylines_table_exists():
			#print "{0}_Moneylines{1} does not exist. Creating table!".format(self.league,self.season)
			self.create_moneylines_table(hasDraws)
		game["time"] = self.translate_datetime(game["date"],game["time"],1)

		game["id"] = self.get_game_id(game)
		if game["id"] == -1:
			print "Could not find id for game on ", game["date"], " between ", game["home_team"], " and ", game["away_team"]
			print "Continuing to next game."
			return -1
		if game["home_score"] > game["away_score"]: game["winner"] = game["home_team"]
		elif game["away_score"] > game["home_score"]: game["winner"] = game["away_team"]
		elif game["home_score"] == game["away_score"]: game["winner"] = "DRAW"
		else: game["winner"] = "Error"
		
		if hasDraws == 1:
			add_home = self.add_team_odds_to_DB(game["id"],game["home_team"],game["home_score"],game["away_team"],game["away_score"],game["books"],game["time"],game["date"],game["winner"],game["home_lines"],game["away_lines"],game["draw_lines"],game["line_times"])
			add_away = self.add_team_odds_to_DB(game["id"],game["away_team"],game["away_score"],game["home_team"],game["home_score"],game["books"],game["time"],game["date"],game["winner"],game["away_lines"],game["home_lines"],game["draw_lines"],game["line_times"])
		else:
			add_home = self.add_team_odds_to_DB(game["id"],game["home_team"],game["home_score"],game["away_team"],game["away_score"],game["books"],game["time"],game["date"],game["winner"],game["home_lines"],game["away_lines"],None,game["line_times"])
			add_away = self.add_team_odds_to_DB(game["id"],game["away_team"],game["away_score"],game["home_team"],game["home_score"],game["books"],game["time"],game["date"],game["winner"],game["away_lines"],game["home_lines"],None,game["line_times"])


		if add_home or add_away:
			return -1
		return 0

	def add_team_odds_to_DB(self,game_id,team,teamScore,opponent,opponentScore,books,gameTime,game_date,winner,odds,opponent_odds,draw_odds,poll_times):
	
		book_counter = -1
		for book in books:
			book_counter += 1
			if book == "betcris": continue
			for odd_counter in range(0,max(len(odds[book_counter]),len(opponent_odds[book_counter]))):
				try:
					odd = float(odds[book_counter][odd_counter])
					opponentOdd = float(opponent_odds[book_counter][odd_counter])
					#odd = convert_odds(int(odds[book_counter][odd_counter]),"american","decimal")
					#opponentOdd = convert_odds(int(opponent_odds[book_counter][odd_counter]),"american","decimal")
					if not draw_odds is None:
						drawOdd = float(draw_odds[book_counter][odd_counter])
						#drawOdd = convert_odds(int(draw_odds[book_counter][odd_counter]),"american","decimal")
				except:
					print "Problem adding odds to DB. Continuing..."
					continue
				pollTime = self.translate_datetime(game_date,poll_times[book_counter][odd_counter],2)
				# Construct query for adding game, then add it
				if draw_odds is None:
					if self.league == "NHL":
						query_string = """INSERT INTO Moneylines{0} (gameID,date,pollTime,gameTime,team,teamScore,odds,opponent,opponentScore,opponentOdds,winner,bookName) VALUES ({1},{2},{3},{4},\'{5}\',{6},{7},\'{8}\',{9},{10},\'{11}\',\'{12}\');""".format(self.season,game_id,game_date,int(pollTime),int(gameTime),team,teamScore,odd,opponent,opponentScore,opponentOdd,winner,translate_name(book,"books"))
					else:
						query_string = """INSERT INTO {0}_Moneylines{1} (gameID,date,pollTime,gameTime,team,teamScore,odds,opponent,opponentScore,opponentOdds,winner,bookName) VALUES ({2},{3},{4},{5},\'{6}\',{7},{8},\'{9}\',{10},{11},\'{12}\',\'{13}\');""".format(self.league,self.season,game_id,game_date,int(pollTime),int(gameTime),team,teamScore,odd,opponent,opponentScore,opponentOdd,winner,translate_name(book,"books"))
				else:
					query_string = """INSERT INTO {0}_Moneylines{1} (gameID,date,pollTime,gameTime,team,teamScore,odds,opponent,opponentScore,opponentOdds,drawOdds,winner,bookName) VALUES ({2},{3},{4},{5},\'{6}\',{7},{8},\'{9}\',{10},{11},{12},\'{13}\',\'{14}\');""".format(self.league,self.season,game_id,game_date,int(pollTime),int(gameTime),team,teamScore,odd,opponent,opponentScore,opponentOdd,drawOdd,winner,translate_name(book,"books"))
				#print query_string
				self.execute_command(query_string)
		return 0

	def get_game_id(self, game):
		# if getting NHL for halcyon analytics, get game id from games table in halcyonnhl db. otherwise, use gameIDs table in other db
		if self.league == "NHL":
			query_string = """SELECT gameID FROM Games{0} WHERE team=\'{1}\' AND opponent=\'{2}\' AND date={3};""".format(self.season,game["home_team"],game["away_team"],game["date"])
			try:
				result = int(self.execute_query(query_string)[0][0])
			except:
				result = -1
			return result

		if not self.ids_table_exists():
			print "game_ids table does not exist"
			self.create_ids_table()
		query_string = """SELECT gameID FROM gameIDs WHERE homeTeam = \'{0}\' AND awayTeam = \'{1}\' AND gameTime > {2}-4500 AND gameTime < {2}+4500  AND sport = \'{3}\' AND season = {4};""".format(game["home_team"],game["away_team"],game["time"], self.league, self.season)

		self.cursor.execute(query_string)
		try:
			# attempts to get the result 
			result = self.cursor.fetchone()[0]
		except:
			#if it fails, make a new id
			result = self.add_id(game)
		return result

	def add_id(self,game):

		if not self.ids_table_exists():
			print "gameIDs table does not exist"
			self.create_ids_table()

		#print "Making new id"
		# Sleep for a short time to make sure DB is updated
		time.sleep(0.05)
		self.cursor.execute("""SELECT MAX(gameID) AS gameID FROM {0}_Moneylines{1}""".format(self.league,self.season))
		largest_id = self.cursor.fetchone()[0]

		# print self.cursor.fetchone()
		if largest_id:
			new_id = largest_id + 1
		else:
			new_id = 1

		query_string = """INSERT INTO gameIDs (gameID,homeTeam,awayTeam,sport,gameTime,season) VALUES ({0},\'{1}\',\'{2}\',\'{3}\',\'{4}\',{5})""".format(new_id,game["home_team"],game["away_team"],self.league,game["time"],self.season)
		self.cursor.execute(query_string)

		# print query_string
		self.db.commit()
		return new_id

	def create_ids_table(self):
		query_string = """CREATE TABLE gameIDs (gameID INT, gameTime TEXT, homeTeam TEXT, awayTeam TEXT, sport TEXT, season INT)"""
		# print query_string
		self.execute_command(query_string)

	def ids_table_exists(self):
		stmt = "SHOW TABLES LIKE \'gameIDs\'"
		self.cursor.execute(stmt)
		result = self.cursor.fetchone()
		if result: return True
		else: return False


	def translate_datetime(self, event_date, event_time, option):
		# in case of simply finding game time
		if option == 1:
			day = event_date%100
			month = int((event_date%10000-day)/100)
			year = int((event_date-month-day)/10000)
			am_or_pm = str(event_time[-1])
			hour = (int(event_time[0:-4]))%12+12*int(am_or_pm=='p')
			minute = int(event_time[-3:-1])
			t = datetime.datetime(year, month, day, hour, minute)
			time_in_secs = (t-datetime.datetime(1970,01,01)).total_seconds()
			return time_in_secs
		# in case of SBR poll time
		elif option == 2:
			day = event_date%100 # for temporary use to get year
			month = int((event_date%10000-day)/100)
			year = int((event_date-month-day)/10000)
			month = int(event_time[0:2])
			day = int(event_time[3:5])
			am_or_pm = str(event_time[-2:])
			hour = (int(event_time[6:8]))%12+12*(am_or_pm=='PM')
			minute = int(event_time[9:11])
			t = datetime.datetime(year, month, day, hour, minute)
			time_in_secs = (t-datetime.datetime(1970,01,01)).total_seconds()
			return time_in_secs

	def create_moneylines_table(self,hasDraws):
		if self.league == "NHL":
			query_string = """CREATE TABLE Moneylines{0} (gameID INT, date INT, pollTime INT, gameTime INT, team TEXT, teamScore INT, odds DOUBLE(8,4), opponent TEXT, opponentScore INT, opponentOdds DOUBLE(8,4), winner TEXT, bookName TEXT)""".format(self.season)
		elif hasDraws == 0:
			query_string = """CREATE TABLE {0}_Moneylines{1} (gameID INT, date INT, pollTime INT, gameTime INT, team TEXT, teamScore INT, odds DOUBLE(8,4), opponent TEXT, opponentScore INT, opponentOdds DOUBLE(8,4), winner TEXT, bookName TEXT)""".format(self.league,self.season)
		elif hasDraws == 1:
			query_string = """CREATE TABLE {0}_Moneylines{1} (gameID INT, date INT, pollTime INT, gameTime INT, team TEXT, teamScore INT, odds DOUBLE(8,4), opponent TEXT, opponentScore INT, opponentOdds DOUBLE(8,4), drawOdds DOUBLE(8,4), winner TEXT, bookName TEXT)""".format(self.league,self.season)
		self.execute_command(query_string)

	def moneylines_table_exists(self):
		if self.league == "NHL":
			stmt = "SHOW TABLES LIKE \'Moneylines{0}\'".format(self.season)
			self.cursor.execute(stmt)
			result = self.cursor.fetchone()
			if result: return True
			else: return False
		else:
			stmt = "SHOW TABLES LIKE \'{0}_Moneylines{1}\'".format(self.league,self.season)
			self.cursor.execute(stmt)
			result = self.cursor.fetchone()
			if result: return True
			else: return False

	def odds_already_added(self,team,opponent,game_date):
		if self.league == "NHL":
			query_string = """SELECT COUNT(*) FROM Moneylines{0} WHERE team=\'{1}\' AND opponent=\'{2}\' AND date={3};""".format(self.season,team,opponent,game_date)
		else:
			query_string = """SELECT COUNT(*) FROM {0}_Moneylines{1} WHERE team=\'{2}\' AND opponent=\'{3}\' AND date={4};""".format(self.league,self.season,team,opponent,game_date)
		try:
			result = int(self.execute_query(query_string)[0][0])
		except:
			return False
		if result > 0: return True
		return False

def translate_name(long_form, league):
	for short_form in config["short_names"][league]:
		if long_form in config["short_names"][league][short_form]:
			return short_form
	return "unknown"

# Converts odds from currentType to desiredType (can be "american" or "decimal")
def convert_odds(odds, currentType, desiredType):
	if currentType == "american":
		# Check that the current type is as claimed
		if abs(odds) < 100: return odds
		# Now convert
		if odds > 0:
			convertedOdds = 1.+float(odds)/100.
		else:
			convertedOdds = 1.-100./float(odds)
	elif currentType == "decimal":
		if abs(odds) >= 100: return odds
		if odds >= 2:
			convertedOdds = (odds-1)*100.
		else:
			convertedOdds = 100./(1-odds)
	return convertedOdds


if __name__ == "__main__":
	hodb = HistOddsDB('NHL',20152016)




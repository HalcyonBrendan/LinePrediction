import MySQLdb, datetime, time
from config import CONFIG as config


class HistOddsDB():

	def __init__(self,league,season):
		self.db = MySQLdb.connect(passwd=config["mysql"]["pw"],host="localhost",user="root", db="halcyonnhl")
		self.cursor = self.db.cursor()
		self.league = league
		self.sport = "hockey" #TODO: make everything league based, not sport
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
		if not self.moneylines_table_exists():
			print "Moneylines{} does not exist. Creating table!".format(self.season)
			self.create_moneylines_table()
		game["home_team"] = translate_name(game["home_team"],self.sport)
		game["away_team"] = translate_name(game["away_team"],self.sport)
		if game["home_team"] == "unknown" or game["away_team"] == "unknown":
			print "Unknown team on date: ", game["date"]
			print "Continuing to next game."
			return 1
		game["id"] = self.get_game_id(game["home_team"],game["away_team"],game["date"])
		if game["id"] == -1:
			print "Could not find id for game on ", game["date"], " between ", game["home_team"], " and ", game["away_team"]
			print "Continuing to next game."
			return 1
		add_home = self.add_team_odds_to_DB(game["id"],game["home_team"],game["away_team"],game["books"],game["time"],game["date"],game["home_lines"],game["away_lines"],game["line_times"])
		add_away = self.add_team_odds_to_DB(game["id"],game["away_team"],game["home_team"],game["books"],game["time"],game["date"],game["away_lines"],game["home_lines"],game["line_times"])
		if add_home or add_away:
			return 1
		return 0

	def add_team_odds_to_DB(self,game_id,team,opponent,books,game_time,game_date,odds,opponent_odds,poll_times):
	
		gameTime = self.translate_datetime(game_date,game_time,1)
		book_counter = -1
		for book in books:
			book_counter += 1
			if book == "betcris": continue
			for odd_counter in range(0,max(len(odds[book_counter]),len(opponent_odds[book_counter]))):
				try:
					odd = convert_odds(int(odds[book_counter][odd_counter]),"american","decimal")
					opponentOdd = convert_odds(int(opponent_odds[book_counter][odd_counter]),"american","decimal")
				except:
					print "Problem adding odds to DB. Continuing..."
					continue
				pollTime = self.translate_datetime(game_date,poll_times[book_counter][odd_counter],2)
				# Construct query for adding game, then add it
				query_string = """INSERT INTO Moneylines{0} (gameID,date,pollTime,gameTime,team,odds,opponent,opponentOdds,bookName) VALUES ({1},{2},{3},{4},\'{5}\',{6},\'{7}\',{8},\'{9}\');""".format(self.season,game_id,game_date,int(pollTime),int(gameTime),team,odd,opponent,opponentOdd,translate_name(book,"books"))
				print query_string
				self.execute_command(query_string)
		return 0

	def get_game_id(self,home_team,away_team,date):
		# Query DB for game matching the given parameters
		query_string = "SELECT gameID FROM Games{0} WHERE team=\'{1}\' AND opponent=\'{2}\' AND date={3};".format(self.season,home_team,away_team,date)
		game_id = self.execute_query(query_string)
		try:
			gid = int(game_id[0][0])
		except:
			gid = -1
		return gid

	def translate_datetime(self, event_date, event_time, option):
		# in case of simply finding game time
		if option == 1:
			day = event_date%100
			month = int((event_date%10000-day)/100)
			year = int((event_date-month-day)/10000)
			am_or_pm = str(event_time[-1])
			hour = (int(event_time[0:-4])-3)%12+12*int(am_or_pm=='p') # Convert to PT
			if hour >= 21 and am_or_pm == 'p': hour -= 12
			if hour >= 9 and am_or_pm == 'a': hour += 12
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
			hour = (int(event_time[6:8])-3)%12+12*(am_or_pm=='PM') # Convert to PT
			if hour >= 21 and am_or_pm == 'PM': hour -= 12
			if hour >= 9 and am_or_pm == 'AM': hour += 12
			minute = int(event_time[9:11])
			t = datetime.datetime(year, month, day, hour, minute)
			time_in_secs = (t-datetime.datetime(1970,01,01)).total_seconds()
			return time_in_secs

	def create_moneylines_table(self):
		query_string = """CREATE TABLE Moneylines{} (gameID INT, date INT, pollTime INT, gameTime INT, team TEXT, odds DOUBLE(8,4), opponent TEXT, opponentOdds DOUBLE(8,4), bookName TEXT)""".format(self.season)
		self.execute_command(query_string)

	def moneylines_table_exists(self):
		stmt = "SHOW TABLES LIKE \'Moneylines{}\'".format(self.season)
		self.cursor.execute(stmt)
		result = self.cursor.fetchone()
		if result: return True
		else: return False

def translate_name(long_form, sport):
	for short_form in config["short_names"][sport]:
		if long_form in config["short_names"][sport][short_form]:
			return short_form
	return "unknown"

# Converts odds from currentType to desiredType (can be "american" or "decimal")
def convert_odds(odds, currentType, desiredType):
	if currentType == "american":
		if odds > 0:
			convertedOdds = 1+odds/100.
		else:
			convertedOdds = 1-100./odds
	elif currentType == "decimal":
		if odds >= 2:
			convertedOdds = (odds-1)*100.
		else:
			convertedOdds = 100./(1-odds)
	return convertedOdds



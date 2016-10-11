import MySQLdb, datetime
from config import CONFIG as config


class HistOddsDB():

	def __init__(self,league):
		self.db = MySQLdb.connect(passwd=config["mysql"]["pw"],host="localhost",user="root", db="betting")
		self.cursor = self.db.cursor()
		self.league = league
		self.sport = "hockey" #TODO: make everything league based, not sport

	def execute_command(self, query_string):
		print "{}\n".format(query_string)
		self.cursor.execute(query_string)
		self.db.commit()

	def execute_query(self, query_string):
		self.cursor.execute(query_string)
		sqlOut = self.cursor.fetchall()
		return sqlOut

	def add_game_to_DB(self,game):
		if not self.moneylines_table_exists():
			print "{}_moneylines does not exist. Creating table!".format(self.league)
			self.create_moneylines_table()
		game["id"] = self.get_game_id(translate_name(game["home_team"],self.sport),translate_name(game["away_team"],self.sport),game["date"])
		add_home = self.add_team_odds_to_DB(game["id"],game["home_team"],game["away_team"],game["books"],game["time"],game["date"],game["home_lines"],game["away_lines"],game["line_times"])
		add_away = self.add_team_odds_to_DB(game["id"],game["away_team"],game["home_team"],game["books"],game["time"],game["date"],game["away_lines"],game["home_lines"],game["line_times"])
		if add_home or add_away:
			return 1
		return 0

	def add_team_odds_to_DB(self,game_id,team,opponent,books,game_time,game_date,odds,opponent_odds,poll_times):
		pass

	def get_game_id(self,home_team,away_team,date):
		print "get_game_id function:"
		print home_team
		print away_team
		print date
		return 1

	def create_moneylines_table(self):
		query_string = """CREATE TABLE {}_moneylines (gameID INT, pollTime INT, gameTime INT, team TEXT, odds DOUBLE(8,4), opponent TEXT, opponentOdds DOUBLE(8,4), bookName TEXT)""".format(self.league)
		self.execute_command(query_string)

	def moneylines_table_exists(self):
		stmt = "SHOW TABLES LIKE \'{}_moneylines\'".format(self.league)
		self.cursor.execute(stmt)
		result = self.cursor.fetchone()
		if result: return True
		else: return False

def translate_name(long_form, sport):
	for short_form in config["short_names"][sport]:
		if long_form in config["short_names"][sport][short_form]:
			return short_form
	return "unknown"



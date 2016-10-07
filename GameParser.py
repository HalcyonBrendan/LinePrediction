from bs4 import BeautifulSoup


class GameParser():

	def __init__(self,date):

		self.date = date
		self.game_time = 0
		self.home_team = ""
		self.away_team = ""
		self.home_line = -1
		self.away_line = -1

	def parse_game(self,game_html):
		pass
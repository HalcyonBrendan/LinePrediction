from bs4 import BeautifulSoup
import time

class GameParser():

	def __init__(self,driver,date):

		self.driver = driver
		self.date = date
		self.game_time = ""
		self.home_team = ""
		self.away_team = ""
		self.home_lines = []
		self.away_lines = []

	def parse_game(self,game_html):

		self.game_time = game_html.find("div", {"class": "el-div eventLine-time"}).find("div", {"class": "eventLine-book-value"}).contents[0]
		print "Game time: ", self.game_time

		team_names = game_html.findAll("span", {"class": "team-name"}) 
		self.away_team = team_names[0].contents[0].contents[0]
		print "Away team: ", self.away_team
		self.home_team = team_names[1].contents[0].contents[0]
		print "Home team: ", self.home_team


		book_html = game_html.findAll("div", {"class": "el-div eventLine-book"})

		for book in book_html:

			element = self.driver.find_element_by_id(book.get('id'))
			element.click()
			#actions.click(book).perform()
			time.sleep(100)

from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException
from bs4 import BeautifulSoup
import time, re
import GameParser


class SBR_parser():

	def __init__(self,start_date,end_date,league,season):
		
		self.driver = webdriver.Chrome()
		self.league = league
		self.season = season
		self.day_parser = day_parser(self.driver,league,season)
		self.start_date = start_date
		self.end_date = end_date
		#self.games = []


	def get_odds(self):
		#print "Parsing Sportsbook Review for historical ", self.league, " odds from ", self.start_date, " to ", self.end_date

		curr_date = self.start_date
		while curr_date <= self.end_date:
			#print "Getting odds data for ", curr_date
			day_games = self.day_parser.parse_day(curr_date)
			curr_date = self.increment_date(curr_date)
			yield day_games

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


class day_parser():

	def __init__(self,driver,league,season):
		self.date = 0
		self.driver = driver
		self.game_parser = []
		self.games = []
		self.books = []
		self.league = league
		self.season = season

	def parse_day(self,curr_date):

		self.date = curr_date
		self.games = []
		self.books = []

		#print "Obtaining webpage for date: ", self.date

		if self.league == "NHL":
			webpage = "http://www.sportsbookreview.com/betting-odds/nhl-hockey/?date={0}".format(self.date)
		elif self.league == "NBA":
			webpage = "http://www.sportsbookreview.com/betting-odds/nba-basketball/money-line/?date={0}".format(self.date)
		elif self.league == "BPL":
			webpage = "http://www.sportsbookreview.com/betting-odds/soccer/?date={0}&leagueId=english-premier-league".format(self.date)
		elif self.league == "FRA":
			webpage = "http://www.sportsbookreview.com/betting-odds/soccer/?leagueId=ligue1&date={0}".format(self.date)
		self.driver.get(webpage)
		#print "Pausing for 2 seconds. Close any popups."
		#time.sleep(2)

		#print "HTML obtained. Scraping site."
		soup = BeautifulSoup(self.driver.page_source, "html.parser")
		# Get book names (just first ten for now)
		books_html = soup.find("ul", {"id": "booksCarousel"}).findAll("a", {"id": "bookName"})
		bookCount = 0
		for book in books_html:
			self.books.append(book.contents[0])
			bookCount+=1
			if bookCount >= 10: break

		# Parse games
		# Sometimes cells have different class name
		game_cells = soup.findAll("div", {"class": re.compile("event-holder*")})
		for cell in game_cells:
			self.game_parser = GameParser.GameParser(self.driver,self.date,self.books,self.league,self.season)
			game = self.game_parser.parse_game(cell)
			if game == -1: continue
			self.games.append(game)

		return self.games



if __name__ == "__main__":
	sbr = SBR_parser(20160228,20160301)
	odds = sbr.get_odds()

	print odds



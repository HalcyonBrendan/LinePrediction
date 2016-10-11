from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException
from bs4 import BeautifulSoup
import time
import GameParser


class SBR_parser():

	def __init__(self,start_date,end_date):
		
		self.driver = webdriver.Chrome()
		self.day_parser = day_parser(self.driver)
		self.start_date = start_date
		self.end_date = end_date
		#self.games = []


	def get_odds(self):
		
		print "Parsing Sportsbook Review for historical NHL odds from ", self.start_date, " to ", self.end_date

		date = self.start_date

		while date <= self.end_date:

			print "Getting odds data for ", date
			#self.games.append(self.day_parser.parse_day(date))
			day_games = self.day_parser.parse_day(date)
			date = self.increment_date(date)
			yield day_games
		#return self.games

	def increment_date(self,date):
		day = date%100
		if day < 28: return date + 1
		month = int((date%10000-day)/100)
		year = int((date-month*100-day)/10000)
		if month == 2:
			if day == 28 and year%4 == 0:
				return date+1
			else:
				return int("{0}0301".format(year))
		if day < 30: return date + 1
		if day == 30 and month in [1,3,5,7,8,10,12]: return date +1
		if month == 12: return int("{0}0101".format(year+1))
		if month < 9: return int("{0}0{1}01".format(year,month+1))
		return int("{0}{1}01".format(year,month+1))


class day_parser():

	def __init__(self,driver):
		self.date = 0
		self.driver = driver
		self.game_parser = []
		self.games = []
		self.books = []

	def parse_day(self,date):

		self.date = date
		self.games = []

		print "Obtaining webpage for date: ", self.date

		webpage = "http://www.sportsbookreview.com/betting-odds/nhl-hockey/?date={0}".format(self.date)
		self.driver.get(webpage)
		print "Pausing for 15 seconds. Close any popups."
		time.sleep(15)

		print "HTML obtained. Scraping site."
		soup = BeautifulSoup(self.driver.page_source, "html.parser")

		# Get book names (just first ten for now)
		books_html = soup.find("ul", {"id": "booksCarousel"}).findAll("a", {"id": "bookName"})
		bookCount = 0
		for book in books_html:
			self.books.append(book.contents[0])
			bookCount+=1
			if bookCount >= 10: break

		# Parse games
		game_cells = soup.findAll("div", {"class": "event-holder holder-complete"})
		game_counter = 0
		for cell in game_cells:
			self.game_parser = GameParser.GameParser(self.driver,self.date,self.books)
			self.games.append(self.game_parser.parse_game(cell))
			game_counter+=1

		return self.games



if __name__ == "__main__":
	sbr = SBR_parser(20160228,20160301)
	odds = sbr.get_odds()

	print odds



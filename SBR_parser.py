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
		self.games = []


	def get_odds(self):
		
		print "Parsing Sportsbook Review for historical NHL odds from ", self.start_date, " to ", self.end_date

		date = self.start_date

		while date <= self.end_date:

			print "Getting odds data for ", date
			self.games.append(self.day_parser.parse_day(date))

			date = self.increment_date(date)

		return self.games

	def increment_date(self,date):
		date += 1
		return date



class day_parser():

	def __init__(self,driver):
		self.date = 0
		self.driver = driver
		self.game_parser = GameParser.GameParser(self.driver,self.date)
		self.games = []

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

		game_cells = soup.findAll("div", {"class": "event-holder holder-complete"})

		game_counter = 0
		for cell in game_cells:

			self.games.append(self.game_parser.parse_game(cell))
			game_counter+=1

		return self.games



if __name__ == "__main__":

	sbr = SBR_parser(20160205,20160205)
	odds = sbr.get_odds()

	print odds



import re, time, sys, datetime, math, signal, random
import SBR_parser
import HistOddsDB



class HistOddsScraper():

	def __init__(self,start_date,end_date):

		self.start_date = start_date
		self.end_date = end_date
		self.parser = SBR_parser.SBR_parser(self.start_date,self.end_date)
		self.histDB = HistOddsDB.HistOddsDB()

	def run(self):

		day_generator = self.parser.get_odds()

		for day in day_generator:
			for game in day:
				print game



if __name__ == "__main__":

	start_date = 20160228
	end_date = 20160301
	odds = HistOddsScraper(start_date,end_date)
	odds.run()
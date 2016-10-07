import re, time, sys, datetime, math, signal, random
import SBR_parser
import HistOddsDB



class HistOddsScraper():

	def __init__(self,start_date,end_date):

		self.start_date = start_date
		self.end_date = end_date
		self.parser = SBR_parser.SBR_parser(self.start_date,self.end_date)
		self.histDB = HistOddsDB.HistOddsDB()
		self.games = {}

	def run(self):

		self.games = self.parser.get_odds()

		for game in self.games:
			pass



if __name__ == "__main__":

	start_date = 20150901
	end_date = 20160701
	odds = HistOddsScraper(start_date)
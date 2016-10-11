import re, time, sys, datetime, math, signal, random
import SBR_parser
import HistOddsDB



class HistOddsScraper():

	def __init__(self,start_date,end_date):

		self.start_date = start_date
		self.end_date = end_date
		self.parser = SBR_parser.SBR_parser(self.start_date,self.end_date)
		self.histDB = HistOddsDB.HistOddsDB("NHL")

	def run(self):

		day_generator = self.parser.get_odds()

		for day in day_generator:
			for game in day:
				print "Adding game to DB: "
				#print game
				add_to_DB = self.histDB.add_game_to_DB(game)
				if add_to_DB == 1:
					print "Game added successfully."
				else:
					print "Problem adding game:"
					print add_to_DB

				break


if __name__ == "__main__":

	start_date = 20160224
	end_date = 20160224
	odds = HistOddsScraper(start_date,end_date)
	odds.run()
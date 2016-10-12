import re, time, sys, datetime, math, signal, random
import SBR_parser
import HistOddsDB



class HistOddsScraper():

	def __init__(self,start_date,end_date,season):

		self.season = season
		self.start_date = start_date
		self.end_date = end_date
		self.parser = SBR_parser.SBR_parser(self.start_date,self.end_date)
		self.histDB = HistOddsDB.HistOddsDB("NHL",self.season)

	def run(self):

		day_generator = self.parser.get_odds()

		for day in day_generator:
			for game in day:
				print "Adding game to DB: "
				#print game
				add_to_DB = self.histDB.add_game_to_DB(game)
				if add_to_DB == 0:
					print "Game added successfully."
				else:
					print "Problem adding game:"
					print add_to_DB


if __name__ == "__main__":

	# SET THIS:
	season = 20152016

	if season == 20152016:
		start_date = 20151007
		end_date = 20160410
	elif season == 20142015:
		start_date = 20141008
		end_date = 20150411
	elif season == 20132014:
		start_date = 20131001
		end_date = 20140413
	elif season == 20122013:
		start_date = 20130119
		end_date = 20130427
	elif season == 20112012:
		start_date = 20111006
		end_date = 20120407

	#temp
	start_date = 20151227
	end_date = 20160410

	odds = HistOddsScraper(start_date,end_date,season)
	odds.run()
import re, time, sys, datetime, math, signal, random
import SBR_parser
import HistOddsDB

class HistOddsScraper():

	def __init__(self,league,season,start_date,end_date):

		self.season = season
		self.league = league
		self.start_date = start_date
		self.end_date = end_date
		self.parser = SBR_parser.SBR_parser(self.start_date,self.end_date,self.league)
		self.histDB = HistOddsDB.HistOddsDB(self.league,self.season)

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

if __name__ == "__main__":

	# SET THIS:
	league = "NBA"
	season = 20152016

	if season == 20152016:
		start_date = 20151027
		end_date = 20160413
	elif season == 20142015:
		start_date = 20141028
		end_date = 20150415
	elif season == 20132014:
		start_date = 20131029
		end_date = 20140416
	elif season == 20122013:
		start_date = 20121030
		end_date = 20130417
	elif season == 20112012:
		start_date = 20111225
		end_date = 20120426

	# Uncomment if you need to restart mid-season
	start_date = 20160221
	#end_date = 20140413

	odds = HistOddsScraper(league,season,start_date,end_date)
	odds.run()
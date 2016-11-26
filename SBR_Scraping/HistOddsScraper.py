import re, time, sys, datetime, math, signal, random
import SBR_parser
import HistOddsDB

class HistOddsScraper():

	def __init__(self,league,season,start_date,end_date):

		self.season = season
		self.league = league
		self.start_date = start_date
		self.end_date = end_date
		self.parser = SBR_parser.SBR_parser(self.start_date,self.end_date,self.league,self.season)
		self.histDB = HistOddsDB.HistOddsDB(self.league,self.season)

	def run(self):

		day_generator = self.parser.get_odds()

		for day in day_generator:
			for game in day:
				#print "Adding game to DB: "
				#print game
				if game in [-1,-2]: continue
				add_to_DB = self.histDB.add_game_to_DB(game)
				if not add_to_DB == 0:
					print "Problem adding game: ", game


def args_parser(args_list):
	if len(args_list) == 1:
		print "\nRun HistOddsScraper.py as \">>> python HistOddsScraper.py [season] -l [league] -s [start_date] -e [end_date]\"\n"
		print "[season]: Mandatory argument, in yyyyyyyy format, specifying season for [league]. EG. 20142015"
		print "[league]: Optional argument - currently compatible with \"NHL\" (default), \"NBA\", \"BPL\", and \"FRA\""
		print "[start_date]: Optional argument, in yyyymmdd format, specifying date at which to start scraping. Regular season start date is default"
		print "[end_date]: Optional argument, in yyyymmdd format, specifying date at which to end scraping. Regular season end date is default\n"
		print "NOTE: Games already entered in DB will not be overwritten and must be deleted if you wish to re-scrape and save the odds.\n"
		exit()
	elif len(args_list) == 2:
		if not args_list[1].isdigit(): 
			print "Error reading arguments. Type \">>> python HistOddsScraper.py\" for help."
			exit()
		season = int(args_list[1])
		league = "NHL"
		start_date = 0
		end_date = 0
	elif len(args_list) > 2:
		if not sys.argv[1].isdigit():
			print "Error reading arguments. Type \">>> python HistOddsScraper.py\" for help."
			exit()
		season = int(args_list[1])
		league = "NHL"
		start_date = 0
		end_date = 0
		for i in range(2,len(args_list)):
			if args_list[i] == "-l":
				league = str(args_list[i+1])
			elif args_list[i] == "-s":
				start_date = int(args_list[i+1])
			elif args_list[i] == "-e":
				end_date = int(args_list[i+1])

	return season, league, start_date, end_date

if __name__ == "__main__":

	season, league, start_date_override, end_date_override = args_parser(sys.argv)

	print "Scraping odds for ", season, " ", league, " season!"

	if league is "NBA":
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
	elif league is "NHL":
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
			end_date = 20130428
		elif season == 20112012:
			start_date = 20111006
			end_date = 20120407
		elif season == 20102011:
			start_date = 20101007
			end_date = 20110410
	elif league is "BPL":
		if season == 20162017:
			start_date = 20160813
			end_date = 20161105
		elif season == 20152016:
			start_date = 20150808
			end_date = 20160517
		elif season == 20142015:
			start_date = 20140816
			end_date = 20150524
		elif season == 20132014:
			start_date = 20130817
			end_date = 20140511
	elif league is "FRA": 
		if season == 20162017:
			start_date = 20160812
			end_date = 20161105
		elif season == 20152016:
			start_date = 20150807
			end_date = 20160514
		elif season == 20142015:
			start_date = 20140808
			end_date = 20150523
		elif season == 20132014:
			start_date = 20130809
			end_date = 20140517

	if start_date_override > 0:
		start_date = start_date_override
	if end_date_override > 0:
		end_date = end_date_override
	

	# Uncomment if you need to restart mid-season
	#start_date = 20140517
	#end_date = 20140413
	
	odds = HistOddsScraper(league,season,start_date,end_date)
	odds.run()
	print "Odds successfully scraped and stored in database!"
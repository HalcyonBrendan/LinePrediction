import time, datetime, pytz, re, sys, importlib, json
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from pyvirtualdisplay import Display
from config import CONFIG as config
import SiteParsers

def print_json(json_object):
    print json.dumps(json_object, indent=4, sort_keys=True) 
    print "\n"

class HTML_parser():

	def __init__(self):

		self.betting_websites = config["bookies"]
		self.sports = config["sports"]
		# self.display = Display(visible=0, size=(800, 600))
		# self.display.start()
		# login to allow modification of roster
		#self.driver = webdriver.PhantomJS()
		self.driver = webdriver.Chrome()
		self.parsers = {}
		self.load_parsers()
		# for parser in self.parsers:
		# 	print parser

	def load_parsers(self):
		self.parsers["bodog"] = SiteParsers.bodog(self.driver)
		self.parsers["FiveDimes"] = SiteParsers.FiveDimes(self.driver)
		self.parsers["Pinnacle"] = SiteParsers.Pinnacle(self.driver)	 
		self.parsers["SportsInteraction"] = SiteParsers.SportsInteraction(self.driver)

	def get_moneylines(self):

		moneylines = []

		for site in self.betting_websites:

			#if site == "Pinnacle":
			#	continue

			print "Parsing", site, "for", ", ".join(self.sports[site])

			moneylines.append(self.parsers[site].get_moneylines(self.sports[site]))

		return moneylines

	def shutdown(self):
		self.driver.close()

if __name__ == "__main__":
	parser = HTML_parser()
	print_json(parser.get_moneylines())

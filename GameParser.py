from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import time

class GameParser():

	def __init__(self,driver,date,books):

		self.driver = driver
		self.date = date
		self.game_time = ""
		self.home_team = ""
		self.away_team = ""
		self.books = books
		self.line_times = []
		self.home_lines = []
		self.away_lines = []
		self.game = {}

	def parse_game(self,game_html):
		self.game_time = game_html.find("div", {"class": "el-div eventLine-time"}).find("div", {"class": "eventLine-book-value"}).contents[0]
		print "Game time: ", self.game_time

		team_names = game_html.findAll("span", {"class": "team-name"}) 
		self.away_team = team_names[0].contents[0].contents[0]
		print "Away team: ", self.away_team
		self.home_team = team_names[1].contents[0].contents[0]
		print "Home team: ", self.home_team


		book_html = game_html.findAll("div", {"class": "el-div eventLine-book"})

		bookCount = 0
		for book in book_html:
			# Click on odds to show line history
			self.driver.find_element_by_id(book.get('id')).click()
			#time.sleep(1)
			try:
				WebDriverWait(self.driver, 15).until(EC.presence_of_element_located((By.XPATH,'//*[@class="thead-fixed"]')))
			except:
				print "Loading line history took too long. Continuing to next book"
				continue

			window = BeautifulSoup(self.driver.page_source,"html.parser")
			moneyline_box = window.find("div", {"id": "dialogPop"}).findAll("div", {"class": "info-box"})[1]
			# Get each odds cell
			odds_cells = moneyline_box.findAll("tr", {"class": "info_line_alternate1"})

			self.line_times.append([])
			self.away_lines.append([])
			self.home_lines.append([])
			for cell in odds_cells:
				self.line_times[bookCount].append(cell.contents[0].contents[0].strip())
				self.away_lines[bookCount].append(cell.contents[1].contents[0].strip())
				self.home_lines[bookCount].append(cell.contents[2].contents[0].strip())
				#print cell.contents[0].contents[0].strip()
				#print cell.contents[1].contents[0].strip()
				#print cell.contents[2].contents[0].strip()

			bookCount += 1

			# Exit line history
			self.driver.find_element_by_xpath('//*[@title="close"]').click()

		game = {"date": self.date, "time": self.game_time, "away_team": self.away_team, "home_team": self.home_team, "books": self.books, "line_times": self.line_times, "away_lines": self.away_lines, "home_lines": self.home_lines}
		return game

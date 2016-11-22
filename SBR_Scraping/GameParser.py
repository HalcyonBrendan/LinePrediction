from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import time, re

class GameParser():

	def __init__(self,driver,date,books,league):

		self.driver = driver
		self.league = league
		# If draw odds aren't available need margin to compute from team lines
		if self.league in ["BPL","FRA"]:
			self.margin = .0205
		self.date = date
		self.game_time = ""
		self.home_team = ""
		self.away_team = ""
		self.books = books
		self.line_times = []
		self.home_lines = []
		self.away_lines = []
		self.draw_lines = None
		self.game = {}

	def parse_game(self,game_html):
		# Check it is a league with draws
		hasDraw = 0
		if self.league in ["BPL","FRA"]:
			hasDraw = 1

		self.game_time = game_html.find("div", {"class": "el-div eventLine-time"}).find("div", {"class": re.compile("eventLine-book-value")}).contents[0]
		#print "Game time: ", self.game_time

		team_names = game_html.findAll("span", {"class": "team-name"}) 
		self.away_team = team_names[0].contents[0].contents[0]
		#print "Away team: ", self.away_team
		self.home_team = team_names[1].contents[0].contents[0]
		#print "Home team: ", self.home_team

		# For NBA games, parse score and then minimize score content
		# Although this should work for other leagues as well
		#if self.league == "NBA":
			
		score_content = game_html.find("div", {"class": "score-content"})
		team_scores = score_content.findAll("div", {"class": "score-periods"})
		away_score = int(team_scores[0].find("span", {"class": "current-score"}).contents[0])
		home_score = int(team_scores[1].find("span", {"class": "current-score"}).contents[0])
		#print away_score, " ", home_score

			#time.sleep(15)

		book_html = game_html.findAll("div", {"class": "el-div eventLine-book"})

		broken_game_flag = 0
		bookCount = -1
		for book in book_html:
			self.line_times.append([])
			self.away_lines.append([])
			self.home_lines.append([])
			bookCount += 1
			# For BPL for now ignore anything that isn't pinnacle
			if self.league in ["BPL","FRA"] and not self.books[bookCount] in ['Pinnacle','Pinnacle Sports']: continue
			if self.books[bookCount] in ['betcris', 'BetCris']: continue
			# Click on odds to show line history
			try:
				self.driver.find_element_by_id(book.find("div", {"class": re.compile("eventLine-book-value")}).get('id')).click()
			except Exception as e:
				#print e
				print "Could not get line histories for ", self.books[bookCount], ". Continuing to next book."
				#broken_game_flag = 1
				continue
			#time.sleep(1)
			try:
				WebDriverWait(self.driver, 8).until(EC.presence_of_element_located((By.XPATH,'//*[@class="thead-fixed"]')))
			except:
				print "Loading line history took too long for ", self.books[bookCount], ". Continuing to next book"
				continue

			window = BeautifulSoup(self.driver.page_source,"html.parser")
			moneyline_box = window.find("div", {"id": "dialogPop"}).findAll("div", {"class": "info-box"})[1]
			# Get each odds cell
			odds_cells = moneyline_box.findAll("tr", {"class": "info_line_alternate1"})

			# Do some indexing stuff because SBR is stupid and behaves different for soccer than other sports
			away_ind = 1
			home_ind = 2
			if self.league in ['BPL', 'FRA']:
				away_ind = 2
				home_ind = 1
			for cell in odds_cells:
				self.line_times[bookCount].append(cell.contents[0].contents[0].strip())
				# Watch for cases where one side of the line is missing
				try:
					self.away_lines[bookCount].append(convert_odds(int(cell.contents[away_ind].contents[0].strip()),"american","decimal"))
				except:
					#print "Problem scraping line - most likely SBR is missing one side. Continuing..."
					continue	
				try:
					self.home_lines[bookCount].append(convert_odds(int(cell.contents[home_ind].contents[0].strip()),"american","decimal"))
				except:
					#print "Problem scraping line - most likely SBR is missing one side. Continuing..."
					# Get rid of last list element of away_lines list, which was added properly
					self.away_lines[bookCount].pop()
					continue

			# Exit line history
			try:
				self.driver.find_element_by_xpath('//*[@title="close"]').click()
			except:
				continue

		if broken_game_flag: return -1

		# For games with draws, need to compute draw lines since they aren't available on SBR
		if hasDraw: self.compute_draw_lines()

		game = {"date": self.date, "time": self.game_time, "away_team": self.away_team, "home_team": self.home_team, "away_score": away_score, "home_score": home_score, "books": self.books, "line_times": self.line_times, "away_lines": self.away_lines, "home_lines": self.home_lines, "draw_lines": self.draw_lines}
		return game


	def compute_draw_lines(self):
		self.draw_lines = []
		bookCount = -1
		for book in self.away_lines:
			self.draw_lines.append([])
			bookCount += 1
			for aLine,hLine in zip(self.away_lines[bookCount],self.home_lines[bookCount]):
				self.draw_lines[bookCount].append(float(1./(1.+self.margin-1./aLine-1./hLine)))


# Converts odds from currentType to desiredType (can be "american" or "decimal")
def convert_odds(odds, currentType, desiredType):
	if currentType == "american":
		# Check that the current type is as claimed
		if abs(odds) < 100: return odds
		# Now convert
		if odds > 0:
			convertedOdds = 1.+float(odds)/100.
		else:
			convertedOdds = 1.-100./float(odds)
	elif currentType == "decimal":
		if abs(odds) >= 100: return odds
		if odds >= 2:
			convertedOdds = (odds-1)*100.
		else:
			convertedOdds = 100./(1-odds)
	return convertedOdds


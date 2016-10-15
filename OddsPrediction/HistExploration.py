import MySQLdb, re, time, sys, datetime, math, signal
import matplotlib.pyplot as plt
import numpy as np
from config import CONFIG as config
import StatsDB


db = StatsDB.StatsDB("hockey")


###########################################################
# Plot some line graphs of odd movements for a team
"""
season = 20142015
book = "Pinnacle"
team = "VAN"

query = "SELECT DISTINCT gameID FROM Moneylines{0} WHERE bookName=\'{1}\' AND team=\'{2}\';".format(season,book,team)
teamIDs = db.execute_query(query)

for i in range(40,50):
	gid = int(teamIDs[i][0])

	query = "SELECT odds,pollTime FROM Moneylines{0} WHERE bookName=\'{1}\' AND team=\'{2}\' AND gameID={3} ORDER BY pollTime ASC;".format(season,book,team,gid)
	temp_odds = db.execute_query(query)
	odds = np.zeros(len(temp_odds))
	pTime = np.zeros(len(temp_odds))
	for j in range(len(temp_odds)): 
		odds[j] = temp_odds[j][0]
		pTime[j] = temp_odds[j][1]-temp_odds[0][1]

	plt.figure(i+1)
	plt.plot(pTime,odds)
	plt.xlabel('Time from Open [s]')
	plt.ylabel('Decimal Odds')
	title_string = team, " ", gid
	plt.title(title_string)
plt.show()
"""


##########################################################
# Make plots of average open, close, max above and below open
season = 20152016
book = "Pinnacle"

teamCount = 0
for short_form in config["short_names"]["hockey"]:
	team = str(short_form)

	query = "SELECT DISTINCT gameID FROM Moneylines{0} WHERE bookName=\'{1}\' AND team=\'{2}\';".format(season,book,team)
	teamIDs = db.execute_query(query)

	avgOpen = 0
	avgClose = 0
	avgMax = 0
	avgMin = 0

	for gid in teamIDs:
		gid = int(gid[0])
		query = "SELECT odds FROM Moneylines{0} WHERE bookName=\'{1}\' AND team=\'{2}\' AND gameID={3} ORDER BY pollTime ASC;".format(season,book,team,gid)
		#print query
		temp_odds = db.execute_query(query)
		odds = np.zeros(len(temp_odds))
		pTime = np.zeros(len(temp_odds))
		for j in range(len(temp_odds)): 
			odds[j] = temp_odds[j][0]

		avgOpen += odds[0]
		avgClose += odds[-1]
		avgMax += max(odds)-odds[0]
		avgMin += min(odds)-odds[0]

	avgOpen = avgOpen/82
	avgClose = avgClose/82
	avgMax = avgOpen + avgMax/82
	avgMin = avgOpen + avgMin/82

	print teamCount, "Completed ", team, " ! "
	
	lineProfile = np.zeros(4)
	lineProfile[0] = avgOpen
	lineProfile[1] = avgClose
	lineProfile[2] = avgMin
	lineProfile[3] = avgMax
	state = np.arange(1,5)

	plt.figure(teamCount+1)
	plt.plot(state,lineProfile)
	title_string = team, " Line Movement Profile ", season
	plt.title(title_string)

	teamCount += 1

plt.show()


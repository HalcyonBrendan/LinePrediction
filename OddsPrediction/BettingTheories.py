import MySQLdb, re, time, sys, datetime, math, signal
import matplotlib.pyplot as plt
import numpy as np
from config import CONFIG as config
import StatsDB


db = StatsDB.StatsDB("hockey")


####################### Theory 1 ###############################
### Use Pinnacle odds and threshold to make bets after line movements
#
# 1. For each game, get opening lines from Pinnacle
# 2. Remove margins such that probabilities add to 1
# 3. Select "edge" threshold that determines bets
# 4. Place bet if threshold is breached


# Get game info for the season
season = 20152016
query = "SELECT gameID,team,opponent,location FROM Games{0} ORDER BY gameID;".format(season)
game_ids = db.execute_query(query)

print game_ids

import re, time, sys, datetime, math, signal
import numpy as np


class LinePredictor():

	def __init__(self,sport,season):
		self.sport = sport
		self.season = season

	def predict(self,start_date,end_date,team_stats,team_line_stats,opp_stats,opp_line_stats):

		for i in range(len(team_stats)):
			pass
import re, time, sys, datetime, math, signal
import numpy as np
from sklearn import linear_model as lm


class LinePredictor():

	def __init__(self,sport,season):
		self.sport = sport
		self.season = season

	def predict(self,start_id,team_stats,team_line_stats,opp_stats,opp_line_stats):
		predictions = []
		# For each game after (and including) start_id, build training matrix and sample outcomes, then test
		for i in range(len(team_stats)):
			# Scroll to first test sample
			gid = int(team_stats[i][0])
			if gid < start_id: continue

			training_mat = self.build_stat_mat(team_stats[:i,1:],team_line_stats[:i,1:],opp_stats[:i,1:],opp_line_stats[:i,1:])
			training_out = team_line_stats[:i,3]

			test_sample = self.build_stat_mat(team_stats[i:i+1,1:],team_line_stats[i:i+1,1:],opp_stats[i:i+1,1:],opp_line_stats[i:i+1,1:])
			test_out = team_line_stats[i,3]

			# Use linear regression to predict max line value
			predictions.append({"gameID":gid, "linePred":float(self.lin_reg_fit(training_mat,training_out,test_sample)),"lineMax":test_out})

		return predictions


	def build_stat_mat(self,team_stats,team_line_stats,opp_stats,opp_line_stats):
		train_mat = np.zeros((len(team_stats),2*(len(team_stats[0])+1)))
		train_mat[:,0:len(team_stats[0])] = team_stats
		train_mat[:,len(team_stats[0])] = team_line_stats[:,0]
		train_mat[:,len(team_stats[0])+1:-1] = opp_stats
		train_mat[:,-1] = opp_line_stats[:,0]
		return train_mat

	def lin_reg_fit(self,training_mat,training_out,test_sample):
		regr = lm.LinearRegression()
		# train
		regr.fit(training_mat,training_out)
		# predict
		test_pred = regr.predict(test_sample)
		return test_pred
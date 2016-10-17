import re, time, sys, datetime, math, signal
import matplotlib.pyplot as plt
import numpy as np
from config import CONFIG as config
import StatRetriever, LinePredictor


class PredictLines():

	def __init__(self,season,train_start_date,start_date,end_date,use_prev_season_train,prev_season,prev_start_date):
		self.sport = "hockey"
		self.train_start_date = train_start_date
		self.start_date = start_date
		self.end_date = end_date
		self.season	= season
		self.sr = StatRetriever.StatRetriever(self.sport,self.season)
		self.lp = LinePredictor.LinePredictor(self.sport,self.season)
		self.use_prev_season_train = use_prev_season_train
		self.prev_season = prev_season
		self.prev_start_date = prev_start_date

	def run(self):
		book = "Pinnacle"
		line_predictions = {}
		teamCount = 0
		cum_error_vec = np.zeros(6)
		for short_form in config["short_names"]["hockey"]:
			team = str(short_form)
			print "Predicting lines for ", team
			gid_list = []
			if self.use_prev_season_train:
				gid_list.append(self.sr.get_game_ids(team,self.prev_season,self.prev_start_date,self.end_date))
			gid_list.append(self.sr.get_game_ids(team,self.season,self.train_start_date,self.end_date))
			gid_start = self.sr.get_game_ids(team,self.season,self.start_date,0)

			team_stats = self.sr.get_team_stats(team,"team",gid_list)
			opp_stats = self.sr.get_team_stats(team,"opp",gid_list)
			team_line_stats = self.sr.get_line_stats(team,"team",gid_list,book)
			opp_line_stats = self.sr.get_line_stats(team,"opp",gid_list,book)
			print team_line_stats
			break

			# Make predictions
			line_predictions[team] = self.lp.predict(gid_start,team_stats,team_line_stats,opp_stats,opp_line_stats)
			#print line_predictions[team]
			# Compute some stats for evaluation
			error_vec = self.compute_error(line_predictions[team])
			print "Error vector: ", error_vec
			cum_error_vec += error_vec
			print "Abs Pred Err, MS Pred Err, Abs Open Err, MS Open Err, Abs Close Err, MS Close Err"
			print "Cum. error vector: ", cum_error_vec



	def compute_error(self,team_predictions):
		abs_pred_error = 0
		ms_pred_error = 0
		abs_open_error = 0
		ms_open_error = 0
		abs_close_error = 0
		ms_close_error = 0
		for game in team_predictions:
			ape = abs(game["linePred"]-game["lineMax"])
			abs_pred_error += ape
			mpe = ape*ape
			ms_pred_error += mpe
			aoe = abs(game["lineOpen"]-game["lineMax"])
			abs_open_error += aoe
			moe = aoe*aoe
			ms_open_error += moe
			ace = abs(game["lineClose"]-game["lineMax"])
			abs_close_error += ace
			mce = ace*ace
			ms_close_error += mce
			print game["linePred"], " ", game["lineMax"], " ", game["lineOpen"], " ", game["lineClose"]
		return np.array([abs_pred_error,ms_pred_error,abs_open_error,ms_open_error,abs_close_error,ms_close_error])

if __name__ == "__main__":
	season = 20142015
	use_prev_season_train = 1

	if season == 20152016:
		train_start_date = 20151027
		start_date = 20151127
		end_date = 20160410
		prev_season = 20142015
		prev_start_date = 20141028
	elif season == 20142015:
		train_start_date = 20141028
		start_date = 20150128
		end_date = 20150411
		prev_season = 20132014
		prev_start_date = 20131021
	elif season == 20132014:
		train_start_date = 20131021
		start_date = 20131121
		end_date = 20140413
		prev_season = 20122013
		prev_start_date = 20130129
	elif season == 20122013:
		train_start_date = 20130129
		start_date = 20130229
		end_date = 20130427
		prev_season = 20112012
		prev_start_date = 20111026
	elif season == 20112012:
		train_start_date = 20111026
		start_date = 20111126
		end_date = 20120407
		prev_season = 20102011
		prev_start_date = 201011026

	# Comment out below two lines if you want to run full season
	#start_date = 20141127
	#end_date = 20141227

	pl = PredictLines(season,train_start_date,start_date,end_date,use_prev_season_train,prev_season,prev_start_date)
	pl.run()
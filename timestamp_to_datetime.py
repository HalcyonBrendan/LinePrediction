#!/usr/bin/python

from datetime import datetime
import time, sys

numTimes = len(sys.argv)

for i in range(1,numTimes):
	timestamp = str(sys.argv[i])
	dt_obj = datetime.fromtimestamp(float(timestamp))
	print dt_obj
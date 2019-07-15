#!/usr/bin/env python3

#SQL/Python Taxi Problem

def choose_file():
	#from tkinter import *
	import tkinter as tk
	from tkinter import filedialog

	root = tk.Tk()
	root.withdraw()
	root.filename =  tk.filedialog.askopenfilename(initialdir = "~/home/zerostrain/Documents/SQL_Practice/",title = "Select file",filetypes =(("all files","*.*"),("jpeg files","*.jpg")))
	print (root.filename)

	return root.filename

def TH(data):
	import numpy as np
	#Calculate take home amount from taxi matrix
	# (0.66*Fare_Rate + Tip_rate - Dollar/mile)*TD
	# Fare_Rate = taxi[4]
	# Tip_Rate = taxi[6]
	# Dollar/mile = DPG/MPG
	# TD = taxi[2]

	MPG=24.9
	DPG=2.42

	take_home=(0.66*data.loc[:,"Fare_Rate"].values+data.loc[:,"Tip_Rate"].values-(DPG/MPG))*data.loc[:,"TD"].values

	return take_home

def sig_TH(data):
	import numpy as np

	A=0.66
	MPG=24.9
	DPG=2.42
	B=DPG/MPG

	x=((data.loc[:,"sig_Fare_Rate"].values)**2)*(A*data.loc[:,"TD"].values)**2
	y=((data.loc[:,"sig_Tip_Rate"].values)**2)*(data.loc[:,"TD"].values)**2
	z=((data.loc[:,"sig_TD"].values)**2)*((A*data.loc[:,"Fare_Rate"].values+data.loc[:,"Tip_Rate"].values-B)**2)

	sig_Take_Home=np.sqrt(x+y+z)

	return sig_Take_Home

def DT(data):
	#Create unique day time notation that can be plotted in cronological order as a single array.
	#Day of Week = taxi[0]
	#Time of Day = taxi[1]
	import numpy as np

	date_time = 24*(data.loc[:,"DOW"].values-1)+data.loc[:,"TOD"].values

	
	return date_time

def SA(TH,sTH):
	#Find averages for 5 hour block shifts. 
	import numpy as np
	SA=np.zeros(len(TH))
	sSA=np.zeros(len(TH))
	for i in range(len(TH)):
		SA[i]=np.average(TH.take(range(i,i+6), mode='wrap'))
		sSA[i]=np.sqrt(np.sum(sTH.take(range(i,i+6),mode='wrap')**2))/5
	return SA, sSA

def nearest_neighbor(date_time, shift_ave, sig_shift_ave, peaks, peak_h, peak_l):
	from scipy.spatial import KDTree
	#Find nearest neighbors for all peaks compared to shift_ave/sig_shift_ave
	#
	dh, ih = KDTree(list(zip(date_time[peak_h],shift_ave[peak_h]/sig_shift_ave[peak_h]))).query(list(zip(date_time[peaks],shift_ave[peaks]/sig_shift_ave[peaks])))
	dl, il = KDTree(list(zip(date_time[peak_l],shift_ave[peak_l]/sig_shift_ave[peak_l]))).query(list(zip(date_time[peaks],shift_ave[peaks]/sig_shift_ave[peaks])))

	return (dh/dl).argsort()[:4];
	
def main():
	import numpy as np
	import pandas as pd
	import matplotlib.pyplot as plt
	import scipy.signal as sps
	plt.cla()
	day_of_week=['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
	
	fl_nm=choose_file()
	data=pd.read_csv(fl_nm)
	
	take_home=TH(data)
	date_time=DT(data)
	
	sig_Take_Home=sig_TH(data)
	shift_ave, sig_shift_ave=SA(take_home,sig_Take_Home)

	#Use signal peak finder to determine local maxima value separated by at least 12 hours
	#Select a minimum height of the average to only select highest peaks
	peaks=(sps.find_peaks(shift_ave,distance=12+1, height=np.average(shift_ave)))[0]
	peak_h=(sps.find_peaks(shift_ave/sig_shift_ave,distance=12+1))[0]
	#Find troughs
	peak_l=(sps.find_peaks(-1*shift_ave/sig_shift_ave,distance=12+1))[0] #,distance=12+1


	good=peaks[nearest_neighbor(date_time, shift_ave, sig_shift_ave, peaks, peak_h, peak_l)]


	nearest_neighbor2(date_time, shift_ave, sig_shift_ave, peaks, peak_h, peak_l)

	fig, ax1 = plt.subplots(nrows=1, ncols=1, sharex=True)
	#Earning potential
	markers, caps, bars = ax1.errorbar(date_time, shift_ave,yerr=sig_shift_ave, color='blue')
	ax1.scatter(date_time[good], shift_ave[good], color='red')
	#Visualization edits
	[bar.set_alpha(0.5) for bar in bars]
	[cap.set_alpha(0.5) for cap in caps]

	ax1.set_xlim(left=np.min(date_time), right=np.max(date_time))
	
	ax1.set_ylabel('Shift Earning Potential \n (Dollars)')
	plt.xticks(range(0,len(date_time), 24), day_of_week)
	ax1.set_xlabel('Shift Start Time')

	plt.tight_layout()
	plt.savefig('SA_ave.png')
	
	
	fig, ax2 = plt.subplots(nrows=1, ncols=1, sharex=True)
	#Weighted earning potential
	ax2.plot(date_time, shift_ave/sig_shift_ave, color='orange')
	ax2.scatter(date_time[good], shift_ave[good]/sig_shift_ave[good], color='red')

	ax2.set_xlim(left=np.min(date_time), right=np.max(date_time))
	
	ax2.set_ylabel('Uncertainty Weighted \n Shift Earning Potential \n (Dollars)')
	plt.xticks(range(0,len(date_time), 24), day_of_week)
	ax2.set_xlabel('Shift Start Time')

	plt.tight_layout()
	plt.savefig('W_SA_ave.png')
	
	print('The best 5 hour shifts to work are: ')

	for i in good:
		dow = day_of_week[data.loc[i,'DOW']-1]
		ampm=('AM' if data.loc[i,'TOD'] <12 else 'PM')
		time = (data.loc[i,'TOD'] if (data.loc[i,'TOD'] <12) else (data.loc[i,'TOD']-12))

		print(dow, time, ampm,shift_ave[i],sig_shift_ave[i])

	return;

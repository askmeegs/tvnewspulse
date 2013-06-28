import webapp2
import json
import urllib2
import jinja2
import os
from google.appengine.ext import db 
from google.appengine.api import users
from collections import defaultdict
from collections import OrderedDict
from collections import Counter
from datetime import datetime, timedelta
from processData import *
import time
import httplib
from google.appengine.api import urlfetch


def cleanToken(searchterm): #inserts %20 into spaces to prepare token for URL request
	searchterm=searchterm.strip()
	searchToken = searchterm
	modifiedToken = ""
	searchTokenList = searchToken.split(" ")
	for item in searchTokenList:
		modifiedToken += str(item) + "%20"
	return modifiedToken

def compileData(modifiedToken):
	moreData = True
	curData = []
	allData = []
	start = 0
	rows = 100 #so will get 100 rows at a time 
	trials = 0
	while moreData:
		try:
			url = "http://archive.org/details/tv?q=" + modifiedToken + "&start=" + str(start) + "&rows=" + str(rows) + "&output=json"
			curData = json.load(urllib2.urlopen(url))
			allData.extend(curData)
			if len(curData) < rows:
				moreData = False
			start = start + rows 
			print "I have " + str(len(allData)) + " results."
			time.sleep(.1) #rest the server"""
		except httplib.HTTPException:
			print "Hit HTTP Exception."
			if not allData and trials < 5:
				trials += 1
				pass  
			else: break 
	return allData

#HELPER METHOD 1: creates a list of all the dates of the broadcasts
def separateDates(data):
	dateslist = []
	for item in data:
		titleparts = item['title'].split(' : ')
		#some of the JSON objects have just a network, not a show-- we account for that here:
		if len(titleparts) == 2:
			dateslist.append(titleparts[1])
		else: 
			dateslist.append(titleparts[2])
	templist = []
	for date in dateslist:
		templist.append(parseDate(str(date)))
	return templist

#HELPER METHOD 2: convert the JSON dates to python dateTime objects
def parseDate(input):
	dateList = str(input).split(" ")
	stringDate = str(dateList[0] + " " + dateList[1] + " " + dateList[2])
	#uses strptime to convert stringDate to a datetime object, in the format "Month day, Year"
	parsedDate = datetime.strptime(stringDate, '%B %d, %Y')
	parsedDate= parsedDate-timedelta(days=31) #forcibly deal with the months in the future bug...
	return parsedDate

#HELPER METHOD 3: create a frequency ordered dictionary for the dateslist just created: 
def countFrequency(dateslist):
	frequencies = defaultdict(int)
	#count frequencies using a defaultdict
	for date in dateslist:
		frequencies[date] += 1
	#sort chronologically- we can't use counter because datetime objects need special treatment
	frequencies = OrderedDict((datetime.strftime(i, '%m, %d, %Y'), j) for i, j in sorted(frequencies.items(), key=lambda t: t[0]))
	return frequencies

#HELPER METHOD 4: extract the networks from the broadcasts and create a frequency dictionary for networks
def classifyNetworks(data):
	networkslist = []
	for item in data:
		#extract the networks
		titleparts = item['title'].split(' : ')
		if len(titleparts) == 2:
			networkslist.append(titleparts[0])
		else:
			networkslist.append(titleparts[1])
	#call Consolidate helper function, below
	umbrellas = consolidate(networkslist)
	#creates a network corporation frequency dictionary using Counter,
	#sorts in order of most common network --> least common
	result = Counter(umbrellas).most_common()
	return result

#HELPER METHOD 5: consolidate dozens of local networks under their corporate umbrellas
def consolidate(networkslist):
	#manually lists which local networks fall under each corporate umbrella; stored as lists
	CNN = ["CNN", "CNNW", "HLN"]
	FOX = ["FOX", "FOXNEWS", "FOXNEWSW", "FBC", "WTTG", "KTVU", "WBFF"]
	NBC = ["NBC", "MSNBC", "MSNBCW", "CNBC", "KNTV", "WRC", "WBAL", "KSTS"]
	ABC = ["ABC", "WMAR", "WJLA"]
	CBS = ["CBS", "WUSA", "KPIX", "KGO", "WJZ"]
	CW = ["CW", "KBCW"]
	CSPAN = ["CSPAN", "CSPAN2", "CSPAN3"]
	PBS = ["PBS", "WMPT", "WETA", "WHUT", "KSCM", "KQED", "KQEH"]
	COM = ["COM", "COMW"] #comedy central 
	UNI = ["UNI", "WFDC", "KDTV"] #univision, spanish language channel
	CURRENT = ["CURRENT"]
	#california independent networks" 
	CAL = ["CAL", "KRCB", "KICU", "KOFY", "KRON"] 
	LINKTV = ["LINKTV"]
	corporations = [CNN, FOX, NBC, ABC, CBS, CW, CSPAN, PBS, COM, UNI, CURRENT, CAL, LINKTV]
	frequencies = defaultdict(int)
	#go through the list of extracted subnetworks and sort under their respective corporation umbrellas
	#done by creating a new frequency defaultdict and storing them under the first item of each 
	#corporation list.
	for subnetwork in networkslist:
		for corp in corporations:
			for affiliate in corp:
				if subnetwork == affiliate:
					frequencies[str(corp[0])] += 1
	return frequencies

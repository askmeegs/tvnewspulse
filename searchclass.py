#define model classes to interact with in the console

from google.appengine.ext import db
import json
import urllib2
from datetime import datetime
import time

class Search(db.Model):
	searchToken = db.StringProperty()
	numberResults = db.IntegerProperty()
	broadcastDates = db.TextProperty()

token = "GOP"
data = "" 
dateslist = []
parsedDates = []
search = Search(searchToken = token, numberResults = 0, broadcastDates = "")
search.put()

#function that repeatedly loads from a JSON all videos on a search token for most recent available date
#(48 hours ago)

def getData():
	rows = 100;
	start = 0;
	moreData = True
	numResults = 0;
	rows = 300
	today = "20130429"
	
	data = json.load(open('GOP.json'))
	numResults = numResults + len(data)
	print "For " + token + ", " + str(numResults) + " RESULTS FOUND."
	separateDates(data) #CALL
	
	#create GAE entity and store in the datastore
	search.numberResults = numResults
	search.broadcastDates = str(parsedDates)
	search.put()
	
#to make a line graph of broadcasts per date, we need date objects paired with int frequencies 
def separateDates(data):
	for item in data:
		titleparts = item['title'].split(' : ')
		if len(titleparts) == 2:
			dateslist.append(titleparts[1])
		else: 
			dateslist.append(titleparts[2])
	for date in dateslist:
		parsedDates.append(parseDate(str(date)))

def parseDate(input):
	dateList = str(input).split(" ")
	stringDate = str(dateList[0] + " " + dateList[1] + " " + dateList[2])
	parsedDate = datetime.strptime(stringDate, '%B %d, %Y')
	return parsedDate
	
getData()

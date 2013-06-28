#Main.py
#Project name: TVNewsPulse
#Written by: Megan O'Keefe & Lindsey Tang
#April 21 - May 12, 2013
#CS 249 Spring '13, Eni Mustafaraj, Project #3

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

#load the html templates environment
jinja = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))

#defines the Search entity, created whenever you enter a search not already in the datastore
class Search(db.Model):
	token = db.StringProperty()
	numberResults = db.IntegerProperty()
	dateFrequency = db.TextProperty()
	networkFrequency = db.TextProperty() 

#saves the searches for a single user when they are logged in    		
class SaveSearches(db.Model):
    searches = db.TextProperty()
    userid = db.StringProperty()
    dateAdded=db.DateTimeProperty(auto_now_add=True)


#saves the notes a user enters for a search
class SaveNotes(db.Model):
	notes=db.TextProperty()

#this handles the index.html when you first go to the url, deals with user login data,
#and, if they have past searches, the user's past searches and notes	
class MainHandler(webapp2.RequestHandler):
	def get(self):
		user = users.get_current_user()
		login_url = users.create_login_url(self.request.path)
		logout_url = users.create_logout_url(self.request.path) 
		s=""
		displayNotes=""
		#if a user is logged in, grab their past searches and saved notes.
		if user: 
			search=db.Query(SaveSearches).filter('userid = ', user.user_id()).order("-dateAdded")
			#get user's saved notes
			grab2=SaveNotes.get_by_key_name(user.user_id())
			if grab2!=None:
				displayNotes=grab2.notes
			#get user's saved searches
			if search.count()>0:
				i=0
				while(i<search.count()):
					s=s+'<option>'+search[i].searches+'</option>'
					i=i+1
												
		template_values = {
			'user': user,
			'login_url': login_url,
			'logout_url': logout_url,
			'scrollList': s,
			'notes': displayNotes,
			 }
	#using an html template, write the user data to index.html to be rendered on the webpage
		template = jinja.get_template('index.html')  
		self.response.write(template.render(template_values))


#this request handler deals with the event that the user presses "Save" for their notes
#what happens when you press Save?
	#gets the current searchTerm and notes passed from the post jQuerey
	#creates a key_name string by combining the user_id and searchterm
	#saves the notes to an entity with that key_name, replacing the exisiting notes if there are any
	#changes displayNotes to newNotes so that the newly entered notes are displayed in the text area
class SaveHandler(webapp2.RequestHandler):
	def post(self):
		user = users.get_current_user()
		if user:
			searchterm = self.request.get("searchterm")
			newNotes = self.request.get("notes")
			key=str(user.user_id()+searchterm)
			obj = SaveNotes(key_name=key,notes=newNotes)
			obj.put() #update the user's saved notes by re-"putting" the Save entity
			displayNotes=newNotes
			responseDict = {
				'notes': displayNotes #update the webpage with your newly saved notes
				 }
			modifiedDict = json.dumps(responseDict)
			self.response.write(modifiedDict)
		
#SearchHandler: handles the event that the user presses the Search button 
#what happens when you press Search?
	#checks to see if a search by your token is in the datastore
	#if not...
		#gets the data from TVNews
		#parses out network and date frequency data 
		#makes a Search entity from this data and puts it into the datastore
		#writes out information through json.dumps to be used in our index JS code
		
class SearchHandler(webapp2.RequestHandler):
		
	def post(self): #not the same post as jquery $.post
		searchterm = self.request.get("searchterm")
		modifiedToken = cleanToken(searchterm)
		user = users.get_current_user()
		s=""
		results=""
		
		if user: 
			user_id=user.user_id()
			key=str(user.user_id()+searchterm)
			obj = SaveSearches(key_name=key, userid=user.user_id(), searches=searchterm)
			obj.put()
			
			search=db.Query(SaveSearches).filter('userid = ', user.user_id()).order("-dateAdded")
			if search.count()>0:
				i=0
				while(i<search.count()):
					s=s+'<option>'+search[i].searches+'</option>'
					i=i+1
					
		else:
			obj = SaveSearches(userid="Anonymous", searches=searchterm)
			obj.put()
		
					
		#query to see if this search is in the datastore
		q = Search.all()
		q.filter("token =", searchterm) #see if a search exists where the searchterm equals the token
		search = q.get()
		print "on querying, got " + str(search)
	
		if search is None: #...is this search isn't already in the datastore, reference processData.py helper functions
			data = compileData(modifiedToken) #get the data from TV News
			numResults = len(data)
			parsedDates = separateDates(data) #parse out the dates from the json data
			dateFreq = str(countFrequency(parsedDates)) #make a date frequency dictionary
			networkFreq = str(classifyNetworks(data)) #make a network frequency dictionary
			#define and put a new search entity with information gotten from helper functions
			search = Search(token = searchterm, numberResults = numResults, dateFrequency = dateFreq, networkFrequency = networkFreq)
			search.put()
			
		#now we have a search no matter what, either newly created or old from datastore
		#let's parse:
		numResults = search.numberResults
		
		#parse our date frequency dictionary so that it's in string form for Javascript to parse and read
		#steps:
		# 1)decompose the data extracted from the datastore- eliminating filler characters, keeping only the values
		# 2)turn the values into a list of strings, by splitting the string
		# 3)reconstruct the string so that the values are in the order required by Google Charts Annotated Time Line (dates and frequencies) 
		# 4)do this systematically so that every date in the data is formatted correctly  
		# 5)repeat the steps for the networkFrequency, but change how the data are formatted (because we're prepping for the Google Pie Chart now) 
		
		list1= search.dateFrequency.replace("OrderedDict","").replace("), (", ",").replace("([(","").replace(")])","").replace("'","").replace(" ","").split(",")
		processedString=""
		i = 0
		while (i+3 < len(list1)):
			processedString=processedString+list1[i+2]+","+list1[i]+","+list1[i+1]+","+list1[i+3]+","
			i = i + 4
			
		#parse our network frequency data into a string that's readable for JavaScript
		#prepares the string by turning it into a list of primitive integers(in type string)in the appropriate order for google pie chart
		
		list2= search.networkFrequency.replace("), (",",").replace("[(","").replace(")]","").replace("'","").replace(" ","").split(",")
		processedString2=""
		i = 0
		while (i+1 < len(list2)):
			processedString2=processedString2+list2[i]+","+list2[i+1]+","
			i = i + 2

		displayNotes = ""
		#if a user has logged in, query the user's saved notes and store them in variable displayNotes
		if user:
			key=str(user.user_id()+searchterm) #the key has to be unique so that notes for a particular searchterm can be updated (overwrite-able)
			temp=SaveNotes.get_by_key_name(key)
			if temp is not None: 
				displayNotes=temp.notes
			else:
				displayNotes=""
		
		login_url = users.create_login_url(self.request.path)
		logout_url = users.create_logout_url(self.request.path)
		responseDict = {
			'token': search.token,
			'numResults' : numResults,
			'timeLineDisplay': processedString,
			'pieChartDisplay': processedString2,
			'information': results,
			'scrollList': s,
			'currentTerm': search.token,
			'notes': displayNotes
			}
		#dump all data into a dictionary and write it
		modifiedDict = json.dumps(responseDict)
		self.response.write(modifiedDict)

		
app = webapp2.WSGIApplication([
    ('/', MainHandler), ('/search', SearchHandler), ('/prefs',SaveHandler)
    ], debug=True)

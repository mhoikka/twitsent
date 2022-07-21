import requests
import json
import datetime as dt
import math
import pickle
from cleantext import clean
import re
import time
import twitsent.plot_sent as ps
import twitsent.parse_sentiment as pars
import twitsent.twitterquery as tq
import sys
import os
import twitsent.store_data as sd
import twitsent.dateselect as ds
import twitsent.makescript as ms
from os import listdir
from os.path import isfile, join
import datetime as dt

bearer_token = ''

class RateLimitError(Exception):
    def __init__(self, message):
        super().__init__(message)
        
class TwitterAPIArgumentError(Exception):
    def __init__(self, message):
        super().__init__(message)

class CalendarError(Exception):
    def __init__(self, message):
        super().__init__(message)
        
def bearer_oauth(r):
    """
    Method required by bearer token authentication.

    Parameters
    --------
    
    Returns
    --------

    Raises
    --------
    
    """
    
    r.headers["Authorization"] = f"Bearer {bearer_token}"
    r.headers["User-Agent"] = "v2RecentSearchPython"
    
    return r

def connect_to_endpoint(acad_access, params, exceeds_rl):
    """
    Make http connection to Twitter Search API v2.

    Parameters
    --------
    acad_access : string
        A string 'y'/'n' that represents whether the user has academic acces and wants to perform a full archive search
    params: dictionary
        contains the specific details of the request to the API
    exceeds_rl :
	whether the given query will likely exceed the Twitter Search API v2 rate limit

    Returns
    --------
     : json
        the response from the Twitter API
        
    Raises
    --------
    RateLimitError
        if user attempts too many requests in a short period of time
        
    """

    url = ""
    if acad_access == 'n':
        url = "https://api.twitter.com/2/tweets/search/recent" 
    else: 
        url = "https://api.twitter.com/2/tweets/search/all"


    response = requests.get(url, auth=bearer_oauth, params=params)
    print(response.status_code)
    # if rate limit response code is received, wait 15 minutes until limit is reset
    if response.status_code == 429:
        print("Rate limit exceeded, waiting until request can be satisfied")
        time.sleep(900)
        print("Restarting query")
        response = requests.get(url, auth=bearer_oauth, params=params)
        print(response.status_code)
    if response.status_code == 429:
        raise RateLimitError("Rate limit was not reset after 15 minutes as expected, quitting")
    if response.status_code != 200:
        raise Exception(response.status_code, response.text)

    #full archive search rate limits searches to 300 per 15 minutes, while recent search is limited to 450 per 15 minutes
    if exceeds_rl == True:
        if acad_access == 'y':
            time.sleep(3) 
        else: 
            time.sleep(2)
	 
    return response.json()

def create_timeseries(query_params, json_max, totaltime, interval_len, acad_access, end_time_raw = dt.datetime.now(dt.timezone.utc)):
    """
    

    Parameters
    --------
    query_params : dictionary
        serves as instructions for the twitter search api 
    json_max : int
        max number of tweets to store as cleaned text per time interval
    totaltime : int
        length of time in minutes between earliest and latest possible tweets retrieved in API requests
    interval_len : int
        length of each distinct time interval for tweet retrieval in minutes
    end_time_raw : dt.datetime()
        non-adjusted end time of tweet range
    acad_access : string
        A string 'y'/'n' that represents whether the user has academic acces and wants to perform a full archive search
        
    Returns
    --------
    json_response_list : 2D list
        each entry is a string containing cleaned tweet text from within the
        time interval represented by the sub-list within which it is contained.
        
    Raises
    --------
    
    """
    
    #calculate number of API requests needed
    req_num = int((totaltime/interval_len)*math.ceil(json_max/100))

    #calculate if rate limit would be exceeded when requests are made
    exceeds_rl = False
    if acad_access == 'n':
        if req_num > 450:
            exceeds_rl = True
    else:	
        if req_num > 300:
            exceeds_rl = True
    
    #calculate likely time needed to complete search
    time_req = -1
    if exceeds_rl:
        time_req = req_num / 20
    else:
        time_req = req_num / 60    
        time_req = math.ceil(time_req)
	
    print(f"{req_num} requests must be made to the API to satisfy your chosen parameters, which could take up to {time_req} minutes")

    #Twitter API request needs to be historical by at least 10 seconds
    offset_delta = dt.timedelta(seconds = 30)
    end_time_raw -= offset_delta   
    
    test_delta = dt.timedelta(minutes=1)
    
    json_count = 0 #stores number of tweets retrieved for each tine interval so far
    json_count_list = [] #stores final number of tweets collected per each time interval
    
    '''
    run test to see how many requests are likely needed to fulfill json_max requirement for a given historical period
    '''
    #calculate start and endpoints for one interval
    start_time_raw = end_time_raw - test_delta
    #convert to the timedate format that the twitter api needs
    start_time = start_time_raw.isoformat()
    end_time = end_time_raw.isoformat()
        
    #TODO retrieve twitter api search results for time interval
    query_params['start_time'] = start_time
    query_params['end_time'] = end_time
    
    #twitter search api v2 limits search results to 100 per request
    if json_max < 100:
        query_params['max_results'] = json_max
    else: 
        query_params['max_results'] = 100
        
    json_response = connect_to_endpoint(acad_access, query_params, exceeds_rl) 
        
    '''
    count number of tweets found within the last minute 
    '''
    if 'data' in json_response:
        #extract tweet data fron json response line
        data = json_response["data"]
        #extract text from tweet list
        for tweet_inst in data:
            json_count += 1
                
        if 'next_token' in json_response:
            next_token = json_response["meta"]["next_token"]
        else:
            next_token = None
                
        while(next_token is not None):
            # construct a ruleset from all rules
            query_params['next_token'] = next_token
            query_params['max_results'] = 100
            json_response = connect_to_endpoint(acad_access, query_params, exceeds_rl)
                
            json_count += 1
                
            if 'next_token' in json_response:
                next_token = json_response["meta"]["next_token"]
            else:
                next_token = None
    #no tweets were found in the last minute, assume that tweets about subject are rare
    else:
        json_count = 1
      
    '''
    retrieve actual data for historical period
    '''
    #how many intervals need to be queried
    interval_num = math.ceil(totaltime / interval_len)  
    if totaltime % interval_len != 0:
        print("Warning: One time interval is of unequal length to the others and will likely not have complete data. Please ensure that total time is divisible by interval length") 
        
    #estimate how many minutes interval_len needs to be to ensure adequate data is collected
    mins = json_max / json_count * 2
    if mins > interval_len:
        print("Warning: data collection will likely be incomplete due to short time intervals allotted for tweet collection or low tweet quantity")
        
    # number of queries within each interval likely needed to retrieve adequate data 
    requests = math.ceil(json_max / 100)
    
    #calculate how long of a time interval is allotted for each search request given the necessary number of requests per interval
    delta = dt.timedelta(minutes=interval_len)
    request_delta = delta/requests
    
    json_interval = [] #stores json tweet data for each time interval
    json_response_list = [] #stores all json interval data
    json_count = 0 #reset json_count variable after test
    end_copy = end_time_raw
    
    #for each interval
    for time_int in range(interval_num):
        #multiple requests are made per time interval due to twitter's limit (100) to the quantity of tweets retrieved per request
        for request in range(requests):
            #if the max number of tweets per interval has not yet been reached
            if json_count < json_max:
                #calculate start and endpoints for one request
                start_time_raw = end_time_raw - request_delta
                #convert to the timedate format that the twitter api needs
                start_time = start_time_raw.isoformat()
                end_time = end_time_raw.isoformat()
                
                query_params['start_time'] = start_time
                query_params['end_time'] = end_time
                
                #twitter search api v2 limits search results to 100 per request
                if json_max < 100:
                    query_params['max_results'] = json_max
                else: 
                    query_params['max_results'] = 100
                    
                json_response = connect_to_endpoint(acad_access, query_params, exceeds_rl) 
                
                '''
                extract and clean useful data from tweet, then store it in a time-delimited array
                '''
                if 'data' in json_response:
                    #extract tweet data fron json response line
                    data = json_response["data"]
                    #extract text from tweet list
                    #twitter returns more than one tweet per request
                    for tweet_inst in data:
                        if json_count < json_max:
                            text = tweet_inst["text"]
                            #remove emojis and other symbols from tweet text
                            text = clean(text,
                                fix_unicode=True,               # fix various unicode errors
                                to_ascii=True,                  # transliterate to closest ASCII representation
                                lower=True,                     # lowercase text
                                no_line_breaks=True,           # fully strip line breaks as opposed to only normalizing them
                                no_urls=True,                  # replace all URLs with a special token
                                no_emails=True,                # replace all email addresses with a special token
                                no_phone_numbers=True,         # replace all phone numbers with a special token
                                no_numbers=True,               # replace all numbers with a special token
                                no_digits=True,                # replace all digits with a special token
                                no_currency_symbols=True,      # replace all currency symbols with a special token
                                no_punct=True,                 # remove punctuations
                                replace_with_url="",
                                replace_with_email="",
                                replace_with_phone_number="",
                                replace_with_number="",
                                replace_with_digit="",
                                replace_with_currency_symbol="",
                                no_emoji=True,
                                lang="en"                       # set to 'de' for German special handling
                                )
                            #remove retweet characters and end of line characters from tweet text
                            text = re.sub(r"\brt\b","",text)
                            #remove non-utf-8 characters from string
                            tweet = bytes(text, 'utf-8').decode('utf-8', 'ignore')
                            
                            tweet = str(tweet)
                            tweet = tweet.strip()
                               
                            #store data retrieved and paginate if necessary
                            json_interval.append(tweet)
                            json_count += 1
                else:
                    print("No matching tweets for time interval starting at " + start_time)
                if 'next_token' in json_response:
                    next_token = json_response["meta"]["next_token"]
                else:
                    next_token = None
            else:
                break
            #twitter requires you to interate through page requests if more tweets were found than fit in one response(up to a limit of 100 tweets total)
            while(next_token is not None):
                if json_count < json_max:
                    # construct a ruleset from all rules
                    query_params['next_token'] = next_token
                    #twitter search api v2 limits search results to 100 per request
                    if json_max < 100:
                        query_params['max_results'] = json_max
                    else: 
                        query_params['max_results'] = 100
                    json_response = connect_to_endpoint(acad_access, query_params, exceeds_rl)
                    
                    '''
                    extract and clean useful data from tweet, then store it in a time-delimited array
                    '''
                    #extract tweet data fron json response line
                    data = json_response["data"] 
                    #extract text from tweet data
                    text = data["text"]
                    #remove emojis from tweet text
                    text = clean(text,
                        fix_unicode=True,               # fix various unicode errors
                        to_ascii=True,                  # transliterate to closest ASCII representation
                        lower=True,                     # lowercase text
                        no_line_breaks=True,           # fully strip line breaks as opposed to only normalizing them
                        no_urls=True,                  # replace all URLs with a special token
                        no_emails=True,                # replace all email addresses with a special token
                        no_phone_numbers=True,         # replace all phone numbers with a special token
                        no_numbers=True,               # replace all numbers with a special token
                        no_digits=True,                # replace all digits with a special token
                        no_currency_symbols=True,      # replace all currency symbols with a special token
                        no_punct=True,                 # remove punctuations
                        replace_with_url="",
                        replace_with_email="",
                        replace_with_phone_number="",
                        replace_with_number="",
                        replace_with_digit="",
                        replace_with_currency_symbol="",
                        no_emoji=True,
                        lang="en"                       # set to 'de' for German special handling
                        )
                    #remove retweet characters and end of line characters from tweet text
                    text = re.sub(r"\brt\b","",text)
                    #remove non-utf-8 characters from string
                    tweet = bytes(text, 'utf-8').decode('utf-8', 'ignore')
                    
                    tweet = str(tweet)
                    tweet = tweet.strip()
                    json_interval.append(tweet)
                    json_count += 1
                    
                    if 'next_token' in json_response:
                        next_token = json_response["meta"]["next_token"]
                    else:
                        next_token = None
                else:
                    next_token = None
        #update datetime endpoints with original undivided delta to ensure uniformity of each interval length is maintained(I am uncertain how the datetime python package rounds values when you perform operations on a timedelta object)
        end_time_raw = end_copy - delta
        end_copy  = end_time_raw

        json_response_list.append(json_interval.copy())
        json_count_list.append(json_count)
        json_count = 0
        json_interval.clear()
        
        
    return json_response_list
            
'''
Retrieve tweets that contain certain keywords, parse sentiment scores from the text, then graph average sentiment over a specific timespan with certain intervals
'''    
def main():
    """
    Prompt user for query details then retrieve tweet responses and parse them
    for sentiment. Store that data in files and create a graph, then open an html
    file that explains the project details.

    Parameters
    --------
    
    Returns
    --------

    Raises
    --------
    TwitterAPIArgumentError
        If illegal arguments to the Twitter Search API v2 are selected by
        the user
        
    CalendarError
        if user does not select valid values from the calendar window before it
        closes
        
    """
    
    # Optional params: start_time,end_time,since_id,until_id,max_results,next_token,
    # expansions,tweet.fields,media.fields,poll.fields,place.fields,user.fields
    rule = None
    rule2 = [['the'],['i'],['to'],['a'],['and'],['is'],['in'],['it'],['you'],['of'],['for'],['on'],['my'],['that'],['at'],['with'],['me'],['do'],['have'],['just'],['this'],['be'],['so'],['are'],['not']] #list of 10 most common english words
   
    lang = ["en"]
    #construct the query for Twitter's search API v2
    #query_params = tq.make_query(rule, lang)
    query_params2 = tq.make_query(rule2, lang)
    
    #set default search and storage parameters
    start_dt = None
    end_dt = None
    datestr = ""
    datestr2 = ""
    newdatestr2 = ""
    academic_access = ""
    use_default = ""
    start_fresh = ""
    past_file = ""
    json_max = 10 #2500 tweets retrieved per hour maxes out 2M tweet per month limit
    interval_len = 240
    totaltime = 0
    exists_prevdata = True
    has_academic = False
    
    #get path to parent directory of this file
    rel_path = os.path.dirname(os.path.realpath(__file__))

    #construct the full path to store collected tweet data
    datadir = "storedqueries"
    mypath = os.path.join(rel_path, datadir)
          
    #make the data storage directory if it doesn't already exist
    os.makedirs(os.path.abspath(mypath), mode=0o666, exist_ok=True)
    
    onlyfiles = [f for f in listdir(mypath) if isfile(join(mypath, f))]

    date_c = []
    
    print("Do you want to use your academic access to the Twitter Search API (if applicable)? Y/N or Q to quit")
    while (academic_access.lower() != 'y' and academic_access.lower() != 'n' and academic_access.lower() != 'q'):
        academic_access = input()
    if academic_access.lower() == 'q':
        return 
        
    while (use_default.lower() != 'y' and use_default.lower() != 'n' and use_default.lower() != 'q'):
        use_default = input("Use default data collection settings? Y/N or Q to quit: ")
    if use_default.lower() == 'q':
        return

    while (start_fresh.lower() != 'y' and start_fresh.lower() != 'n' and start_fresh.lower() != 'q'):
        start_fresh = input("Start new data collection? Y/N or Q to quit: ")
    if start_fresh.lower() == 'q':
        return
    
    search_terms = input("Enter a comma delimited list of search terms, D for default terms, or Q to quit: ").lower()
    if search_terms == 'q':
        return
    if search_terms == 'd':
        rule = [["corona virus"],['coronavirus'],["corona", "-beer"], ["covid"], ['covid 19'], ['covid19'], ['covid-19'], ['sarscov2'], ['sars cov 2'], ['sars-cov-2'], ['#coronavirus'], ['#corona'], ['#covid'], ['#covid19'], ['#sarscov2']]
    else:
        #Create a rule array from user input
        terms = search_terms.split(",")# TODO watch out for malicious input here
        rule = [sub_term.split(" ") for sub_term in terms]

    query_params = tq.make_query(rule, lang)
    
    if(use_default.lower() == 'y'):
        if start_fresh.lower() == 'y':
            ci = ds.Cal_Impl(False)
            ci.run_cal()

            if( not ci.has_values): #check if parameters were chosen from the calendar, or if it was closed prematurely
                raise CalendarError("Calendar did not select values before quitting")
            #retrieve start and end dates from calendar
            datestr = ci.datestr
            datestr2 = ci.datestr2
            newdatestr2 = datestr2
            
            #construct datetime dates for query limits calculation
            date2_r = datestr2.split("/")  
            date2 = dt.date(int(date2_r[2])+2000, int(date2_r[0]), int(date2_r[1]))
                
            #retrieve timezone-aware time at exactly midnight
            ti = dt.time(tzinfo = dt.timezone.utc)
                
            end_dt = dt.datetime.combine(date2,ti)
              
            #retrieve query params from calendar 
            json_max = int(ci.json_max)
            interval_len = int(ci.interval_len)
            totaltime = ci.totaltime
            
            #calculate the time in minutes between the current time and the time of the first request
            delta_first_request = (dt.datetime.now(dt.timezone.utc)-end_dt)/dt.timedelta(minutes = 1)
            
            #ensure that users follow API request time limitations 
            if totaltime + delta_first_request >= 10080 and academic_access != 'y': #if user does not have academic access, they cannot request tweets more than a week in the past
                raise TwitterAPIArgumentError("Academic access to Twitter's API is required to search for tweets more than a week in the past")
            '''
            If starting fresh, delete past data
            '''
            #find past data storage files with matching search parameters
            file_matches = []
            for file in onlyfiles:
                file_data = file.split("_")
                file_prefix = file_data[0]
                if file_prefix == "":
                    continue
                file_json_max = int(file_data[3])
                file_interval_len = int(file_data[4])
                if ((file_prefix == 'tweet' or file_prefix == 'senti') and file_json_max == json_max and file_interval_len == interval_len):
                    file_matches.append(file)
                 
            #if previous data storage file exists, delete it
            for file in file_matches: 
                filepath = os.path.join(mypath,file)
                if "_archived_" in file:
                    os.remove(filepath)
                if os.path.exists(filepath):
                    os.rename(filepath, os.path.join(mypath, "_archived_" + file))
                else:
                    print(f"Cannot delete the file ({filepath}) because it does not exist")   
                    
        elif start_fresh.lower() == 'n':
            ci = ds.Cal_End(False)
            ci.run_cal()
            
            if( not ci.has_values): #check if parameters were chosen from the calendar, or if it was closed prematurely
                raise CalendarError("Calendar did not select values before quitting")
            #search in specified directory for file that matches default data storage file values (which are contained within the file name)
            for file in onlyfiles:
                file_data = file.split("_")
                file_prefix = file_data[0]
                if file_prefix == "":
                    continue
                file_startdate = file_data[1]
                datestr = file_startdate
                file_enddate = file_data[2]
                datestr2 = file_enddate
                date_c = file_enddate.split(".")
                file_json_max = int(file_data[3])
                file_interval_len = int(file_data[4])
                if ((file_prefix == 'tweet' or file_prefix == 'senti') and file_json_max == json_max and file_interval_len == interval_len):
                    past_file = file
                    break
            if past_file == "":
                print("No previous tweet data found")
                return
                
            newdatestr2 = ci.datestr2
            
            #construct datetime date for query end
            date2_r = newdatestr2.split("/")  
            end_date = dt.date(int(date2_r[2])+2000, int(date2_r[0]), int(date2_r[1]))
                
            #retrieve timezone-aware time at exactly midnight
            ti = dt.time(tzinfo = dt.timezone.utc)
              
            #date of last recorded entry in csv file
            prev_end_date = dt.date(int(date_c[2])+2000, int(date_c[0]), int(date_c[1])) #prev_end_date date of data collection will be end date of last data collection period
            
            #string representation of query end date for use in csv filenames
            newdatestr2 = str(end_date.month).lstrip("0") + "." + str(end_date.day).lstrip("0") + "." + str(end_date.year)[-2:] 
            
            #set query time constraints
            start_dt = dt.datetime.combine(prev_end_date,ti) #Note that start_dt does NOT correspond to the datetime when data collection first started, but the most recent data collection starting point!
            end_dt = dt.datetime.combine(end_date,ti)
            totaltime = int((end_dt - start_dt) / dt.timedelta(minutes = 1))
            
            #calculate the time in minutes between the current time and the time of the first request
            delta_first_request = (dt.datetime.now(dt.timezone.utc)-end_dt)/dt.timedelta(minutes = 1)
            
            #ensure that users follow API request time limitations 
            if totaltime + delta_first_request >= 10080 and academic_access != 'y': #if user does not have academic access, they cannot request tweets more than a week in the past
                raise TwitterAPIArgumentError("Academic access to Twitter's API is required to search for tweets more than a week in the past")

    elif(use_default.lower() == 'n'):      
        if start_fresh.lower() == 'y':
            ci = ds.Cal_Impl(True)
            ci.run_cal()
            
            if( not ci.has_values): #check if parameters were chosen from the calendar, or if it was closed prematurely
                raise CalendarError("Calendar did not select values before quitting")
            #retrieve start and end dates from calendar
            datestr = ci.datestr
            datestr2 = ci.datestr2
            newdatestr2 = datestr2
            
            #construct datetime dates for query limits calculation
            date2_r = datestr2.split("/")  
            date2 = dt.date(int(date2_r[2])+2000, int(date2_r[0]), int(date2_r[1]))
                
            #retrieve timezone-aware time at exactly midnight
            ti = dt.time(tzinfo = dt.timezone.utc)
                
            end_dt = dt.datetime.combine(date2,ti)
              
            #retrieve query params from calendar 
            json_max = int(ci.json_max)
            interval_len = int(ci.interval_len)
            totaltime = ci.totaltime
            
            #calculate the time in minutes between the current time and the time of the first request
            delta_first_request = (dt.datetime.now(dt.timezone.utc)-end_dt)/dt.timedelta(minutes = 1)
            
            #ensure that users follow API request time limitations 
            if totaltime + delta_first_request >= 10080 and academic_access != 'y': #if user does not have academic access, they cannot request tweets more than a week in the past
                raise TwitterAPIArgumentError("Academic access to Twitter's API is required to search for tweets more than a week in the past")
                
            '''
            If starting fresh, delete past data
            '''
            #find past data storage files with matching search parameters
            file_matches = []
            for file in onlyfiles:
                file_data = file.split("_")
                file_prefix = file_data[0]
                if file_prefix == "":
                    continue
                file_json_max = int(file_data[3])
                file_interval_len = int(file_data[4])
                if ((file_prefix == 'tweet' or file_prefix == 'senti') and file_json_max == json_max and file_interval_len == interval_len):
                    file_matches.append(file)
                 
            #if previous data storage file exists, delete it
            for file in file_matches: 
                filepath = os.path.join(mypath,file)
                if "_archived_" in file:
                    os.remove(filepath)
                if os.path.exists(filepath):
                    os.rename(filepath, os.path.join(mypath, "_archived_" + file))
                else:
                  print(f"Cannot delete the file ({filepath}) because it does not exist")
                  
        elif start_fresh.lower() == 'n':
            ci = ds.Cal_End(True)
            ci.run_cal()
            
            if( not ci.has_values): #check if parameters were chosen from the calendar, or if it was closed prematurely
                raise CalendarError("Calendar did not select values before quitting")
            #retrieve query params from calendar 
            json_max = int(ci.json_max)
            interval_len = int(ci.interval_len) 
                
            #search in specified directory for file that matches default data storage file values (which are contained within the file name)
            for file in onlyfiles:
                file_data = file.split("_")
                file_prefix = file_data[0]
                if file_prefix == "":
                    continue
                file_startdate = file_data[1]
                datestr = file_startdate
                file_enddate = file_data[2]
                datestr2 = file_enddate
                date_c = file_enddate.split(".")
                file_json_max = int(file_data[3])
                file_interval_len = int(file_data[4])
                if ((file_prefix == 'tweet' or file_prefix == 'senti') and file_json_max == json_max and file_interval_len == interval_len):
                    past_file = file
                    break
            if past_file == "":
                print("No previous tweet data found")
                return
            
            newdatestr2 = ci.datestr2
            
            #construct datetime dates for query limits calculation
            date2_r = newdatestr2.split("/")  
            end_date = dt.date(int(date2_r[2])+2000, int(date2_r[0]), int(date2_r[1]))
                
            #retrieve timezone-aware time at exactly midnight
            ti = dt.time(tzinfo = dt.timezone.utc)      
            
            prev_end_date = dt.date(int(date_c[2])+2000, int(date_c[0]), int(date_c[1])) #prev_end_date date of data collection will be end date of last data collection period
            
            #string representation of query end date for use in csv filenames
            newdatestr2 = str(end_date.month).lstrip("0") + "." + str(end_date.day).lstrip("0") + "." + str(end_date.year)[-2:] 
            
            #set query time constraints
            start_dt = dt.datetime.combine(prev_end_date,ti) #Note that start_dt does NOT correspond to the datetime when data collection first started, but the most recent data collection starting point!
            end_dt = dt.datetime.combine(end_date,ti)
            totaltime = int((end_dt - start_dt) / dt.timedelta(minutes = 1))
            
            #calculate the time in minutes between the current time and the time of the first request
            delta_first_request = (dt.datetime.now(dt.timezone.utc)-end_dt)/dt.timedelta(minutes = 1)
            
            #ensure that users follow API request time limitations 
            if totaltime + delta_first_request >= 10080 and academic_access != 'y': #if user does not have academic access, they cannot request tweets more than a week in the past
                raise TwitterAPIArgumentError("Academic access to Twitter's API is required to search for tweets more than a week in the past")
        
    #check for illegal arguments 
    if interval_len < 1:
        raise TwitterAPIArgumentError(f"Invalid time interval ({interval_len}) received")
    if totaltime < 1:
        raise TwitterAPIArgumentError(f"Invalid duration of search ({totaltime}) received. Ensure that start date and end date arguments of data collection are sequential.")
    pluralizer = "s" if interval_len > 1 else ""
    if json_max < 1:
        raise TwitterAPIArgumentError(f"Invalid rate of tweets ({json_max}) per ({interval_len}) minute{pluralizer} requested. At least one tweet must be requested per time interval.")
    
    #retrieve tweet data for each time interval within the total time queried
    json_response_list = create_timeseries(query_params, json_max, totaltime, interval_len, academic_access, end_dt)  
    json_response_list2 = create_timeseries(query_params2, json_max, totaltime, interval_len, academic_access, end_dt)
    
    #convert tweet text list into sentiment score list
    sentiment_list = pars.parse(json_response_list)
    sentiment_list2 = pars.parse(json_response_list2)
    
    #save tweet data collected for later use
    sd.save_lists(json_response_list, json_response_list2, sentiment_list, sentiment_list2, datestr, datestr2, newdatestr2, json_max, interval_len)
    
    #load all historical data for graphing if the user desires
    sentiment_list, _, sentiment_list2, _, totaltime = sd.load_lists(json_max, interval_len)

    #take mean of sentiment scores for each interval, using zero for the mean of any intervals that have no scores due to lack of data
    avg_sent = [sum(interval)/len(interval) if len(interval) != 0 else 0 for interval in sentiment_list]
    comp_sent = [sum(interval)/len(interval) if len(interval) != 0 else 0 for interval in sentiment_list2]
    
    #graph sentiment data 
    ps.sent_line(avg_sent, comp_sent, totaltime, interval_len)
    ms.make_page()
    
if __name__ == "__main__":
    print("Enter your Twitter API v2 bearer token or Q to quit")
    bearer_token = input()
    if bearer_token == 'q' or bearer_token == 'Q':
        exit()
    main()

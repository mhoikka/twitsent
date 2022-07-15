import os
import datetime as dt
import re
import pickle
import csv
from os import listdir
from os.path import isfile, join
import datetime as dt

class FileMatchException(Exception):
    def __init__(self, message):
        super().__init__(message)
        
def save_lists(json_response_list, json_sample_list, sentiment_list, sentiment_sample, start_t, end_t, new_end_t, json_max, interval_len):
    """
    Stores tweet data collected in files for later access

    Parameters
    --------
    json_response_list : list of strings
        cleaned text of tweets collected containing certain keywords
    json_sample_list : list of strings
        cleaned text of random tweets collected 
    sentiment_list- : list of floats
        sentiment scores of tweets collected containing certain keywords
    sentiment_sample : list of floats
        sentiment scores of random tweets collected 
    start_t- : string
        Start date of data collection.
    end_t : string
        End date of previous data collection file
    new_end_t : string
        End date of data collection
    json_max : int
        number of tweets collected per interval
    interval_len : int
        number of minutes per interval

    Returns
    --------
    None
    
    Raises
    --------
    FileMatchException
        Raised if files are unexpectedly missing when searched for
    """
    
    #string format of the time at the current moment
    time_now = dt.datetime.now().isoformat()
    
    #get path to parent directory of this file
    rel_path = os.path.dirname(os.path.realpath(__file__))

    #construct the full path to store collected tweet data
    datadir = "storedqueries"
    fullpath = os.path.join(rel_path, datadir)
    
    #remove illegal characters from filename
    tweetfile = "tweet_" + start_t + "_" + end_t + "_" + str(json_max) + "_" + str(interval_len) + "_"
    tweetfile = re.sub(r":",".",tweetfile)
    tweetfile = re.sub(r"/",".",tweetfile)
    tweetfile = re.sub(r"\.",".",tweetfile)
    sample_tweetfile = tweetfile
    tweetfile += ".csv"
    sample_tweetfile += "sample.csv"
    os.makedirs(os.path.abspath(fullpath), mode=0o666, exist_ok=True)
    
    #make new filename for updated enddate
    newtweetfile = "tweet_" + start_t + "_" + new_end_t + "_" + str(json_max) + "_" + str(interval_len) + "_"
    newtweetfile = re.sub(r":",".",newtweetfile)
    newtweetfile = re.sub(r"/",".",newtweetfile)
    newtweetfile = re.sub(r"\.",".",newtweetfile)
    new_sample_tweetfile = newtweetfile
    newtweetfile += ".csv"
    new_sample_tweetfile += "sample.csv"
    
    #remove illegal characters from filename
    sentifile = "senti_" + start_t + "_" + end_t + "_" + str(json_max) + "_" + str(interval_len) + "_"
    sentifile = re.sub(r":",".",sentifile)
    sentifile = re.sub(r"/",".",sentifile)
    sentifile = re.sub(r"\.",".",sentifile)
    sample_sentifile = sentifile
    sentifile += ".csv"
    sample_sentifile += "sample.csv"
    
    #make new filename for updated enddate
    newsentifile = "senti_" + start_t + "_" + new_end_t + "_" + str(json_max) + "_" + str(interval_len) + "_"
    newsentifile = re.sub(r":",".",newsentifile)
    newsentifile = re.sub(r"/",".",newsentifile)
    newsentifile = re.sub(r"\.",".",newsentifile)
    new_sample_sentifile = newsentifile
    newsentifile += ".csv"
    new_sample_sentifile += "sample.csv"
    
    #store tweet text array if needed
    with open(os.path.join(fullpath,tweetfile), "a", newline='') as csvfile:
        tweetwriter = csv.writer(csvfile, delimiter=',',quotechar='|', quoting=csv.QUOTE_MINIMAL)
        for row in json_response_list:
            tweetwriter.writerow(row)
    with open(os.path.join(fullpath,sample_tweetfile), "a", newline='') as csvfile:
        tweetwriter = csv.writer(csvfile, delimiter=',',quotechar='|', quoting=csv.QUOTE_MINIMAL)
        for row in json_sample_list:
            tweetwriter.writerow(row)
            
    #store tweet sentiment array if needed
    with open(os.path.join(fullpath,sentifile), "a", newline='') as csvfile:
        sentiwriter = csv.writer(csvfile, delimiter=',',quotechar='|', quoting=csv.QUOTE_MINIMAL)
        for row in sentiment_list:
            sentiwriter.writerow(row)
    with open(os.path.join(fullpath,sample_sentifile), "a", newline='') as csvfile:
        sentiwriter = csv.writer(csvfile, delimiter=',',quotechar='|', quoting=csv.QUOTE_MINIMAL)
        for row in sentiment_sample:
            sentiwriter.writerow(row)
    
    #check if tweet and sentiment files with matching parameters exists
    if not (os.path.exists(os.path.join(fullpath,tweetfile)) and os.path.exists(os.path.join(fullpath,sentifile))):
        raise FileMatchException("No matching tweet and sentiment files found")
        
    #rename file to reflect updated enddate
    if os.path.exists(os.path.join(fullpath,tweetfile)) and tweetfile != newtweetfile:
        os.rename(os.path.join(fullpath,tweetfile), os.path.join(fullpath,newtweetfile))
        
    if os.path.exists(os.path.join(fullpath,sample_tweetfile)) and tweetfile != new_sample_tweetfile:
        os.rename(os.path.join(fullpath,sample_tweetfile), os.path.join(fullpath,new_sample_tweetfile))
        
    #rename file to reflect updated enddate
    if os.path.exists(os.path.join(fullpath,sentifile)) and sentifile != newsentifile:
        os.rename(os.path.join(fullpath,sentifile), os.path.join(fullpath,newsentifile))
        
    if os.path.exists(os.path.join(fullpath,sample_sentifile)) and sentifile != new_sample_sentifile:
        os.rename(os.path.join(fullpath,sample_sentifile), os.path.join(fullpath,new_sample_sentifile))
        
def find_file(onlyfiles, prefix, json_max, interval_len, has_sample):
    """
    Given a list of parameters, this method returns data about the
    file that matches those parameters
    
    Parameters
    --------
    onlyfiles : list of paths
        Contains references to the files to be searched on with this method
    prefix : string
        file prefix to be searched for
    json_max : int
        max number of results stored in file for each time interval
    interval_len : int
        Represents length of collection intervals in minutes
    has_sample : boolean
        Represents whether the file is a comparison sample or contains the
        requested keywords

    Returns
    --------
    (past_file, datestr, datestr2, totaltime) : Tuple
        Contains the string file name that was searched for, the string start
        and end date of data storage and the int length of data collection in minutes
        
    Raises
    --------
    
    """
    
    past_file = ""

    #search in specified file list for sentiment file that matches specified data storage file values (which are contained within the file name)
    for file in onlyfiles:
        file_data = file.split("_")
        file_prefix = file_data[0]
        if file_prefix == "":
            continue
        file_startdate = file_data[1]
        datestr = file_startdate
        date_s = file_startdate.split(".")
        file_enddate = file_data[2]
        datestr2 = file_enddate
        date_c = file_enddate.split(".")
        file_json_max = int(file_data[3])
        file_interval_len = int(file_data[4])
        if ((file_prefix == prefix) and file_json_max == json_max and file_interval_len == interval_len):
            if has_sample:
                if "sample" in file:
                    past_file = file
                    break
            else:
                if "sample" not in file:
                    past_file = file
                    break
                    
    if past_file == "":
        raise FileMatchException("No sentiment storage files found")
        
    #create dates that represent the start and stop dates of file data storage
    start_date = dt.date(int(date_s[2])+2000, int(date_s[0]), int(date_s[1])) #using the date values from tweet_date_s and tweet_date_c is arbitrary; you could also use the equivalent sentiment values
    end_date = dt.date(int(date_c[2])+2000, int(date_c[0]), int(date_c[1]))
            
    #retrieve timezone-aware time at midnight
    ti = dt.time(tzinfo = dt.timezone.utc) 
        
    #make datetime from date and utc time 
    start_dt = dt.datetime.combine(start_date,ti) 
    end_dt = dt.datetime.combine(end_date,ti)
    
    #calculate totaltime from beginning of data collection to end
    totaltime = int((end_dt - start_dt) / dt.timedelta(minutes = 1))
        
    return (past_file, datestr, datestr2, totaltime)
        
def load_lists(json_max, interval_len):
    """
    Retrieve tweet data lists from file storage based on search parameters
    
    Parameters
    --------
    json_max- : int
        number of tweets collected per interval
    interval_len : int
        number of minutes per interval
        
    Returns
    --------
    (sentiment_list,tweet_list,sentiment_sample, tweet_sample, totaltime) : Tuple
        All lists that correspond to the search parameters received by this
        method as well as the total time (int) in minutes that the files contain
        data over

    Raises
    --------
    
    """
    
    #get path to parent directory of this file
    rel_path = os.path.dirname(os.path.realpath(__file__))

    #construct the full path to store collected tweet data
    datadir = "storedqueries"
    mypath = os.path.join(rel_path, datadir)
            
    onlyfiles = [f for f in listdir(mypath) if isfile(join(mypath, f))]
    
    past_sentifile = ""
    past_tweetfile = ""
    senti_datestr = "a"
    tweet_datestr = "b"
    tweet_datestr2 = "c"
    senti_datestr2 = "d"
    
    if not onlyfiles:
        raise FileMatchException("No data storage files found")
        
    #retrieve file name with specified parameters
    past_sentifile, senti_datestr, senti_datestr2, _ = find_file(onlyfiles, 'senti', json_max, interval_len, False)
    past_tweetfile, tweet_datestr, tweet_datestr2, _ = find_file(onlyfiles, 'tweet', json_max, interval_len, False)
    
    #retrieve file name with specified parameters that contains sample comparison data
    past_sample_sentifile, sample_senti_datestr, sample_senti_datestr2, _ = find_file(onlyfiles, 'senti', json_max, interval_len, True)
    past_sample_tweetfile, sample_tweet_datestr, sample_tweet_datestr2, totaltime = find_file(onlyfiles, 'tweet', json_max, interval_len, True)
    
    if tweet_datestr != tweet_datestr or tweet_datestr2 != senti_datestr2:
        raise FileMatchException("No matching tweet and sentiment files found")
    else:
        sentiment_list = []
        if os.path.exists(os.path.join(mypath,past_sentifile)):
            #retrieve tweet sentiment array 
            with open(os.path.join(mypath,past_sentifile), "r", newline='') as csvfile:
                sentireader = csv.reader(csvfile, delimiter=',',quotechar='|', quoting=csv.QUOTE_MINIMAL)
                for row in sentireader:
                    sentiment_list.append([float(row[0]), float(row[1])])
        sentiment_sample = []
        if os.path.exists(os.path.join(mypath,past_sample_sentifile)):
            #retrieve tweet sentiment array 
            with open(os.path.join(mypath,past_sample_sentifile), "r", newline='') as csvfile:
                sentireader = csv.reader(csvfile, delimiter=',',quotechar='|', quoting=csv.QUOTE_MINIMAL)
                for row in sentireader:
                    sentiment_sample.append([float(row[0]), float(row[1])])

        tweet_list = []
        if os.path.exists(os.path.join(mypath,past_tweetfile)):
            #retrieve tweet sentiment array 
            with open(os.path.join(mypath,past_tweetfile), "r", newline='') as csvfile:
                tweetreader = csv.reader(csvfile, delimiter=',',quotechar='|', quoting=csv.QUOTE_MINIMAL)
                for row in tweetreader:
                    tweet_list.append(row)
        tweet_sample = []
        if os.path.exists(os.path.join(mypath,past_sample_tweetfile)):
            #retrieve tweet sentiment array 
            with open(os.path.join(mypath,past_sample_tweetfile), "r", newline='') as csvfile:
                tweetreader = csv.reader(csvfile, delimiter=',',quotechar='|', quoting=csv.QUOTE_MINIMAL)
                for row in tweetreader:
                    tweet_sample.append(row)

        return (sentiment_list,tweet_list,sentiment_sample, tweet_sample, totaltime)
    

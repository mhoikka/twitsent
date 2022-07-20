import matplotlib.pyplot as plt
import math
import pymannkendall as mk
import pickle
import os

class TwitterAPIArgumentError(Exception):
    def __init__(self, message):
        super().__init__(message)
        
def sent_line(sent_array, sent_array_neu, totaltime, interval_len):
    """
    Given a list containing sentiment scores collected at specific intervals,
    this method draws a line-graph and tests for trends in the data, then saves
    the graph as a png for later use

    --------
    Parameters
    sent_array : list of floats
        Sentiment scores of tweets containing keywords being analyzed
    sent_array_neu : list of floats
        Sentiment scores of random tweets being analyzed
    totaltime : int
        time in minutes that data is collected for
    interval_len : int
        length of each interval that data is collected within

    --------
    Return
        None
        
    --------
    Raises
    TwitterAPIArgumentError
        If illegal parameters are attempted to be given to the Twitter API
    """
    
    if interval_len < 1:
        raise TwitterAPIArgumentError(f"Invalid time interval ({interval_len}) received")
    if totaltime < 1:
        raise TwitterAPIArgumentError(f"Invalid duration of search ({totaltime}) received. Ensure that start date and end date arguments of data collection are sequential.")
    time_list = [] #list of cumulative times elapsed since start time for each interval, in minutes 
    is_sig = ""
    num_intervals = math.ceil(totaltime/interval_len)
    time_elapsed = 0
    try:
        #calculate statistical significance of timeseries data without the assumption of gaussian distribution
        stat_sig = mk.original_test(sent_array, alpha = .05)
    except ZeroDivisionError:
        print("Time intervals of data collection exceed duration of data collection")

    #create x axis timeseries data for graphing, each datapoint spaced interval_len apart
    for i in range(num_intervals):
        #make sure that a smaller interval at the end(assuming total time isn't divided evenly by interval_len) isn't allotted the max interval_len
        time_list.append(min(time_elapsed,totaltime))
        time_elapsed += interval_len
    
    if stat_sig[1] is True:
        is_sig = 'statistically signicant'
    else:
        is_sig = 'statistically insignicant'
        
    #create a string that informs users about the statistical significance of any trend observed in the data
    stat_string = 'The trendline y = ' + str(round(stat_sig[7], 2)) + 'x' + ' + ' + str(round(stat_sig[8], 2)) + ' is ' + is_sig + '. The p-value of this particular \ntimeseries using the Mann-Kendall test is ' + str(round(stat_sig[2], 2)) + '.'

    #plt.figure(figsize=(8,6))
    fig, ax = plt.subplots(figsize=(8, 6))
    #entries in the sent_array list are in reverse chronological order
    ax.invert_xaxis()
    plt.gcf().subplots_adjust(bottom=0.2)
    plt.plot(time_list, sent_array, color = 'blue', marker = 'o', label="Search Term Sentiment")
    plt.plot(time_list, sent_array_neu, color = 'red', marker = 'o', label="Baseline Tweet Sentiment")
    plt.legend()
    plt.title('Sentiment Over Time', pad = 20, fontsize=24)
    plt.xlabel('Minutes Ago', fontsize=14)
    plt.ylabel('Average Sentiment', fontsize=14)
    plt.grid(True)
    plt.ylim((-1,1))
    plt.annotate(stat_string, xy = (0,-.2), fontsize=10,xycoords='axes fraction',ha='left') 
    #get path to parent directory of this file
    rel_path = os.path.dirname(os.path.realpath(__file__))
    plt.savefig(os.path.join(rel_path, 'sentiment_comparisongraph.png'), bbox_inches='tight')
        
'''
Hussain et al., (2019). pyMannKendall: a python package for non parametric Mann Kendall family of trend tests.. Journal of Open Source Software, 4(39), 1556, https://doi.org/10.21105/joss.01556
'''

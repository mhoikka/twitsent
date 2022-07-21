
# Twitter Sentiment Tracker
# Summer 2022 ACO 499

Tracks Twitter sentiment over time using Tweets that contain certain keywords and meet certain conditions. The data retrieved from Twitter can then be stored for later use, and an HTML file will open at the end of execution that describes the process and methodologies of data collection. Twitter's rate limits should be well understood BEFORE this package is run, as the Search API has hard restritions on how many Tweets can be retrieved per month, 15 min, and second depending on user's access level and the search type. In general, using default parameters in this package and not re-searching over the same date range will not cause the user to exceed these limits. You must have a Twitter Search API v2 bearer token to use this software.   
**To Install:**    
Enter into a command line terminal   
> pip install twitsent  
> 
**To Execute:**    
Also in the terminal, type  
> python -m twitsent  
> 
**OR**    
> python3 -m twitsent
> 

## Authors

- [Mitchell Hoikka](https://www.github.com/mhoikka)

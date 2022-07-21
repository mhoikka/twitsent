
# Twitter Sentiment Tracker
# Summer 2022 ACO 499

Tracks Twitter sentiment over time using Tweets that contain certain keywords and meet certain conditions. The data retrieved from Twitter can then be stored for later use, and an HTML file will open at the end of execution that describes the process and methodologies of data collection. Twitter's rate limits should be well understood BEFORE this package is run, as the Search API has hard restritions on how many Tweets can be retrieved per month, 15 min, and second depending on access level and search type. In general, using default parameters in this package and not re-searching the same day will not cause the user to exceed these limits. The user must have a Twitter Search API v2 bearer token to use this software.   
To Install:  
Open a command line terminal and type  
pip install twitsent  
Then to run program, type   
python -m twitsent  
OR    
python3 -m twitsent, if applicable

## Authors

- [Mitchell Hoikka](https://www.github.com/mhoikka)

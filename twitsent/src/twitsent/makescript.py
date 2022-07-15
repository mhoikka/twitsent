# import module
import codecs
import webbrowser
import os

def make_page():

    #directory of python script as variable      
    #get path to parent directory of this file
    rel_path = os.path.dirname(os.path.realpath(__file__))
    
    # to open/create a new html file in the write mode
    f = open(os.path.join(rel_path, 'Results-Page-TweetSA.html'), 'w')
    
    #construct the full path to store collected tweet data
    filename = "sentiment_comparisongraph.png"
    mypath = os.path.join(rel_path, filename)

    # the html code which will go in the file Results-Page-TweetSA.html
    html_template = f"""

    <html lang="en-US">

    <head>
    <title>Tweet Sentiment Analysis Student Research</title>
    <basefont size=4>
    </head>

    <body bgcolor=FFFFFF>

    <h1 align=center>Twitter Sentiment Analysis With NLTK's Vader</h1>
    <h2 align=center>(ACO 499) 2022 Summer Session B</h2>

    <h3 align=center>Mitchell Hoikka</h3>

    <p align=left>The purpose of this project is to detect and compare trends in sentiment data extracted from Tweets that contain certain keywords. Using a Twitter developer account, users can run historical
    searches. Those searches will return Tweets that match certain specifications (such as containing keywords, and language), then plot the sentiment score data of those tweets against the scores of
    random Tweets in a matching time period. The sentiment score is determined using NLTK's Vader software, and matches the compound score value. The Tweet text is then stored in local files, and the
     data can be used again or appended by running the software again over a different time frame with matching user-defined parameters.</p>

    <img src={mypath} alt="Graph comparing baseline sentiment to keyword sentiment scores">
    <hr>
    <p align=left>How to read the graph:<br>
    As Y values(sentiment score) approach 1, the sentiment in tweets containing the keywords becomes more positive. There can be multiple causes of this, and it should <b>not</b> be assumed that 
    increased positive sentiment related to a keyword implies positive emotions about that keyword. For instance, if the keyword list is (covid, coronavirus) and the sentiment score increases over a period
    of a week, people may be expressing that they feek positively about Covid-19- or perhaps that a lockdown was just lifted, or a vaccine was found. In other words, sentiment related to specific set of keywords
    may be incidental to those keywords rather than directly related to them. More specific keyword lists can reduce this effect, but it cannot be entirely removed.</p>

    <p align=left>A sentiment score is calculated as the average of scores collected in a specified interval. Each of the initial scores are the compound sentiment score calculated by NLTK'S
    Vader software for a specific tweet's cleaned(1) text. By comparing a baseline set of averaged scores over a certain time frame to the scores collected for the desired keywords in the same span, it is possible to determine if tweets containing those keywords
    differ from the baseline sentiment, and if there are any trends in the sentiment scores over time. The baseline scores are currently calculated by searching Twitter's APIV2 for the 25 most common tweeted english words(2)(3). Here we assume
    that in general, the sentiment of the most common words correlates with the most common sentiments. </p>

    <hr>
    <p align=left>Configuration Specific Details<br>
    The Twitter Search API V2 allows users with elevated access to search 2 million Tweets each month, and users with academic access to search 10 million tweets each month. Users with elevated access
    are limited to 450 requests per 15 minute interval using Recent Search(Up to one week in the past). Users with Academic access can use full archive search, which is limited to 300 requests per 15 minutes and 1 request per second.
    Each response to a request can contain up to 100 tweets.
    This translates to a maximum of roughly 2500 Tweets per hour when Tweets collection is consistent, and up to 45,000 Tweets collected per hour for an elevated access user. 
    For academic access collection, recent search and full archive search can sustain a rate of 10,000 Tweets per hour for the entire month interval. Recent search's hourly maximum is the same as with elevated access; however full archive search can only retrieve 30,000 
    Tweets per hour maximum. 
    Keep in mind that this application uses double the number of requests that would be expected, as an equal number of baseline tweets are collected when keyword tweets are requested. Thus 
    elevated access allows the user to collect 1250 keyword Tweets per hour, and academic access extends that limit to 5000 Tweets.
    When choosing an interval length for Tweet collection, ensure that it divides the duration of collection evenly(both are represented in minutes). Otherwise, there will be an unevenly sized time interval in the 
    dataset that will likely not have the desired quantity of Tweets. This helps prevent outliers from altering the sentiment graph.<p>
    <hr>
    <ol>
            <li> Punctutation, emojis, symbols, numbers, email addresses, websites, and languages other than english were removed from the text. The case was normalized to lowercase.
            <li> As determined by Oxford University Press
            <li> Only full words were used and website names were omitted

    </ol>

    <hr>



    <h2>Unordered list</h2>
    <ul>
      <li>First element
      <li>Second element
      <li>Third element
    </ul>

    <hr>

    <h2>Nested Lists!</h2>
    <ul>
      <li>Things to to today:
        <ol>
          <li>Walk the dog
          <li>Feed the cat
          <li>Mow the lawn
        </ol>
      <li>Things to do tomorrow:
        <ol>
          <li>Lunch with mom
          <li>Feed the hamster
          <li>Clean kitchen
        </ol>
    </ul>

    <p>And finally, how about some <a href=http://www.yahoo.com/>Links?</a></p>

    <p>Or let's just link to <a href=../../index.html>another page on this server</a></p>

    <p>Remember, you can view the HTMl code from this or any other page by using the "View Page Source" command of your browser.</p>

    </body>

    </html>

    """

    # writing the code into the file
    f.write(html_template)

    # close the file
    f.close()

    # viewing html files
    # below code creates a
    # codecs.StreamReaderWriter object
    file = codecs.open(os.path.join(rel_path, 'Results-Page-TweetSA.html'), 'r', "utf-8")

    # using .read method to view the html
    # code from our object
    print(file.read())

    # open html file
    webbrowser.open(os.path.join(rel_path, 'Results-Page-TweetSA.html'))

import tkinter as tk
from tkcalendar import *
from tkinter import ttk
import datetime as dt
import math

class TwitterAPIArgumentError(Exception):
    def __init__(self, message):
        super().__init__(message)
        
class Cal_Impl:
    """
    Contains methods to use and access  date-selection tkinter calendar with
    start and end date options and comboboxes to select other values

    Parameters
    --------
    enabled : boolean
        Whether non-date parameter selection is enabled when the date selection
        method is run
        
    Attributes
    --------
    ws : tkinter.Tk
        Tk object
    cal_label_frame : tkinter.Frame
    fzero : tkinter.Frame
        Outer frame
    fone : tkinter.Frame
        Inner frame for start date calendar
    ftwo : tkinter.Frame
        Inner frame for end date calendar
    start_cal_label : tkinter.Label
        Label for start date calendar
    end_cal_label : tkinter.Label
        Label for end date calendar
    start_cal : tkcalendar.Calendar
        Calendar for selecting starting date
    end_cal : tkcalendar.Calendar
        Calendar for selecting ending date
    msg : tkinter.Label
        Label that asks user how long the time intervals should be
    msg2 : tkinter.Label
        Label that asks user how many tweets should be collected per time interval
    msg_display : tkinter.Label
        Label for displaying selected parameters after calendar is used
    interval_bxstr : tkinter.StringVar
        Stores default value for interval length combobox
    max_bxstr : tkinter.StringVar
        Stores default value for number of tweets collected per interval
    interval_bx : tkinter.ComboBox
        Allows user to select time interval length in minutes
    max_bx : tkinter.ComboBox
        Allows user to select the maximum number of tweets collected per interval
    end_dt : dt.datetime
        The end date selected using the calendar
    _totaltime : int
        The number of minutes that the tweet search will retrieve data from
    _datestr2 : str
        The end date of data collection selected with the calendar
    _interval_len : int
        length of time interval in minutes
    _datestr : str
        The start date of data collection selected with the calendar
    _json_max : int
        maximum number of tweets collected per time interval
    _has_values : boolean
        Whether the user has submitted their selections to the calendar
        
    Methods
    --------
    interval_len()
        getter method
    totaltime()
        getter method
    datestr()
        getter method
    datestr2()
        getter method
    json_max()
        getter method
    has_values()
        returns a boolean that corresponds to whether the user has selected a
        date from the calendar yet
    run_cal()
        Instantiates the calendar
    on_quit()
        Terminates the calendar on unexpected exit from tkinter window
    display_msg()
        Extracts values from user input from the calendar and informs user of
        their selections, then sets _has_values to True.
        Called when user submits their choices on the calendar.
        
    Exceptions:
    --------
    TwitterAPIArgumentError
        Raised when illegal arguments are selected for Twitter Search API v2
    """
    
    def __init__(self, enabled):
        #set up tkinter objects for initial display
        self.ws = tk.Tk()
        
        cal_label_frame = tk.Frame(self.ws)
        fzero = tk.Frame(self.ws)
        fone = tk.Frame(fzero)
        ftwo = tk.Frame(fzero)
        
        self.start_cal_label = tk.Label(
            cal_label_frame, 
            text="Select Start Date For Tweet Collection",
            font=("Times", 12),
            bg="#cae7e8"
            )
        self.end_cal_label = tk.Label(
            cal_label_frame, 
            text="Select End Date For Tweet Collection",
            font=("Times", 12),
            bg="#cae7e8"
            )
            
        fone.pack(side=tk.LEFT, padx=10, pady=10)
        ftwo.pack(side=tk.RIGHT, padx=10, pady=10)
        
        self.start_cal_label.pack(side=tk.LEFT, padx=10, pady=(2,5))
        self.end_cal_label.pack(side=tk.RIGHT, padx=10, pady=(2,5))
        
        cal_label_frame.pack(side=tk.TOP)
        cal_label_frame.config(bg="#cae7e8")
        
        fzero.pack(side=tk.TOP)
        fzero.config(bg="#cae7e8")
        
        #calculate maximum and minimum days that can be queried on Twitter Search API
        delta_day = dt.timedelta(days = 1)
        tw_start_date = dt.date(2006,3,21)
        
        self.start_cal = Calendar(
            fone, 
            selectmode="day", 
            mindate = tw_start_date,
            maxdate = dt.datetime.now() - delta_day,
            side=tk.LEFT
            )
        
        self.end_cal = Calendar(
            ftwo, 
            selectmode="day", 
            mindate = tw_start_date,
            maxdate = dt.datetime.now(),
            side=tk.RIGHT
            )
            
        self.msg = tk.Label(
            self.ws, 
            text="How long should data collection intervals be?",
            font=("Times", 12),
            bg="#cae7e8"
            )
        self.msg2 = tk.Label(
            self.ws, 
            text="How many tweets should be collected per interval?",
            font=("Times", 12),
            bg="#cae7e8"
            )
        self.msg_display = tk.Label(
            self.ws,
            text="",
            bg="#cae7e8"
        )
        
        #initialize combobox for interval length variable selection
        self.interval_bxstr = tk.StringVar(value = 240)
        self.interval_bx = ttk.Combobox(self.ws, textvariable=self.interval_bxstr)
        self.interval_bx['values'] = (60,240,1440)
        self.interval_bx.config(width = 15)
        
        #if default data collection is selected
        if not enabled:
            self.interval_bx.config(state=tk.DISABLED)
            
        #initialize combobox for interval length variable selection
        self.max_bxstr = tk.StringVar(value = 100)
        self.max_bx = ttk.Combobox(self.ws, textvariable=self.max_bxstr)
        self.max_bx['values'] = (10,50,100,500,1000)
        self.max_bx.config(width = 15)
        
        #if default data collection is selected
        if not enabled:
            self.max_bx.config(state=tk.DISABLED)
            
        #declare and initialize variables used to send data outside of the class
        self.end_dt = dt.datetime.now(dt.timezone.utc)
        self._totaltime = 0
        self._datestr2 = ""
        self._interval_len = 0
        self._datestr = ""
        self._json_max = 0
        self._has_values = False
        
    def on_quit(self):
        """
        Shuts down tkcalendar when the window containing it is closed unexpectedly

        Parameters
        --------

        Returns
        --------
        None

        Raises
        --------
        
        
        """
        print("Calendar was terminated by exiting the window")
        self.ws.destroy()
        
    def display_msg(self):
        """
        Displays a message with selected parameters after user submits their
        choices to the calendar, then quits out of the tkinter window.

        Parameters
        --------

        Returns
        --------
        None

        Raises
        --------
        TwitterAPIArgumentError
            if illegal arguments are selected for Twitter Search API v2
        """
        
        #retrieve selected start and end date from calendar  
        self._datestr = self.start_cal.get_date()
        
        self._datestr2 = self.end_cal.get_date()

        date_r = self._datestr.split("/")
        date2_r = self._datestr2.split("/")
        
        #adding the 2000 is bad practice, but this code will not exist in the year 3000 and twitter did not exist in 1999
        date = dt.date(int(date_r[2])+2000, int(date_r[0]), int(date_r[1]))
        date2 = dt.date(int(date2_r[2])+2000, int(date2_r[0]), int(date2_r[1]))
        
        #retrieve timezone-aware time at exactly midnight UTC
        ti = dt.time(tzinfo = dt.timezone.utc)
        
        self.start_dt = dt.datetime.combine(date,ti)
        self.end_dt = dt.datetime.combine(date2,ti)
        
        #retrieve use selections from comboboxes
        self._interval_len = self.interval_bx.get()
        self._json_max = self.max_bx.get()
        
        self._totaltime = (self.end_dt-self.start_dt)/dt.timedelta(minutes = 1)
        
        t = f"Your query is for tweets created between {self._datestr} and {self._datestr2} with data collection intervals of length {self._interval_len} minutes."
        print(t)
        
        #check for illegal arguments 
        if float(self._interval_len) < 1:
            raise TwitterAPIArgumentError(f"Invalid time interval ({self._interval_len}) received")
        pluralizer = "s" if float(self._interval_len) > 1 else ""
        if float(self._json_max) < 1:
            raise TwitterAPIArgumentError(f"Invalid rate of tweets ({self._json_max}) per ({self._interval_len}) minute{pluralizer} requested. At least one tweet must be requested per time interval.") 
        
        self._has_values = True
        #once user selects search parameters, UI is no longer necesssary
        self.ws.quit()
    
    #getter methods for user input
    @property   
    def interval_len(self):
        """
        getter method for _interval_len

        Parameters
        --------

        Returns
        --------
        _interval_len : int
            an int representing the length of the intervals that tweets will be
            collected from

        Raises
        --------

        """
        
        return self._interval_len
    @property
    def totaltime(self):
        """
        getter method for _totaltime

        Parameters
        --------

        Returns
        --------
        _totaltime : int
            an int representing the range of the timeframe that tweets will
            be collected from in minutes

        Raises
        --------

        """
        
        return self._totaltime
    @property
    def datestr(self):
        """
        getter method for _datestr

        Parameters
        --------

        Returns
        --------
        _datestr : str
            a string representing the start date selected from the calendar

        Raises
        --------

        """
        
        return self._datestr
    @property
    def datestr2(self):
        """
        getter method for _datestr2

        Parameters
        --------

        Returns
        --------
        _datestr2 : str
            a string representing the end date selected from the calendar

        Raises
        --------

        """
        
        return self._datestr2
    @property
    def json_max(self):
        """
        getter method for _json_max

        Parameters
        --------

        Returns
        --------
        _json_max : int
            maximum number of tweets retrieved per time interval

        Raises
        --------

        """
        
        return self._json_max
    @property
    def has_values(self):
        """
        getter method for _has_values

        Parameters
        --------

        Returns
        --------
        _has_values : boolean
            if calendar values were selected

        Raises
        --------

        """
        
        return self._has_values
        
    def run_cal(self):
        """
        Creates a formatted tkinter window and runs mainloop on it

        Parameters
        --------

        Returns
        --------
        None

        Raises
        --------

        """
        
        self.ws.title("Set Date Range for Data Collection")
        self.ws.geometry("600x430")
        self.ws.config(bg="#cae7e8")#819394 #cae7e8 borderwidth
        self.ws.config(borderwidth=15)
        
        self.start_cal.pack()
        self.end_cal.pack()

        actionBtn = tk.Button(
            self.ws,
            text="Run Query",
            command=self.display_msg
        )
        
        self.interval_bx.pack(side=tk.BOTTOM, expand=False, pady=2)
        self.msg.pack(side=tk.BOTTOM, pady=2)
        
        self.max_bx.pack(side=tk.BOTTOM, expand=False, pady=2)
        self.msg2.pack(side=tk.BOTTOM, pady=2)
        actionBtn.pack(side=tk.BOTTOM, pady=2)
        
        self.msg_display.pack(side=tk.BOTTOM, pady=3)
        
        self.ws.protocol('WM_DELETE_WINDOW', self.on_quit)
        self.ws.mainloop()
        
class Cal_End:
    """
    Contains methods to use and access  date-selection tkinter calendar with
    end date options and comboboxes to select other values

    Parameters
    --------
    enabled : boolean
        Whether non-date parameter selection is enabled when the date selection
        method is run
        
    Attributes
    --------
    ws : tkinter.Tk
        Tk object
    end_cal_label : tkinter.Label
        Label for end date calendar
    end_cal : tkcalendar.Calendar
        Calendar for selecting ending date
    msg : tkinter.Label
        Label that asks user how long the time intervals should be
    msg2 : tkinter.Label
        Label that asks user how many tweets should be collected per time interval
    msg_display : tkinter.Label
        Label for displaying selected parameters after calendar is used
    interval_bxstr : tkinter.StringVar
        Stores default value for interval length combobox
    max_bxstr : tkinter.StringVar
        Stores default value for number of tweets collected per interval
    interval_bx : tkinter.ComboBox
        Allows user to select time interval length in minutes
    max_bx : tkinter.ComboBox
        Allows user to select the maximum number of tweets collected per interval
    end_dt : dt.datetime
        The end date selected using the calendar
    _totaltime : int
        The number of minutes that the tweet search will retrieve data from
    _datestr2 : str
        The end date of data collection selected with the calendar
    _interval_len : int
        length of time interval in minutes
    _json_max : int
        maximum number of tweets collected per time interval
    _has_values : boolean
        Whether the user has submitted their selections to the calendar
        
    Methods
    --------
    interval_len()
        getter method
    datestr2()
        getter method
    json_max()
        getter method
    has_values()
        returns a boolean that corresponds to whether the user has selected a
        date from the calendar yet
    run_cal()
        Instantiates the calendar
    on_quit()
        Terminates the calendar on unexpected exit from tkinter window
    display_msg()
        Extracts values from user input from the calendar and informs user of
        their selections, then sets _has_values to True.
        Called when user submits their choices on the calendar.
        
    Exceptions:
    --------
    TwitterAPIArgumentError
        Illegal arguments are selected for Twitter Search API v2
    """
    
    def __init__(self, enabled):
        #set up tkinter objects for initial display
        self.ws = tk.Tk()
        
        #calculate maximum and minimum days that can be queried on Twitter Search API
        delta_day = dt.timedelta(days = 1)
        tw_start_date = dt.date(2006,3,21)

        self.end_cal = Calendar(
            self.ws, 
            selectmode="day", 
            mindate = tw_start_date,
            maxdate = dt.datetime.now()
            )
        self.msg = tk.Label(
            self.ws, 
            text="How long should data collection intervals be?",
            font=("Times", 12),
            bg="#cae7e8"
            )
        self.msg2 = tk.Label(
            self.ws, 
            text="How many tweets should be collected per interval?",
            font=("Times", 12),
            bg="#cae7e8"
            )
        self.msg_display = tk.Label(
            self.ws,
            text="",
            bg="#cae7e8"
        )
        
        #initialize combobox for interval length variable selection
        self.interval_bxstr = tk.StringVar(value = 240)
        self.interval_bx = ttk.Combobox(self.ws, textvariable=self.interval_bxstr)
        self.interval_bx['values'] = (60,240,1440)
        self.interval_bx.config(width = 15)
        
        #if default data collection is selected, parameter selection is unnecessary
        if not enabled:
            self.interval_bx.config(state=tk.DISABLED)
            
        #initialize combobox for interval length variable selection
        self.max_bxstr = tk.StringVar(value = 100)
        self.max_bx = ttk.Combobox(self.ws, textvariable=self.max_bxstr)
        self.max_bx['values'] = (10,50,100,500,1000)
        self.max_bx.config(width = 15)
        
        #if default data collection is selected, parameter selection is unnecessary
        if not enabled:
            self.max_bx.config(state=tk.DISABLED)
            
        #declare and initialize variables used to send data outside of the class
        self.end_dt = dt.datetime.now(dt.timezone.utc)
        self._datestr2 = ""
        self._interval_len = 0
        self._json_max = 0
        self._has_values = False
        
    def on_quit(self):
        """
        Shuts down tkcalendar when the window containing it is closed unexpectedly

        Parameters
        --------

        Returns
        --------
        None

        Raises
        --------
        
        
        """
        
        print("Calendar was terminated by exiting the window")
        self.ws.destroy()
        
    def display_msg(self):
        """
        Displays a message with selected parameters after user submits their
        choices to the calendar, then quits out of the tkinter window.

        Parameters
        --------

        Returns
        --------
        None

        Raises
        --------
        TwitterAPIArgumentError
            if illegal arguments are selected for Twitter Search API v2
        """
        
        #retrieve selected end date from calendar         
        self._datestr2 = self.end_cal.get_date()

        date2_r = self._datestr2.split("/")
        
        #adding the 2000 is bad practice, but this code will not exist in the year 3000 and twitter did not exist in 1999
        date2 = dt.date(int(date2_r[2])+2000, int(date2_r[0]), int(date2_r[1]))
        
        #retrieve timezone-aware time at exactly midnight UTC
        ti = dt.time(tzinfo = dt.timezone.utc)
        
        self.end_dt = dt.datetime.combine(date2,ti)
        
        #retrieve use selections from comboboxes
        self._interval_len = self.interval_bx.get()
        self._json_max = self.max_bx.get()

        
        t = f"Your query is for tweets created before {self._datestr2} with data collection intervals of length {self._interval_len} minutes."
        print(t)
 
        #check for illegal arguments 
        if float(self._interval_len) < 1:
            raise TwitterAPIArgumentError(f"Invalid time interval ({self._interval_len}) received")
        pluralizer = "s" if float(self._interval_len) > 1 else ""
        if float(self._json_max) < 1:
            raise TwitterAPIArgumentError(f"Invalid rate of tweets ({self._json_max}) per ({self._interval_len}) minute{pluralizer} requested. At least one tweet must be requested per time interval.")  

        self._has_values = True
        
        #once user selects search parameters, UI is no longer necesssary
        self.ws.quit()
    
    #getter methods for user input
    @property   
    def interval_len(self):
        """
        getter method for _interval_len

        Parameters
        --------

        Returns
        --------
        _interval_len : int
            an int representing the length of the intervals that tweets will be
            collected from

        Raises
        --------

        """
        
        return self._interval_len
    @property
    def datestr2(self):
        """
        getter method for _datestr2

        Parameters
        --------

        Returns
        --------
        _datestr2 : str
            a string representing the end date selected from the calendar

        Raises
        --------

        """
        
        return self._datestr2
    @property
    def json_max(self):
        """
        getter method for _json_max

        Parameters
        --------

        Returns
        --------
        _json_max : int
            maximum number of tweets retrieved per time interval

        Raises
        --------

        """
        
        return self._json_max
    @property
    def has_values(self):
        """
        getter method for _has_values

        Parameters
        --------

        Returns
        --------
        _has_values : boolean
            if calendar values were selected

        Raises
        --------

        """
        
        return self._has_values
        
    def run_cal(self):
        """
        Creates a formatted tkinter window and runs mainloop on it

        Parameters
        --------

        Returns
        --------
        None

        Raises
        --------

        """
        
        self.ws.title("Set Date Range for Data Collection")
        self.ws.geometry("600x430")
        self.ws.config(bg="#cae7e8")
        self.ws.config(borderwidth=15)
        
        self.end_cal_label = tk.Label(
            self.ws, 
            text="Select End Date For Tweet Collection",
            font=("Times", 12),
            bg="#cae7e8"
            )
            
        self.end_cal_label.pack(side = tk.TOP, pady = 5)
        self.end_cal.pack(side = tk.TOP)

        actionBtn = tk.Button(
            self.ws,
            text="Run Query",
            padx=10,
            pady=10,
            command=self.display_msg
        )
        self.interval_bx.pack(side=tk.BOTTOM, expand=False, pady=2)
        self.msg.pack(side=tk.BOTTOM, pady=2)
        
        self.max_bx.pack(side=tk.BOTTOM, expand=False, pady=2)
        self.msg2.pack(side=tk.BOTTOM, pady=2)
        actionBtn.pack(side=tk.BOTTOM, pady=2)
        
        self.msg_display.pack(side=tk.BOTTOM, pady=3)
        
        self.ws.protocol('WM_DELETE_WINDOW', self.on_quit)
        self.ws.mainloop()

from tkinter import *
from time import *
from clockface import ClockFace
import json



################
# MoneyTimer: main interface, initiates all other dialogs;
# derivative of tkinter.Frame
#   Class members:
#     SETTINGS_FILE   HISTORY_FILE    DEFAULT_HOURLY_RATE
#     PERCENT_EARN    BAR_WIDTH       BAR_HEIGHT      
#     BAR_FILL_COLOR  BAR_LINE_COLOR  BAR_BG_COLOR
#     BAR_TEXT_COLOR  BAR_TEXT_FONT   AFTER_TIME
#     AFTER_TIME_SEC  DAYS            DEFAULT_SETTINGS
#     HISTORY_FORMAT
#   Subclasses:
#     SetupWindow     SettingsWindow  HistoryWindow
#   Members:
#     menuBar     : Menu for master
#     upperFrame  : Frame containing timeLabel and pauseButton
#     timeLabel   : Label displaying time and earnings
#     pauseButton : Button for toggling pause of time update
#     secSoFar    : Stores time in seconds that have been clocked
#   Methods:
#     __init__           : initializes GUI elements, loads settings, creates SetupWindow
#     setup              : initializes a SetupWindow
#     complete_setup     : takes return of SetupWindow and begins updates
#     auto_pause         : helper fcn for auto lunch break events
#     auto_unpause       :   "                               "
#     toggle_pause       : toggles whether to track time or not
#     update             : main update, updates members and display elements
#     make_lunch_events  : creates lunch events if needed and deletes previous lunch events
#     on_settings_click  : opens SettingsWindow window allowing configuration
#     configure_settings : configures settings from SettingsWindow return
#     load_settings      : loads settings from file, filling in gaps with defaults
#     save_settings      : saves settings to file for use on next startup
#     on_history_click   : opens HistoryWindow window
#     load_history       : loads history from file, ignoring current day
#     save_history       : saves history to file for use on next startup
#     destroy            : modified to save settings and history
class MoneyTimer(Frame):

  # files
  SETTINGS_FILE = "money_timer_settings.json"
  HISTORY_FILE  = "money_timer_history.json"
  # constants
  DEFAULT_HOURLY_RATE = 21.5 # $/hr
  PERCENT_EARN = 0.71
  BAR_WIDTH = 150 # px
  BAR_HEIGHT = 20 # px
  BAR_FILL_COLOR = "#00CC00" # green
  BAR_LINE_COLOR = "#006600" # dark green
  BAR_BG_COLOR = "#DDDDDD"   # grey
  BAR_TEXT_COLOR = "#FFFFFF" # white
  BAR_TEXT_FONT = ("Arial", -BAR_HEIGHT * 3 // 5)
  AFTER_TIME = 500 # ms
  AFTER_TIME_SEC = AFTER_TIME / 1000 # s
  DAYS = ["Mon", "Tues", "Wed", "Thurs", "Fri", "Sat", "Sun"]

  CREDITS_TEXT = \
"""\
Icons from NounProject contributors:
Alexandr Cherkinsky
Arthur Shlain
Dalpat Prajapati
David Francisco
Mateo Zlatar\
"""

  # default configuration
  DEFAULT_SETTINGS = {"autoLunchEnabled"  : False,
                      "autoLunchStartTime": [12, 0],
                      "autoLunchStopTime" : [13, 0],
                      "hourlyRate"        : 21.50,
                      "Mon"  : 8.0,
                      "Tues" : 8.0,
                      "Wed"  : 8.0,
                      "Thurs": 8.0,
                      "Fri"  : 8.0,
                      "Sat"  : 0.0,
                      "Sun"  : 0.0}
  HISTORY_FORMAT = {"year": int,
                    "mon" : int,
                    "day" : int,
                    "wday": str,
                    "secSoFar": float,
                    "earnings": float,
                    "percent" : float}


  ################
  # SetupWindow: used for initialization of MoneyTimer object;
  # derivative of tkinter.Toplevel
  #   Members:
  #     infoLabel    : Label displaying input prompt
  #     inputVar     : StringVar tracking inputEntry's contents
  #     inputEntry   : Entry for input time
  #     okButton     : Button for confirming entry
  #     invalidLabel : displays error message if invalid input
  #     secSoFar     : calculated seconds between input time and current time
  #   Methods:
  #     __init__         : sets up GUI and member data
  #     check_input      : traced to inputVar, validates input and calculates secSoFar
  #     destroy          : modified with conditional; calls master.complete_setup
  class SetupWindow(Toplevel):
    
    ########
    # __init__: initializes GUI elements and data
    def __init__(self, root):
      # tkinter stuff
      Toplevel.__init__(self, root, width = MoneyTimer.BAR_WIDTH)
      self.title("Setup [Money Timer]")
      self.lift()

      self.frame = Frame(self)

      self.infoLabel = Label(self,
                             padx = 5,
                             pady = 5,
                             text = "Start time (hh:mm)\nLeave blank to use current time.")
      self.infoLabel.pack(side = "top")

      self.inputVar = StringVar(self)
      self.inputVar.trace("w", self.check_input)
      self.inputEntry = Entry(self.frame,
                              width = 5,
                              textvariable = self.inputVar)
      self.inputEntry.bind("<Return>", self.destroy)
      self.inputEntry.pack(side = "left")

      self.okButton = Button(self.frame,
                             text = "OK",
                             command = self.destroy)
      self.okButton.pack(side = "left")
      self.frame.pack(side = "top")

      # invalid entry label
      self.invalidLabel = Label(self,
                                text = "Invalid input.",
                                foreground = "#FF0000")

      self.secSoFar = 0
      self.inputEntry.focus_set()

    ########
    # check_input: validates user input; enables closing window if valid
    def check_input(self, *args):
      s = self.inputVar.get()
      self.secSoFar = 0 # reset to 0 to fix backspace stuff
      self.okButton.config(state = DISABLED)

      # clip at max
      if len(s) > 5:
        self.inputVar.set(s[:5])
        return

      # validate input
      try:
        if len(s) == 5 and s[2] == ':': # format hh:mm
          intHr = int(s[:2])
          intMin = int(s[3:])
        elif len(s) == 4 and s[1] == ':': # format h:mm
          intHr = int(s[:1])
          intMin = int(s[2:])
        elif len(s) != 0: #invalid input
          return
      except Exception: # invalid input
        return

      if len(s) > 0:
        if intHr < 0 or intHr > 24 or intMin < 0 or intMin > 60: # invalid input
          return

      # calculate time if valid time entered
      if len(s) != 0:
        currTime = localtime()
        self.secSoFar = (currTime.tm_hour - intHr) * 3600
        self.secSoFar += (currTime.tm_min - intMin) * 60
        self.secSoFar += currTime.tm_sec

        if self.secSoFar < 0: # invalid input
          self.secSoFar = 0
          return

      # enable exit button
      self.okButton.config(state = NORMAL)


    #######
    # destroy: only succeeds if valid input; modified to call master.complete_setup
    def destroy(self, *args):
      if self.okButton.cget("state") == NORMAL:
        self.master.complete_setup(self.secSoFar)
        super().destroy()
      else:
        self.invalidLabel.pack()
  # SetupWindow
  ################

  ################
  # SettingsWindow: allows for configuration of settings
  #   Members:
  #     autoLunchBreak : contains variables and GUI elements for automatic lunch break settings
  #     lowerFrame     : contains goals, rate, and confim/cancel GUI elements
  #     goals          : contains variables and GUI elements for daily goal settings
  #     hourlyRate     : contains variables and GUI elements for hourly rate setting
  #     confirmButton  : Button to commit setting changes; destroys window if entries valid
  #     cancel         : Button to cancel setting changes; destroys window
  #   Methods:
  #     __init__                : calls create_widgets, then loads current settings
  #     create_widgets          : creates all GUI elements
  #     load_settings           : loads current settings
  #     toggle_auto_lunch_break : toggles automatic lunch break setting
  #     clip_time_entries       : clips time entries to 5 chars
  #     clip_goal_entries       : clips daily goal entries to 4 chars
  #     clip_rate_entry         : clips rate entry to 6 chars
  #     on_confirm_click        : validates entries, calls master.configure, destroys window
  #     parse_time              : parses a string into hours and minutes if valid; else returns None
  class SettingsWindow(Toplevel):

    ########
    # __init__: initializes SettingsWindow instance
    def __init__(self, root):
      # tkinter stuff
      Toplevel.__init__(self, root, width = MoneyTimer.BAR_WIDTH)
      self.title("Settings [Money Timer]")
      self.lift()

      self.create_widgets()
      self.load_settings()

    ########
    # create_widgets: set up all GUI elements
    def create_widgets(self):
      # auto lunch break checkbox
      self.autoLunchBreak = {}
      self.autoLunchBreak["checkboxFrame"] = Frame(self)
      self.autoLunchBreak["checkboxVar"]   = IntVar(self)
      self.autoLunchBreak["checkboxVar"].trace("w", self.toggle_auto_lunch_break)
      self.autoLunchBreak["checkbutton"]   = Checkbutton(self.autoLunchBreak["checkboxFrame"],
                                                         text = "Auto Lunch Break",
                                                         variable = self.autoLunchBreak["checkboxVar"])
      self.autoLunchBreak["checkbutton"].pack(side = "left")
      self.autoLunchBreak["checkboxFrame"].pack(side = "top")

      # auto lunch break times
      self.autoLunchBreak["timesFrame"] = Frame(self)
      self.autoLunchBreak["startTimeVar"]   = StringVar(self)
      self.autoLunchBreak["startTimeVar"].trace("w", self.clip_time_entries)
      self.autoLunchBreak["startTimeEntry"] = Entry(self.autoLunchBreak["timesFrame"],
                                                    width = 5,
                                                    state = DISABLED,
                                                    textvariable = self.autoLunchBreak["startTimeVar"])
      self.autoLunchBreak["startTimeEntry"].pack(side = "left")
      self.autoLunchBreak["timeSeparator"] = Label(self.autoLunchBreak["timesFrame"],
                                                   text = "to")
      self.autoLunchBreak["timeSeparator"].pack(side = "left")
      self.autoLunchBreak["stopTimeVar"]   = StringVar(self)
      self.autoLunchBreak["stopTimeVar"].trace("w", self.clip_time_entries)
      self.autoLunchBreak["stopTimeEntry"] = Entry(self.autoLunchBreak["timesFrame"],
                                                    width = 5,
                                                    state = DISABLED,
                                                    textvariable = self.autoLunchBreak["stopTimeVar"])
      self.autoLunchBreak["stopTimeEntry"].pack(side = "left")
      self.autoLunchBreak["invalidLabel"] = Label(self.autoLunchBreak["timesFrame"],
                                                  foreground = "#FF0000",
                                                  text = "Invalid input.")
      self.autoLunchBreak["timesFrame"].pack(side = "top")

      # lower frame
      self.lowerFrame = Frame(self)

      # goals window
      self.goals = {}
      self.goals["mainFrame"] = Frame(self.lowerFrame)
      self.goals["headingFrame"] = Frame(self.goals["mainFrame"])
      self.goals["headingLabel"] = Label(self.goals["headingFrame"],
                                         text = "Daily Goals:")
      self.goals["headingLabel"].pack(side = "left")
      self.goals["headingFrame"].pack(side = "top", fill = X)
      # set up each day
      for day in MoneyTimer.DAYS:
        self.goals[day] = {}
        self.goals[day]["frame"] = Frame(self.goals["mainFrame"], padx = 20)
        self.goals[day]["hrLabel"] = Label(self.goals[day]["frame"],
                                           text = "hrs")
        self.goals[day]["hrLabel"].pack(side = "right")
        self.goals[day]["var"]   = StringVar(self.goals[day]["frame"])
        self.goals[day]["var"].trace("w", self.clip_goal_entries)
        self.goals[day]["entry"] = Entry(self.goals[day]["frame"],
                                         width = 4,
                                         textvariable = self.goals[day]["var"])
        self.goals[day]["entry"].pack(side = "right")
        self.goals[day]["dayLabel"] = Label(self.goals[day]["frame"],
                                            text = day)
        self.goals[day]["dayLabel"].pack(side = "right")
        self.goals[day]["frame"].pack(fill = X, side = "top")
      self.goals["invalidLabel"] = Label(self.goals["mainFrame"],
                                         foreground = "#FF0000",
                                         text = "Invalid input.")

      self.goals["mainFrame"].pack(side = "left")

      self.lowerRightFrame = Frame(self.lowerFrame)

      self.hourlyRate = {}
      self.hourlyRate["headingFrame"] = Frame(self.lowerRightFrame)
      self.hourlyRate["headingLabel"] = Label(self.hourlyRate["headingFrame"],
                                              text = "Hourly Rate:")
      self.hourlyRate["headingLabel"].pack(side = "left")
      self.hourlyRate["headingFrame"].pack(fill = X, side = "top")
      self.hourlyRate["mainFrame"] = Frame(self.lowerRightFrame, padx = 20)
      self.hourlyRate["dollarLabel"] = Label(self.hourlyRate["mainFrame"],
                                             text = "$")
      self.hourlyRate["dollarLabel"].pack(side = "left")
      self.hourlyRate["var"] = StringVar(self.hourlyRate["mainFrame"])
      self.hourlyRate["var"].trace("w", self.clip_rate_entry)
      self.hourlyRate["entry"] = Entry(self.hourlyRate["mainFrame"],
                                       width = 6,
                                       textvariable = self.hourlyRate["var"])
      self.hourlyRate["entry"].pack(side = "left")
      self.hourlyRate["invalidLabel"] = Label(self.lowerRightFrame,
                                              foreground = "#FF0000",
                                              text = "Invalid input.")
      self.hourlyRate["mainFrame"].pack(side = "top")

      self.confirmCancelFrame = Frame(self.lowerRightFrame)
      self.confirmButton = Button(self.confirmCancelFrame,
                                  text = "Confirm",
                                  command = self.on_confirm_click)
      self.confirmButton.pack(side = "top", fill = X)
      self.cancelButton = Button(self.confirmCancelFrame,
                                 text = "Cancel",
                                 command = self.destroy)
      self.cancelButton.pack(side = "top", fill = X)
      self.confirmCancelFrame.pack(side = "top")

      self.lowerRightFrame.pack(fill = Y, side = "left")

      self.lowerFrame.pack(side = "top")

    ########
    # load_settings: loads current settings from parent MoneyTimer
    def load_settings(self):
      settings = self.master.settings
      if settings["autoLunchEnabled"]:
        self.autoLunchBreak["checkboxVar"].set(1)
      else:
        self.autoLunchBreak["checkboxVar"].set(0)
      time = settings["autoLunchStartTime"]
      minStr = str(time[1]) if time[1] >= 10 else "0" + str(time[1])
      self.autoLunchBreak["startTimeVar"].set("{}:{}".format(time[0], minStr))
      time = settings["autoLunchStopTime"]
      minStr = str(time[1]) if time[1] >= 10 else "0" + str(time[1])
      self.autoLunchBreak["stopTimeVar"].set("{}:{}".format(time[0], minStr))
      self.hourlyRate["var"].set(str(settings["hourlyRate"]))
      for day in MoneyTimer.DAYS:
        self.goals[day]["var"].set(str(settings[day]))

    ########
    # toggle_auto_lunch_break: toggles states of lunch break entries
    def toggle_auto_lunch_break(self, *args):
      if self.autoLunchBreak["checkboxVar"].get() == 1:
        self.autoLunchBreak["startTimeEntry"].config(state = NORMAL)
        self.autoLunchBreak["stopTimeEntry"].config(state = NORMAL)
      else:
        self.autoLunchBreak["startTimeEntry"].config(state = DISABLED)
        self.autoLunchBreak["stopTimeEntry"].config(state = DISABLED)

    ########
    # clip_time_entries: limits max input size of times entries
    def clip_time_entries(self, *args):
      s = self.autoLunchBreak["startTimeVar"].get()
      if len(s) > 5:
        self.autoLunchBreak["startTimeVar"].set(s[:5])
      s = self.autoLunchBreak["stopTimeVar"].get()
      if len(s) > 5:
        self.autoLunchBreak["stopTimeVar"].set(s[:5])

    ########
    # clip_goal_entries: limits max input size of daily goals entries
    def clip_goal_entries(self, *args):
      for day in MoneyTimer.DAYS:
        s = self.goals[day]["var"].get()
        if len(s) > 4:
          self.goals[day]["var"].set(s[:4])

    ########
    # clip_rate_entry: limits max input size of hourly rate entry
    def clip_rate_entry(self, *args):
      s = self.hourlyRate["var"].get()
      if len(s) > 6:
        self.hourlyRate["var"].set(s[:6])

    ########
    # on_confirm_click: validates entries and handles cleanup and updating of settings
    def on_confirm_click(self):
      inputsValid = True

      self.autoLunchBreak["invalidLabel"].pack_forget()
      self.hourlyRate["invalidLabel"].pack_forget()
      self.goals["invalidLabel"].pack_forget()
      ret = {}
      ret["autoLunchEnabled"]   = False if self.autoLunchBreak["checkboxVar"].get() == 0 else True
      
      if ret["autoLunchEnabled"]: # need to return start and stop times
        time = self.parse_time(self.autoLunchBreak["startTimeVar"].get())
        if time != None:
          ret["autoLunchStartTime"] = time
        else: # invalid
          self.autoLunchBreak["invalidLabel"].pack(side = "left")
          inputsValid = False
        time = self.parse_time(self.autoLunchBreak["stopTimeVar"].get())
        if time != None:
          ret["autoLunchStopTime"]  = time
        else: # invalid
          self.autoLunchBreak["invalidLabel"].pack(side = "left")
          inputsValid = False

        netTime = (ret["autoLunchStopTime"][0] - ret["autoLunchStartTime"][0]) * 60
        netTime += ret["autoLunchStopTime"][1] - ret["autoLunchStartTime"][1]
        if netTime <= 0:
          self.autoLunchBreak["invalidLabel"].pack(side = "left")
          inputsValid = False

      s = self.hourlyRate["var"].get()
      ret["hourlyRate"] = 0.0
      if len(s) != 0:
        try:
          ret["hourlyRate"] = 0.0 if s == "" else float(s)
        except Exception: # invalid
          self.hourlyRate["invalidLabel"].pack(side = "top")
          inputsValid = False

      for day in MoneyTimer.DAYS:
        ret[day] = 0.0
        s = self.goals[day]["var"].get()
        if len(s) != 0:
          try:
            ret[day] = float(s)
          except Exception:
            self.goals["invalidLabel"].pack(side = "top")
            inputsValid = False
            break

      if inputsValid:
        self.master.configure_settings(ret)
        self.destroy()

    ########
    # parse_time: parses a string into hours and minutes, if valid; else, returns None
    def parse_time(self, s):
      try:
        if len(s) == 5 and s[2] == ':': # format hh:mm
          intHr = int(s[:2])
          intMin = int(s[3:])
        elif len(s) == 4 and s[1] == ':': # format h:mm
          intHr = int(s[:1])
          intMin = int(s[2:])
        else: #invalid input
          return None
      except Exception:
        return None

      if intHr < 0 or intMin < 0 or intMin > 60:
        return None

      return [intHr, intMin]

    ########
    # destroy: augmented to modify bool in parent
    def destroy(self):
      self.master.settingsOpen = False
      super().destroy()
  # SettingsWindow
  ################

  ################
  # HistoryWindow: displays log of daily stats;
  # derivative of Toplevel
  #   Members:
  #   Methods:
  #     __init__ : creates display
  #     destroy  : updates bool of parent, then destroys
  class HistoryWindow(Toplevel):

    def __init__(self, root):
      Toplevel.__init__(self, root)
      self.title("History [Money Timer]")
      self.scrollbar = Scrollbar(self)
      self.scrollbar.pack(side = "right", fill = Y)
      self.text = Text(self,
                       width = 50,
                       yscrollcommand = self.scrollbar.set)
      self.text.pack(side = "right", fill = Y)
      self.scrollbar.config(command = self.text.yview)
      if len(self.master.history) > 0:
        for entry in self.master.history:
          monStr  = str(entry["mon"]) if entry["mon"] >= 10 else "0" + str(entry["mon"])
          dayStr  = str(entry["day"]) if entry["day"] >= 10 else "0" + str(entry["day"])
          wDayStr = entry["wday"] + " "*(5-len(entry["wday"])) if 5 - len(entry["wday"]) > 0 else entry["wday"]
          intHr   = int(entry["secSoFar"] // 3600)
          intMin  = int(entry["secSoFar"] % 3600 // 60)
          intSec  = int(entry["secSoFar"] % 60)
          strMin  = str(intMin) if intMin >= 10 else "0" + str(intMin)
          strSec  = str(intSec) if intSec >= 10 else "0" + str(intSec)
          earningsStr = "{:.2f}".format(entry["earnings"])
          earningsStr += " "*(7 - len(earningsStr)) if ((7 - len(earningsStr)) > 0) else earningsStr

          inputStr = "{}-{}-{} {}\t{}:{}:{}\t${}\t{:.1f}%\n".format(entry["year"],
                                                                        monStr,
                                                                        dayStr,
                                                                        wDayStr,
                                                                        intHr,
                                                                        strMin,
                                                                        strSec,
                                                                        earningsStr,
                                                                        entry["percent"])
          self.text.insert(END, inputStr)
      else:
        self.text.insert(END, "No history recorded.")

      self.text.config(state = DISABLED)

    def destroy(self):
      self.master.historyOpen = False
      super().destroy()


  ########
  # __init__: sets up MoneyTimer class, creates a SetupWindow to get start time
  def __init__(self, root):
    Frame.__init__(self, root)
    self.settings = self.load_settings()
    self.paused = False
    self.settingsOpen = False
    self.historyOpen  = False
    self.credits = None
    if self.settings["autoLunchEnabled"]:
      self.startLunchEvt, self.endLunchEvt = self.make_lunch_events()
    else:
      self.startLunchEvt = None
      self.endLunchEvt   = None

    # menubar
    self.menuBar = {}
    self.menuBar["frame"] = Frame(self)
    self.menuBar["settingsIcon"]   = PhotoImage(file = "settings.gif")
    self.menuBar["settingsButton"] = Button(self.menuBar["frame"],
                                            image    = self.menuBar["settingsIcon"],
                                            text     = "Settings",
                                            compound = LEFT,
                                            relief   = GROOVE,
                                            command  = self.on_settings_click)
    self.menuBar["settingsButton"].pack(side = "left", fill = Y)
    self.menuBar["historyIcon"]    = PhotoImage(file = "history.gif")
    self.menuBar["historyButton"]  = Button(self.menuBar["frame"],
                                            image    = self.menuBar["historyIcon"],
                                            text     = "History",
                                            compound = LEFT,
                                            relief   = GROOVE,
                                            command  = self.on_history_click)
    self.menuBar["historyButton"].pack(side = "right", fill = Y)
    self.menuBar["stopwatchIcon"] = PhotoImage(file = "stopwatch.gif")
    self.menuBar["stopwatchButton"] = Button(self.menuBar["frame"],
                                             image   = self.menuBar["stopwatchIcon"],
                                             relief  = GROOVE,
                                             command = self.on_credits_click)
    self.menuBar["stopwatchButton"].pack(side = "top", fill = BOTH, expand = 1)
    self.menuBar["frame"].pack(side="top", fill = X)

    # hotkeys
    self.bind("<Control-s>", self.on_settings_click)
    self.bind("<Control-S>", self.on_settings_click)
    self.bind("<Control-h>", self.on_history_click)
    self.bind("<Control-H>", self.on_history_click)
    self.focus_set()

    # time and pause button
    self.upperFrame = Frame(self)
    self.spacerLabel = Label(self.upperFrame, # too lazy to actually try and use pack efficiently
                             text = "      ")
    self.spacerLabel.pack(side = "left")
    self.timeLabel = Label(self.upperFrame,
                           text = "config in\nsetup window")
    self.timeLabel.pack(side = "left")
    self.spacerLabel2 = Label(self.upperFrame,
                              text = "      ")
    self.spacerLabel2.pack(side = "left")
    self.pauseButton = Button(self.upperFrame,
                              command = self.toggle_pause)
    self.pauseButtonVar           = StringVar(self.pauseButton,"Pause")
    self.pauseButton.pauseImage   = PhotoImage(file = "pause.gif")
    self.pauseButton.unpauseImage = PhotoImage(file = "unpause.gif")
    self.pauseButton.config(image = self.pauseButton.pauseImage,
                            textvariable = self.pauseButtonVar,
                            compound = LEFT)
    self.pauseButton.pack(side = "right")
    self.upperFrame.pack(side = "top", fill = X)

    # progress bar
    self.progressBar = Canvas(self,
                              width = MoneyTimer.BAR_WIDTH,
                              height = MoneyTimer.BAR_HEIGHT,
                              bg = MoneyTimer.BAR_BG_COLOR,
                              relief = SUNKEN,
                              bd = 2)
    self.progressBarRect = self.progressBar.create_rectangle(-5, -5, 0, MoneyTimer.BAR_HEIGHT + 5,
                                                             fill = MoneyTimer.BAR_FILL_COLOR,
                                                             outline = MoneyTimer.BAR_LINE_COLOR,
                                                             width = 1.5)
    self.progressBarPct = self.progressBar.create_text(-3, MoneyTimer.BAR_HEIGHT / 2 + 3,
                                                       anchor = E,
                                                       fill = MoneyTimer.BAR_TEXT_COLOR,
                                                       font = MoneyTimer.BAR_TEXT_FONT,
                                                       text = "0%")
    self.progressBar.pack()

    self.secSoFar = 0 # sec

    self.setup()

  ########
  # setup: creates a SetupWindow to input start time
  def setup(self):
    self.setupWindow = MoneyTimer.SetupWindow(self)

  ########
  # complete_setup: completes setup and begins updates
  def complete_setup(self, secSoFar):
    self.secSoFar = secSoFar
    currTime = localtime()
    self.startDay = MoneyTimer.DAYS[currTime.tm_wday]
    self.startDate = [currTime.tm_year, currTime.tm_mon, currTime.tm_mday]
    self.todaysGoal = self.settings[self.startDay]

    # has to be done after startDay and startDate are initialized
    self.history = self.load_history()
    for entry in self.history:
      entry["percent"] = (entry["percent"] * 100 // 1) / 100

    self.update()
    del self.setupWindow

  ########
  # auto_pause: wrapper that calls toggle_pause if not paused because I'm a lazy bum
  def auto_pause(self):
    if not self.paused:
      self.toggle_pause()

  ########
  # auto_unpause: opposite of auto_pause
  def auto_unpause(self):
    if self.paused:
      self.toggle_pause()

  ########
  # toggle_pause: toggles whether time is tracked or not
  def toggle_pause(self):
    if self.paused:
      self.pauseButton.config(image = self.pauseButton.pauseImage)
      self.pauseButtonVar.set("Pause")
      self.paused = False
      self.update()
    else:
      try:
        self.after_cancel(self.nextUpdate)
        self.pauseButton.config(image = self.pauseButton.unpauseImage)
        self.pauseButtonVar.set("Unpause")
        self.paused = True
      except Exception:
        pass

  ########
  # update: updates secSoFar and GUI elements
  def update(self):
    self.secSoFar += MoneyTimer.AFTER_TIME_SEC

    # calculate hour, min, sec, and earnings; put times in strings
    displayHr  = int(self.secSoFar // 3600)
    displayMin = int(self.secSoFar %  3600 // 60)
    displayMin = str(displayMin) if displayMin >= 10 else "0" + str(displayMin)
    displaySec = int(self.secSoFar %  60)
    displaySec = str(displaySec) if displaySec >= 10 else "0" + str(displaySec)
    earnings = self.secSoFar / 3600 * self.settings["hourlyRate"] * MoneyTimer.PERCENT_EARN
    
    # update text
    labelStr = "{}:{}:{}\n${:.2f}".format(displayHr, displayMin, displaySec, earnings)
    self.timeLabel.config(text = labelStr)

    # update menubar
    if self.todaysGoal != 0:
      pct = self.secSoFar / (self.todaysGoal * 3600)
    else:
      pct = 1.0
    if pct <= 1:
      self.progressBar.coords(self.progressBarRect,
                              -5, -5, pct * MoneyTimer.BAR_WIDTH + 3, MoneyTimer.BAR_HEIGHT + 5)
      self.progressBar.coords(self.progressBarPct,
                              pct * MoneyTimer.BAR_WIDTH, MoneyTimer.BAR_HEIGHT / 2 + 3)
    else:
      self.progressBar.coords(self.progressBarRect,
                              -5, -5, MoneyTimer.BAR_WIDTH + 3, MoneyTimer.BAR_HEIGHT + 5)
      self.progressBar.coords(self.progressBarPct,
                              MoneyTimer.BAR_WIDTH, MoneyTimer.BAR_HEIGHT / 2 + 3)
    self.progressBar.itemconfig(self.progressBarPct,
                                text = "{:.0f}%".format(pct * 100))

    self.nextUpdate = self.after(MoneyTimer.AFTER_TIME, self.update)

  ########
  # make_lunch_events: sets up auto pause/unpause events if needed
  def make_lunch_events(self):
    currTime = localtime()
    ctSec = currTime.tm_hour * 3600 + currTime.tm_min * 60 + currTime.tm_sec
    breakStart = self.settings["autoLunchStartTime"][0] * 3600 + self.settings["autoLunchStartTime"][1] * 60
    breakEnd   = self.settings["autoLunchStopTime"][0]  * 3600 + self.settings["autoLunchStopTime"][1] * 60

    # make events if they haven't occured yet today
    if breakStart - ctSec > 0:
      startAfterEvt = self.after(1000 * (breakStart - ctSec), self.auto_pause)
    else:
      startAfterEvt = None
    if breakEnd - ctSec > 0:
      endAfterEvt   = self.after(1000 * (breakEnd - ctSec), self.auto_unpause)
    else:
      endAfterEvt = None

    return startAfterEvt, endAfterEvt

  ########
  # on_settings_click: opens an SettingsWindow for configuration
  def on_settings_click(self, *args):
    if not self.settingsOpen:
      self.settingsWindow = MoneyTimer.SettingsWindow(self)
      self.settingsOpen = True
    else:
      self.settingsWindow.lift()

  ########
  # configure: called from SettingsWindow; commits configuration
  def configure_settings(self, config):
    for key in config.keys():
      self.settings[key] = config[key]
    self.todaysGoal = self.settings[self.startDay]
    if self.settings["autoLunchEnabled"]:
      if self.startLunchEvt != None:
        self.after_cancel(self.startLunchEvt)
      if self.endLunchEvt != None:
        self.after_cancel(self.endLunchEvt)
      self.startLunchEvt, self.endLunchEvt = self.make_lunch_events()
    del self.settingsWindow

  ########
  # load_settings: gets settings from file, else to default
  def load_settings(self):
    try:
      f = open(MoneyTimer.SETTINGS_FILE, "r")
      s = f.read()
      f.close()
      temp = json.loads(s)
      for key in MoneyTimer.DEFAULT_SETTINGS.keys():
        if key not in temp.keys():
          temp[key] = MoneyTimer.DEFAULT_SETTINGS[key]
        elif type(temp[key]) != type(MoneyTimer.DEFAULT_SETTINGS[key]):
          temp[key] = MoneyTimer.DEFAULT_SETTINGS[key]
      return temp
    except Exception:
      return MoneyTimer.DEFAULT_SETTINGS

  ########
  # save_settings: saves settings to file
  def save_settings(self):
    s = json.dumps(self.settings)

    f = open(MoneyTimer.SETTINGS_FILE, "w")
    f.write(s)
    f.close()

  ########
  # on_history_click: opens a HistoryWindow to display past recorded time/earnings
  def on_history_click(self, *args):
    if not self.historyOpen:
      self.historyWindow = MoneyTimer.HistoryWindow(self)
      self.historyOpen = True
    else:
      self.historyWindow.lift()

  ########
  # load_history: loads history from file
  def load_history(self):
    try:
      f = open(MoneyTimer.HISTORY_FILE, "r")
      s = f.read()
      f.close()
      temp = json.loads(s)
      currTime = localtime()
      toDel = None
      for i in range(len(temp)): # if current day in file, forget it
        if (temp[i]["year"] == currTime.tm_year and
            temp[i]["mon"]  == currTime.tm_mon and
            temp[i]["day"]  == currTime.tm_mday):
          toDel = i
          continue
        for key in MoneyTimer.HISTORY_FORMAT.keys(): # validate entries
          if not isinstance(temp[i][key], MoneyTimer.HISTORY_FORMAT[key]):
            return []
      if toDel != None:
        del temp[toDel]
      return temp
    except Exception:
      return []

  ########
  # save_history: saves history to file
  def save_history(self):
    earnings = self.secSoFar / 3600 * self.settings["hourlyRate"] * MoneyTimer.PERCENT_EARN
    if self.todaysGoal != 0:
      pct = self.secSoFar / (self.todaysGoal * 3600)
    else:
      pct = 1.0
    currentDayStats = {"year": self.startDate[0],
                       "mon" : self.startDate[1],
                       "day" : self.startDate[2],
                       "wday": self.startDay,
                       "secSoFar": self.secSoFar,
                       "earnings": (earnings * 100 // 1) / 100, # clip to cents
                       "percent" : (pct * 10000 // 1) / 100 } # clip to 2 decimals
    self.history.insert(0, currentDayStats)
    s = json.dumps(self.history)

    f = open(MoneyTimer.HISTORY_FILE, "w")
    f.write(s)
    f.close()

  ########
  # on_credits_click: displays credits
  def on_credits_click(self):
    if self.credits != None:
      self.credits.destroy()
    self.credits = Toplevel(self)
    self.credits.title("Credits [Money Timer]")
    self.credits.text = Text(self.credits,
                             width = 50)
    self.credits.text.insert(END, MoneyTimer.CREDITS_TEXT)
    self.credits.text.config(state = DISABLED)
    self.credits.text.pack(side = "top", fill = BOTH)

  ########
  # destroy: modified to save configurations and recorded time/earnings
  def destroy(self):
    self.save_settings()
    self.save_history()
    super().destroy()
# MoneyTimer
################


########
# main: if you need a description for this, I cannot help you
def main():
  root = Tk()
  root.title("Money Timer")
  root.lift()
  cf = ClockFace(root, size = 100, smooth = True, bg = PhotoImage(file = "art.gif"), handcolor = "#000000", markcolor = "#000000")
  cf.pack(side = "left")
  mt = MoneyTimer(root)
  mt.pack(side = "left")

  root.mainloop()

main()

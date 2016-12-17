################################
# clockface.py
# Noah Ansel
# 2016-12-17
# ------------------------------
# A configurable clock widget for use in Tkinter programs.
################################

# imports
from tkinter import *
from time import localtime
from math import *


################
# ClockFace: A configurable clock widget for use in Tkinter programs.
# Has some support for basic Tkinter methods, but not all.
#   Configurable Parameters:
#     background  : Either a color or a Tkinter-compatible PhotoImage or BitmapImage.
#     handcolor   : Color of clock hands.
#     markcolor   : Color of hour marks/numbers.
#     marks       : Type of hour marks to use.
#                   Must be one of TICKS, ARABIC, ROMAN.
#     shape       : Clock shape to use. TODO: Implement this functionality.
#                   Must be one of SQUARE or ROUND.
#     size        : Size of the clock face in pixels. May be slightly smaller
#                   due to widget borders.
#     smooth      : Flag indicating whether hands should update on <1s intervals.
#     wedge_size  : Percentage of radius wedges should occupy. TODO: Implement this.
#     update_rate : When smooth enabled, the amount of updates per second.
class ClockFace:

  # tick mark types
  TICKS  = "TICKS"
  ARABIC = "ARABIC"
  ROMAN  = "ROMAN"

  # shape types
  SQUARE = "SQUARE"
  ROUND  = "ROUND"

  # default configuration values
  DEFAULT_CONFIG = {"background" : "#DDEEEE",
                    "handcolor"  : "#0000EE",
                    "markcolor"  : "#FF9933",
                    "marks"      : TICKS,
                    "shape"      : SQUARE,
                    "size"       : 300,
                    "smooth"     : False,
                    "wedge_size" : 0.5,
                    "update_rate" : 10}

  # default colors for non-configurable parameters
  BG_COLOR_WITH_IMAGE = "#000000"
  DEFAULT_WEDGE_COLOR = "#FFDD00"

  # drawing constants
  _OFFSET = 3
  _STEP_12 = 2 * pi / 12
  _STEP_60 = 2 * pi / 60
  _TICK_SIZE = 0.8

  _FONTS = {ARABIC: "Helvetica",
            ROMAN:  "Times New Roman"}

  ########
  # Initializes canvas, sets config if given as parameters.
  # See class description for configurable parameters.
  #   Params:
  #     master : Reference to parent Tkinter object.
  def __init__(self, master = None, **kwargs):

    self._configVars = {} # copy over default config
    for k, v in ClockFace.DEFAULT_CONFIG.items():
      self._configVars[k] = v

    self._canvas = Canvas(master,
                          relief = SUNKEN,
                          bd = 2,
                          bg = self._configVars["background"],
                          width = self._configVars["size"],
                          height = self._configVars["size"])

    self._mid = self._configVars["size"] / 2 + ClockFace._OFFSET
    self._bgImg = None
    self._bgImgId = None
    self._ms = 0

    self.config(**kwargs) # now config based on passed variables

    self._init_face()
    self._tick()

  ################
  # Configuration
  ################

  ########
  # Alternate name for config method.
  def configure(self, **kwargs):
    self.config(**kwargs)

  ########
  # Updates configuration of the object and updates view as needed.
  # See class description for configurable parameters.
  def config(self, **kwargs):
    redraw = False
    for key, val in kwargs.items():
      # error check for key
      if not isinstance(key, str):
        raise TypeError("Expected 'str' type for key, got '{}'.".format(str(type(key))))


      # background color or picture
      if key == "background" or key == "bg":
        if isinstance(val, str): # color bg
          if self._bgImg != None: # delete img if previous background
            self._canvas.delete(self._bgImgId)
            self._bgImg = None
            self._bgImgId = None
          self._canvas.config(bg = val)
          self._configVars["background"] = val
        elif isinstance(val, PhotoImage): # image bg
          self._canvas.config(bg = ClockFace.BG_COLOR_WITH_IMAGE) # border in case img not big enough
          if self._bgImgId != None:
            self._canvas.delete(self._bgImgId)
          self._bgImg = val
          self._bgImgId = self._canvas.create_image(self._mid,
                                                    self._mid,
                                                    image = self._bgImg)
          self._canvas.tag_lower(self._bgImgId)
        else:
          raise TypeError("Option 'background' must be of type 'str' or 'Tk.PhotoImage'.")

      # hand color
      elif key == "handcolor":
        if isinstance(val, str):
          if self._valid_hex(val):
            self._configVars["handcolor"] = val
            redraw = True
          else:
            raise ValueError("Option 'handcolor' received invalid value '{}'.".format(val))
        else:
          raise TypeError("Option 'handcolor' must be of type 'str'.")

      # tick mark/numeral color
      elif key == "markcolor" or key == "mk":
        if isinstance(val, str):
          if self._valid_hex(val):
            self._configVars["markcolor"] = val
            redraw = True
          else:
            raise ValueError("Option 'markcolor' received invalid value '{}'.".format(val))
        else:
          raise TypeError("Option 'markcolor' must be of type 'str'.")

      # tick mark type
      elif key == "marks":
        if val in (ClockFace.TICKS, ClockFace.ARABIC, ClockFace.ROMAN):
          self._configVars["marks"] = val
          redraw = True
        else:
          raise ValueError("Option 'marks' received invalid value '{}'.".format(val))

      # clock shape
      elif key == "shape":
        if val == ClockFace.SQUARE:
          raise NotImplementedError()
        elif val == ClockFace.ROUND:
          raise NotImplementedError()
        else:
          raise ValueError("Option 'shape' received invalid value '{}'.".format(val))

      # size
      elif key == "size":
        if isinstance(val, int) or isinstance(val, float):
          self._configVars["size"] = val
          self._resize()
        else:
          raise TypeError("Option 'size' must be of type 'int' or 'float'.")

      # smooth movement
      elif key == "smooth":
        if isinstance(val, bool):
          self._configVars["smooth"] = val
        else:
          raise TypeError("Option 'smooth' must be of type 'bool'.")

      elif key == "wedge_size":
        if isinstance(val, float) or isinstance(val, int):
          if val > 0 and val <= 1:
            raise NotImplementedError()
          else:
            raise ValueError("Option 'wedge_size' must be between 0 and 1.")
        else:
          raise TypeError("Option 'wedge_size' must be of type 'int' or 'float'.")

      # update rate for smooth movement
      elif key == "update_rate":
        if isinstance(val, float) or isinstance(val, int):
          if val > 0:
            self._configVars["update_rate"] = val
          else:
            raise ValueError("Option 'update_rate' must be greater than 0.")
        else:
          raise TypeError("Option 'update_rate' must be of type 'int' or 'float'.")


      # unknown key
      else:
        raise KeyError("Option '{}' not recognized.".format(key))

    if redraw:
      self._init_face()

  ########
  # Obtains a config variable. Note that for 'bg', return can be a PhotoImage or
  # BitmapImage object.
  # See class description for configurable parameters.
  #   Params:
  #     key : Name of parameter to be fetched.
  #   Returns: Value of requested parameter.
  def cget(self, key):
    if isinstance(key, str):
      if key in self._configVars.keys():
        return self._configVars[key]
      elif key == "bg":
        return self._configVars["background"]
      elif key == "mk":
        return self._configVars["markcolor"]
      else:
        raise KeyError("Key '{}' not recognized.".format(key))
    else:
      raise TypeError("Expected 'str' type for key, got '{}'.".format(str(type(key))))


  ################
  # Private methods
  ################

  ########
  # Initializes canvas display including hands, background, marks, and wedges.
  # TODO: implement wedges.
  def _init_face(self):
    self._canvas.delete("all")
    self._bgImgId = self._canvas.create_image(self._mid,
                                              self._mid,
                                              image = self._bgImg)
    self._mid = self._configVars["size"] / 2 + ClockFace._OFFSET

    self._hrLen = self._configVars["size"] * 0.2
    self._minLen = self._configVars["size"] * 0.3
    self._secLen = self._configVars["size"] * 0.4
    self._time = localtime()

    tickSize = self._configVars["size"] / sqrt(2) # has to be big enough to cover the diagonal
    sideStep = self._configVars["size"] / 2 * tan(pi / 6)
    for i in range(12):
      if i < 3:
        dy = -self._configVars["size"] / 2
        dx = (i % 3 - 1) * sideStep
      elif i >= 3 and i < 6:
        dx = self._configVars["size"] / 2
        dy = (i % 3 - 1) * sideStep
      elif i >= 6 and i < 9:
        dy = self._configVars["size"] / 2
        dx = -(i % 3 - 1) * sideStep
      elif i >= 9:
        dx = -self._configVars["size"] / 2
        dy = -(i % 3 - 1) * sideStep

      hr = (i - 1) % 12
      hr += 12 if (hr <= 0) else 0

      if self._configVars["marks"] == ClockFace.TICKS:
        start = (self._mid + 0.8 * dx, self._mid + 0.8 * dy)
        end   = (self._mid + dx, self._mid + dy)
        if i % 3 != 1:
          newTick = self._canvas.create_line(start[0],
                                     start[1],
                                     end[0],
                                     end[1],
                                     width = self._configVars["size"] * 0.01,
                                     fill = self._configVars["markcolor"],
                                     # capstyle = ROUND,
                                     tags = "fg",
                                     smooth = True)
        else:
          newTick = self._canvas.create_line(start[0],
                                     start[1],
                                     end[0],
                                     end[1],
                                     width = self._configVars["size"] * 0.02,
                                     fill = self._configVars["markcolor"],
                                     # capstyle = ROUND,
                                     tags = "fg",
                                     smooth = True)

      elif self._configVars["marks"] in (ClockFace.ARABIC, ClockFace.ROMAN):
        center = (self._mid + 0.9 * dx, self._mid + 0.9 * dy)
        showText = self._roman_num(hr) if self._configVars["marks"] == ClockFace.ROMAN else int(hr)
        showFont = (ClockFace._FONTS[self._configVars["marks"]], -self._configVars["size"] // 10)
        if hr != 8:
          newTick = self._canvas.create_text(center[0],
                                             center[1],
                                             text = showText,
                                             font = showFont,
                                             fill = self._configVars["markcolor"])
        else:
          newTick = self._canvas.create_text(center[0] + self._configVars["size"] / 20,
                                             center[1],
                                             text = showText,
                                             font = showFont,
                                             fill = self._configVars["markcolor"])

      else:
        raise ValueError("Unexpected value '{}' for 'marks' parameter.".format(self._configVars["marks"]))



    hrAng, minAng, secAng = self._get_hand_angles()
    coords = self._get_line_coords(self._mid,self._mid, self._hrLen, hrAng)
    self._hrHand  = self._canvas.create_line(coords[0],
                                    coords[1],
                                    coords[2],
                                    coords[3],
                                    width = self._configVars["size"] * 0.03,
                                    fill = self._configVars["handcolor"],
                                    capstyle = ROUND,
                                    tags = "fg",
                                    smooth = True)
    coords = self._get_line_coords(self._mid,self._mid, self._minLen, minAng)
    self._minHand  = self._canvas.create_line(coords[0],
                                     coords[1],
                                     coords[2],
                                     coords[3],
                                     width = self._configVars["size"] * 0.02,
                                     fill = self._configVars["handcolor"],
                                     capstyle = ROUND,
                                     tags = "fg",
                                     smooth = True)
    coords = self._get_line_coords(self._mid,self._mid, self._secLen, secAng)
    self._secHand  = self._canvas.create_line(coords[0],
                                     coords[1],
                                     coords[2],
                                     coords[3],
                                     width = self._configVars["size"] * 0.01,
                                     fill = self._configVars["handcolor"],
                                     capstyle = ROUND,
                                     tags = "fg",
                                     smooth = True)


  ########
  # Helper function to get angles of hands based on current time.
  #   Returns: Hour, minute, and second hand angles, in that order.
  def _get_hand_angles(self):
    hrAng = ClockFace._STEP_12 * (self._time.tm_hour % 12 +
                                 self._time.tm_min / 60 +
                                 self._time.tm_sec / 3600)
    minAng = ClockFace._STEP_60 * (self._time.tm_min + self._time.tm_sec / 60)
    if self._configVars["smooth"]:
      secAng = ClockFace._STEP_60 * (self._time.tm_sec + self._ms / 1000)
    else:
      secAng = ClockFace._STEP_60 * (self._time.tm_sec)
    return hrAng, minAng, secAng
    raise NotImplementedError()

  ########
  # Helper function to get line coordinates given fixed location, length, and direction.
  #   Params:
  #     x, y  : Cartesian coordinates of start point.
  #     mag   : Length of the line.
  #     theta : Rotation counter-clockwise from x-axis, in radians.
  #   Returns: Coordinates of the line.
  def _get_line_coords(self, x, y, mag, theta):
    dx, dy = self._get_components(mag, theta)
    return x, y, x+dx, y-dy

  ########
  # Helper function to convert polar coordinates to Cartesian coordinates.
  #   Params:
  #     mag   : Distance from origin.
  #     theta : Rotation counter-clockwise from x-axis, in radians.
  #   Returns: Cartesian coordinates of point as (x,y).
  def _get_components(self, mag, theta):
    return mag*sin(theta), mag*cos(theta)

  ########
  # Helper function to convert a number into roman numerals.
  # Only supports numbers up to 99.
  #   Params:
  #     num : Number to be processed.
  #   Returns: Roman numeral representation of number.
  def _roman_num(self, num):
    ret = ""

    # 10's
    temp = num // 10
    if temp % 10 == 9:
      ret = ret + 'XC'
    elif temp % 10 >= 5:
      ret = ret + 'L' + 'X'*(temp % 5)
    elif temp % 5 == 4:
      ret = ret + 'XL'
    else:
      ret = ret + 'X'*(temp % 5)

    # 1's
    if num % 10 == 9:
      ret = ret + 'IX'
    elif num % 10 >= 5:
      ret = ret + 'V' + 'I'*(num % 5)
    elif num % 5 == 4:
      ret = ret + 'IV'
    else:
      ret = ret + 'I'*(num % 5)

    return ret

  ########
  # Resizes the clockface based on current configuration and redraws face.
  def _resize(self):
    self._canvas.delete("all")
    self._canvas.config(width = self._configVars["size"],
                        height = self._configVars["size"])
    self._mid = self._configVars["size"] / 2

    self._bgImgId = self._canvas.create_image(self._mid,
                                              self._mid,
                                              image = self._bgImg)
    self._init_face()

  ########
  # Updates hands and wedges based on current time. TODO: implement wedges.
  # Runs once per second if 'smooth' disabled.
  # Otherwise runs 'update_rate' times per second.
  def _tick(self):
    newTime = localtime()
    if newTime.tm_sec != self._time.tm_sec:
      self._ms = 0
    else:
      self._ms += 1000 // self._configVars["update_rate"]
    self._time = newTime
    hrAng, minAng, secAng = self._get_hand_angles()
    coords = self._get_line_coords(self._mid, self._mid, self._hrLen, hrAng)
    self._canvas.coords(self._hrHand, coords[0], coords[1], coords[2], coords[3])
    coords = self._get_line_coords(self._mid, self._mid, self._minLen, minAng)
    self._canvas.coords(self._minHand, coords[0], coords[1], coords[2], coords[3])
    coords = self._get_line_coords(self._mid, self._mid, self._secLen, secAng)
    self._canvas.coords(self._secHand, coords[0], coords[1], coords[2], coords[3])

    self._canvas.after(1000 // self._configVars["update_rate"], self._tick)

  ########
  # Determines if given string is a valid Tkinter hex string.
  #   Params:
  #     hexString : String to be tested.
  #   Returns: True if valid, False if not.
  def _valid_hex(self, hexString):
    if len(hexString) == 7:
      if hexString[0] == '#':
        for i in range(1,7):
          if hexString[i].lower() not in '0123456789abcdef':
            return False
        return True
    return False


  ################
  # Custom methods
  ################

  ########
  # TODO: Implement and document.
  def begin_wedge(self, color = DEFAULT_WEDGE_COLOR, tags = None):
    raise NotImplementedError()

  ########
  # TODO: Implement and document.
  def end_wedge(self):
    raise NotImplementedError()

  ########
  # TODO: Implement and document.
  def get_wedges(self, tags):
    raise NotImplementedError()

  ########
  # TODO: Implement and document.
  def clear_wedges(self, *args):
    raise NotImplementedError()


  ################
  # Geometry managers: See Tkinter documentation.
  ################

  def grid(self, **kwargs):
    return self._canvas.grid(**kwargs)

  def grid_forget(self, **kwargs):
    return self._canvas.grid_forget(**kwargs)

  def pack(self, **kwargs):
    return self._canvas.pack(**kwargs)

  def pack_forget(self, **kwargs):
    return self._canvas.pack_forget(**kwargs)

  def place(self, **kwargs):
    return self._canvas.place(**kwargs)

  def place_forget(self, **kwargs):
    return self._canvas.place_forget(**kwargs)

  ################
  # Misc Tkinter Methods: See Tkinter documentation.
  ################

  def bind(self, **kwargs):
    return self._canvas.bind(**kwargs)

  def unbind(self, **kwargs):
    return self._canvas.unbind(**kwargs)

  def destroy(self, **kwargs):
    return self._canvas.destroy(**kwargs)

  def lift(self, **kwargs):
    return self._canvas.lift(**kwargs)

  def lower(self, **kwargs):
    return self._canvas.lower(**kwargs)

  def keys(self):
    return self._configVars.keys()

  def size(self, **kwargs):
    return self._canvas.size(**kwargs)

  def quit(self, **kwargs):
    return self._canvas.quit(**kwargs)
# ClockFace
################



################
# Testing
if __name__ == "__main__":
  root = Tk()
  root.title("ClockFace [Test Suite]")
  cf = ClockFace(root, smooth = True, update_rate = 10)
  photo = PhotoImage(file = "art.gif")
  photo2 = PhotoImage(file = "art2.gif")
  cf2 = ClockFace(root, bg = photo2, size = 400, handcolor = "#000000", marks = ClockFace.ARABIC)
  root.after(5000, lambda: cf.config(size = cf.cget("size") + 50, bg = photo, handcolor = "#00FF00", marks = ClockFace.ROMAN, markcolor = "#FFFFFF"))
  cf.grid(row = 0, column = 0)
  cf2.grid(row = 1, column = 0)

  miniFrame = Frame(root)
  miniFrame.grid(row = 0, column = 1, rowspan = 2)
  minis = []
  for i in range(5):
    minis.append(ClockFace(miniFrame, size = 150 + 15 * i, smooth = True, update_rate = i*2 + 1, marks = ClockFace.ROMAN))
    minis[i].grid(row = i % 3, column = i // 3)

  root.mainloop()
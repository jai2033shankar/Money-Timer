from tkinter import *
from time import localtime
from math import *

class ClockFace(Canvas):

  DEFAULT_SIZE = 300
  DEFAULT_BG = "#DDEEEE"
  DEFAULT_FG = "#0000EE"

  OFFSET = 3

  STEP_12 = 2*pi/12
  STEP_60 = 2*pi/60

  def __init__(self,
               master = None,
               size = DEFAULT_SIZE,
               background = DEFAULT_BG,
               foreground = DEFAULT_FG):
    super().__init__(master,
                   width = size,
                   height = size,
                   bg = background,
                   bd = 2,
                   relief = SUNKEN)
    self._size = size
    self._background = background
    self._foreground = foreground
    self._mid = self._size / 2 + ClockFace.OFFSET
    self._hrLen = self._size * 0.2
    self._minLen = self._size * 0.3
    self._secLen = self._size * 0.4
    self._time = localtime()

    self._draw_face()

    self._tick()

  def _get_hand_angles(self):
    hrAng = ClockFace.STEP_12 * (self._time.tm_hour % 12 +
                                 self._time.tm_min / 60 +
                                 self._time.tm_sec / 3600)
    minAng = ClockFace.STEP_60 * (self._time.tm_min + self._time.tm_sec / 60)
    secAng = ClockFace.STEP_60 * (self._time.tm_sec)
    return hrAng, minAng, secAng

  def _draw_face(self):
    tickSize = self._size * sqrt(2) # has to be big enough to cover the diagonal
    for i in range(12):
      coords = self._get_line_coords(self._mid,
                                     self._mid,
                                     tickSize,
                                     ClockFace.STEP_12 * i)
      if i % 3 == 0:
        newTick = self.create_line(coords[0],
                                   coords[1],
                                   coords[2],
                                   coords[3],
                                   width = self._size * 0.02,
                                   fill = self._foreground,
                                   capstyle = ROUND,
                                   tags = "fg",
                                   smooth = True)
      else:
        newTick = self.create_line(coords[0],
                                   coords[1],
                                   coords[2],
                                   coords[3],
                                   width = self._size * 0.01,
                                   fill = self._foreground,
                                   capstyle = ROUND,
                                   tags = "fg",
                                   smooth = True)

    self.create_rectangle(self._size * 0.1 + ClockFace.OFFSET,
                          self._size * 0.1 + ClockFace.OFFSET,
                          self._size * 0.9 + ClockFace.OFFSET,
                          self._size * 0.9 + ClockFace.OFFSET,
                          fill = self._background,
                          outline = "",
                          tags = "bg")

    hrAng, minAng, secAng = self._get_hand_angles()
    coords = self._get_line_coords(self._mid,self._mid, self._hrLen, hrAng)
    self._hrHand  = self.create_line(coords[0],
                                    coords[1],
                                    coords[2],
                                    coords[3],
                                    width = self._size * 0.03,
                                    fill = self._foreground,
                                    capstyle = ROUND,
                                    tags = "fg",
                                    smooth = True)
    coords = self._get_line_coords(self._mid,self._mid, self._minLen, minAng)
    self._minHand  = self.create_line(coords[0],
                                     coords[1],
                                     coords[2],
                                     coords[3],
                                     width = self._size * 0.02,
                                     fill = self._foreground,
                                     capstyle = ROUND,
                                     tags = "fg",
                                     smooth = True)
    coords = self._get_line_coords(self._mid,self._mid, self._secLen, secAng)
    self._secHand  = self.create_line(coords[0],
                                     coords[1],
                                     coords[2],
                                     coords[3],
                                     width = self._size * 0.01,
                                     fill = self._foreground,
                                     capstyle = ROUND,
                                     tags = "fg",
                                     smooth = True)

  def _recolor(self):
    fg = self.find_withtag("fg")
    bg = self.find_withtag("bg")
    for item in fg:
      self.itemconfig(item, fill = self._foreground)
    for item in bg:
      self.itemconfig(item, fill = self._background)


  def _tick(self):
    self._time = localtime()
    hrAng, minAng, secAng = self._get_hand_angles()
    coords = self._get_line_coords(self._mid, self._mid, self._hrLen, hrAng)
    self.coords(self._hrHand, coords[0], coords[1], coords[2], coords[3])
    coords = self._get_line_coords(self._mid, self._mid, self._minLen, minAng)
    self.coords(self._minHand, coords[0], coords[1], coords[2], coords[3])
    coords = self._get_line_coords(self._mid, self._mid, self._secLen, secAng)
    self.coords(self._secHand, coords[0], coords[1], coords[2], coords[3])


    self.after(100, self._tick)

  def _get_line_coords(self, x, y, mag, theta):
    dx, dy = self._get_components(mag, theta)
    return x, y, x+dx, y-dy


  def _get_components(self, mag, theta):
    return mag*sin(theta), mag*cos(theta)

if __name__ == "__main__":
  root = Tk()
  root.title("ClockFace [test]")
  cf = ClockFace(root)
  cf.grid(row = 0, column = 0)

  root.mainloop()
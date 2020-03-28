#!/usr/bin/env python

from sense_hat import SenseHat

E = 0.1
MIN_TEMP = -40
MAX_TEMP = abs(MIN_TEMP)
MIN_PRESSURE = 950
MAX_PRESSURE = 1050
        
class View:
  """View interface"""
  def draw(self, hat):
    pass

class ColorCalc:
  """Computes color for value from given range"""
  def __init__(self, min_value, max_value):
    self.min_value = min_value
    self.levels = max_value - min_value
    self.prev_value = None
    self.color = None

  def compute_color(self, value):
    if (
      self.prev_value is not None
        and self.color is not None
        and abs(self.prev_value - value) < E
      ):
      return self.color
      
    self.prev_value = value
      
    score = 0
    if value > self.min_value:
      score = min(1.0, (abs(self.min_value - value) / self.levels))
        
    saturation = 255 * (score * 2 - 1) if score > 0.5 else 255 * (1 - score * 2)
    saturation = int(saturation)
        
    self.color = (saturation, 0, 0) if score > 0.5 else (0, 0, saturation)
        
    return self.color


class TemperatureView(View):
  def __init__(self):
    self.level = ColorCalc(MIN_TEMP, MAX_TEMP)
        
  def draw(self, hat):
    temp = hat.temp
    color = self.level.compute_color(temp)
    pixels = [color for _ in range(64)]

    hat.set_pixels(pixels)

class PressureView(View):
  def __init__(self):
    self.level = ColorCalc(MIN_PRESSURE, MAX_PRESSURE)
        
  def draw(self, hat):
    pressure = hat.pressure
    color = self.level.compute_color(pressure)
    pixels = [color for _ in range(64)]

    hat.set_pixels(pixels)

class EventHandler:
  def __init__(self, hat):
      self.hat = hat
      self.views = []
      self.current_view = None
      self.current_idx = None
      
  def register_view(self, view):
    view_type = type(view)
    if not issubclass(view_type, View):
      raise TypeError("Not a View subclass; got {}".format(view_type))

    self.views.append(view)

  def handle_event(self, event):
    if event.action == 'pressed':
      new_idx = self.current_idx
      new_idx += { 'left': -1, 'right': +1 }.get(event.direction, 0)

      max_idx = len(self.views) - 1
      if new_idx > max_idx:
        new_idx = 0
      elif new_idx < 0:
        new_idx = max_idx

      self.current_idx = new_idx
      self.hat.clear()
      self.current_view = self.views[self.current_idx]
        
  def event_loop(self):
    self.current_idx = 0
    self.current_view = self.views[self.current_idx]
    while True:
      for event in self.hat.stick.get_events():
        self.handle_event(event)
      
      self.current_view.draw(self.hat)

# Program begins here
hat = SenseHat()
hat.clear()

event_handler = EventHandler(hat)
event_handler.register_view(TemperatureView())
event_handler.register_view(PressureView())
event_handler.event_loop()

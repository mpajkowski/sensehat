#!/usr/bin/env python

from sense_hat import SenseHat
import copy

E = 0.1
MIN_TEMP = -40
MAX_TEMP = abs(MIN_TEMP)
MIN_PRESSURE = 950
MAX_PRESSURE = 1050
MIN_HUMIDITY = 0
MAX_HUMIDITY = 100
MIN_DEGREE = 0
MAX_DEGREE = 360
WHITE = (0xFF, 0xFF, 0xFF)
BLACK = (0x00, 0x00, 0x00)

def set_pixel(hat, idx, color):
  x = idx % 8
  y = int(idx / 8)

  hat.set_pixel(x, y, color)
  

class View:
  """View interface"""
  def draw(self, hat):
    raise NotImplementedError


class ColorCalc:
  """Computes color for value from given range"""
  def __init__(self, min_value, max_value):
    self.min_value = min_value
    self.levels = max_value - min_value
    self.prev_value = None
    self.color = None

  def compute(self, value):
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
  def __init__(self, color_calc):
    self.color_calc = color_calc
        
  def draw(self, hat):
    temp = hat.temp
    color = self.color_calc.compute(temp)
    
    for idx in range(48):
      set_pixel(hat, idx, color)

class PressureView(View):
  def __init__(self, color_calc):
    self.color_calc = color_calc

  def draw(self, hat):
    pressure = hat.pressure
    color = self.color_calc.compute(pressure)
    
    for idx in range(48):
      set_pixel(hat, idx, color)


class OrientationView(View):
  def __init__(self, color_calc_roll, color_calc_pitch, color_calc_yaw):
    self.color_calc_roll = color_calc_roll
    self.color_calc_pitch = color_calc_pitch
    self.color_calc_yaw = color_calc_yaw

  def draw(self, hat):
    orientation = hat.orientation

    roll = orientation.get('roll', 0)
    pitch = orientation.get('pitch', 0)
    yaw = orientation.get('yaw', 0)
    
    color_roll = self.color_calc_roll.compute(roll)
    color_pitch = self.color_calc_pitch.compute(pitch)
    color_yaw = self.color_calc_yaw.compute(yaw)

    for idx in range(16):
      set_pixel(hat, idx, color_roll)
      
    for idx in range(16, 32):
      set_pixel(hat, idx, color_pitch)
      
    for idx in range(32, 48):
      set_pixel(hat, idx, color_yaw)


class HumidityView(View):
  def __init__(self, color_calc):
    self.color_calc = color_calc

  def draw(self, hat):
    humidity = hat.humidity
    color = self.color_calc.compute(humidity)

    for idx in range(48):
      set_pixel(hat, idx, color)


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
      
      if new_idx != self.current_idx:
        max_idx = len(self.views) - 1
        if new_idx > max_idx:
          new_idx = 0
        elif new_idx < 0:
          new_idx = max_idx
          
        # turn off current idx
        set_pixel(self.hat, 48 + self.current_idx, BLACK)
        
        # turn on new
        set_pixel(self.hat, 48 + new_idx, WHITE)
  
        self.current_idx = new_idx
        self.current_view = self.views[self.current_idx]

  def event_loop(self):
    self.current_idx = 0
    set_pixel(self.hat, 48, WHITE)
    self.current_view = self.views[self.current_idx]
    while True:
      for event in self.hat.stick.get_events():
        self.handle_event(event)

      self.current_view.draw(self.hat)

# Program begins here
hat = SenseHat()
hat.set_imu_config(True, True, True)
hat.clear()

event_handler = EventHandler(hat)

event_handler.register_view(TemperatureView(ColorCalc(MIN_TEMP, MAX_TEMP)))
event_handler.register_view(PressureView(ColorCalc(MIN_PRESSURE, MAX_PRESSURE)))
event_handler.register_view(HumidityView(ColorCalc(MIN_HUMIDITY, MAX_HUMIDITY)))

calc_roll = ColorCalc(MIN_DEGREE, MAX_DEGREE)
calc_pitch = ColorCalc(MIN_DEGREE, MAX_DEGREE)
calc_yaw = ColorCalc(MIN_DEGREE, MAX_DEGREE)
orientation_view = OrientationView(calc_roll, calc_pitch, calc_yaw)

event_handler.register_view(orientation_view)

event_handler.event_loop()

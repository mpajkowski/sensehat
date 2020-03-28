from sense_hat import SenseHat
from copy import deepcopy
 
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
  '''View interface'''
 
  def setup(self, hat):
    '''Adjusts hat before drawing'''
 
  def draw(self, hat):
    '''Reads value(s) from hat and presents it on the hat's LED matrix'''
    raise NotImplementedError
 
 
class ColorCalc:
  '''Computes color for value from given range'''
  def __init__(self, min_value, max_value, reverse=False):
    self.min_value = min_value
    self.levels = max_value - min_value
    self.reverse = reverse
    self.prev_value = None
    self.color = None
 
  def __copy__(self):
    return type(self)(self.min_value, self.max_value)
 
  def __deepcopy__(self, memo):
    id_self = id(self)
    copy = memo.get(id_self)
    if copy is None:
      copy = type(self)(
        deepcopy(self.min_value, memo),
        deepcopy(self.levels, memo)
      )
 
      memo[id_self] = copy
 
    return copy
 
  def compute(self, value):
    '''Compute color value'''
 
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
 
    red = (saturation, 0, 0)
    blue = (0, 0, saturation)
 
    if score > 0.5:
      if not self.reverse:
        self.color = red
      else:
        self.color = blue
    else:
      if not self.reverse:
        self.color = blue
      else:
        self.color = red
 
    return self.color
 
class FullScreenView(View):
  '''Populate screen with one color (without touching status bar)'''
  def __init__(self, color_calc, property, **kwargs):
    self.color_calc = color_calc
    self.property = property
    self.config = kwargs
 
  def draw(self, hat):
    value = getattr(hat, self.property)
 
    if value is None:
      raise ValueError('Unknown property: {}'.format(self.property))
 
    color = self.color_calc.compute(value)
 
    for idx in range(48):
      set_pixel(hat, idx, color)
 
class AxisView(View):
  '''Splits the screen for 3 rows, each one for corresponding axis - roll, pitch and yaw'''
 
  ROW_WIDTH = 16
 
  def __init__(self, color_calc_roll, color_calc_pitch, color_calc_yaw, **kwargs):
    self.color_calc_roll = color_calc_roll
    self.color_calc_pitch = color_calc_pitch
    self.color_calc_yaw = color_calc_yaw
    self.config = kwargs
 
  def setup(self, hat):
    compass_state = self.config.get('compass', False)
    gyro_state = self.config.get('gyro', False)
    accel_state = self.config.get('accel', False)
 
    hat.set_imu_config(compass_state, gyro_state, accel_state)
 
  def draw(self, hat):
    orientation = hat.orientation
 
    roll = orientation.get('roll', 0)
    pitch = orientation.get('pitch', 0)
    yaw = orientation.get('yaw', 0)
 
    color_roll = self.color_calc_roll.compute(roll)
    color_pitch = self.color_calc_pitch.compute(pitch)
    color_yaw = self.color_calc_yaw.compute(yaw)
 
    for idx in range(AxisView.ROW_WIDTH):
      set_pixel(hat, idx, color_roll)
 
    for idx in range(AxisView.ROW_WIDTH, AxisView.ROW_WIDTH*2):
      set_pixel(hat, idx, color_pitch)
 
    for idx in range(AxisView.ROW_WIDTH*2, AxisView.ROW_WIDTH*3):
      set_pixel(hat, idx, color_yaw)
 
 
class EventHandler:
  def __init__(self, hat):
      self.hat = hat
      self.views = []
      self.current_view = None
      self.current_idx = None
 
  def register_view(self, view):
    view_type = type(view)
    if not issubclass(view_type, View):
      raise TypeError('Not a View subclass; got {}'.format(view_type))
 
    self.views.append(view)
 
  def event_loop(self):
    self.current_idx = 0
    self.__set_new_view(0)
 
    while True:
      for event in self.hat.stick.get_events():
        self.__handle_event(event)
 
      self.current_view.draw(self.hat)
 
  def __handle_event(self, event):
    if event.action == 'pressed':
      new_idx = self.current_idx
      new_idx += { 'left': -1, 'right': +1 }.get(event.direction, 0)
 
      if new_idx != self.current_idx:
        max_idx = len(self.views) - 1
        if new_idx > max_idx:
          new_idx = 0
        elif new_idx < 0:
          new_idx = max_idx
 
        self.__set_new_view(new_idx)
 
  def __set_new_view(self, new_idx):
    # turn off current idx
    set_pixel(self.hat, 48 + self.current_idx, BLACK)
   
    # turn on new
    set_pixel(self.hat, 48 + new_idx, WHITE)
 
    self.current_idx = new_idx
    self.current_view = self.views[self.current_idx]
    self.current_view.setup(self.hat)
 
# Program begins here
hat = SenseHat()
hat.clear()
 
event_handler = EventHandler(hat)
 
degree_color_calc = ColorCalc(MIN_DEGREE, MAX_DEGREE)
 
gyroscope_view = AxisView(
  deepcopy(degree_color_calc),
  deepcopy(degree_color_calc),
  deepcopy(degree_color_calc),
  gyro=True
)
 
accel_view = AxisView(
  deepcopy(degree_color_calc),
  deepcopy(degree_color_calc),
  deepcopy(degree_color_calc),
  accel=True
)
 
compas_view = AxisView(
  deepcopy(degree_color_calc),
  deepcopy(degree_color_calc),
  deepcopy(degree_color_calc),
  compass=True
)
 
event_handler.register_view(FullScreenView(ColorCalc(MIN_TEMP, MAX_TEMP), 'temperature'))
event_handler.register_view(FullScreenView(ColorCalc(MIN_PRESSURE, MAX_PRESSURE), 'pressure'))
event_handler.register_view(FullScreenView(ColorCalc(MIN_HUMIDITY, MAX_HUMIDITY, reverse=True), 'humidity'))
event_handler.register_view(gyroscope_view)
event_handler.register_view(accel_view)
event_handler.register_view(compas_view)
 
event_handler.event_loop()
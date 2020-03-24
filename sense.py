#!/usr/bin/env python

from abc import ABC, abstractmethod
from sense_emu import SenseHat

class View(ABC):
    @abstractmethod
    def draw(self, hat: SenseHat):
        pass

class TemperatureView(View):
    def draw(self, hat: SenseHat):
        temp = hat.temp
        #coeffitient = abs(temp) / (if temp < 0 30 else 105)
            
        print(temp)

class PressureView(View):
    def draw(self, hat: SenseHat):
        print("test2")

class ContextViewer:
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



hat = SenseHat()

hat.clear()
context_viewer = ContextViewer(hat)
context_viewer.register_view(TemperatureView())
context_viewer.register_view(PressureView())
context_viewer.event_loop()

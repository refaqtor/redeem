#!/usr/bin/env python
"""
A filament sensor is a class of sensors that either 
detect the presence of filament, measures filament travel distance 
or filament diameter. For now, only filament distance 
is implemented. The idea is that the filament sensor can 
gather data from various sources and make decisions based 
on the data it gathers. 

Author: Elias Bakken

 Redeem is free software: you can redistribute it and/or modify
 it under the terms of the GNU General Public License as published by
 the Free Software Foundation, either version 3 of the License, or
 (at your option) any later version.

 Redeem is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 GNU General Public License for more details.

 You should have received a copy of the GNU General Public License
 along with Redeem.  If not, see <http://www.gnu.org/licenses/>.
"""
from threading import Thread
import time
import logging

class FilamentSensor:

    def __init__(self, name, sensor, ext_nr, printer=None):
        self.name = name
        self.sensor = sensor
        self.ext_nr = ext_nr
        self.printer = printer
        self.alarm_level = 0
        self.current_pos = 0
        self.ideal_pos = 0
        self.error_pos = 0

        self.t = Thread(target=self._loop)
        self.running = True
        self.t.start()
        
    def execute_alarm(self):
        logging.warning("Extruder {0} has reported too large deviation: {1:.2f} mm".format(self.ext_nr, self.error_pos*1000))

    def get_status(self):
        """ return a human readable status report """
        return "Filament sensor {0}: measured error is {1:.2f} mm ".format(self.name, self.error_pos*1000)

    def set_distance(self, distance):
        """ Set sensor distance """
        self.sensor.distance = distance

    def _loop(self):
        ''' Gather distance travelled from each of the sensors '''
        while self.running:
            self.current_pos = self.sensor.get_distance()
            self.error_pos = self.current_pos-self.ideal_pos
            if self.printer and self.printer.path_planner:
                self.ideal_pos = self.printer.path_planner.get_extruder_pos(self.ext_nr)
            #logging.debug("Set: {}, Measured: {}, Error : {}, alarm: {}".format(
            #    self.ideal_pos, self.current_pos, self.error_pos, self.alarm_level))
            if abs(self.error_pos) >= self.alarm_level: 
                self.execute_alarm()
            time.sleep(1)

    def stop(self):
        self.running = False
        self.t.join()



if __name__ == '__main__':
    from RotaryEncoder import *
    r = RotaryEncoder("/dev/input/event1", 360, 3)
    f = FilamentSensor()
    f.add_sensor(r)
    f.set_alarm_level(1, 0)
    time.sleep(10)
    r.stop()
    f.stop()




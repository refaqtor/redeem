#!/usr/bin/env python
'''
A Stepper Motor Driver class for Replicape. 

Author: Elias Bakken
email: elias.bakken@gmail.com
Website: http://www.hipstercircuits.com
License: BSD

You can use and change this, but keep this heading :)
'''

'''
The bits in the shift register are as follows:
D0 = DECAY   = X
D1 = MODE0   = X
D2 = MODE1   = X
D3 = MODE2 	 = X
D4 = nRESET  = 1
D5 = nSLEEP  = 1
D6 = nENABLE = 0
D7 = 		 = 0
'''
from spi import SPI
from bbio import *
from threading import Thread
import time

# init the SPI for the DAC
spi2_0 = SPI(2, 0)
spi2_0.bpw = 8
spi2_0.mode = 1
# Init the SPI for the serial to parallel
spi2_1 = SPI(2, 1)
spi2_1.bpw = 8
spi2_1.mode = 0

class SMD:

    all_smds = list()

    ''' Send the values to the serial to parallel chips '''
    @staticmethod
    def commit():        
        bytes = []
        for smd in SMD.all_smds:	   
            bytes.append(smd.getState())
        print "Updating registers with: "+str(bytes[::-1])
        spi2_1.writebytes(bytes[::-1])

    ''' Init'''
    def __init__(self, stepPin, dirPin, faultPin, dac_channel, name):
        self.dac_channel     = dac_channel  # Which channel on the dac is connected to this SMD
        self.stepPin         = stepPin
        self.dirPin          = dirPin
        self.faultPin        = faultPin
        self.name            = name
        self.state           = 0x70   	    # The state of the inputs
        self.dacvalue 	     = 0x00   	    # The voltage value on the VREF		
        self.enabled 	     = False	    # Start disabled
        self.currentPosition = 0.0 	        # Starts in pos 0
        self.set_position    = 0.0          # The desired position
        self.seconds_pr_step = 0.001        # Delay between each step (will be set by feed rate)
        self.steps_pr_mm     = 1            # Numer of steps pr mm. 
        self.debug           = 2            # Debug level
        self.direction       = 0            # Direction of movement
        self.moving          = False        # We start out stationary 
        self.microsteps      = 1.0          # Well, this is the microstep number
        self.pru_num         = -1           # PRU number, if any 
        SMD.all_smds.append(self) 	        # Add to list of smds

        pinMode(stepPin,   0, 0) 	        # Output, no pull up
        pinMode(dirPin,    0, 0) 	        # Output, no pull up
        pinMode(faultPin,  1, 0) 	        # Input, no pull up
 						
    ''' Sets the SMD enabled '''
    def setEnabled(self):
        if not self.enabled:
            self.state &= ~(1<<6)
            self.update()
            self.enabled = True
	
    ''' Sets the SMD disabled '''
    def setDisabled(self):
        print "setDisabled called"
        if self.enabled:
            self.state |= (1<<6)
            self.update()
            self.enabled = False
            print "smd disabled, state = "+bin(self.state)

    '''Logic high to enable device, logic low to enter
    low-power sleep mode. Internal pulldown.'''
    def enableSleepmode(self):
        self.state &= ~(1<<5)		
        self.update()

    ''' Disables sleepmode (awake) '''
    def disableSleepmode(self):
        self.state |= (1<<5)		
        self.update()

    '''nReset - Active-low reset input initializes the indexer
    logic and disables the H-bridge outputs.
    Internal pulldown.'''
    def reset(self):
        self.state |= (1<<4)
        self.update()
        self.state &= ~(1<<4)
        self.update()

    ''' Microstepping (default = 0) 0 to 5 '''
    def set_microstepping(self, value):
        self.microsteps = (1<<value) 
        self.state &= ~(7<<1)
        self.state |= (value << 1)
        self.update()
        self.mmPrStep = 1.0/(self.steps_pr_mm*self.microsteps)
        if self.debug > 2:
            print "State is: "+bin(self.state)
            print "Microsteps: "+str(self.microsteps)
            print "mmPrStep is: "+str(self.mmPrStep)

    ''' Current chopping limit (This is the value you can change) '''
    def setCurrentValue(self, iChop):        
        vRef = 3.3                              # Voltage reference on the DAC
        rSense = 0.1                            # Resistance for the 
        vOut = iChop*5.0*rSense                 # Calculated voltage out from the DAC (See page 9 in the datasheet for the DAC)

        self.dacval = int((vOut*256.0)/vRef)
        byte1 = ((self.dacval & 0xF0)>>4) + (self.dac_channel<<4)
        byte2 = (self.dacval & 0x0F)<<4
        spi2_0.writebytes([byte1, byte2])       # Update all channels
        spi2_0.writebytes([0xA0, 0xFF])         # TODO: Change to only this channel (1<<dac_channel) ?

    ''' Returns the current state '''
    def getState(self):
        return self.state & 0xFF				# Return the satate of the serial to parallel

    ''' Commits the changes	'''
    def update(self):
        SMD.commit()							# Commit the serial to parallel

    '''
    Higher level commands 
    '''

    ''' Move a certain distance, relative movement '''
    def move(self, mm, movement):
        if movement == "ABSOLUTE":
            self.set_position = mm
        else:
            self.set_position += mm
        if self.set_position > self.currentPosition:
            self.direction = 1
        else:
            self.direction = 0
        digitalWrite(self.dirPin, self.direction)            

        while(abs(self.currentPosition - self.set_position) > self.mmPrStep):
            toggle(self.stepPin)
            time.sleep(self.seconds_pr_step/2.0)
            toggle(self.stepPin)
            time.sleep(self.seconds_pr_step/2.0)
            if self.direction == 1:
                self.currentPosition += self.mmPrStep
            else:
                self.currentPosition -= self.mmPrStep
            #print "curr: "+str(self.currentPosition)+", set: "+str(self.set_position)+" mmPrStep: "+str(self.mmPrStep)


    ''' Set timing and pin data '''
    def add_data(self, data):
        (pins, delays) = data

    ''' Ok, go! Start stepping with the just set data '''
    def go(self):
        pass

    ''' Prepare a move. But do not start the thread yet. '''
    def prepare_move(self, mm):
        if mm > 0:
            self.direction = 1
        else:
            self.direction = 0
        digitalWrite(self.dirPin, self.direction)        
        self.set_position = self.currentPosition+mm
        self.t = Thread(target=self.do_work)
        if self.debug > 1: 
            print "Prepare done"

    ''' Execute the planned move. '''
    def execute_move(self):
        self.moving = True
        self.t.start()		

    ''' Move to an absolute position '''
    def moveTo(self, pos):
        self.move(pos-self.currentPosition)

    ''' Do the work '''
    def do_work(self):
        if self.debug > 1:         
            print "Do work, delay is "+str(self.seconds_pr_step)
        i = 0
        while(abs(self.currentPosition - self.set_position) > self.mmPrStep):
            toggle(self.stepPin)
            time.sleep(self.seconds_pr_step/2.0)
            toggle(self.stepPin)
            time.sleep(self.seconds_pr_step/2.0)
            if self.direction == 1:
                self.currentPosition += self.mmPrStep
            else:
                self.currentPosition -= self.mmPrStep
            i += 1
        if self.debug > 1:
            print "Done, stepped %d times"%i
        self.moving = False

    ''' Returns true if the stepper is still moving '''
    def is_moving(self):
        return self.moving

    ''' Join the thread '''
    def end_move(self):
        self.t.join()

    ''' Set the current position of this stepper '''
    def setCurrentPosition(self, pos):
        self.currentPosition = pos

    ''' Return the position this stepper has '''	
    def get_current_position(self):
        return self.currentPosition


    ''' Set the feed rate in mm/min '''
    def setFeedRate(self, feed_rate):		
        minutes_pr_mm = 1.0/float(feed_rate)
        seconds_pr_mm = minutes_pr_mm*60.0
        self.seconds_pr_step = self.mmPrStep*seconds_pr_mm

        if self.debug > 0:
            print self.name+": feed rate: %f, sec.pr.mm: %f, sec.pr.step: %f"%(feed_rate, seconds_pr_mm, self.seconds_pr_step)

    ''' Toggle the "step" pin n times. '''
    def step(self, steps):
        print self.name+"Stepping %d times "%steps 
        for i in range(steps):
            toggle(self.stepPin)
            delay(self.stepDelay)
			
    ''' Sets the number of mm the stepper moves pr step. 
        This must be measured and calibrated '''
    def _setMMPrstep(self, mmPrStep):
        self.mmPrStep = mmPrStep

    ''' Set the number of steps pr mm. '''			
    def set_steps_pr_mm(self, steps_pr_mm):
        self.steps_pr_mm = steps_pr_mm
        self.mmPrStep = 1.0/(steps_pr_mm*self.microsteps)
	
    ''' Well, you can only guess what this function does. '''
    def set_max_feed_rate(self, max_feed_rate):
        self.max_feed_rate = max_feed_rate

    ''' If this can be controlled by a PRU, set the PRU number  (0 or 1) '''
    def set_pru(self, pru_num):
        self.pru_num = pru_num

    ''' Return true is this has a PRU nmuber assiciated with it '''
    def has_pru(self):
        return (self.pru_num > -1)

    ''' Return the pru number '''
    def get_pru(self):
        return self.pru_num

    ''' Get the number of steps pr meter '''
    def get_steps_pr_meter(self):        
        return self.steps_pr_mm*1000.0

    ''' The pin that steps, it looks like GPIO1_31 aso '''
    def get_step_pin(self):
        return (1<<int(self.stepPin.split("_")[1]))
    
    ''' '''
    def get_dir_pin(self):
        return (1<<int(self.dirPin.split("_")[1]))





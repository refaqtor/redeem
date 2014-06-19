/*
 This file is part of Redeem - 3D Printer control software
 
 Author: Mathieu Monney
 Website: http://www.xwaves.net
 License: GNU GPLv3 http://www.gnu.org/copyleft/gpl.html
 
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
 
 */

#ifndef PathPlanner_StepperCommand_h
#define PathPlanner_StepperCommand_h

#include <stdint.h>

typedef struct SteppersCommand {
	uint8_t     step  ;              //Steppers are defined as 0b000HEZYX - A 1 for a stepper means we will do a step for this stepper
	uint8_t     direction ;          //Steppers are defined as 0b000HEZYX - Direction for each stepper
	uint16_t    options   ;          //Options for the move - If the first bit is set to 1, then the stepper has the cancelable
	//option meaning that as soon as an endstop is hit, all the moves in the DDR are removed and canceled without making the steppers to move.
	uint32_t    delay    ;           //number of cycle to wait (this is the # of PRU click cycles)
} SteppersCommand;

static_assert(sizeof(SteppersCommand)==8,"Invalid stepper command size");

#endif
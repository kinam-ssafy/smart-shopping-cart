/*
 * cmd_handler.c
 *
 *  Created on: Feb 3, 2026
 *      Author: SSAFY
 */
#include "cmd_handler.h"
#include "cmd_kv.h"
#include "servo.h"
#include "motor_a.h"
#include <string.h> // strcmp
#include <stdlib.h> // abs
#include <stdint.h>
void handle_line(char *line)
{
  char *s = trim(line);
  if (*s == '\0') return;

  char key[3];
  int value;

  if (parse_kv(s, key, &value) == 0) {

    // TODO: 여기서 key/value에 따른 동작 넣으면 됨
    // 예: if (strcmp(key,"kp")==0) { ... }
    if(strcmp(key,"x")==0){
    	if(value < 0){
    	    Servo_Write_us(1470 + ((1470-1130) * value) / 34);
    	}
    	else{
    	    Servo_Write_us(1470 + ((1800-1470) * value) / 34);
    	}
    }
    else if(strcmp(key,"z")==0){
        MotorA_SetDir(1);
        MotorA_SetSpeed((uint8_t)value);
    }
    else if(strcmp(key,"r")==0){
        MotorA_SetDir(2);
        MotorA_SetSpeed(abs(value));
    }

  } else {
  }
}

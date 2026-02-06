/*
 * servo.c
 *
 *  Created on: Feb 3, 2026
 *      Author: SSAFY
 */
#include "servo.h"
#include "tim.h"

void Servo_Write_us(uint16_t us)
{

    __HAL_TIM_SET_COMPARE(&htim4, TIM_CHANNEL_1, us); // PB6=TIM4_CH1
}

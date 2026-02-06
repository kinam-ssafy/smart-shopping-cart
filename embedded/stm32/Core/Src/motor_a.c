/*
 * motor_a.c
 *
 *  Created on: Feb 3, 2026
 *      Author: SSAFY
 */
#include "motor_a.h"
#include "tim.h"
#include "gpio.h"
#include "main.h"
void MotorA_SetDir(uint8_t dir)
{
    // dir: 0=stop, 1=fwd, 2=rev
    if (dir == 1) {
        HAL_GPIO_WritePin(GPIOA, GPIO_PIN_10, GPIO_PIN_SET);   // IN1
        HAL_GPIO_WritePin(GPIOB, GPIO_PIN_4, GPIO_PIN_RESET); // IN2
    } else if (dir == 2) {
        HAL_GPIO_WritePin(GPIOA, GPIO_PIN_10, GPIO_PIN_RESET);
        HAL_GPIO_WritePin(GPIOB, GPIO_PIN_4, GPIO_PIN_SET);
    } else {
        HAL_GPIO_WritePin(GPIOA, GPIO_PIN_10, GPIO_PIN_RESET);
        HAL_GPIO_WritePin(GPIOB, GPIO_PIN_4, GPIO_PIN_RESET);
    }
}

void MotorA_SetSpeed(uint8_t duty) // 0~100
{
    if (duty > 100) duty = 100;

    // TIM3 Period가 999라면 CCR은 0~999 범위
    uint32_t arr = __HAL_TIM_GET_AUTORELOAD(&htim3);
    uint32_t ccr = (arr * duty) / 100;

    __HAL_TIM_SET_COMPARE(&htim3, TIM_CHANNEL_1, ccr); // PA6=TIM3_CH1
}

/* USER CODE BEGIN Header */
/**
  ******************************************************************************
  * @file           : main.c
  * @brief          : Main program body
  ******************************************************************************
  * @attention
  *
  * Copyright (c) 2023 STMicroelectronics.
  * All rights reserved.
  *
  * This software is licensed under terms that can be found in the LICENSE file
  * in the root directory of this software component.
  * If no LICENSE file comes with this software, it is provided AS-IS.
  *
  ******************************************************************************
  */
/* USER CODE END Header */
/* Includes ------------------------------------------------------------------*/
#include "main.h"
#include "tim.h"
#include "usart.h"
#include "gpio.h"

/* Private includes ----------------------------------------------------------*/
/* USER CODE BEGIN Includes */
extern TIM_HandleTypeDef htim3;   // CubeMX가 tim.c에 만들어줌

static void MotorA_SetDir(uint8_t dir)
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

static void MotorA_SetSpeed(uint8_t duty) // 0~100
{
    if (duty > 100) duty = 100;

    // TIM3 Period가 999라면 CCR은 0~999 범위
    uint32_t arr = __HAL_TIM_GET_AUTORELOAD(&htim3);
    uint32_t ccr = (arr * duty) / 100;

    __HAL_TIM_SET_COMPARE(&htim3, TIM_CHANNEL_1, ccr); // PA6=TIM3_CH1
}


#include <string.h>
#include <stdio.h>
#include <ctype.h>
#include <stdlib.h>
#include <stdarg.h>
/* USER CODE END Includes */

/* Private typedef -----------------------------------------------------------*/
/* USER CODE BEGIN PTD */
/* USER CODE END PTD */

/* Private define ------------------------------------------------------------*/
/* USER CODE BEGIN PD */
/* USER CODE END PD */

/* Private macro -------------------------------------------------------------*/
/* USER CODE BEGIN PM */
/* USER CODE END PM */

/* Private variables ---------------------------------------------------------*/

/* USER CODE BEGIN PV */
static char rx_line[32];   // 한 줄 커맨드 버퍼
static uint8_t rx_idx = 0;
/* USER CODE END PV */

/* Private function prototypes -----------------------------------------------*/
void SystemClock_Config(void);
/* USER CODE BEGIN PFP */
static void uart_print(const char *s);
static void uart_printf(const char *fmt, ...);
static char* trim(char *s);
static int parse_kv(const char *line, char key_out[3], int *value_out);
static void handle_line(char *line);
/* USER CODE END PFP */

/* Private user code ---------------------------------------------------------*/
/* USER CODE BEGIN 0 */
extern TIM_HandleTypeDef htim4;

static void Servo_Write_us(uint16_t us)
{

    __HAL_TIM_SET_COMPARE(&htim4, TIM_CHANNEL_1, us); // PB6=TIM4_CH1
}


static void uart_print(const char *s)
{
  HAL_UART_Transmit(&huart2, (uint8_t*)s, (uint16_t)strlen(s), 100);
}

static void uart_printf(const char *fmt, ...)
{
  char out[96];
  va_list ap;
  va_start(ap, fmt);
  vsnprintf(out, sizeof(out), fmt, ap);
  va_end(ap);
}

// 공백 제거(앞/뒤)
static char* trim(char *s)
{
  while (*s && isspace((unsigned char)*s)) s++;
  if (*s == 0) return s;

  char *end = s + strlen(s) - 1;
  while (end > s && isspace((unsigned char)*end)) end--;
  end[1] = '\0';
  return s;
}

/**
 * 입력: "k=123" 또는 "kp=-3" 같은 문자열
 * 출력: key(최대2), value(int)
 * 성공: 0, 실패: -1
 */
static int parse_kv(const char *line, char key_out[3], int *value_out)
{
  const char *eq = strchr(line, '=');
  if (!eq) return -1;

  int klen = (int)(eq - line);
  if (klen < 1 || klen > 2) return -1;

  for (int i = 0; i < klen; i++) {
    char c = line[i];
    if (!isalnum((unsigned char)c)) return -1; // key는 영문/숫자만 허용
    key_out[i] = c;
  }
  key_out[klen] = '\0';

  const char *vstr = eq + 1;
  if (*vstr == '\0') return -1;

  char *endptr = NULL;
  long v = strtol(vstr, &endptr, 10);

  // value 뒤에 쓰레기 문자가 있으면 실패(공백은 허용)
  while (endptr && *endptr && isspace((unsigned char)*endptr)) endptr++;
  if (endptr && *endptr != '\0') return -1;

  *value_out = (int)v;
  return 0;
}

static void handle_line(char *line)
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

/* USER CODE END 0 */

/**
  * @brief  The application entry point.
  * @retval int
  */
int main(void)
{

  /* USER CODE BEGIN 1 */

  /* USER CODE END 1 */

  /* MCU Configuration--------------------------------------------------------*/

  /* Reset of all peripherals, Initializes the Flash interface and the Systick. */
  HAL_Init();

  /* USER CODE BEGIN Init */

  /* USER CODE END Init */

  /* Configure the system clock */
  SystemClock_Config();

  /* USER CODE BEGIN SysInit */

  /* USER CODE END SysInit */

  /* Initialize all configured peripherals */
  MX_GPIO_Init();
  MX_USART2_UART_Init();

  MX_TIM3_Init();
  MX_TIM4_Init();

  /* USER CODE BEGIN 2 */
  HAL_TIM_PWM_Start(&htim3, TIM_CHANNEL_1);  // 모터 PWM (PA6)
  HAL_TIM_PWM_Start(&htim4, TIM_CHANNEL_1);  // 서보 PWM (PB6)

  Servo_Write_us(1470); HAL_Delay(500); //중심
  Servo_Write_us(1100); HAL_Delay(500);
  Servo_Write_us(1800); HAL_Delay(500);
  Servo_Write_us(1500); HAL_Delay(500);
  /* USER CODE END 2 */

  /* Infinite loop */
  /* USER CODE BEGIN WHILE */

  while (1)
  {
    uint8_t ch;
    HAL_UART_Receive(&huart2, &ch, 1, 0xFFFF); // 1바이트 블로킹 수신

    // 줄 종료 처리
    if (ch == '\r' || ch == '\n') {
      if (rx_idx > 0) {
        rx_line[rx_idx] = '\0';
        handle_line(rx_line);
        rx_idx = 0;
      }
      continue;
    }

    // 에코
    HAL_UART_Transmit(&huart2, &ch, 1, 100);

    // 버퍼 저장
    if (rx_idx < (sizeof(rx_line) - 1)) {
      rx_line[rx_idx++] = (char)ch;
    } else {
      // 오버플로우: 라인 리셋
      rx_idx = 0;
    }
  }
    /* USER CODE END WHILE */

    /* USER CODE BEGIN 3 */
  /* USER CODE END 3 */
}

/**
  * @brief System Clock Configuration
  * @retval None
  */
void SystemClock_Config(void)
{
  RCC_OscInitTypeDef RCC_OscInitStruct = {0};
  RCC_ClkInitTypeDef RCC_ClkInitStruct = {0};

  /** Initializes the RCC Oscillators according to the specified parameters
  * in the RCC_OscInitTypeDef structure.
  */
  RCC_OscInitStruct.OscillatorType = RCC_OSCILLATORTYPE_HSI;
  RCC_OscInitStruct.HSIState = RCC_HSI_ON;
  RCC_OscInitStruct.HSICalibrationValue = RCC_HSICALIBRATION_DEFAULT;
  RCC_OscInitStruct.PLL.PLLState = RCC_PLL_ON;
  RCC_OscInitStruct.PLL.PLLSource = RCC_PLLSOURCE_HSI_DIV2;
  RCC_OscInitStruct.PLL.PLLMUL = RCC_PLL_MUL16;
  if (HAL_RCC_OscConfig(&RCC_OscInitStruct) != HAL_OK)
  {
    Error_Handler();
  }

  /** Initializes the CPU, AHB and APB buses clocks
  */
  RCC_ClkInitStruct.ClockType = RCC_CLOCKTYPE_HCLK|RCC_CLOCKTYPE_SYSCLK
                              |RCC_CLOCKTYPE_PCLK1|RCC_CLOCKTYPE_PCLK2;
  RCC_ClkInitStruct.SYSCLKSource = RCC_SYSCLKSOURCE_PLLCLK;
  RCC_ClkInitStruct.AHBCLKDivider = RCC_SYSCLK_DIV1;
  RCC_ClkInitStruct.APB1CLKDivider = RCC_HCLK_DIV2;
  RCC_ClkInitStruct.APB2CLKDivider = RCC_HCLK_DIV1;

  if (HAL_RCC_ClockConfig(&RCC_ClkInitStruct, FLASH_LATENCY_2) != HAL_OK)
  {
    Error_Handler();
  }
}

/* USER CODE BEGIN 4 */

/* USER CODE END 4 */

/**
  * @brief  This function is executed in case of error occurrence.
  * @retval None
  */
void Error_Handler(void)
{
  /* USER CODE BEGIN Error_Handler_Debug */
  /* User can add his own implementation to report the HAL error return state */
  __disable_irq();
  while (1)
  {
  }
  /* USER CODE END Error_Handler_Debug */
}
#ifdef USE_FULL_ASSERT
/**
  * @brief  Reports the name of the source file and the source line number
  *         where the assert_param error has occurred.
  * @param  file: pointer to the source file name
  * @param  line: assert_param error line source number
  * @retval None
  */
void assert_failed(uint8_t *file, uint32_t line)
{
  /* USER CODE BEGIN 6 */
  /* User can add his own implementation to report the file name and line number,
     ex: printf("Wrong parameters value: file %s on line %d\r\n", file, line) */
  /* USER CODE END 6 */
}
#endif /* USE_FULL_ASSERT */

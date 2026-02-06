/*
 * comm_uart_line.c
 *
 *  Created on: Feb 3, 2026
 *      Author: SSAFY
 */


#include "comm_uart_line.h"
#include "usart.h"
#include "dma.h"
#include <string.h>

#define RX_DMA_SIZE 64
#define Q_LEN 4

static uint8_t rx_dma[RX_DMA_SIZE];

static char line_buf[COMM_UART_LINE_MAX];
static uint8_t line_idx = 0;

static char q[Q_LEN][COMM_UART_LINE_MAX];
static volatile uint8_t q_w = 0;
static volatile uint8_t q_r = 0;
static volatile uint8_t q_count = 0;

static void q_push(const char *s)
{
  if (q_count >= Q_LEN) {
    // 큐가 가득 차면 가장 오래된 것 버림
    q_r = (uint8_t)((q_r + 1) % Q_LEN);
    q_count--;
  }

  strncpy(q[q_w], s, COMM_UART_LINE_MAX);
  q[q_w][COMM_UART_LINE_MAX - 1] = '\0';

  q_w = (uint8_t)((q_w + 1) % Q_LEN);
  q_count++;
}

void comm_uart_line_init(void)
{
  line_idx = 0;
  q_w = 0;
  q_r = 0;
  q_count = 0;

  HAL_UARTEx_ReceiveToIdle_DMA(&huart2, rx_dma, sizeof(rx_dma));
  __HAL_DMA_DISABLE_IT(huart2.hdmarx, DMA_IT_HT);
}

void comm_uart_line_on_rx(uint16_t Size)
{
  for (uint16_t i = 0; i < Size; i++) {
    uint8_t ch = rx_dma[i];

    // 줄 종료 처리
    if (ch == '\r' || ch == '\n') {
      if (line_idx > 0) {
        line_buf[line_idx] = '\0';
        q_push(line_buf);
        line_idx = 0;
      }
      continue;
    }

    // 버퍼 저장
    if (line_idx < (COMM_UART_LINE_MAX - 1)) {
      line_buf[line_idx++] = (char)ch;
    } else {
      // 오버플로우: 라인 리셋
      line_idx = 0;
    }
  }

  // 다음 수신 재시작 (중요)
  HAL_UARTEx_ReceiveToIdle_DMA(&huart2, rx_dma, sizeof(rx_dma));
  __HAL_DMA_DISABLE_IT(huart2.hdmarx, DMA_IT_HT);
}

int comm_uart_line_pop(char *out, uint16_t out_len)
{
  if (out_len == 0) return 0;

  __disable_irq();
  if (q_count == 0) {
    __enable_irq();
    return 0;
  }

  strncpy(out, q[q_r], out_len);
  out[out_len - 1] = '\0';

  q_r = (uint8_t)((q_r + 1) % Q_LEN);
  q_count--;
  __enable_irq();

  return 1;
}

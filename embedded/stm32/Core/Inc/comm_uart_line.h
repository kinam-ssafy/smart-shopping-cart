/*
 * comm_uart_line.h
 *
 *  Created on: Feb 3, 2026
 *      Author: SSAFY
 */

#ifndef INC_COMM_UART_LINE_H_
#define INC_COMM_UART_LINE_H_
#ifndef COMM_UART_LINE_H
#define COMM_UART_LINE_H

#include <stdint.h>

#define COMM_UART_LINE_MAX 32

void comm_uart_line_init(void);
void comm_uart_line_on_rx(uint16_t Size);
int  comm_uart_line_pop(char *out, uint16_t out_len);

#endif



#endif /* INC_COMM_UART_LINE_H_ */

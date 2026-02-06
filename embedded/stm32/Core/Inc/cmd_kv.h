/*
 * cmd_kv.h
 *
 *  Created on: Feb 3, 2026
 *      Author: SSAFY
 */

#ifndef INC_CMD_KV_H_
#define INC_CMD_KV_H_

char* trim(char *s);
int parse_kv(const char *line, char key_out[3], int *value_out);
#endif /* INC_CMD_KV_H_ */

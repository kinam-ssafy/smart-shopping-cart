/*
 * cmd_kv.c
 *
 *  Created on: Feb 3, 2026
 *      Author: SSAFY
 */

#include "cmd_kv.h"
#include <string.h>
#include <ctype.h>
#include <stdlib.h>
char* trim(char *s)
{
  while (*s && isspace((unsigned char)*s)) s++;
  if (*s == 0) return s;

  char *end = s + strlen(s) - 1;
  while (end > s && isspace((unsigned char)*end)) end--;
  end[1] = '\0';
  return s;
}
int parse_kv(const char *line, char key_out[3], int *value_out)
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

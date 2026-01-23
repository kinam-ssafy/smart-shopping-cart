// generated from rosidl_generator_c/resource/idl__struct.h.em
// with input from rc_detection:msg/Detection.idl
// generated code does not contain a copyright notice

#ifndef RC_DETECTION__MSG__DETAIL__DETECTION__STRUCT_H_
#define RC_DETECTION__MSG__DETAIL__DETECTION__STRUCT_H_

#ifdef __cplusplus
extern "C"
{
#endif

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>


// Constants defined in the message

// Include directives for member types
// Member 'class_name'
#include "rosidl_runtime_c/string.h"

/// Struct defined in msg/Detection in the package rc_detection.
typedef struct rc_detection__msg__Detection
{
  int32_t track_id;
  rosidl_runtime_c__String class_name;
  float confidence;
  /// Bounding box in image coordinates
  int32_t x_min;
  int32_t y_min;
  int32_t x_max;
  int32_t y_max;
  /// Center point in image
  float center_x;
  float center_y;
} rc_detection__msg__Detection;

// Struct for a sequence of rc_detection__msg__Detection.
typedef struct rc_detection__msg__Detection__Sequence
{
  rc_detection__msg__Detection * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} rc_detection__msg__Detection__Sequence;

#ifdef __cplusplus
}
#endif

#endif  // RC_DETECTION__MSG__DETAIL__DETECTION__STRUCT_H_

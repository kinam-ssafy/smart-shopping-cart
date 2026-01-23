// generated from rosidl_generator_c/resource/idl__struct.h.em
// with input from rc_detection:msg/DetectionArray.idl
// generated code does not contain a copyright notice

#ifndef RC_DETECTION__MSG__DETAIL__DETECTION_ARRAY__STRUCT_H_
#define RC_DETECTION__MSG__DETAIL__DETECTION_ARRAY__STRUCT_H_

#ifdef __cplusplus
extern "C"
{
#endif

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>


// Constants defined in the message

// Include directives for member types
// Member 'header'
#include "std_msgs/msg/detail/header__struct.h"
// Member 'detections'
#include "rc_detection/msg/detail/detection__struct.h"

/// Struct defined in msg/DetectionArray in the package rc_detection.
typedef struct rc_detection__msg__DetectionArray
{
  std_msgs__msg__Header header;
  rc_detection__msg__Detection__Sequence detections;
} rc_detection__msg__DetectionArray;

// Struct for a sequence of rc_detection__msg__DetectionArray.
typedef struct rc_detection__msg__DetectionArray__Sequence
{
  rc_detection__msg__DetectionArray * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} rc_detection__msg__DetectionArray__Sequence;

#ifdef __cplusplus
}
#endif

#endif  // RC_DETECTION__MSG__DETAIL__DETECTION_ARRAY__STRUCT_H_

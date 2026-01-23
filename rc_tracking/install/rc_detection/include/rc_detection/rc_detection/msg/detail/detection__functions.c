// generated from rosidl_generator_c/resource/idl__functions.c.em
// with input from rc_detection:msg/Detection.idl
// generated code does not contain a copyright notice
#include "rc_detection/msg/detail/detection__functions.h"

#include <assert.h>
#include <stdbool.h>
#include <stdlib.h>
#include <string.h>

#include "rcutils/allocator.h"


// Include directives for member types
// Member `class_name`
#include "rosidl_runtime_c/string_functions.h"

bool
rc_detection__msg__Detection__init(rc_detection__msg__Detection * msg)
{
  if (!msg) {
    return false;
  }
  // track_id
  // class_name
  if (!rosidl_runtime_c__String__init(&msg->class_name)) {
    rc_detection__msg__Detection__fini(msg);
    return false;
  }
  // confidence
  // x_min
  // y_min
  // x_max
  // y_max
  // center_x
  // center_y
  return true;
}

void
rc_detection__msg__Detection__fini(rc_detection__msg__Detection * msg)
{
  if (!msg) {
    return;
  }
  // track_id
  // class_name
  rosidl_runtime_c__String__fini(&msg->class_name);
  // confidence
  // x_min
  // y_min
  // x_max
  // y_max
  // center_x
  // center_y
}

bool
rc_detection__msg__Detection__are_equal(const rc_detection__msg__Detection * lhs, const rc_detection__msg__Detection * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  // track_id
  if (lhs->track_id != rhs->track_id) {
    return false;
  }
  // class_name
  if (!rosidl_runtime_c__String__are_equal(
      &(lhs->class_name), &(rhs->class_name)))
  {
    return false;
  }
  // confidence
  if (lhs->confidence != rhs->confidence) {
    return false;
  }
  // x_min
  if (lhs->x_min != rhs->x_min) {
    return false;
  }
  // y_min
  if (lhs->y_min != rhs->y_min) {
    return false;
  }
  // x_max
  if (lhs->x_max != rhs->x_max) {
    return false;
  }
  // y_max
  if (lhs->y_max != rhs->y_max) {
    return false;
  }
  // center_x
  if (lhs->center_x != rhs->center_x) {
    return false;
  }
  // center_y
  if (lhs->center_y != rhs->center_y) {
    return false;
  }
  return true;
}

bool
rc_detection__msg__Detection__copy(
  const rc_detection__msg__Detection * input,
  rc_detection__msg__Detection * output)
{
  if (!input || !output) {
    return false;
  }
  // track_id
  output->track_id = input->track_id;
  // class_name
  if (!rosidl_runtime_c__String__copy(
      &(input->class_name), &(output->class_name)))
  {
    return false;
  }
  // confidence
  output->confidence = input->confidence;
  // x_min
  output->x_min = input->x_min;
  // y_min
  output->y_min = input->y_min;
  // x_max
  output->x_max = input->x_max;
  // y_max
  output->y_max = input->y_max;
  // center_x
  output->center_x = input->center_x;
  // center_y
  output->center_y = input->center_y;
  return true;
}

rc_detection__msg__Detection *
rc_detection__msg__Detection__create()
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  rc_detection__msg__Detection * msg = (rc_detection__msg__Detection *)allocator.allocate(sizeof(rc_detection__msg__Detection), allocator.state);
  if (!msg) {
    return NULL;
  }
  memset(msg, 0, sizeof(rc_detection__msg__Detection));
  bool success = rc_detection__msg__Detection__init(msg);
  if (!success) {
    allocator.deallocate(msg, allocator.state);
    return NULL;
  }
  return msg;
}

void
rc_detection__msg__Detection__destroy(rc_detection__msg__Detection * msg)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (msg) {
    rc_detection__msg__Detection__fini(msg);
  }
  allocator.deallocate(msg, allocator.state);
}


bool
rc_detection__msg__Detection__Sequence__init(rc_detection__msg__Detection__Sequence * array, size_t size)
{
  if (!array) {
    return false;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  rc_detection__msg__Detection * data = NULL;

  if (size) {
    data = (rc_detection__msg__Detection *)allocator.zero_allocate(size, sizeof(rc_detection__msg__Detection), allocator.state);
    if (!data) {
      return false;
    }
    // initialize all array elements
    size_t i;
    for (i = 0; i < size; ++i) {
      bool success = rc_detection__msg__Detection__init(&data[i]);
      if (!success) {
        break;
      }
    }
    if (i < size) {
      // if initialization failed finalize the already initialized array elements
      for (; i > 0; --i) {
        rc_detection__msg__Detection__fini(&data[i - 1]);
      }
      allocator.deallocate(data, allocator.state);
      return false;
    }
  }
  array->data = data;
  array->size = size;
  array->capacity = size;
  return true;
}

void
rc_detection__msg__Detection__Sequence__fini(rc_detection__msg__Detection__Sequence * array)
{
  if (!array) {
    return;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();

  if (array->data) {
    // ensure that data and capacity values are consistent
    assert(array->capacity > 0);
    // finalize all array elements
    for (size_t i = 0; i < array->capacity; ++i) {
      rc_detection__msg__Detection__fini(&array->data[i]);
    }
    allocator.deallocate(array->data, allocator.state);
    array->data = NULL;
    array->size = 0;
    array->capacity = 0;
  } else {
    // ensure that data, size, and capacity values are consistent
    assert(0 == array->size);
    assert(0 == array->capacity);
  }
}

rc_detection__msg__Detection__Sequence *
rc_detection__msg__Detection__Sequence__create(size_t size)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  rc_detection__msg__Detection__Sequence * array = (rc_detection__msg__Detection__Sequence *)allocator.allocate(sizeof(rc_detection__msg__Detection__Sequence), allocator.state);
  if (!array) {
    return NULL;
  }
  bool success = rc_detection__msg__Detection__Sequence__init(array, size);
  if (!success) {
    allocator.deallocate(array, allocator.state);
    return NULL;
  }
  return array;
}

void
rc_detection__msg__Detection__Sequence__destroy(rc_detection__msg__Detection__Sequence * array)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (array) {
    rc_detection__msg__Detection__Sequence__fini(array);
  }
  allocator.deallocate(array, allocator.state);
}

bool
rc_detection__msg__Detection__Sequence__are_equal(const rc_detection__msg__Detection__Sequence * lhs, const rc_detection__msg__Detection__Sequence * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  if (lhs->size != rhs->size) {
    return false;
  }
  for (size_t i = 0; i < lhs->size; ++i) {
    if (!rc_detection__msg__Detection__are_equal(&(lhs->data[i]), &(rhs->data[i]))) {
      return false;
    }
  }
  return true;
}

bool
rc_detection__msg__Detection__Sequence__copy(
  const rc_detection__msg__Detection__Sequence * input,
  rc_detection__msg__Detection__Sequence * output)
{
  if (!input || !output) {
    return false;
  }
  if (output->capacity < input->size) {
    const size_t allocation_size =
      input->size * sizeof(rc_detection__msg__Detection);
    rcutils_allocator_t allocator = rcutils_get_default_allocator();
    rc_detection__msg__Detection * data =
      (rc_detection__msg__Detection *)allocator.reallocate(
      output->data, allocation_size, allocator.state);
    if (!data) {
      return false;
    }
    // If reallocation succeeded, memory may or may not have been moved
    // to fulfill the allocation request, invalidating output->data.
    output->data = data;
    for (size_t i = output->capacity; i < input->size; ++i) {
      if (!rc_detection__msg__Detection__init(&output->data[i])) {
        // If initialization of any new item fails, roll back
        // all previously initialized items. Existing items
        // in output are to be left unmodified.
        for (; i-- > output->capacity; ) {
          rc_detection__msg__Detection__fini(&output->data[i]);
        }
        return false;
      }
    }
    output->capacity = input->size;
  }
  output->size = input->size;
  for (size_t i = 0; i < input->size; ++i) {
    if (!rc_detection__msg__Detection__copy(
        &(input->data[i]), &(output->data[i])))
    {
      return false;
    }
  }
  return true;
}

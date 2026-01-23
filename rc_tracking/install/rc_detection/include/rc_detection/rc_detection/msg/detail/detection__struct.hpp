// generated from rosidl_generator_cpp/resource/idl__struct.hpp.em
// with input from rc_detection:msg/Detection.idl
// generated code does not contain a copyright notice

#ifndef RC_DETECTION__MSG__DETAIL__DETECTION__STRUCT_HPP_
#define RC_DETECTION__MSG__DETAIL__DETECTION__STRUCT_HPP_

#include <algorithm>
#include <array>
#include <cstdint>
#include <memory>
#include <string>
#include <vector>

#include "rosidl_runtime_cpp/bounded_vector.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


#ifndef _WIN32
# define DEPRECATED__rc_detection__msg__Detection __attribute__((deprecated))
#else
# define DEPRECATED__rc_detection__msg__Detection __declspec(deprecated)
#endif

namespace rc_detection
{

namespace msg
{

// message struct
template<class ContainerAllocator>
struct Detection_
{
  using Type = Detection_<ContainerAllocator>;

  explicit Detection_(rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->track_id = 0l;
      this->class_name = "";
      this->confidence = 0.0f;
      this->x_min = 0l;
      this->y_min = 0l;
      this->x_max = 0l;
      this->y_max = 0l;
      this->center_x = 0.0f;
      this->center_y = 0.0f;
    }
  }

  explicit Detection_(const ContainerAllocator & _alloc, rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : class_name(_alloc)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->track_id = 0l;
      this->class_name = "";
      this->confidence = 0.0f;
      this->x_min = 0l;
      this->y_min = 0l;
      this->x_max = 0l;
      this->y_max = 0l;
      this->center_x = 0.0f;
      this->center_y = 0.0f;
    }
  }

  // field types and members
  using _track_id_type =
    int32_t;
  _track_id_type track_id;
  using _class_name_type =
    std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>>;
  _class_name_type class_name;
  using _confidence_type =
    float;
  _confidence_type confidence;
  using _x_min_type =
    int32_t;
  _x_min_type x_min;
  using _y_min_type =
    int32_t;
  _y_min_type y_min;
  using _x_max_type =
    int32_t;
  _x_max_type x_max;
  using _y_max_type =
    int32_t;
  _y_max_type y_max;
  using _center_x_type =
    float;
  _center_x_type center_x;
  using _center_y_type =
    float;
  _center_y_type center_y;

  // setters for named parameter idiom
  Type & set__track_id(
    const int32_t & _arg)
  {
    this->track_id = _arg;
    return *this;
  }
  Type & set__class_name(
    const std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>> & _arg)
  {
    this->class_name = _arg;
    return *this;
  }
  Type & set__confidence(
    const float & _arg)
  {
    this->confidence = _arg;
    return *this;
  }
  Type & set__x_min(
    const int32_t & _arg)
  {
    this->x_min = _arg;
    return *this;
  }
  Type & set__y_min(
    const int32_t & _arg)
  {
    this->y_min = _arg;
    return *this;
  }
  Type & set__x_max(
    const int32_t & _arg)
  {
    this->x_max = _arg;
    return *this;
  }
  Type & set__y_max(
    const int32_t & _arg)
  {
    this->y_max = _arg;
    return *this;
  }
  Type & set__center_x(
    const float & _arg)
  {
    this->center_x = _arg;
    return *this;
  }
  Type & set__center_y(
    const float & _arg)
  {
    this->center_y = _arg;
    return *this;
  }

  // constant declarations

  // pointer types
  using RawPtr =
    rc_detection::msg::Detection_<ContainerAllocator> *;
  using ConstRawPtr =
    const rc_detection::msg::Detection_<ContainerAllocator> *;
  using SharedPtr =
    std::shared_ptr<rc_detection::msg::Detection_<ContainerAllocator>>;
  using ConstSharedPtr =
    std::shared_ptr<rc_detection::msg::Detection_<ContainerAllocator> const>;

  template<typename Deleter = std::default_delete<
      rc_detection::msg::Detection_<ContainerAllocator>>>
  using UniquePtrWithDeleter =
    std::unique_ptr<rc_detection::msg::Detection_<ContainerAllocator>, Deleter>;

  using UniquePtr = UniquePtrWithDeleter<>;

  template<typename Deleter = std::default_delete<
      rc_detection::msg::Detection_<ContainerAllocator>>>
  using ConstUniquePtrWithDeleter =
    std::unique_ptr<rc_detection::msg::Detection_<ContainerAllocator> const, Deleter>;
  using ConstUniquePtr = ConstUniquePtrWithDeleter<>;

  using WeakPtr =
    std::weak_ptr<rc_detection::msg::Detection_<ContainerAllocator>>;
  using ConstWeakPtr =
    std::weak_ptr<rc_detection::msg::Detection_<ContainerAllocator> const>;

  // pointer types similar to ROS 1, use SharedPtr / ConstSharedPtr instead
  // NOTE: Can't use 'using' here because GNU C++ can't parse attributes properly
  typedef DEPRECATED__rc_detection__msg__Detection
    std::shared_ptr<rc_detection::msg::Detection_<ContainerAllocator>>
    Ptr;
  typedef DEPRECATED__rc_detection__msg__Detection
    std::shared_ptr<rc_detection::msg::Detection_<ContainerAllocator> const>
    ConstPtr;

  // comparison operators
  bool operator==(const Detection_ & other) const
  {
    if (this->track_id != other.track_id) {
      return false;
    }
    if (this->class_name != other.class_name) {
      return false;
    }
    if (this->confidence != other.confidence) {
      return false;
    }
    if (this->x_min != other.x_min) {
      return false;
    }
    if (this->y_min != other.y_min) {
      return false;
    }
    if (this->x_max != other.x_max) {
      return false;
    }
    if (this->y_max != other.y_max) {
      return false;
    }
    if (this->center_x != other.center_x) {
      return false;
    }
    if (this->center_y != other.center_y) {
      return false;
    }
    return true;
  }
  bool operator!=(const Detection_ & other) const
  {
    return !this->operator==(other);
  }
};  // struct Detection_

// alias to use template instance with default allocator
using Detection =
  rc_detection::msg::Detection_<std::allocator<void>>;

// constant definitions

}  // namespace msg

}  // namespace rc_detection

#endif  // RC_DETECTION__MSG__DETAIL__DETECTION__STRUCT_HPP_

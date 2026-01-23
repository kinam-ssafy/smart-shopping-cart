// generated from rosidl_generator_cpp/resource/idl__builder.hpp.em
// with input from rc_detection:msg/DetectionArray.idl
// generated code does not contain a copyright notice

#ifndef RC_DETECTION__MSG__DETAIL__DETECTION_ARRAY__BUILDER_HPP_
#define RC_DETECTION__MSG__DETAIL__DETECTION_ARRAY__BUILDER_HPP_

#include <algorithm>
#include <utility>

#include "rc_detection/msg/detail/detection_array__struct.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


namespace rc_detection
{

namespace msg
{

namespace builder
{

class Init_DetectionArray_detections
{
public:
  explicit Init_DetectionArray_detections(::rc_detection::msg::DetectionArray & msg)
  : msg_(msg)
  {}
  ::rc_detection::msg::DetectionArray detections(::rc_detection::msg::DetectionArray::_detections_type arg)
  {
    msg_.detections = std::move(arg);
    return std::move(msg_);
  }

private:
  ::rc_detection::msg::DetectionArray msg_;
};

class Init_DetectionArray_header
{
public:
  Init_DetectionArray_header()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_DetectionArray_detections header(::rc_detection::msg::DetectionArray::_header_type arg)
  {
    msg_.header = std::move(arg);
    return Init_DetectionArray_detections(msg_);
  }

private:
  ::rc_detection::msg::DetectionArray msg_;
};

}  // namespace builder

}  // namespace msg

template<typename MessageType>
auto build();

template<>
inline
auto build<::rc_detection::msg::DetectionArray>()
{
  return rc_detection::msg::builder::Init_DetectionArray_header();
}

}  // namespace rc_detection

#endif  // RC_DETECTION__MSG__DETAIL__DETECTION_ARRAY__BUILDER_HPP_

// generated from rosidl_generator_cpp/resource/idl__builder.hpp.em
// with input from rc_detection:msg/Detection.idl
// generated code does not contain a copyright notice

#ifndef RC_DETECTION__MSG__DETAIL__DETECTION__BUILDER_HPP_
#define RC_DETECTION__MSG__DETAIL__DETECTION__BUILDER_HPP_

#include <algorithm>
#include <utility>

#include "rc_detection/msg/detail/detection__struct.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


namespace rc_detection
{

namespace msg
{

namespace builder
{

class Init_Detection_center_y
{
public:
  explicit Init_Detection_center_y(::rc_detection::msg::Detection & msg)
  : msg_(msg)
  {}
  ::rc_detection::msg::Detection center_y(::rc_detection::msg::Detection::_center_y_type arg)
  {
    msg_.center_y = std::move(arg);
    return std::move(msg_);
  }

private:
  ::rc_detection::msg::Detection msg_;
};

class Init_Detection_center_x
{
public:
  explicit Init_Detection_center_x(::rc_detection::msg::Detection & msg)
  : msg_(msg)
  {}
  Init_Detection_center_y center_x(::rc_detection::msg::Detection::_center_x_type arg)
  {
    msg_.center_x = std::move(arg);
    return Init_Detection_center_y(msg_);
  }

private:
  ::rc_detection::msg::Detection msg_;
};

class Init_Detection_y_max
{
public:
  explicit Init_Detection_y_max(::rc_detection::msg::Detection & msg)
  : msg_(msg)
  {}
  Init_Detection_center_x y_max(::rc_detection::msg::Detection::_y_max_type arg)
  {
    msg_.y_max = std::move(arg);
    return Init_Detection_center_x(msg_);
  }

private:
  ::rc_detection::msg::Detection msg_;
};

class Init_Detection_x_max
{
public:
  explicit Init_Detection_x_max(::rc_detection::msg::Detection & msg)
  : msg_(msg)
  {}
  Init_Detection_y_max x_max(::rc_detection::msg::Detection::_x_max_type arg)
  {
    msg_.x_max = std::move(arg);
    return Init_Detection_y_max(msg_);
  }

private:
  ::rc_detection::msg::Detection msg_;
};

class Init_Detection_y_min
{
public:
  explicit Init_Detection_y_min(::rc_detection::msg::Detection & msg)
  : msg_(msg)
  {}
  Init_Detection_x_max y_min(::rc_detection::msg::Detection::_y_min_type arg)
  {
    msg_.y_min = std::move(arg);
    return Init_Detection_x_max(msg_);
  }

private:
  ::rc_detection::msg::Detection msg_;
};

class Init_Detection_x_min
{
public:
  explicit Init_Detection_x_min(::rc_detection::msg::Detection & msg)
  : msg_(msg)
  {}
  Init_Detection_y_min x_min(::rc_detection::msg::Detection::_x_min_type arg)
  {
    msg_.x_min = std::move(arg);
    return Init_Detection_y_min(msg_);
  }

private:
  ::rc_detection::msg::Detection msg_;
};

class Init_Detection_confidence
{
public:
  explicit Init_Detection_confidence(::rc_detection::msg::Detection & msg)
  : msg_(msg)
  {}
  Init_Detection_x_min confidence(::rc_detection::msg::Detection::_confidence_type arg)
  {
    msg_.confidence = std::move(arg);
    return Init_Detection_x_min(msg_);
  }

private:
  ::rc_detection::msg::Detection msg_;
};

class Init_Detection_class_name
{
public:
  explicit Init_Detection_class_name(::rc_detection::msg::Detection & msg)
  : msg_(msg)
  {}
  Init_Detection_confidence class_name(::rc_detection::msg::Detection::_class_name_type arg)
  {
    msg_.class_name = std::move(arg);
    return Init_Detection_confidence(msg_);
  }

private:
  ::rc_detection::msg::Detection msg_;
};

class Init_Detection_track_id
{
public:
  Init_Detection_track_id()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_Detection_class_name track_id(::rc_detection::msg::Detection::_track_id_type arg)
  {
    msg_.track_id = std::move(arg);
    return Init_Detection_class_name(msg_);
  }

private:
  ::rc_detection::msg::Detection msg_;
};

}  // namespace builder

}  // namespace msg

template<typename MessageType>
auto build();

template<>
inline
auto build<::rc_detection::msg::Detection>()
{
  return rc_detection::msg::builder::Init_Detection_track_id();
}

}  // namespace rc_detection

#endif  // RC_DETECTION__MSG__DETAIL__DETECTION__BUILDER_HPP_

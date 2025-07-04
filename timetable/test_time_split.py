#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试时间拆分和合并功能
"""

from datetime import datetime, timedelta

def test_time_split():
    """测试时间拆分功能"""
    print("=== 测试时间拆分功能 ===")
    
    test_times = [
        "00:00:00",
        "12:30:45", 
        "23:59:59",
        "08:15:30",
        "16:45:12"
    ]
    
    for time_str in test_times:
        try:
            time_parts = time_str.split(':')
            if len(time_parts) == 3:
                hour = time_parts[0]
                minute = time_parts[1]
                second = time_parts[2]
                print(f"原始时间: {time_str} -> 时:{hour}, 分:{minute}, 秒:{second}")
            else:
                print(f"时间格式错误: {time_str}")
        except Exception as e:
            print(f"解析错误: {time_str} - {e}")

def test_time_merge():
    """测试时间合并功能"""
    print("\n=== 测试时间合并功能 ===")
    
    test_cases = [
        ("00", "00", "00"),
        ("12", "30", "45"),
        ("23", "59", "59"),
        ("08", "15", "30"),
        ("16", "45", "12")
    ]
    
    for hour, minute, second in test_cases:
        try:
            merged_time = f"{hour}:{minute}:{second}"
            # 验证时间格式
            datetime.strptime(merged_time, "%H:%M:%S")
            print(f"合并时间: 时:{hour}, 分:{minute}, 秒:{second} -> {merged_time} ✓")
        except ValueError as e:
            print(f"时间格式无效: 时:{hour}, 分:{minute}, 秒:{second} -> {e} ✗")

def test_time_validation():
    """测试时间验证功能"""
    print("\n=== 测试时间验证功能 ===")
    
    test_cases = [
        ("00:00:00", True),
        ("12:30:45", True),
        ("23:59:59", True),
        ("24:00:00", False),  # 无效
        ("12:60:00", False),  # 无效
        ("12:30:60", False),  # 无效
        ("abc:def:ghi", False),  # 无效
        ("", False),  # 无效
    ]
    
    for time_str, expected_valid in test_cases:
        try:
            datetime.strptime(time_str, "%H:%M:%S")
            is_valid = True
        except ValueError:
            is_valid = False
        
        status = "✓" if is_valid == expected_valid else "✗"
        print(f"时间: {time_str} -> 有效:{is_valid} (期望:{expected_valid}) {status}")

def test_time_calculation():
    """测试时间计算功能"""
    print("\n=== 测试时间计算功能 ===")
    
    test_cases = [
        ("12:00:00", "13:00:00", 1.0),  # 1小时
        ("12:00:00", "12:30:00", 0.5),  # 30分钟
        ("12:00:00", "12:00:30", 0.008),  # 30秒
        ("23:59:59", "00:00:00", 0.000),  # 跨天（简化处理）
    ]
    
    for start_str, end_str, expected_hours in test_cases:
        try:
            start = datetime.strptime(start_str, "%H:%M:%S")
            end = datetime.strptime(end_str, "%H:%M:%S")
            
            # 处理跨天的情况
            if end < start:
                end = end + timedelta(days=1)
            
            duration = (end - start).total_seconds() / 3600
            duration = round(duration, 3)
            
            print(f"时间: {start_str} - {end_str} -> {duration}小时 (期望: {expected_hours})")
        except ValueError as e:
            print(f"计算错误: {start_str} - {end_str} -> {e}")

if __name__ == "__main__":
    test_time_split()
    test_time_merge()
    test_time_validation()
    test_time_calculation()
    print("\n=== 测试完成 ===") 
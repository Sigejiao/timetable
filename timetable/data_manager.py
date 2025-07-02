import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import glob

class DataManager:
    """数据管理类，负责读取、解析和保存时间数据"""
    
    def __init__(self, data_dir: str = "../time_data"):
        """
        初始化数据管理器
        
        Args:
            data_dir: 数据文件目录路径
        """
        self.data_dir = data_dir
        self._data_cache = {}  # 缓存已读取的数据
        self._ensure_data_dir()
    
    def _ensure_data_dir(self):
        """确保数据目录存在"""
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
    
    def get_all_dates(self) -> List[str]:
        """
        获取所有有数据的日期列表
        
        Returns:
            日期列表，格式为 'YYYY-MM-DD'
        """
        pattern = os.path.join(self.data_dir, "timedata_*.json")
        files = glob.glob(pattern)
        dates = []
        
        for file_path in files:
            filename = os.path.basename(file_path)
            # 从文件名提取日期
            if filename.startswith("timedata_") and filename.endswith(".json"):
                date_str = filename[9:-5]  # 去掉 "timedata_" 和 ".json"
                try:
                    # 验证日期格式
                    datetime.strptime(date_str, "%Y-%m-%d")
                    dates.append(date_str)
                except ValueError:
                    continue
        
        return sorted(dates)
    
    def load_day_data(self, date: str) -> List[Dict]:
        """
        加载指定日期的数据
        
        Args:
            date: 日期字符串，格式为 'YYYY-MM-DD'
            
        Returns:
            该日期的数据列表，每个元素包含 time 和 event
        """
        if date in self._data_cache:
            return self._data_cache[date]
        
        file_path = os.path.join(self.data_dir, f"timedata_{date}.json")
        
        if not os.path.exists(file_path):
            return []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self._data_cache[date] = data
                return data
        except (json.JSONDecodeError, FileNotFoundError) as e:
            print(f"加载数据文件 {file_path} 时出错: {e}")
            return []
    
    def load_all_data(self) -> Dict[str, List[Dict]]:
        """
        加载所有日期的数据
        
        Returns:
            字典，键为日期，值为该日期的数据列表
        """
        all_data = {}
        dates = self.get_all_dates()
        
        for date in dates:
            all_data[date] = self.load_day_data(date)
        
        return all_data
    
    def save_day_data(self, date: str, data: List[Dict]) -> bool:
        """
        保存指定日期的数据
        
        Args:
            date: 日期字符串，格式为 'YYYY-MM-DD'
            data: 要保存的数据列表
            
        Returns:
            保存是否成功
        """
        try:
            file_path = os.path.join(self.data_dir, f"timedata_{date}.json")
            
            # 确保数据按时间排序
            sorted_data = sorted(data, key=lambda x: x.get('time', '00:00:00'))
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(sorted_data, f, ensure_ascii=False, indent=2)
            
            # 更新缓存
            self._data_cache[date] = sorted_data
            return True
            
        except Exception as e:
            print(f"保存数据文件时出错: {e}")
            return False
    
    def parse_time_events(self, date: str) -> List[Dict]:
        """
        解析指定日期的时间事件，计算每个事件的持续时间
        
        Args:
            date: 日期字符串
            
        Returns:
            包含起止时间和事件名的列表
        """
        raw_data = self.load_day_data(date)
        if not raw_data:
            return []
        
        events = []
        
        for i in range(len(raw_data)):
            current_event = raw_data[i]
            start_time = current_event['time']
            
            # 计算结束时间
            if i + 1 < len(raw_data):
                end_time = raw_data[i + 1]['time']
            else:
                # 最后一个事件，结束时间设为 24:00:00
                end_time = "24:00:00"
            
            events.append({
                'start_time': start_time,
                'end_time': end_time,
                'event': current_event['event'],
                'duration': self._calculate_duration(start_time, end_time)
            })
        
        return events
    
    def _calculate_duration(self, start_time: str, end_time: str) -> float:
        """
        计算两个时间点之间的持续时间（小时）
        
        Args:
            start_time: 开始时间，格式为 'HH:MM:SS'
            end_time: 结束时间，格式为 'HH:MM:SS'
            
        Returns:
            持续时间（小时）
        """
        try:
            start = datetime.strptime(start_time, "%H:%M:%S")
            end = datetime.strptime(end_time, "%H:%M:%S")
            
            # 如果结束时间小于开始时间，说明跨天了
            if end < start:
                end = datetime.strptime("24:00:00", "%H:%M:%S")
            
            duration = end - start
            return duration.total_seconds() / 3600  # 转换为小时
            
        except ValueError:
            return 0.0
    
    def get_today_data(self) -> List[Dict]:
        """
        获取今天的数据
        
        Returns:
            今天的数据列表
        """
        today = datetime.now().strftime("%Y-%m-%d")
        return self.load_day_data(today)
    
    def get_recent_dates(self, days: int = 7) -> List[str]:
        """
        获取最近几天的日期列表
        
        Args:
            days: 天数
            
        Returns:
            日期列表
        """
        all_dates = self.get_all_dates()
        if not all_dates:
            return []
        
        # 获取最近的日期
        recent_dates = all_dates[-days:] if len(all_dates) >= days else all_dates
        return recent_dates

# 测试代码
if __name__ == "__main__":
    # 测试数据管理器
    dm = DataManager()
    
    print("所有日期:", dm.get_all_dates())
    
    # 测试加载数据
    for date in dm.get_all_dates():
        print(f"\n日期: {date}")
        data = dm.load_day_data(date)
        print(f"原始数据: {data}")
        
        events = dm.parse_time_events(date)
        print(f"解析后事件: {events}") 
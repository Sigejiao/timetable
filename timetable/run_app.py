#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
时间管理可视化应用启动脚本
"""

import sys
import os

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def main():
    """主函数"""
    try:
        # 导入必要的模块
        from data_manager import DataManager
        from app import app
        
        print("=" * 50)
        print("时间管理可视化应用")
        print("=" * 50)
        
        # 初始化数据管理器
        data_manager = DataManager()
        
        # 检查数据文件
        dates = data_manager.get_all_dates()
        print(f"找到 {len(dates)} 个数据文件:")
        for date in dates:
            print(f"  - {date}")
        
        if not dates:
            print("警告：未找到任何数据文件！")
            print("请确保 time_data/ 目录下有 timedata_YYYY-MM-DD.json 格式的文件")
        
        print("\n启动Web应用...")
        print("应用将在浏览器中打开: http://127.0.0.1:8050")
        print("按 Ctrl+C 停止应用")
        print("=" * 50)
        
        # 启动应用
        app.run(debug=True, host='127.0.0.1', port=8050)
        
    except ImportError as e:
        print(f"导入错误: {e}")
        print("请确保已安装所需依赖:")
        print("pip install dash plotly pandas")
        return 1
    except Exception as e:
        print(f"启动应用时出错: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 
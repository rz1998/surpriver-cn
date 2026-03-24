#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
A股异动检测引擎 - Surpriver-CN
基于Isolation Forest算法检测A股异常波动

用法示例:
python detection_engine_cn.py --top_n 25 --min_volume 10000 --data_granularity_minutes 60 --history_to_use 14 --is_load_from_dictionary 0 --data_dictionary_path 'dictionaries/cn_data_dict.npy' --is_save_dictionary 1 --is_test 0 --future_bars 0
"""

import os
import sys
import ta
import json
import math
import collections
import numpy as np
import pandas as pd
import datetime as dt
import matplotlib.pyplot as plt
from scipy.stats import linregress
from sklearn.ensemble import IsolationForest
import warnings

warnings.filterwarnings("ignore")

# 设置字体(兼容Linux服务器环境)
try:
    plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'WenQuanYi Micro Hei', 'SimHei', 'Arial Unicode MS']
    plt.rcParams['axes.unicode_minus'] = False
except:
    pass
# plt.style.use('seaborn-white')  # disabled
plt.rc('grid', linestyle="dotted", color='#a0a0a0')

# 导入A股数据引擎
from data_loader_cn import DataEngineCN

# 命令行参数解析
import argparse
argParser = argparse.ArgumentParser(description='A股异动检测 - Surpriver-CN')
argParser.add_argument("--top_n", type=int, default=25, help="显示的TOP N异常股票数量")
argParser.add_argument("--min_volume", type=int, default=10000, help="最低成交量过滤")
argParser.add_argument("--history_to_use", type=int, default=7, help="用于检测的历史K线数")
argParser.add_argument("--is_load_from_dictionary", type=int, default=0, help="是否从字典加载数据")
argParser.add_argument("--data_dictionary_path", type=str, default="dictionaries/cn_data_dict.npy", help="数据字典路径")
argParser.add_argument("--is_save_dictionary", type=int, default=1, help="是否保存数据字典")
argParser.add_argument("--data_granularity_minutes", type=int, default=60, help="数据粒度(分钟)")
argParser.add_argument("--is_test", type=int, default=0, help="是否测试模式")
argParser.add_argument("--future_bars", type=int, default=25, help="测试用未来K线数")
argParser.add_argument("--volatility_filter", type=float, default=0.05, help="波动率过滤阈值")
argParser.add_argument("--output_format", type=str, default="CLI", help="输出格式: CLI 或 JSON")
argParser.add_argument("--stock_list", type=str, default="stocks_cn.txt", help="股票列表文件名")

args = argParser.parse_args()

top_n = args.top_n
min_volume = args.min_volume
history_to_use = args.history_to_use
is_load_from_dictionary = args.is_load_from_dictionary
data_dictionary_path = args.data_dictionary_path
is_save_dictionary = args.is_save_dictionary
data_granularity_minutes = args.data_granularity_minutes
is_test = args.is_test
future_bars = args.future_bars
volatility_filter = args.volatility_filter
output_format = args.output_format.upper()
stock_list = args.stock_list


class ArgChecker:
    """参数检查器"""
    def __init__(self):
        print("Checking arguments...")
        self.check_arguments()
    
    def check_arguments(self):
        granularity_list = [1, 5, 10, 15, 30, 60]
        directory_path = str(os.path.dirname(os.path.abspath(__file__)))
        
        if data_granularity_minutes not in granularity_list:
            print(f"Data granularity must be one of: {granularity_list}")
            sys.exit()
        
        if is_test == 1 and future_bars < 2:
            print("Test mode requires future_bars > 2")
            sys.exit()
        
        if output_format not in ["CLI", "JSON"]:
            print("Output format must be CLI or JSON")
            sys.exit()
        
        if not os.path.exists(directory_path + f'/stocks/{stock_list}'):
            print(f"Stock list file not found: stocks/{stock_list}")
            sys.exit()


class SurpriverCN:
    """A股异动检测主类"""
    
    def __init__(self):
        print("Surpriver-CN initializing...")
        self.TOP_PREDICTIONS = top_n
        self.HISTORY_TO_USE = history_to_use
        self.MINIMUM_VOLUME = min_volume
        self.IS_LOAD_FROM_DICTIONARY = is_load_from_dictionary
        self.DATA_DICTIONARY_PATH = data_dictionary_path
        self.IS_SAVE_DICTIONARY = is_save_dictionary
        self.DATA_GRANULARITY_MINUTES = data_granularity_minutes
        self.IS_TEST = is_test
        self.FUTURE_BARS = future_bars
        self.VOLATILITY_FILTER = volatility_filter
        self.OUTPUT_FORMAT = output_format
        self.STOCK_LIST = stock_list
        
        # 创建数据引擎
        self.dataEngine = DataEngineCN(
            self.HISTORY_TO_USE, self.DATA_GRANULARITY_MINUTES,
            self.IS_SAVE_DICTIONARY, self.IS_LOAD_FROM_DICTIONARY, self.DATA_DICTIONARY_PATH,
            self.MINIMUM_VOLUME, self.IS_TEST, self.FUTURE_BARS,
            self.VOLATILITY_FILTER, self.STOCK_LIST
        )
    
    @staticmethod
    def is_nan(obj):
        """检查是否为NaN"""
        return obj != obj
    
    @staticmethod
    def calculate_percentage_change(old, new):
        """计算百分比变化"""
        if old == 0:
            return 0
        return ((new - old) * 100) / old
    
    @staticmethod
    def parse_large_values(value):
        """格式化大数字"""
        if value < 10000:
            return str(round(value, 2))
        elif value < 100000000:
            return f"{round(value / 10000, 2)}W"
        else:
            return f"{round(value / 100000000, 2)}Y"
    
    def calculate_volume_changes(self, historical_price):
        """计算成交量变化"""
        volume = list(historical_price["Volume"])
        dates = list(historical_price["Datetime"])
        dates = [str(date) for date in dates]
        
        # 按日期分组
        volume_by_date = collections.defaultdict(list)
        for j in range(len(volume)):
            date = dates[j].split(" ")[0]
            volume_by_date[date].append(volume[j])
        
        for key in volume_by_date:
            volume_by_date[key] = np.sum(volume_by_date[key])
        
        all_dates = list(reversed(sorted(volume_by_date.keys())))
        
        if len(all_dates) < 2:
            return dates[0] if dates else "N/A", "N/A", "N/A", "N/A"
        
        latest_date = all_dates[0]
        latest_data_point = list(reversed(dates))[0]
        
        today_volume = volume_by_date[latest_date]
        avg_vol_5d = np.mean([volume_by_date.get(d, 0) for d in all_dates[1:6]])
        avg_vol_20d = np.mean([volume_by_date.get(d, 0) for d in all_dates[1:20]])
        
        return latest_data_point, self.parse_large_values(today_volume), \
               self.parse_large_values(avg_vol_5d), self.parse_large_values(avg_vol_20d)
    
    def calculate_recent_volatility(self, historical_price):
        """计算近期波动率"""
        close_price = list(historical_price["Close"])
        vol_5bars = np.std(close_price[-5:]) if len(close_price) >= 5 else 0
        vol_20bars = np.std(close_price[-20:]) if len(close_price) >= 20 else vol_5bars
        vol_all = np.std(close_price)
        return vol_5bars, vol_20bars, vol_all
    
    def calculate_future_performance(self, future_data):
        """计算未来表现"""
        CLOSE_INDEX = 4
        if len(future_data) < 2:
            return 0, 0
        
        price_at_alert = future_data[0][CLOSE_INDEX]
        prices_future = [item[CLOSE_INDEX] for item in future_data[1:]]
        prices_future = [p for p in prices_future if p != 0]
        
        if not prices_future or price_at_alert == 0:
            return 0, 0
        
        total_change = sum([abs(self.calculate_percentage_change(price_at_alert, p)) for p in prices_future])
        future_volatility = np.std(prices_future)
        
        return total_change, future_volatility
    
    def get_stock_display(self, symbol):
        """获取股票显示名称"""
        market = symbol.split(".")[-1] if "." in symbol else ""
        code = symbol.split(".")[0] if "." in symbol else symbol
        markets = {"SH": "[SH]", "SZ": "[SZ]", "BJ": "[BJ]"}
        return f"{markets.get(market, '')}{code}"
    
    def find_anomalies(self):
        """主检测函数"""
        # 收集所有股票数据
        if self.IS_LOAD_FROM_DICTIONARY == 0:
            features, historical_price_info, future_prices, symbol_names = \
                self.dataEngine.collect_data_for_all_tickers()
        else:
            features, historical_price_info, future_prices, symbol_names = \
                self.dataEngine.load_data_from_dictionary()
        
        if not features:
            print("No valid data collected. Please check stock list and network connection.")
            return
        
        print(f"\nAnalyzing {len(features)} stocks...")
        
        # Isolation Forest 异常检测
        detector = IsolationForest(n_estimators=100, random_state=0, contamination=0.1)
        detector.fit(features)
        predictions = detector.decision_function(features)
        
        # 组装结果
        predictions_with_data = [[predictions[i], symbol_names[i], 
                                   historical_price_info[i], future_prices[i]] 
                                  for i in range(len(predictions))]
        predictions_with_data = list(sorted(predictions_with_data))
        
        results = []
        
        print("\n" + "=" * 60)
        print("A-Share Anomaly Detection Results - Surpriver-CN")
        print("=" * 60)
        
        for item in predictions_with_data[:self.TOP_PREDICTIONS]:
            prediction, symbol, historical_price, future_price = item
            
            latest_date, today_volume, avg_vol_5d, avg_vol_20d = self.calculate_volume_changes(historical_price)
            vol_5, vol_20, _ = self.calculate_recent_volatility(historical_price)
            
            if avg_vol_5d is None or vol_5 is None:
                continue
            
            stock_display = self.get_stock_display(symbol)
            
            if self.IS_TEST == 0:
                if self.OUTPUT_FORMAT == "CLI":
                    sep = "-" * 40
                    print(f"""
[Stock] {stock_display}
  Last Update: {latest_date}
  Anomaly Score: {prediction:.3f} (lower = more anomalous)
  Today's Volume: {today_volume}
  Avg Volume 5d: {avg_vol_5d}
  Avg Volume 20d: {avg_vol_20d}
  Volatility 5 bars: {vol_5:.4f}
  Volatility 20 bars: {vol_20:.4f}
{sep}""")
                
                results.append({
                    'code': symbol,
                    'display': stock_display,
                    'last_update': latest_date,
                    'anomaly_score': round(prediction, 3),
                    'today_volume': today_volume,
                    'avg_vol_5d': avg_vol_5d,
                    'avg_vol_20d': avg_vol_20d,
                    'vol_5': round(vol_5, 4),
                    'vol_20': round(vol_20, 4)
                })
            else:
                future_change, _ = self.calculate_future_performance(future_price)
                
                if self.OUTPUT_FORMAT == "CLI":
                    sep = "-" * 40
                    print(f"""
[Stock] {stock_display}
  Anomaly Score: {prediction:.3f}
  Future Change: {future_change:.2f}%
{sep}""")
                
                results.append({
                    'code': symbol,
                    'display': stock_display,
                    'anomaly_score': round(prediction, 3),
                    'future_change': round(future_change, 2)
                })
        
        if self.OUTPUT_FORMAT == "JSON":
            self.store_results(results)
        
        if self.IS_TEST == 1:
            self.calculate_future_stats(predictions_with_data)
    
    def store_results(self, results):
        """保存结果到JSON文件"""
        today = dt.datetime.today().strftime('%Y-%m-%d')
        prefix = "results_cn" if self.IS_TEST == 0 else "results_cn_test"
        filename = f'{prefix}_{today}.json'
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        print(f"\nResults saved to: {filename}")
    
    def calculate_future_stats(self, predictions_with_data):
        """计算测试统计"""
        future_changes = []
        anomaly_scores = []
        hist_vols = []
        future_vols = []
        
        for item in predictions_with_data:
            prediction, symbol, historical_price, future_price = item
            future_change, fut_vol = self.calculate_future_performance(future_price)
            _, _, hist_vol = self.calculate_recent_volatility(historical_price)
            
            if abs(future_change) > 250 or self.is_nan(future_change) or self.is_nan(prediction):
                continue
            
            future_changes.append(future_change)
            anomaly_scores.append(prediction)
            hist_vols.append(hist_vol)
            future_vols.append(fut_vol)
        
        if not future_changes:
            return
        
        correlation = np.corrcoef(anomaly_scores, future_changes)[0, 1]
        anomalous_changes = np.mean([future_changes[i] for i in range(len(future_changes)) 
                                     if anomaly_scores[i] < 0])
        normal_changes = np.mean([future_changes[i] for i in range(len(future_changes)) 
                                  if anomaly_scores[i] >= 0])
        
        print("\n" + "=" * 60)
        print("Test Statistics")
        print("=" * 60)
        print(f"Correlation (anomaly vs future change): {correlation:.3f}")
        print(f"Avg future change for anomalous stocks: {anomalous_changes:.2f}%")
        print(f"Avg future change for normal stocks: {normal_changes:.2f}%")
        
        # 绑图
        colors = ['#c91414' if anomaly_scores[i] < 0 else '#035AA6' for i in range(len(anomaly_scores))]
        anomalous_mask = np.array([1 if s < 0 else 0 for s in anomaly_scores])
        
        plt.figure(figsize=(10, 6))
        plt.scatter(np.array(anomaly_scores)[anomalous_mask == 1], 
                   np.array(future_changes)[anomalous_mask == 1], 
                   marker='v', color='#c91414', label='Anomalous')
        plt.scatter(np.array(anomaly_scores)[anomalous_mask == 0], 
                   np.array(future_changes)[anomalous_mask == 0], 
                   marker='P', color='#035AA6', label='Normal')
        plt.axvline(x=0, linestyle='--', color='#848484')
        plt.xlabel("Anomaly Score", fontsize=14)
        plt.ylabel("Future Absolute Change", fontsize=14)
        plt.legend(fontsize=12)
        plt.title("A-Share Anomaly Detection - Future Performance", fontsize=14)
        plt.grid()
        plt.tight_layout()
        plt.show()


if __name__ == "__main__":
    # 检查参数
    argumentChecker = ArgChecker()
    
    # 创建并运行检测器
    supriver_cn = SurpriverCN()
    supriver_cn.find_anomalies()

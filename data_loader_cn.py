# A股数据加载引擎 - 基于AKShare
import os
import sys
import ta
import math
import json
import collections
import numpy as np
import pandas as pd
import datetime as dt
from tqdm import tqdm
from scipy.stats import linregress
from feature_generator import TAEngine
import warnings

warnings.filterwarnings("ignore")

# 尝试导入AKShare
try:
    import akshare as ak
    AKSHARE_AVAILABLE = True
except ImportError:
    AKSHARE_AVAILABLE = False
    print("警告: AKShare 未安装，将尝试安装...")
    os.system(f"{sys.executable} -m pip install akshare -q")


class DataEngineCN:
    """A股数据引擎，使用AKShare获取中国A股数据"""
    
    def __init__(self, history_to_use, data_granularity_minutes, is_save_dict, is_load_dict, 
                 dict_path, min_volume_filter, is_test, future_bars_for_testing, 
                 volatility_filter, stocks_list, market="auto"):
        print("A股数据引擎初始化中...")
        self.DATA_GRANULARITY_MINUTES = data_granularity_minutes
        self.IS_SAVE_DICT = is_save_dict
        self.IS_LOAD_DICT = is_load_dict
        self.DICT_PATH = dict_path
        self.VOLUME_FILTER = min_volume_filter
        self.FUTURE_FOR_TESTING = future_bars_for_testing
        self.IS_TEST = is_test
        self.VOLATILITY_THRESHOLD = volatility_filter
        self.MARKET = market  # auto, sh, sz, bj
        
        # 股票列表
        self.directory_path = str(os.path.dirname(os.path.abspath(__file__)))
        self.stocks_file_path = self.directory_path + f"/stocks/{stocks_list}"
        self.stocks_list = []
        
        # 加载股票列表
        self.load_stocks_from_file()
        
        # 加载技术指标引擎
        self.taEngine = TAEngine(history_to_use=history_to_use)
        
        # 数据字典
        self.features_dictionary_for_all_symbols = {}
        self.stock_data_length = []
        
        # 确保AKShare可用
        if not AKSHARE_AVAILABLE:
            import subprocess
            subprocess.check_call([sys.executable, "-m", "pip", "install", "akshare", "-q"])
            global ak
            import akshare as ak
            AKSHARE_AVAILABLE = True

    def load_stocks_from_file(self):
        """从文件加载股票代码列表"""
        print("正在加载股票列表...")
        with open(self.stocks_file_path, "r", encoding="utf-8") as f:
            stocks_list = f.readlines()
        stocks_list = [str(item).strip("\n").strip() for item in stocks_list]
        stocks_list = [s for s in stocks_list if s and not s.startswith("#")]
        
        # 自动识别市场后缀
        processed_stocks = []
        for stock in stocks_list:
            stock = stock.strip()
            if not stock:
                continue
            # 已经是完整代码（带后缀）
            if stock.endswith(".SH") or stock.endswith(".SZ") or stock.endswith(".BJ"):
                processed_stocks.append(stock)
            # 纯数字代码，自动判断市场
            elif stock.isdigit():
                code = stock.zfill(6)
                if code.startswith(("6", "5", "9")):
                    processed_stocks.append(f"{code}.SH")  # 上海
                elif code.startswith(("0", "3")):
                    processed_stocks.append(f"{code}.SZ")  # 深圳
                elif code.startswith(("4", "8")):
                    processed_stocks.append(f"{code}.BJ")  # 北京
                else:
                    processed_stocks.append(f"{code}.SH")  # 默认上海
            else:
                processed_stocks.append(stock)
        
        stocks_list = list(sorted(set(processed_stocks)))
        print(f"股票总数: {len(stocks_list)}")
        self.stocks_list = stocks_list

    def get_most_frequent_key(self, input_list):
        counter = collections.Counter(input_list)
        counter_keys = list(counter.keys())
        return counter_keys[0]

    def get_data(self, symbol):
        """获取A股数据"""
        # 确定时间周期
        if self.DATA_GRANULARITY_MINUTES == 1:
            period = "7"
        elif self.DATA_GRANULARITY_MINUTES <= 5:
            period = "30"
        elif self.DATA_GRANULARITY_MINUTES <= 15:
            period = "60"
        elif self.DATA_GRANULARITY_MINUTES <= 30:
            period = "120"
        else:
            period = "240"
        
        try:
            # 转换时间粒度为AKShare格式
            if self.DATA_GRANULARITY_MINUTES == 1:
                period_str = f"{period}d"
            else:
                period_str = f"{period}d"
            
            # 获取数据
            stock_prices = ak.stock_zh_a_hist(
                symbol=symbol.split(".")[0],  # 去掉后缀
                period="1",  # 1分钟
                start_date=(dt.datetime.now() - dt.timedelta(days=int(period))).strftime("%Y%m%d"),
                end_date=dt.datetime.now().strftime("%Y%m%d"),
                adjust="qfq"
            )
            
            if stock_prices is None or len(stock_prices) == 0:
                return [], [], True
            
            # 重命名列
            stock_prices = stock_prices.rename(columns={
                "时间": "Datetime",
                "开盘": "Open",
                "最高": "High",
                "最低": "Low",
                "收盘": "Close",
                "成交量": "Volume",
                "成交额": "Amount"
            })
            
            # 转换时间格式
            stock_prices["Datetime"] = pd.to_datetime(stock_prices["Datetime"])
            
            # 选择需要的列
            stock_prices = stock_prices[['Datetime', 'Open', 'High', 'Low', 'Close', 'Volume']]
            stock_prices = stock_prices.sort_values("Datetime")
            
            # 限制数据长度（AKShare免费版限制）
            max_bars = 800
            if len(stock_prices) > max_bars:
                stock_prices = stock_prices.tail(max_bars)
            
            data_length = len(stock_prices)
            self.stock_data_length.append(data_length)
            
            # 检查数据完整性
            if len(self.stock_data_length) > 5:
                most_frequent_key = self.get_most_frequent_key(self.stock_data_length)
                if data_length != most_frequent_key:
                    return [], [], True
            
            if self.IS_TEST == 1:
                stock_prices_list = stock_prices.values.tolist()
                stock_prices_list = stock_prices_list[1:]
                future_prices_list = stock_prices_list[-(self.FUTURE_FOR_TESTING + 1):]
                historical_prices = pd.DataFrame(stock_prices_list[:-self.FUTURE_FOR_TESTING])
                historical_prices.columns = ['Datetime', 'Open', 'High', 'Low', 'Close', 'Volume']
            else:
                stock_prices_list = stock_prices.values.tolist()
                stock_prices_list = stock_prices_list[1:]
                historical_prices = pd.DataFrame(stock_prices_list)
                historical_prices.columns = ['Datetime', 'Open', 'High', 'Low', 'Close', 'Volume']
                future_prices_list = []
            
            if len(stock_prices_list) == 0:
                return [], [], True
                
        except Exception as e:
            print(f"获取 {symbol} 数据失败: {e}")
            return [], [], True
        
        return historical_prices, future_prices_list, False

    def calculate_volatility(self, stock_price_data):
        """计算波动率"""
        close_prices = stock_price_data['Close'].values.tolist()
        close_prices = [float(item) for item in close_prices if item != 0]
        if len(close_prices) < 2:
            return 0
        volatility = np.std(close_prices)
        return volatility

    def collect_data_for_all_tickers(self):
        """为所有股票收集数据"""
        print("正在为所有股票加载数据...")
        
        features = []
        symbol_names = []
        historical_price_info = []
        future_price_info = []
        
        for i in tqdm(range(len(self.stocks_list))):
            symbol = self.stocks_list[i]
            try:
                stock_price_data, future_prices, not_found = self.get_data(symbol)
                
                if not not_found:
                    volatility = self.calculate_volatility(stock_price_data)
                    
                    # 过滤低波动股票
                    if volatility < self.VOLATILITY_THRESHOLD:
                        continue
                    
                    features_dictionary = self.taEngine.get_technical_indicators(stock_price_data)
                    feature_list = self.taEngine.get_features(features_dictionary)
                    
                    # 保存到字典
                    self.features_dictionary_for_all_symbols[symbol] = {
                        "features": features_dictionary, 
                        "current_prices": stock_price_data, 
                        "future_prices": future_prices
                    }
                    
                    # 每100支股票保存一次
                    if len(self.features_dictionary_for_all_symbols) % 100 == 0 and self.IS_SAVE_DICT == 1:
                        np.save(self.DICT_PATH, self.features_dictionary_for_all_symbols)
                    
                    if np.isnan(feature_list).any():
                        continue
                    
                    # 检查成交量
                    average_volume = np.mean(list(stock_price_data["Volume"])[-30:])
                    if average_volume < self.VOLUME_FILTER:
                        continue
                    
                    features.append(feature_list)
                    symbol_names.append(symbol)
                    historical_price_info.append(stock_price_data)
                    future_price_info.append(future_prices)
                    
            except Exception as e:
                print(f"处理 {symbol} 时出错: {e}")
                continue
        
        # 清理异常数据
        features, historical_price_info, future_price_info, symbol_names = \
            self.remove_bad_data(features, historical_price_info, future_price_info, symbol_names)
        
        return features, historical_price_info, future_price_info, symbol_names

    def load_data_from_dictionary(self):
        """从字典加载数据"""
        print("从字典加载数据")
        dictionary_data = np.load(self.DICT_PATH, allow_pickle=True).item()
        
        features = []
        symbol_names = []
        historical_price_info = []
        future_price_info = []
        
        for symbol in dictionary_data:
            feature_list = self.taEngine.get_features(dictionary_data[symbol]["features"])
            current_prices = dictionary_data[symbol]["current_prices"]
            future_prices = dictionary_data[symbol]["future_prices"]
            
            if np.isnan(feature_list).any():
                continue
            
            features.append(feature_list)
            symbol_names.append(symbol)
            historical_price_info.append(current_prices)
            future_price_info.append(future_prices)
        
        features, historical_price_info, future_price_info, symbol_names = \
            self.remove_bad_data(features, historical_price_info, future_price_info, symbol_names)
        
        return features, historical_price_info, future_price_info, symbol_names

    def remove_bad_data(self, features, historical_price_info, future_price_info, symbol_names):
        """移除异常数据"""
        length_dictionary = collections.Counter([len(feature) for feature in features])
        length_dictionary = list(length_dictionary.keys())
        most_common_length = length_dictionary[0]
        
        filtered_features, filtered_historical_price = [], []
        filtered_future_prices, filtered_symbols = [], []
        
        for i in range(len(features)):
            if len(features[i]) == most_common_length:
                filtered_features.append(features[i])
                filtered_symbols.append(symbol_names[i])
                filtered_historical_price.append(historical_price_info[i])
                filtered_future_prices.append(future_price_info[i])
        
        return filtered_features, filtered_historical_price, filtered_future_prices, filtered_symbols

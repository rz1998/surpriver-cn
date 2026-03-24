# A股数据加载引擎 - 支持AKShare和Tushare
import os
import sys
import math
import collections
import numpy as np
import pandas as pd
import datetime as dt
from tqdm import tqdm
from scipy.stats import linregress
from feature_generator import TAEngine
import warnings

warnings.filterwarnings("ignore")

# 加载环境变量
def load_env():
    """从.env文件加载环境变量"""
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
    if os.path.exists(env_path):
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()

load_env()

# 获取数据源配置
DATA_SOURCE = os.environ.get('DATA_SOURCE', 'akshare').lower()
TUSHARE_TOKEN = os.environ.get('TUSHARE_TOKEN', '')

# 尝试导入数据源库
AKSHARE_AVAILABLE = False
TUSHARE_AVAILABLE = False

try:
    import akshare as ak
    AKSHARE_AVAILABLE = True
except ImportError:
    pass

try:
    import tushare as ts
    TUSHARE_AVAILABLE = True
except ImportError:
    pass


class DataSourceFactory:
    """数据源工厂类"""
    
    @staticmethod
    def get_data_source():
        """获取数据源实例"""
        if DATA_SOURCE == 'tushare':
            if not TUSHARE_AVAILABLE:
                raise ImportError("Tushare not installed. Run: uv pip install tushare")
            if not TUSHARE_TOKEN:
                raise ValueError("TUSHARE_TOKEN not configured in .env file")
            return TushareDataSource()
            import subprocess
            subprocess.check_call([sys.executable, "-m", "pip", "install", "tushare", "-q"])
            import tushare as ts
            TUSHARE_AVAILABLE = True
            return TushareDataSource()
        else:  # 默认akshare
            if not AKSHARE_AVAILABLE:
                raise ImportError("AKShare not installed. Run: uv pip install akshare")
            return AKShareDataSource()


class AKShareDataSource:
    """AKShare数据源"""
    
    def get_data(self, symbol, period, days):
        """获取A股数据 - AKShare"""
        end_time = dt.datetime.now()
        start_time = end_time - dt.timedelta(days=days)
        
        # 转换symbol（去掉后缀）
        code = symbol.split(".")[0]
        
        # 转换period格式
        period_map = {1: "1", 5: "5", 15: "15", 30: "30", 60: "60"}
        period_str = period_map.get(period, "60")
        
        try:
            df = ak.stock_zh_a_hist_min_em(
                symbol=code,
                period=period_str,
                start_date=start_time.strftime("%Y%m%d %H:%M:%S"),
                end_date=end_time.strftime("%Y%m%d %H:%M:%S"),
                adjust="qfq"
            )
            
            if df is None or len(df) == 0:
                return None
            
            # 重命名列
            df = df.rename(columns={
                "时间": "Datetime",
                "开盘": "Open",
                "收盘": "Close",
                "最高": "High",
                "最低": "Low",
                "成交量": "Volume",
                "成交额": "Amount",
                "均价": "AvgPrice"
            })
            
            df["Datetime"] = pd.to_datetime(df["Datetime"])
            df = df[['Datetime', 'Open', 'High', 'Low', 'Close', 'Volume']]
            df = df.sort_values("Datetime")
            
            return df
        except Exception as e:
            print(f"AKShare获取{symbol}数据失败: {e}")
            return None


class TushareDataSource:
    """Tushare数据源"""
    
    def __init__(self):
        self.pro = ts.pro(TUSHARE_TOKEN)
    
    def get_data(self, symbol, period, days):
        """获取A股数据 - Tushare"""
        end_date = dt.datetime.now().strftime("%Y%m%d")
        start_date = (dt.datetime.now() - dt.timedelta(days=days)).strftime("%Y%m%d")
        
        # 转换symbol
        code = symbol.split(".")[0]
        
        # 判断市场
        if code.startswith(("6", "5", "9")):
            ts_code = f"{code}.SH"
        else:
            ts_code = f"{code}.SZ"
        
        # 转换period到Tushare格式
        period_map = {
            1: "1min",
            5: "5min", 
            15: "15min",
            30: "30min",
            60: "60min"
        }
        freq = period_map.get(period, "60min")
        
        try:
            df = self.pro.ts_bar(
                ts_code=ts_code,
                freq=freq,
                start_date=start_date,
                end_date=end_date,
                adjust="qfq"
            )
            
            if df is None or len(df) == 0:
                return None
            
            # 重命名列
            df = df.rename(columns={
                "trade_date": "Datetime",
                "open": "Open",
                "high": "High",
                "low": "Low",
                "close": "Close",
                "vol": "Volume",
                "amount": "Amount"
            })
            
            df["Datetime"] = pd.to_datetime(df["Datetime"])
            df = df[['Datetime', 'Open', 'High', 'Low', 'Close', 'Volume']]
            df = df.sort_values("Datetime")
            
            return df
        except Exception as e:
            print(f"Tushare获取{symbol}数据失败: {e}")
            return None


class DataEngineCN:
    """A股数据引擎"""
    
    def __init__(self, history_to_use, data_granularity_minutes, is_save_dict, is_load_dict, 
                 dict_path, min_volume_filter, is_test, future_bars_for_testing, 
                 volatility_filter, stocks_list, market="auto"):
        print(f"A股数据引擎初始化中... (数据源: {DATA_SOURCE})")
        
        self.DATA_GRANULARITY_MINUTES = data_granularity_minutes
        self.IS_SAVE_DICT = is_save_dict
        self.IS_LOAD_DICT = is_load_dict
        self.DICT_PATH = dict_path
        self.VOLUME_FILTER = min_volume_filter
        self.FUTURE_FOR_TESTING = future_bars_for_testing
        self.IS_TEST = is_test
        self.VOLATILITY_THRESHOLD = volatility_filter
        self.MARKET = market
        
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
        
        # 初始化数据源
        self.data_source = DataSourceFactory.get_data_source()
        
        # 确定获取数据的天数
        self.days = self._get_days_for_period(data_granularity_minutes)
    
    def _get_days_for_period(self, minutes):
        """根据周期确定获取数据的天数"""
        if minutes == 1:
            return 7
        elif minutes <= 5:
            return 30
        elif minutes <= 15:
            return 60
        elif minutes <= 30:
            return 120
        else:
            return 240

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
            if stock.endswith(".SH") or stock.endswith(".SZ") or stock.endswith(".BJ"):
                processed_stocks.append(stock)
            elif stock.isdigit():
                code = stock.zfill(6)
                if code.startswith(("6", "5", "9")):
                    processed_stocks.append(f"{code}.SH")
                elif code.startswith(("0", "3")):
                    processed_stocks.append(f"{code}.SZ")
                elif code.startswith(("4", "8")):
                    processed_stocks.append(f"{code}.BJ")
                else:
                    processed_stocks.append(f"{code}.SH")
            else:
                processed_stocks.append(stock)
        
        stocks_list = list(sorted(set(processed_stocks)))
        print(f"股票总数: {len(stocks_list)}")
        self.stocks_list = stocks_list

    def get_most_frequent_key(self, input_list):
        counter = collections.Counter(input_list)
        counter_keys = list(counter.keys())
        return counter_keys[0] if counter_keys else 0

    def get_data(self, symbol):
        """获取A股数据"""
        try:
            df = self.data_source.get_data(
                symbol=symbol,
                period=self.DATA_GRANULARITY_MINUTES,
                days=self.days
            )
            
            if df is None or len(df) == 0:
                return [], [], True
            
            # 限制数据长度
            max_bars = 800
            if len(df) > max_bars:
                df = df.tail(max_bars)
            
            data_length = len(df)
            self.stock_data_length.append(data_length)
            
            # 检查数据完整性
            if len(self.stock_data_length) > 5:
                most_frequent_key = self.get_most_frequent_key(self.stock_data_length)
                if data_length != most_frequent_key:
                    return [], [], True
            
            if self.IS_TEST == 1:
                stock_prices_list = df.values.tolist()
                stock_prices_list = stock_prices_list[1:]
                future_prices_list = stock_prices_list[-(self.FUTURE_FOR_TESTING + 1):]
                historical_prices = pd.DataFrame(stock_prices_list[:-self.FUTURE_FOR_TESTING])
                historical_prices.columns = ['Datetime', 'Open', 'High', 'Low', 'Close', 'Volume']
            else:
                stock_prices_list = df.values.tolist()
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
        return np.std(close_prices)

    def collect_data_for_all_tickers(self):
        """为所有股票收集数据"""
        print(f"正在为所有股票加载数据 (数据源: {DATA_SOURCE})...")
        
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
                    
                    if volatility < self.VOLATILITY_THRESHOLD:
                        continue
                    
                    features_dictionary = self.taEngine.get_technical_indicators(stock_price_data)
                    feature_list = self.taEngine.get_features(features_dictionary)
                    
                    self.features_dictionary_for_all_symbols[symbol] = {
                        "features": features_dictionary, 
                        "current_prices": stock_price_data, 
                        "future_prices": future_prices
                    }
                    
                    if len(self.features_dictionary_for_all_symbols) % 100 == 0 and self.IS_SAVE_DICT == 1:
                        np.save(self.DICT_PATH, self.features_dictionary_for_all_symbols)
                    
                    if np.isnan(feature_list).any():
                        continue
                    
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
        if features:
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
        
        if features:
            features, historical_price_info, future_price_info, symbol_names = \
                self.remove_bad_data(features, historical_price_info, future_price_info, symbol_names)
        
        return features, historical_price_info, future_price_info, symbol_names

    def remove_bad_data(self, features, historical_price_info, future_price_info, symbol_names):
        """移除异常数据"""
        if not features:
            return [], [], [], []
            
        length_dictionary = collections.Counter([len(feature) for feature in features])
        length_dictionary = list(length_dictionary.keys())
        
        if not length_dictionary:
            return [], [], [], []
            
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

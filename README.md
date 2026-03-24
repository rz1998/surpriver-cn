# Surpriver-CN

> 🇨🇳 A股异动检测 - 基于Isolation Forest机器学习算法

**完全由AI改造自 [tradynamics/surpriver](https://github.com/tradynamics/surpriver)，专为A股市场设计。**

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)

## 项目说明

本项目是对 [tradynamics/surpriver](https://github.com/tradynamics/surpriver) 的AI自动化改造版本，原项目专注于美股异动检测。本版本针对中国A股市场进行了深度适配：

- **数据源**：Yahoo Finance → AKShare / Tushare（可选）
- **市场支持**：美股 → 沪深北交所全支持
- **代码体系**：美股代码（AAPL）→ A股代码（600000.SH）
- **输出语言**：英文 → 中英双语

### 核心功能

- 🔍 **异动检测**：Isolation Forest 算法识别异常波动股票
- 📊 **技术指标**：RSI、Stochastics、CCI、EOM等
- 📈 **成交量分析**：今日量能与历史均量对比
- 🎯 **波动率过滤**：过滤低波动股票，聚焦活跃标的
- 📝 **测试模式**：验证策略有效性

## 技术栈

| 类别 | 技术 |
|------|------|
| 数据获取 | AKShare / Tushare（可选）|
| 技术分析 | ta-lib |
| 数据处理 | Pandas, NumPy, SciPy |
| 机器学习 | Scikit-learn (Isolation Forest) |
| 可视化 | Matplotlib |

## 数据源配置

项目支持两个数据源，通过 `.env` 文件切换：

### 方式一：AKShare（默认，免费）

```bash
# .env 文件
DATA_SOURCE=akshare
```

无需配置，直接使用。但需要能访问东方财富接口。

### 方式二：Tushare（推荐，更稳定）

```bash
# .env 文件
DATA_SOURCE=tushare
TUSHARE_TOKEN=your_tushare_token_here
```

**申请Tushare Token：**
1. 打开 https://tushare.pro/register 注册账号
2. 申请 Token：https://tushare.pro/document/88
3. 将 Token 填入 `.env` 文件

### 配置示例

```bash
# 复制模板
cp .env.template .env

# 编辑配置
nano .env
```

```ini
# .env
DATA_SOURCE=tushare
TUSHARE_TOKEN=your_token_here
```

## 安装

```bash
# 克隆项目
git clone https://github.com/rz1998/surpriver-cn.git
cd surpriver-cn

# 创建虚拟环境（推荐）
uv venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows

# 安装依赖（根据数据源选择）
uv pip install akshare ta numpy pandas scipy scikit-learn matplotlib tqdm
# 或
uv pip install tushare ta numpy pandas scipy scikit-learn matplotlib tqdm
```

## 快速开始

### 1. 配置数据源

```bash
cp .env.template .env
# 编辑 .env 选择数据源并填入 Token（如果是 Tushare）
```

### 2. 准备股票列表

编辑 `stocks/stocks_cn.txt`，支持格式：
```
600000  # 浦发银行
600036  # 招商银行
000001  # 平安银行
300760  # 迈瑞医疗
430047.BJ  # 北交所
```

### 3. 运行检测

```bash
# 检测异动股票
python detection_engine_cn.py \
    --top_n 25 \
    --min_volume 10000 \
    --data_granularity_minutes 60 \
    --history_to_use 14 \
    --stock_list stocks_cn.txt

# 从缓存加载（再次运行）
python detection_engine_cn.py \
    --top_n 25 \
    --min_volume 10000 \
    --data_granularity_minutes 60 \
    --history_to_use 14 \
    --is_load_from_dictionary 1 \
    --data_dictionary_path 'dictionaries/cn_data_dict.npy'
```

### 4. 测试模式

```bash
# 测试历史表现
python detection_engine_cn.py \
    --top_n 25 \
    --min_volume 10000 \
    --data_granularity_minutes 60 \
    --history_to_use 14 \
    --is_load_from_dictionary 0 \
    --is_save_dictionary 1 \
    --is_test 1 \
    --future_bars 25
```

## 参数说明

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `--top_n` | 25 | 显示异动评分最高的N只股票 |
| `--min_volume` | 10000 | 最低成交量过滤（手） |
| `--data_granularity_minutes` | 60 | K线周期（分钟） |
| `--history_to_use` | 14 | 用于检测的历史K线数 |
| `--is_load_from_dictionary` | 0 | 是否从缓存加载 |
| `--data_dictionary_path` | `dictionaries/cn_data_dict.npy` | 缓存路径 |
| `--is_save_dictionary` | 1 | 是否保存数据缓存 |
| `--is_test` | 0 | 是否启用测试模式 |
| `--future_bars` | 25 | 测试用未来K线数 |
| `--output_format` | CLI | 输出格式（CLI/JSON） |
| `--stock_list` | `stocks_cn.txt` | 股票列表文件 |

## 股票代码说明

| 市场 | 代码前缀 | 后缀示例 |
|------|----------|----------|
| 上海主板 | 6xx xxx | 600000.SH |
| 深圳主板 | 0xx xxx | 000001.SZ |
| 创业板 | 300 xxx | 300760.SZ |
| 北交所 | 43x/83x | 430047.BJ |

## 项目结构

```
surpriver-cn/
├── data_loader_cn.py      # A股数据加载（支持AKShare/Tushare）
├── detection_engine_cn.py  # 主检测引擎
├── feature_generator.py    # 技术指标生成
├── requirements.txt        # 依赖
├── .env.template         # 环境变量模板
├── stocks/
│   └── stocks_cn.txt     # A股股票列表示例
├── dictionaries/          # 数据缓存
└── figures/              # 图表输出
```

## 注意事项

1. **数据源选择**：Tushare更稳定但需要Token；AKShare免费但依赖网络环境
2. **数据限制**：AKShare免费版有数据量限制，高频交易建议付费数据源
3. **市场兼容性**：仅支持A股，不支持港股、美股
4. **时间延迟**：实时数据可能有15分钟延迟
5. **异动≠涨跌**：异动检测只识别异常波动，不预测方向

## 原项目

- [tradynamics/surpriver](https://github.com/tradynamics/surpriver) - 美股版本

## License

基于 GPL v3，继承自 [tradynamics/surpriver](https://github.com/tradynamics/surpriver)

---

**🤖 本项目由AI（MiniMax-M2.7）基于原始surpriver项目完全自动化改造完成，专为A股市场设计。**

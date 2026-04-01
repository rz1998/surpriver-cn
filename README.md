# Surpriver-CN

> 🇨🇳 A股异动检测 — 基于 Isolation Forest 算法

**专为A股市场设计的异动股票检测工具**，[原项目](https://github.com/tradytics/surpriver) 为美股版本。

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)

---

## 目录

- [项目简介](#项目简介)
- [核心功能](#核心功能)
- [技术栈](#技术栈)
- [环境要求](#环境要求)
- [安装](#安装)
- [⚡ 中国网络环境最佳实践](#-中国网络环境最佳实践)
- [数据源配置](#数据源配置)
- [快速开始](#快速开始)
- [参数说明](#参数说明)
- [股票代码说明](#股票代码说明)
- [项目结构](#项目结构)
- [注意事项](#注意事项)
- [原项目](#原项目)

---

## 项目简介

Surpriver-CN 是对 [tradytics/surpriver](https://github.com/tradytics/surpriver) 的AI自动化改造版本，原项目专注于美股异动检测。本版本针对中国A股市场进行了深度适配：

| 对比项 | 原项目 | 本项目 |
|--------|--------|--------|
| 数据源 | Yahoo Finance | AKShare / Tushare |
| 市场 | 美股 | 沪深北交所全支持 |
| 代码体系 | AAPL | 600000.SH |

### 算法原理

Surpriver 基于 **Isolation Forest（隔离森林）** 算法，通过分析以下特征来检测异常：

- 📊 **成交量异常**：今日成交量与历史均量的对比
- 📈 **价格波动异常**：短期与长期波动率的差异
- 🔍 **技术指标异常**：RSI、Stochastic、CCI、EOM等指标的非典型模式

---

## 核心功能

- 🔍 **异动检测**：Isolation Forest 算法识别异常波动股票
- 📊 **技术指标**：RSI、Stochastics、CCI、EOM等
- 📈 **成交量分析**：今日量能与历史均量对比
- 🎯 **波动率过滤**：过滤低波动股票，聚焦活跃标的
- 📝 **测试模式**：验证策略历史表现

---

## 技术栈

| 类别 | 技术 |
|------|------|
| 数据获取 | AKShare / Tushare（可选）|
| 技术分析 | ta-lib |
| 数据处理 | Pandas, NumPy, SciPy |
| 机器学习 | Scikit-learn (Isolation Forest) |
| 可视化 | Matplotlib |

---

## 环境要求

- Python >= 3.8
- Git
- UV 或 pip（推荐使用 UV）

---

## 安装

### 1. 安装 Git

<details open>
<summary><b>Linux (Ubuntu/Debian)</b></summary>

```bash
sudo apt update
sudo apt install git
git --version
```

</details>

<details>
<summary><b>Linux (CentOS/RHEL)</b></summary>

```bash
sudo yum install git
git --version
```

</details>

<details>
<summary><b>Windows</b></summary>

1. 下载 [Git for Windows](https://gitforwindows.org/)
2. 运行安装程序，建议勾选"Add Git to PATH"
3. 打开 PowerShell 验证：

```powershell
git --version
```

</details>

### 2. 安装 UV (Python 包管理器)

<details open>
<summary><b>Linux / macOS</b></summary>

```bash
# 安装 UV
curl -LsSf https://astral.sh/uv/install.sh | sh

# 刷新环境变量
source ~/.bashrc

# 验证
uv --version
```

</details>

<details>
<summary><b>Windows</b></summary>

```powershell
# 使用 PowerShell 安装
irm https://astral.sh/uv/install.ps1 | iex

# 验证
uv --version
```

</details>

### 3. 克隆项目

<details open>
<summary><b>Linux / macOS / Windows (Git Bash / WSL)</b></summary>

```bash
git clone https://github.com/rz1998/surpriver-cn.git
cd surpriver-cn
```

</details>

### 4. 创建虚拟环境

<details open>
<summary><b>Linux / macOS</b></summary>

```bash
uv venv .venv
source .venv/bin/activate
```

</details>

<details>
<summary><b>Windows</b></summary>

```powershell
uv venv .venv
.venv\Scripts\activate
```

</details>

### 5. 安装依赖

<details open>
<summary><b>Linux / macOS / Windows</b></summary>

```bash
uv pip install -r requirements.txt
```

</details>

> **提示**：如果 `uv pip` 速度慢，可使用 `pip install -r requirements.txt` 替代

---

## ⚡ 中国网络环境最佳实践

> **推荐安装方式**（避免网络超时、下载失败）

<details open>
<summary><b>点击查看详情</b></summary>

```bash
# 1. 使用 pip + 国内镜像安装依赖
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 2. 如果 pip 速度慢，试试 uv（国内镜像）
pip install uv -i https://pypi.tuna.tsinghua.edu.cn/simple
uv venv .venv
source .venv/bin/activate
uv pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 3. 数据源推荐 Tushare（比 AKShare 更稳定）
#    注册地址：https://tushare.pro/register
```

</details>

---

## 数据源配置

### 1. 复制环境变量模板

<details open>
<summary><b>Linux / macOS</b></summary>

```bash
cp .env.template .env
```

</details>

<details>
<summary><b>Windows</b></summary>

```powershell
copy .env.template .env
```

</details>

### 2. 选择数据源并配置

编辑 `.env` 文件：

```ini
# .env

# 方式一：AKShare（默认，免费）
DATA_SOURCE=akshare

# 方式二：Tushare（推荐，更稳定）
DATA_SOURCE=tushare
TUSHARE_TOKEN=your_tushare_token_here
```

### 数据源对比

| 数据源 | 优点 | 缺点 |
|--------|------|------|
| AKShare | 免费，无需配置 | 可能有访问限制 |
| Tushare | 更稳定，数据更全 | 需要注册申请 Token |

### 申请 Tushare Token

1. 打开 https://tushare.pro/register 注册账号
2. 申请 Token：https://tushare.pro/document/88
3. 将 Token 填入 `.env` 文件的 `TUSHARE_TOKEN` 字段

---

## 快速开始

### 检测异动股票

<details open>
<summary><b>Linux / macOS / Windows</b></summary>

```bash
# 自动获取全A股列表并检测（推荐）
python detection_engine_cn.py --auto_fetch_stocks

# 指定股票列表检测
python detection_engine_cn.py --stock_list stocks/stocks_cn.txt

# 使用缓存数据（再次运行更快）
python detection_engine_cn.py --is_load_from_dictionary 1

# 测试模式（验证策略）
python detection_engine_cn.py --is_test 1 --future_bars 25
```

</details>

---

## 参数说明

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `--top_n` | 25 | 显示异动评分最高的 N 只股票 |
| `--min_volume` | 10000 | 最低成交量过滤（手） |
| `--data_granularity_minutes` | 60 | K 线周期（分钟），可选：1, 5, 10, 15, 30, 60 |
| `--history_to_use` | 14 | 用于检测的历史 K 线数 |
| `--is_load_from_dictionary` | 0 | 是否从缓存加载（0=否，1=是） |
| `--data_dictionary_path` | `dictionaries/cn_data_dict.npy` | 缓存数据路径 |
| `--is_save_dictionary` | 1 | 是否保存数据缓存（0=否，1=是） |
| `--is_test` | 0 | 是否启用测试模式（0=否，1=是） |
| `--future_bars` | 25 | 测试用未来 K 线数 |
| `--output_format` | CLI | 输出格式：`CLI` 或 `JSON` |
| `--stock_list` | `stocks_cn.txt` | 股票列表文件名 |
| `--auto_fetch_stocks` | False | 自动从 API 获取 A 股股票列表 |

完整参数列表：

```bash
python detection_engine_cn.py --help
```

---

## 股票代码说明

| 市场 | 代码前缀 | 后缀示例 |
|------|----------|----------|
| 上海主板 | 6xx xxx | 600000.SH |
| 深圳主板 | 0xx xxx | 000001.SZ |
| 创业板 | 300 xxx | 300760.SZ |
| 北交所 | 43x / 83x | 430047.BJ |

---

## 项目结构

```
surpriver-cn/
├── detection_engine_cn.py    # 主检测引擎
├── data_loader_cn.py        # A股数据加载（支持AKShare/Tushare）
├── feature_generator.py     # 技术指标生成
├── requirements.txt         # 依赖列表
├── .env.template            # 环境变量模板
├── stocks/
│   └── stocks_cn.txt        # A股股票列表示例
├── dictionaries/            # 数据缓存目录
└── figures/                 # 图表输出目录
```

---

## 注意事项

1. **数据源选择**：Tushare 更稳定但需要 Token；AKShare 免费但依赖网络环境
2. **数据限制**：AKShare 免费版有数据量限制，高频交易建议付费数据源
3. **市场兼容性**：仅支持 A 股，不支持港股、美股
4. **时间延迟**：实时数据可能有 15 分钟延迟
5. **异动 ≠ 涨跌**：异动检测只识别异常波动，不预测方向

---

## 原项目

- [tradytics/surpriver](https://github.com/tradytics/surpriver) - 美股版本

## License

基于 GPL v3，继承自 [tradytics/surpriver](https://github.com/tradytics/surpriver)

---

**🤖 本项目由 AI 改造完成，专为 A 股市场设计。**

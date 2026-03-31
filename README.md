# Surpriver-CN

> 🇨🇳 A股异动检测 — 基于 Isolation Forest 算法

**专为A股市场设计的异动股票检测工具**，[原项目](https://github.com/tradytics/surpriver) 为美股版本。

---

## ⚡ 中国网络环境最佳实践

> **推荐安装方式**（避免网络超时、下载失败）

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

---

## 功能特点

- 🔍 **异动检测**：Isolation Forest 算法识别异常波动股票
- 📊 **技术指标**：RSI、Stochastics、CCI、EOM 等
- 📈 **成交量分析**：今日量能与历史均量对比
- 🎯 **波动率过滤**：过滤低波动股票，聚焦活跃标的
- 📝 **测试模式**：验证策略有效性

---

## 快速开始

### 1. 安装依赖

```bash
# 中国网络环境推荐使用 pip + 国内镜像
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 2. 配置数据源

```bash
cp .env.template .env
```

编辑 `.env` 文件，选择数据源：

| 数据源 | 配置 | 说明 |
|--------|------|------|
| AKShare | `DATA_SOURCE=akshare` | 免费，需访问东方财富 |
| Tushare | `DATA_SOURCE=tushare`<br>`TUSHARE_TOKEN=你的token` | 更稳定，需注册 |

**Tushare Token 申请**：<https://tushare.pro/register>

### 3. 运行检测

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

---

## 参数说明

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `--top_n` | 25 | 显示异动评分最高的 N 只股票 |
| `--min_volume` | 10000 | 最低成交量过滤（手） |
| `--data_granularity_minutes` | 60 | K 线周期（分钟） |
| `--history_to_use` | 14 | 用于检测的历史 K 线数 |
| `--auto_fetch_stocks` | False | 自动获取 A 股列表 |
| `--is_load_from_dictionary` | 0 | 从缓存加载数据 |
| `--is_test` | 0 | 测试模式 |

完整参数列表：

```bash
python detection_engine_cn.py --help
```

---

## 股票代码格式

| 市场 | 格式示例 |
|------|----------|
| 上海主板 | 600000.SH |
| 深圳主板 | 000001.SZ |
| 创业板 | 300760.SZ |
| 北交所 | 430047.BJ |

---

## 项目结构

```
surpriver-cn/
├── detection_engine_cn.py   # 主检测引擎
├── data_loader_cn.py       # 数据加载（AKShare/Tushare）
├── feature_generator.py     # 技术指标生成
├── requirements.txt         # Python 依赖
├── stocks/
│   └── stocks_cn.txt       # 股票列表示例
├── dictionaries/          # 数据缓存
└── figures/                # 图表输出
```

---

## 技术栈

| 类别 | 技术 |
|------|------|
| 数据获取 | AKShare / Tushare |
| 机器学习 | Scikit-learn (Isolation Forest) |
| 数据处理 | Pandas, NumPy |
| 技术分析 | ta-lib |
| 可视化 | Matplotlib |

---

## 注意事项

1. **数据源**：Tushare 更稳定，推荐使用
2. **市场支持**：仅支持 A 股（沪深北交所）
3. **异动 ≠ 涨跌**：检测识别的是异常波动，不预测方向
4. **缓存复用**：`--is_load_from_dictionary 1` 可加速重复检测

---

## License

基于 GPL v3，继承自 [tradytics/surpriver](https://github.com/tradytics/surpriver)

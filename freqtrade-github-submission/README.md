# 基于 Freqtrade 的双周期现货趋势策略

课程项目：使用现有开源运行平台，开发可运行的策略算法模块并进行回测验证。
策略类为 **DualHorizonTrendV2**，接口为 Freqtrade V3。

## 策略逻辑
BTC/USDT与ETH/USDT，1小时K线，现货做多、无杠杆。
买入：价格>SMA480，SMA120>SMA480，SMA480高于48小时前，SMA24>SMA72，ATR24/价格<4%，成交量>0。
退出：(SMA24<SMA72且价格<SMA120)，或价格<SMA480×0.98；固定止损10%。
均线均为简单均线，ATR使用24小时真实波幅简单平均。收盘产生信号，下一根开盘执行。
初始10000USDT，99%资金可用，最多两仓，不加仓。

## 复现
推荐Python 3.12，Freqtrade 2026.9。需要联网读取Binance公共市场信息，不需要交易密钥。

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/macOS: source .venv/bin/activate
python -m pip install -r requirements.txt
python -m freqtrade backtesting --config config.shared.json --userdir user_data --strategy DualHorizonTrendV2 --timerange 20240101-20260101 --fee 0.001 --cache none
```

Windows也可激活环境后双击run-backtest.cmd。脚本寻找包内/上级.venv或已安装的freqtrade。
附带BTC、ETH的2023年12月至2025年底小时数据，12月供预热。可用`python scripts/download_archive.py`重下官方档案并校验SHA256。
本配置将公共API设为Binance官方data-api.binance.vision，以适配本次网络；网络不可用时需自行调整。

## 回测结果

| 指标（2024—2025连续、单边费0.1%） | 旧策略 | 新策略 |
|---|---:|---:|
| 累计收益 | 18.17% | 87.27% |
| 钱包最大回撤（含浮盈亏） | 26.47% | 15.73% |
| 交易次数 | 145 | 107 |

新策略2024收益50.96%，2025独立收益24.05%；两年胜率28.97%。单边费0.2%时两年收益68.74%。
2025下半年新策略8.32%，低于旧策略19.64%。
只按2024在3候选中筛选，再查看2025；2025是既有历史数据，不称真正前瞻样本。
官方前视检查抽查30信号未检出偏差；递归检查存在舍入级0.000%均线差异，日志在evidence/。
尚未显式模拟滑点，尚无持续模拟或实盘验证，不保证未来收益。

## 目录
- user_data/strategies/TrendResearchV2.py：V2候选及选中策略，需保留完整文件。
- user_data/strategies/TrendBreakoutV1.py：原基线。
- user_data/data/binance/：小时数据。
- config.shared.json：不含密钥的回测配置。
- REPORT_V2.md：策略报告，部分路径属于原研发工程。
- expected-results.json：原回测摘要，其中路径是原工程中的结果索引。
- RESEARCH_V2_PLAN.md：研发与筛选记录。
- evidence/：数据校验清单及关键验证日志。
- requirements-lock.txt：原Windows环境完整依赖快照，跨平台优先使用requirements.txt。

## 依赖与归属
策略及脚本在AI辅助下开发。运行平台为[Freqtrade](https://github.com/freqtrade/freqtrade)，市场数据来自[Binance Public Data](https://github.com/binance/binance-public-data)。
本仓库不包含Freqtrade平台源码或Python运行时，未附加本项目授权许可证；如需再分发须另行明确许可。

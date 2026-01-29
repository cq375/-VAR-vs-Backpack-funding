# 💰 VAR vs Backpack 资金费率监控器

> 实时监控 VAR 和 Backpack 两个交易所的资金费率差异，智能识别跨平台套利机会

[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Status](https://img.shields.io/badge/status-active-success.svg)]()

## 📖 项目简介

这是一个专为加密货币永续合约套利设计的实时监控工具。通过同时监控 VAR 和 Backpack (BPX) 两个交易所的资金费率，自动计算费率差异，并根据套利空间大小给出智能推荐。

### 🎯 核心功能

- **实时监控**：每 30 秒自动更新 49 个币种的资金费率数据
- **智能推荐**：根据费率差自动生成 4 级套利建议（强烈推荐/推荐/可考虑/无机会）
- **可视化界面**：美观的 Web 界面，支持颜色编码和动画效果
- **自动排序**：按费率差绝对值排序，最佳机会一目了然
- **双平台对比**：同时显示两个交易所的价格、费率和结算间隔

### ✨ 特色亮点

- 🚀 **异步架构**：基于 asyncio 的高性能异步设计
- 📊 **数据完整**：监控资金费率、价格、结算间隔等多维度数据
- 🎨 **用户友好**：响应式设计，支持 Tooltip 提示
- 💡 **智能分析**：自动计算年化收益，给出操作方向
- 🔄 **自动刷新**：前端每 5 秒自动更新，无需手动刷新

## 🖼️ 界面预览

### 主界面特性
- **顶部统计卡片**：总币种数、共同币种、高费率币种、更新次数、运行时间
- **数据表格**：11 列详细数据，包括费率、价格、费率差、推荐等
- **颜色编码**：
  - 🟡 黄色闪烁：强烈推荐（费率差 ≥ 0.02%）
  - 🟣 紫色加粗：推荐（费率差 ≥ 0.01%）
  - 🔵 蓝色：可考虑（费率差 ≥ 0.005%）
  - ⚪ 灰色：无机会（费率差 < 0.005%）

### 推荐逻辑

| 费率差绝对值 | 推荐等级 | 显示文本 | 年化收益估算 | 说明 |
|------------|---------|---------|------------|------|
| ≥ 0.02% | 🔥 强烈推荐 | 🔥 强烈推荐 方向 | > 175% | 极佳套利机会 |
| ≥ 0.01% | ⭐ 推荐 | ⭐ 推荐 方向 | > 87% | 不错的套利机会 |
| ≥ 0.005% | ✓ 可考虑 | ✓ 可考虑 方向 | > 43% | 有一定套利空间 |
| < 0.005% | - 无机会 | - 无机会 | < 43% | 费率差太小 |

**操作方向说明**：
- `VAR空/BP多`：在 VAR 做空收费，在 BP 做多对冲
- `BP空/VAR多`：在 BP 做空收费，在 VAR 做多对冲

**年化收益计算公式**：
```
年化收益 = 每小时费率差 × 24小时 × 365天
例如：0.02% × 24 × 365 = 175.2%
```

## 🛠️ 技术栈

- **后端**：Python 3.8+
- **异步框架**：asyncio + aiohttp
- **Web 服务器**：aiohttp.web
- **前端**：原生 HTML + CSS + JavaScript（无框架依赖）
- **数据格式**：JSON
- **部署方式**：单文件应用，支持后台运行

## 📦 安装步骤

### 1. 克隆项目

```bash
git clone https://github.com/cq375/-VAR-vs-Backpack-funding.git
cd funding-rate-monitor
```

### 2. 安装依赖

```bash
pip install aiohttp python-dotenv
```

或使用 requirements.txt：

```bash
pip install -r requirements.txt
```

**依赖列表**：
```
aiohttp==3.10.11
python-dotenv==1.0.0
```

### 3. 配置代理（可选）

如果需要通过代理访问交易所 API，创建 `.env` 文件：

```bash
# .env
HTTP_PROXY=http://127.0.0.1:10808
```

如果不需要代理，可以跳过此步骤。程序会自动检测环境变量。

## 🚀 使用方法

### 前台运行（调试模式）

```bash
python funding_rate_monitor.py
```

启动后会看到：
```
======================================================================
VAR 资金费率监控器
实时监控VAR交易所的资金费率，对比Backpack价格
======================================================================

开始定期更新资金费率...

======================================================================
✓ Web服务器已启动
✓ 访问地址: http://127.0.0.1:17010
======================================================================
```

### 后台运行（生产模式）

```bash
# 启动程序
nohup python funding_rate_monitor.py > monitor.log 2>&1 &

# 查看日志
tail -f monitor.log

# 查看进程
ps aux | grep funding_rate_monitor

# 停止程序
pkill -f funding_rate_monitor.py
```

### 访问界面

启动成功后，在浏览器中访问：

```
http://127.0.0.1:17010
```

## 📡 API 文档

### 获取数据接口

**端点**：`GET /api/data`

**参数**：
- `limit`（可选）：返回前 N 个币种，不传则返回全部

**示例**：

```bash
# 获取全部数据
curl http://127.0.0.1:17010/api/data

# 获取前 10 个币种
curl http://127.0.0.1:17010/api/data?limit=10
```

**响应格式**：

```json
{
  "summary": [
    {
      "symbol": "AVNT",
      "var_symbol": "AVNT",
      "var_funding": 0.0012,
      "var_interval": 3600,
      "var_price": 0.1234,
      "bpx_price": 0.1235,
      "bpx_funding": 0.0269,
      "bpx_interval": 3600,
      "price_spread": 0.081,
      "funding_rate_diff": -0.0257,
      "recommendation": {
        "level": 3,
        "text": "🔥 强烈推荐 BP空/VAR多",
        "direction": "BP空/VAR多",
        "class": "rec-excellent"
      },
      "has_bpx_price": true,
      "has_bpx_funding": true,
      "has_var_data": true
    }
  ],
  "stats": {
    "total_symbols": 49,
    "common_count": 49,
    "high_funding_count": 3,
    "update_count": 120,
    "runtime": 3600,
    "last_update": "22:30:15"
  }
}
```

**字段说明**：

| 字段 | 类型 | 说明 |
|------|------|------|
| symbol | string | BP 币种名称 |
| var_symbol | string | VAR 币种名称（可能不同） |
| var_funding | float | VAR 资金费率（每小时，%） |
| var_interval | int | VAR 结算间隔（秒） |
| var_price | float | VAR 标记价格 |
| bpx_price | float | BP 最新价格 |
| bpx_funding | float | BP 资金费率（每小时，%） |
| bpx_interval | int | BP 结算间隔（秒） |
| price_spread | float | 价格差异百分比 |
| funding_rate_diff | float | 费率差（VAR - BP） |
| recommendation | object | 推荐信息对象 |
| recommendation.level | int | 推荐等级（0-3） |
| recommendation.text | string | 推荐文本 |
| recommendation.direction | string | 操作方向 |
| recommendation.class | string | CSS 类名 |

## ⚙️ 配置说明

### 端口配置

默认端口为 `17010`，可在代码中修改：

```python
WEB_PORT = 17010  # 修改为您需要的端口
```

### 更新频率

默认每 30 秒更新一次数据，可在代码中调整：

```python
await asyncio.sleep(30)  # 修改为您需要的秒数
```

### 币种名称映射

部分币种在两个交易所的命名不同，已内置映射：

```python
BPX_TO_VAR_SYMBOL_MAP = {
    'PUMP': 'PUMPFUN',
    'kBONK': 'BONK',
    'kPEPE': 'PEPE',
    'kSHIB': 'SHIB',
}
```

如需添加新的映射，直接在此字典中添加即可。

### 币种黑名单（屏蔽功能）

程序支持屏蔽特定币种，使其不在前端界面显示。默认已屏蔽 kBONK、kPEPE、kSHIB：

```python
# 币种黑名单（不在前端显示的币种）
SYMBOL_BLACKLIST = {'kBONK', 'kPEPE', 'kSHIB'}
```

**功能特点**：
- ✅ 只影响前端显示，不影响后台数据获取
- ✅ 使用 set 数据结构，查询效率 O(1)
- ✅ 统计数据会自动排除黑名单币种
- ✅ 易于维护和修改

**如何添加更多黑名单币种**：

```python
# 添加更多币种到黑名单
SYMBOL_BLACKLIST = {'kBONK', 'kPEPE', 'kSHIB', 'NEW_COIN'}
```

**如何移除黑名单币种**：

```python
# 只保留 kBONK
SYMBOL_BLACKLIST = {'kBONK'}

# 或完全禁用黑名单
SYMBOL_BLACKLIST = set()
```

**注意事项**：
- 黑名单使用 BP 交易所的币种名称（不是 VAR 的名称）
- 黑名单币种的数据仍会从 API 获取，只是不显示
- 修改黑名单后需要重启程序才能生效

## 📊 数据说明

### 资金费率

**什么是资金费率？**

资金费率（Funding Rate）是永续合约特有的机制，用于让合约价格锚定现货价格。

- **正费率**：多头支付空头（做空可收费）
- **负费率**：空头支付多头（做多可收费）

**费率转换**：

程序自动处理两个交易所的费率格式差异：

- **VAR**：API 返回年化费率，程序转换为每小时费率
  ```python
  hourly_rate = (annual_rate * 100) / (365 * 24)
  ```

- **Backpack**：API 返回小数格式，程序转换为百分比
  ```python
  funding_rate_percent = funding_rate * 100
  ```

### 套利原理

**基本逻辑**：

1. 监控两个平台的资金费率差异
2. 在费率高的平台做空（收取资金费）
3. 在费率低的平台做多（对冲风险）
4. 赚取费率差

**示例**：

假设 BTC 的费率情况：
- VAR 费率：+0.03%/小时
- BP 费率：+0.01%/小时
- 费率差：0.02%/小时

**操作**：
- 在 VAR 做空 1 BTC（收取 0.03%）
- 在 BP 做多 1 BTC（支付 0.01%）
- 净收益：0.02%/小时

**年化收益**：
```
0.02% × 24小时 × 365天 = 175.2%
```

## 🏗️ 项目架构

### 文件结构

```
funding-rate-monitor/
├── funding_rate_monitor.py    # 主程序（单文件）
├── .env                        # 环境配置（可选）
├── README.md                   # 项目文档
├── requirements.txt            # 依赖列表
└── monitor.log                 # 运行日志（自动生成）
```

### 核心模块

```
funding_rate_monitor.py
├── 配置模块 (19-31行)
│   ├── API 端点配置
│   ├── 代理配置
│   └── 币种名称映射
│
├── 数据存储类 (34-197行)
│   ├── FundingRateStore
│   ├── update_data()           # 更新数据
│   ├── _generate_recommendation()  # 生成推荐
│   ├── get_summary()           # 获取汇总
│   └── get_stats()             # 获取统计
│
├── 数据获取模块 (203-357行)
│   ├── fetch_var_funding_rates()   # 获取 VAR 数据
│   ├── fetch_bpx_funding_rates()   # 获取 BP 数据
│   └── update_funding_rates()      # 定时更新任务
│
├── Web 服务器模块 (389-852行)
│   ├── handle_index()          # 主页路由
│   ├── handle_api_data()       # API 路由
│   └── start_web_server()      # 启动服务器
│
└── 主函数 (855-873行)
    └── main()                  # 程序入口
```

### 数据流

```
启动程序
    ↓
并发启动两个任务
    ├─→ update_funding_rates()  (每30秒循环)
    │       ├─→ fetch_bpx_funding_rates()
    │       ├─→ fetch_var_funding_rates()
    │       └─→ store.update_data()
    │
    └─→ start_web_server()
            ├─→ GET /  → handle_index()  (返回HTML)
            └─→ GET /api/data → handle_api_data()  (返回JSON)
                    └─→ store.get_summary()
                            ├─→ 计算费率差
                            ├─→ _generate_recommendation()
                            └─→ 排序并返回
```

## 🔧 故障排除

### 问题 1：程序无法启动

**可能原因**：
- 端口 17010 被占用
- 依赖未安装

**解决方法**：
```bash
# 检查端口占用
lsof -i :17010

# 杀死占用进程
kill -9 <PID>

# 重新安装依赖
pip install --upgrade aiohttp python-dotenv
```

### 问题 2：数据显示为 0 或 -

**可能原因**：
- API 请求失败
- 代理配置错误
- 网络连接问题

**解决方法**：
```bash
# 查看日志
tail -f monitor.log

# 测试 API 连接
curl -x http://127.0.0.1:10808 https://api.backpack.exchange/api/v1/tickers

# 尝试不使用代理
unset HTTP_PROXY
python funding_rate_monitor.py
```

### 问题 3：推荐显示异常

**可能原因**：
- 数据未更新
- 计算逻辑错误

**解决方法**：
```bash
# 测试 API 接口
curl http://127.0.0.1:17010/api/data | python3 -m json.tool

# 检查推荐字段
curl -s http://127.0.0.1:17010/api/data | jq '.summary[0].recommendation'
```

### 问题 4：浏览器无法访问

**可能原因**：
- 防火墙阻止
- 服务器未启动

**解决方法**：
```bash
# 检查进程
ps aux | grep funding_rate_monitor

# 检查端口监听
netstat -an | grep 17010

# 尝试使用 localhost
curl http://localhost:17010
```


## 📈 性能指标

- **数据更新频率**：30 秒/次
- **前端刷新频率**：5 秒/次
- **监控币种数量**：49 个
- **并发请求**：异步处理，高效无阻塞
- **内存占用**：< 100MB
- **CPU 占用**：< 5%
- **支持运行时长**：7×24 小时持续运行

## 🔒 安全提示

### 数据安全

- ✅ 本程序**仅监控数据**，不涉及交易操作
- ✅ 无需配置 API 密钥或钱包私钥
- ✅ 所有数据通过公开 API 获取
- ✅ 不存储任何敏感信息

### 网络安全

- 建议在本地运行，不要暴露到公网
- 如需远程访问，建议使用 SSH 隧道或 VPN
- 默认监听 `0.0.0.0`，可修改为 `127.0.0.1` 仅本地访问

### 代理使用

- 代理配置存储在 `.env` 文件中
- 确保 `.env` 文件不被提交到版本控制
- 建议添加到 `.gitignore`

## 🎓 使用场景

### 1. 套利机会发现

实时监控 49 个币种的资金费率差异，快速发现套利机会。

**适用人群**：
- 量化交易者
- 套利交易员
- 加密货币投资者

### 2. 市场研究

分析不同交易所的资金费率差异，了解市场情绪和资金流向。

**研究方向**：
- 资金费率与价格走势的关系
- 不同交易所的流动性差异
- 市场情绪指标

### 3. 风险管理

监控持仓币种的资金费率，优化持仓成本。

**应用场景**：
- 长期持仓成本优化
- 对冲策略制定
- 风险敞口管理

## 📚 扩展开发

### 添加新交易所

如需添加其他交易所，可参考以下步骤：

1. **创建数据获取函数**：
```python
async def fetch_exchange_funding_rates():
    """获取新交易所的资金费率"""
    # 实现 API 调用逻辑
    pass
```

2. **更新数据存储类**：
```python
class FundingRateStore:
    def __init__(self):
        # 添加新交易所的数据字段
        self.new_exchange_funding_rates = {}
        self.new_exchange_prices = {}
```

3. **修改推荐逻辑**：
```python
def _generate_recommendation(self, funding_rate_diff):
    # 支持多交易所对比
    pass
```

### 添加新功能

**建议功能**：
- 历史数据记录和分析
- 费率差异预警通知（邮件/Telegram）
- 数据导出功能（CSV/Excel）
- 图表可视化（费率走势图）
- 移动端适配

### API 集成

程序提供 RESTful API，可轻松集成到其他系统：

```python
import requests

# 获取数据
response = requests.get('http://127.0.0.1:17010/api/data')
data = response.json()

# 处理数据
for item in data['summary']:
    if item['recommendation']['level'] >= 2:
        print(f"发现机会: {item['symbol']} - {item['recommendation']['text']}")
```

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request！

### 提交 Issue

- 描述问题或建议
- 提供复现步骤（如果是 Bug）
- 附上相关日志或截图

### 提交 Pull Request

1. Fork 本项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

### 代码规范

- 遵循 PEP 8 Python 代码规范
- 添加必要的注释和文档字符串
- 确保代码通过测试

## 📝 更新日志

### v1.0.0 (2026-01-29)

**新增功能**：
- ✨ 实时监控 VAR 和 Backpack 两个交易所
- ✨ 智能推荐系统（4 级推荐）
- ✨ 美观的 Web 界面
- ✨ RESTful API 接口
- ✨ 自动排序和颜色编码
- ✨ 支持币种名称映射

**技术特性**：
- 🚀 异步架构，高性能
- 📊 监控 49 个币种
- 🎨 响应式设计
- 💡 智能套利建议

## ❓ 常见问题

### Q1: 为什么有些币种显示 "-"？

**A**: 可能的原因：
- 该币种在某个交易所没有永续合约
- API 暂时无法获取数据
- 币种名称映射不正确

### Q2: 推荐等级是如何计算的？

**A**: 基于费率差绝对值：
- 强烈推荐：≥ 0.02%（年化 > 175%）
- 推荐：≥ 0.01%（年化 > 87%）
- 可考虑：≥ 0.005%（年化 > 43%）
- 无机会：< 0.005%

### Q3: 可以修改监控的币种吗？

**A**: 当前版本自动监控 Backpack 支持的所有永续合约币种。如需自定义，可修改代码中的 `fetch_bpx_funding_rates()` 函数。

### Q4: 数据更新频率可以调整吗？

**A**: 可以。修改代码第 386 行：
```python
await asyncio.sleep(30)  # 改为您需要的秒数
```

### Q5: 支持其他交易所吗？

**A**: 当前版本仅支持 VAR 和 Backpack。如需添加其他交易所，请参考"扩展开发"章节。

### Q6: 程序会自动执行交易吗？

**A**: 不会。本程序仅用于监控和分析，不涉及任何交易操作。

## 📞 联系方式

- **GitHub Issues**: [提交问题](https://github.com/yourusername/funding-rate-monitor/issues)
- **Email**: your.email@example.com
- **Twitter**: @yourhandle

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

## 🙏 致谢

感谢以下项目和服务：

- [aiohttp](https://github.com/aio-libs/aiohttp) - 异步 HTTP 框架
- [VAR Exchange](https://variational.io/) - 提供资金费率 API
- [Backpack Exchange](https://backpack.exchange/) - 提供资金费率 API

## 🌟 Star History

如果这个项目对您有帮助，请给个 Star ⭐️

---

**项目状态**: ✅ 稳定运行中

**最后更新**: 2026-01-29

**版本**: v1.0.0

---

Made with ❤️ by [Your Name]

#!/usr/bin/env python
"""
VAR vs Backpack 资金费率监控器
实时监控VAR交易所的资金费率，对比两个交易所的价格差异
访问地址: http://127.0.0.1:17010
"""

import asyncio
import json
import os
import aiohttp
import requests
from datetime import datetime
from aiohttp import web

# ==================== 配置 ====================
VAR_STATS_API = "https://omni-client-api.prod.ap-northeast-1.variational.io/metadata/stats"
BPX_TICKERS_API = "https://api.backpack.exchange/api/v1/tickers"
PROXY_URL = "http://127.0.0.1:10808"  # Backpack 需要代理访问
WEB_PORT = 17010

# BP到VAR的币种名称映射（BP币种名 -> VAR币种名）
BPX_TO_VAR_SYMBOL_MAP = {
    'PUMP': 'PUMPFUN',
    'kBONK': 'BONK',
    'kPEPE': 'PEPE',
    'kSHIB': 'SHIB',
}

# 币种黑名单（不在前端显示的币种）
SYMBOL_BLACKLIST = {'kBONK', 'kPEPE', 'kSHIB'}

# ==================== 数据存储 ====================
class FundingRateStore:
    def __init__(self):
        self.var_funding_rates = {}
        self.var_funding_intervals = {}  # 新增：存储资金费间隔
        self.var_prices = {}

        # BP 数据 - 新增资金费率和间隔
        self.bpx_prices = {}
        self.bpx_funding_rates = {}      # 新增
        self.bpx_funding_intervals = {}  # 新增

        self.symbols = []
        self.start_time = datetime.now()
        self.update_count = 0
        self.last_update = None

    def update_data(self, var_data, bpx_data):
        """更新所有数据"""
        self.var_funding_rates = var_data.get('funding_rates', {})
        self.var_funding_intervals = var_data.get('funding_intervals', {})  # 新增
        self.var_prices = var_data.get('prices', {})

        # BP 数据 - 更新所有三个字典
        self.bpx_prices = bpx_data.get('prices', {})
        self.bpx_funding_rates = bpx_data.get('funding_rates', {})
        self.bpx_funding_intervals = bpx_data.get('funding_intervals', {})

        # 更新币种列表（改为以BP有资金费率的币种为基准）
        self.symbols = sorted(self.bpx_funding_rates.keys())

        self.update_count += 1
        self.last_update = datetime.now()

    def _generate_recommendation(self, funding_rate_diff):
        """根据费率差生成套利推荐

        Args:
            funding_rate_diff: 费率差（VAR - BP）

        Returns:
            dict: {
                'level': 推荐等级 (0-3),
                'text': 推荐文本,
                'direction': 操作方向,
                'class': CSS类名
            }
        """
        abs_diff = abs(funding_rate_diff)

        # 无机会
        if abs_diff < 0.005:
            return {
                'level': 0,
                'text': '- 无机会',
                'direction': '',
                'class': 'rec-none'
            }

        # 确定方向
        if funding_rate_diff > 0:
            direction = 'VAR空/BP多'
        else:
            direction = 'BP空/VAR多'

        # 一般机会
        if abs_diff < 0.01:
            return {
                'level': 1,
                'text': f'✓ 可考虑 {direction}',
                'direction': direction,
                'class': 'rec-normal'
            }

        # 好机会
        if abs_diff < 0.02:
            return {
                'level': 2,
                'text': f'⭐ 推荐 {direction}',
                'direction': direction,
                'class': 'rec-good'
            }

        # 极佳机会
        return {
            'level': 3,
            'text': f'🔥 强烈推荐 {direction}',
            'direction': direction,
            'class': 'rec-excellent'
        }

    def get_summary(self, limit=None):
        """获取汇总数据，显示所有BP支持的币种，按费率差绝对值排序"""
        summary = []

        # 遍历BP的币种（self.symbols现在是BP的币种列表）
        for symbol in self.symbols:
            bpx_price = self.bpx_prices.get(symbol, 0)
            bpx_funding = self.bpx_funding_rates.get(symbol, 0)
            bpx_interval = self.bpx_funding_intervals.get(symbol, 0)

            # 获取VAR对应的币种名（使用映射）
            var_symbol = BPX_TO_VAR_SYMBOL_MAP.get(symbol, symbol)
            var_funding = self.var_funding_rates.get(var_symbol, 0)
            var_interval = self.var_funding_intervals.get(var_symbol, 0)
            var_price = self.var_prices.get(var_symbol, 0)

            # 只保留BP有完整数据的币种
            if not (bpx_price > 0 and bpx_funding != 0):
                continue

            # 跳过黑名单中的币种
            if symbol in SYMBOL_BLACKLIST:
                continue

            # 计算价格差异
            price_spread = 0
            if var_price > 0 and bpx_price > 0:
                price_spread = (bpx_price - var_price) / var_price * 100

            # 计算资金费率差（每小时）
            funding_rate_diff = var_funding - bpx_funding

            # 生成套利推荐
            recommendation = self._generate_recommendation(funding_rate_diff)

            summary.append({
                'symbol': symbol,
                'var_symbol': var_symbol,  # 添加VAR币种名，用于显示
                'var_funding': var_funding,
                'var_interval': var_interval,
                'var_price': var_price,
                'bpx_price': bpx_price,
                'bpx_funding': bpx_funding,
                'bpx_interval': bpx_interval,
                'price_spread': price_spread,
                'funding_rate_diff': funding_rate_diff,
                'recommendation': recommendation,  # 新增：推荐信息
                'has_bpx_price': True,
                'has_bpx_funding': True,
                'has_var_data': var_price > 0 and var_funding != 0  # 标记是否有VAR数据
            })

        # 按资金费率差的绝对值排序（从大到小）
        summary.sort(key=lambda x: abs(x['funding_rate_diff']), reverse=True)

        # 如果指定了limit，返回前N个，否则返回全部
        if limit:
            return summary[:limit]
        return summary

    def get_stats(self):
        """获取统计信息"""
        runtime = (datetime.now() - self.start_time).total_seconds()

        # 统计有BPX价格的币种数量（排除黑名单）
        common_count = len([s for s in self.symbols
                           if self.bpx_prices.get(s, 0) > 0
                           and s not in SYMBOL_BLACKLIST])

        # 统计高资金费率币种
        high_funding = len([f for f in self.var_funding_rates.values() if abs(f) > 0.01])

        return {
            'total_symbols': len(self.symbols),
            'common_count': common_count,
            'high_funding_count': high_funding,
            'update_count': self.update_count,
            'runtime': int(runtime),
            'last_update': self.last_update.strftime('%H:%M:%S') if self.last_update else '-'
        }

# 全局存储
store = FundingRateStore()

# ==================== 数据获取 ====================
async def fetch_var_funding_rates():
    """获取VAR交易所的资金费率"""
    try:
        async with aiohttp.ClientSession() as session:
            # VAR API 不需要代理
            async with session.get(VAR_STATS_API, timeout=15) as response:
                if response.status == 200:
                    data = await response.json()
                    funding_rates = {}
                    funding_intervals = {}  # 新增
                    prices = {}

                    if 'listings' in data:
                        for listing in data['listings']:
                            ticker = listing.get('ticker', '')
                            funding_rate = float(listing.get('funding_rate', 0))
                            funding_interval_s = int(listing.get('funding_interval_s', 3600))
                            mark_price = float(listing.get('mark_price', 0))

                            if ticker:
                                # funding_rate是年化费率（小数格式）
                                # 例如：BTC funding_rate=0.1095 表示年化10.95%
                                # 需要转换为每小时费率

                                # 年化费率转换为百分比
                                annual_rate_percent = funding_rate * 100

                                # 一年的小时数
                                hours_per_year = 365 * 24

                                # 每小时费率 = 年化费率 / 一年的小时数
                                hourly_rate = annual_rate_percent / hours_per_year

                                funding_rates[ticker] = hourly_rate
                                funding_intervals[ticker] = funding_interval_s  # 新增：保存间隔
                                prices[ticker] = mark_price

                    return {
                        'funding_rates': funding_rates,
                        'funding_intervals': funding_intervals,  # 新增
                        'prices': prices,
                        'success': True
                    }
                else:
                    print(f"VAR API错误: HTTP {response.status}")
                    return {'funding_rates': {}, 'prices': {}, 'success': False}

    except Exception as e:
        print(f"VAR获取失败: {e}")
        return {'funding_rates': {}, 'prices': {}, 'success': False}

async def fetch_bpx_funding_rates(var_symbols=None):
    """获取Backpack交易所的资金费率、价格和结算间隔

    Args:
        var_symbols: VAR交易所的币种列表，用于只获取这些币种的资金费率
    """
    try:
        async with aiohttp.ClientSession() as session:
            # 1. 获取市场信息（结算间隔）- Backpack 需要代理
            async with session.get(
                "https://api.backpack.exchange/api/v1/markets",
                timeout=10,
                proxy=PROXY_URL
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    prices = {}
                    funding_rates = {}
                    funding_intervals = {}
                    perp_symbols = {}  # 改为字典，key是base，value是完整symbol

                    if isinstance(data, list):
                        for market in data:
                            symbol = market.get('symbol', '')

                            if '_USDC_PERP' in symbol:
                                base = symbol.split('_')[0]
                                perp_symbols[base] = symbol

                                # 获取结算间隔（毫秒转秒）
                                funding_interval_ms = market.get('fundingInterval', 3600000)
                                funding_interval_s = funding_interval_ms // 1000 if funding_interval_ms else 3600
                                funding_intervals[base] = funding_interval_s

                    # 2. 获取价格数据 - Backpack 需要代理
                    async with session.get(
                        "https://api.backpack.exchange/api/v1/tickers",
                        timeout=10,
                        proxy=PROXY_URL
                    ) as ticker_response:
                        if ticker_response.status == 200:
                            ticker_data = await ticker_response.json()
                            if isinstance(ticker_data, list):
                                for ticker in ticker_data:
                                    symbol = ticker.get('symbol', '')
                                    if '_USDC_PERP' in symbol:
                                        base = symbol.split('_')[0]
                                        last_price = float(ticker.get('lastPrice', 0))
                                        if last_price > 0:
                                            prices[base] = last_price

                    # 3. 获取资金费率（只获取VAR中有的币种）
                    symbols_to_fetch = []
                    if var_symbols:
                        # 只获取VAR和BP都有的币种
                        for base in var_symbols:
                            if base in perp_symbols:
                                symbols_to_fetch.append(perp_symbols[base])
                    else:
                        # 如果没有提供VAR币种列表，获取所有BP币种（限制50个）
                        symbols_to_fetch = list(perp_symbols.values())[:50]

                    # 并发获取资金费率 - Backpack 需要代理
                    for symbol in symbols_to_fetch:
                        try:
                            async with session.get(
                                f"https://api.backpack.exchange/api/v1/fundingRates?symbol={symbol}&limit=1",
                                timeout=10,
                                proxy=PROXY_URL
                            ) as funding_response:
                                if funding_response.status == 200:
                                    funding_data = await funding_response.json()
                                    if isinstance(funding_data, list) and len(funding_data) > 0:
                                        base = symbol.split('_')[0]
                                        # 资金费率是小数格式，需要转换为百分比
                                        # 例如：0.0000125 表示 0.00125%
                                        funding_rate = float(funding_data[0].get('fundingRate', 0))
                                        funding_rates[base] = funding_rate * 100  # 转换为百分比
                        except Exception as e:
                            # 静默处理单个币种的错误
                            continue

                    return {
                        'prices': prices,
                        'funding_rates': funding_rates,
                        'funding_intervals': funding_intervals,
                        'success': True
                    }
                else:
                    print(f"BPX API错误: HTTP {response.status}")
                    return {
                        'prices': {},
                        'funding_rates': {},
                        'funding_intervals': {},
                        'success': False
                    }

    except Exception as e:
        print(f"BPX获取失败: {e}")
        return {
            'prices': {},
            'funding_rates': {},
            'funding_intervals': {},
            'success': False
        }

async def update_funding_rates():
    """定期更新资金费率数据"""
    print("\n开始定期更新资金费率...")

    while True:
        try:
            # 先获取BP数据（不传入币种列表，获取所有BP币种）
            bpx_data = await fetch_bpx_funding_rates(var_symbols=None)

            # 再获取VAR数据（获取所有VAR币种）
            var_data = await fetch_var_funding_rates()

            # 更新存储
            store.update_data(var_data, bpx_data)

            if bpx_data['success']:
                bpx_funding_count = len([r for r in bpx_data.get('funding_rates', {}).values() if r != 0])
                var_funding_count = len(var_data.get('funding_rates', {}))
                print(f"[{datetime.now().strftime('%H:%M:%S')}] 数据更新成功 - "
                      f"BPX: {len(bpx_data.get('prices', {}))} 币种 "
                      f"(资金费率: {bpx_funding_count} 个), "
                      f"VAR: {var_funding_count} 币种")

        except Exception as e:
            print(f"更新失败: {e}")

        # 每30秒更新一次
        await asyncio.sleep(30)

# ==================== Web服务器 ====================
async def handle_index(request):
    """主页"""
    html = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>VAR资金费率监控</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Monaco', 'Menlo', 'Consolas', monospace;
            background: linear-gradient(135deg, #0a0e27 0%, #1a1f3a 100%);
            color: #e0e0e0;
            padding: 20px;
            min-height: 100vh;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 30px;
            border-radius: 15px;
            margin-bottom: 20px;
            box-shadow: 0 8px 16px rgba(0,0,0,0.3);
        }
        .header h1 {
            font-size: 32px;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        .header p {
            opacity: 0.95;
            font-size: 14px;
        }
        .info-box {
            background: rgba(26, 31, 58, 0.8);
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 20px;
            border-left: 4px solid #fbbf24;
            backdrop-filter: blur(10px);
        }
        .info-box h3 {
            color: #fbbf24;
            margin-bottom: 10px;
            font-size: 16px;
        }
        .info-box p {
            color: #aaa;
            font-size: 13px;
            line-height: 1.8;
        }
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 15px;
            margin-bottom: 20px;
        }
        .stat-card {
            background: rgba(26, 31, 58, 0.8);
            padding: 20px;
            border-radius: 10px;
            border-left: 4px solid #667eea;
            backdrop-filter: blur(10px);
            transition: transform 0.2s;
        }
        .stat-card:hover {
            transform: translateY(-2px);
        }
        .stat-label {
            color: #888;
            font-size: 11px;
            margin-bottom: 8px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        .stat-value {
            font-size: 28px;
            font-weight: bold;
            color: #667eea;
        }
        .table-container {
            background: rgba(26, 31, 58, 0.8);
            border-radius: 15px;
            overflow: hidden;
            box-shadow: 0 8px 16px rgba(0,0,0,0.3);
            backdrop-filter: blur(10px);
        }
        table {
            width: 100%;
            border-collapse: collapse;
        }
        th {
            background: rgba(37, 43, 74, 0.9);
            padding: 18px 15px;
            text-align: left;
            font-weight: bold;
            color: #667eea;
            position: sticky;
            top: 0;
            font-size: 13px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        td {
            padding: 15px;
            border-bottom: 1px solid rgba(37, 43, 74, 0.5);
            font-size: 13px;
        }
        tr:hover {
            background: rgba(37, 43, 74, 0.5);
        }
        .symbol {
            font-weight: bold;
            color: #fff;
            font-size: 14px;
        }
        .price {
            font-family: 'Courier New', monospace;
            color: #aaa;
        }
        .funding-positive {
            color: #4ade80;
        }
        .funding-negative {
            color: #f87171;
        }
        .funding-high {
            color: #a78bfa;
            font-weight: bold;
        }
        .funding-extreme {
            color: #fbbf24;
            font-weight: bold;
            animation: pulse 2s infinite;
        }
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.7; }
        }
        .spread-positive {
            color: #4ade80;
        }
        .spread-negative {
            color: #f87171;
        }
        .spread-large {
            color: #fbbf24;
            font-weight: bold;
        }
        .status-ok {
            color: #4ade80;
        }
        .status-no {
            color: #666;
        }
        /* 推荐等级样式 */
        .rec-none {
            color: #666;
            font-size: 12px;
        }
        .rec-normal {
            color: #60a5fa;
            font-weight: 500;
        }
        .rec-good {
            color: #a78bfa;
            font-weight: bold;
        }
        .rec-excellent {
            color: #fbbf24;
            font-weight: bold;
            animation: pulse 2s infinite;
        }
        .loading {
            text-align: center;
            padding: 60px;
            color: #888;
            font-size: 14px;
        }
        .update-time {
            text-align: center;
            color: #888;
            margin-top: 20px;
            font-size: 12px;
        }
        .opportunity {
            background: rgba(251, 191, 36, 0.1);
            border-left: 4px solid #fbbf24;
        }
        .tooltip {
            position: relative;
            cursor: help;
        }
        .tooltip:hover::after {
            content: attr(data-tooltip);
            position: absolute;
            bottom: 100%;
            left: 50%;
            transform: translateX(-50%);
            background: rgba(0, 0, 0, 0.9);
            color: white;
            padding: 8px 12px;
            border-radius: 6px;
            white-space: nowrap;
            font-size: 11px;
            z-index: 1000;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>💰 VAR 资金费率监控</h1>
        <p>实时监控VAR交易所的资金费率 | 对比Backpack价格差异</p>
    </div>

    <div class="info-box">
        <h3>💡 说明</h3>
        <p>
            <strong>资金费率</strong>：永续合约中多空双方的资金交换费率（每小时）。正值表示多头支付空头（做空可收费），负值表示空头支付多头（做多可收费）。<br>
            <strong>推荐逻辑</strong>：根据两平台费率差给出套利建议。费率差越大，套利空间越大。<br>
            <strong>操作方式</strong>：在费率高的平台做空收费，在费率低的平台做多对冲，赚取费率差。<br>
            <strong>推荐等级</strong>：🔥 强烈推荐（≥0.02%）、⭐ 推荐（≥0.01%）、✓ 可考虑（≥0.005%）、- 无机会（<0.005%）
        </p>
    </div>

    <div class="stats">
        <div class="stat-card">
            <div class="stat-label">总币种数</div>
            <div class="stat-value" id="total-symbols">-</div>
        </div>
        <div class="stat-card">
            <div class="stat-label">共同币种</div>
            <div class="stat-value" id="common-count">-</div>
        </div>
        <div class="stat-card">
            <div class="stat-label">高费率币种</div>
            <div class="stat-value" id="high-funding">-</div>
        </div>
        <div class="stat-card">
            <div class="stat-label">更新次数</div>
            <div class="stat-value" id="update-count">-</div>
        </div>
        <div class="stat-card">
            <div class="stat-label">运行时间</div>
            <div class="stat-value" id="runtime">-</div>
        </div>
    </div>

    <div class="table-container">
        <table>
            <thead>
                <tr>
                    <th>排名</th>
                    <th>币种</th>
                    <th class="tooltip" data-tooltip="VAR交易所资金费率（每小时）">VAR费率/小时</th>
                    <th class="tooltip" data-tooltip="VAR资金费结算间隔">VAR间隔</th>
                    <th class="tooltip" data-tooltip="Backpack资金费率（每小时）">BPX费率/小时</th>
                    <th class="tooltip" data-tooltip="Backpack资金费结算间隔">BPX间隔</th>
                    <th class="tooltip" data-tooltip="两平台资金费率差异（VAR - BPX）">费率差/小时</th>
                    <th class="tooltip" data-tooltip="VAR标记价格">VAR价格</th>
                    <th class="tooltip" data-tooltip="Backpack最新价格">BPX价格</th>
                    <th class="tooltip" data-tooltip="价格差异百分比">价差%</th>
                    <th class="tooltip" data-tooltip="套利操作建议">推荐</th>
                </tr>
            </thead>
            <tbody id="funding-table">
                <tr>
                    <td colspan="11" class="loading">正在加载数据...</td>
                </tr>
            </tbody>
        </table>
    </div>

    <div class="update-time" id="update-time">-</div>

    <script>
        function formatFundingRate(rate) {
            if (rate === 0) return '-';
            // VAR API返回的funding_rate已经是百分比格式，不需要再乘100
            return (rate > 0 ? '+' : '') + rate.toFixed(4) + '%';
        }

        function formatPrice(price) {
            if (price === 0) return '-';
            if (price >= 1000) return price.toFixed(2);
            if (price >= 10) return price.toFixed(3);
            if (price >= 1) return price.toFixed(4);
            if (price >= 0.1) return price.toFixed(5);
            return price.toFixed(6);
        }

        function formatRuntime(seconds) {
            const hours = Math.floor(seconds / 3600);
            const minutes = Math.floor((seconds % 3600) / 60);
            const secs = seconds % 60;
            if (hours > 0) return `${hours}h ${minutes}m`;
            if (minutes > 0) return `${minutes}m ${secs}s`;
            return `${secs}s`;
        }

        function formatInterval(seconds) {
            if (seconds === 0) return '-';
            const hours = seconds / 3600;
            if (hours >= 1) return `${hours.toFixed(0)}小时`;
            const minutes = seconds / 60;
            return `${minutes.toFixed(0)}分钟`;
        }

        function formatFundingRateDiff(diff) {
            if (diff === 0) return '-';
            return (diff > 0 ? '+' : '') + diff.toFixed(4) + '%';
        }

        async function updateData() {
            try {
                const response = await fetch('/api/data');
                const data = await response.json();

                // 更新统计
                document.getElementById('total-symbols').textContent = data.stats.total_symbols;
                document.getElementById('common-count').textContent = data.stats.common_count;
                document.getElementById('high-funding').textContent = data.stats.high_funding_count;
                document.getElementById('update-count').textContent = data.stats.update_count;
                document.getElementById('runtime').textContent = formatRuntime(data.stats.runtime);

                // 更新表格
                const tbody = document.getElementById('funding-table');
                tbody.innerHTML = data.summary.map((item, index) => {
                    const varFunding = formatFundingRate(item.var_funding);
                    const varInterval = formatInterval(item.var_interval);
                    const bpxFunding = formatFundingRate(item.bpx_funding);
                    const bpxInterval = formatInterval(item.bpx_interval);

                    // 格式化费率差
                    const fundingDiff = formatFundingRateDiff(item.funding_rate_diff);

                    // 费率差样式
                    let fundingDiffClass = '';
                    if (Math.abs(item.funding_rate_diff) > 0.02) {
                        fundingDiffClass = 'funding-extreme';
                    } else if (Math.abs(item.funding_rate_diff) > 0.01) {
                        fundingDiffClass = 'funding-high';
                    } else if (item.funding_rate_diff > 0) {
                        fundingDiffClass = 'funding-positive';
                    } else if (item.funding_rate_diff < 0) {
                        fundingDiffClass = 'funding-negative';
                    }

                    const varPrice = formatPrice(item.var_price);
                    const bpxPrice = formatPrice(item.bpx_price);

                    let priceSpreadText = '-';
                    let priceSpreadClass = '';
                    if (item.price_spread !== 0) {
                        priceSpreadText = (item.price_spread > 0 ? '+' : '') + item.price_spread.toFixed(3) + '%';
                        if (Math.abs(item.price_spread) > 0.5) {
                            priceSpreadClass = 'spread-large';
                        } else if (item.price_spread > 0) {
                            priceSpreadClass = 'spread-positive';
                        } else {
                            priceSpreadClass = 'spread-negative';
                        }
                    }

                    // VAR 资金费率样式
                    let varFundingClass = '';
                    if (Math.abs(item.var_funding) > 0.02) {
                        varFundingClass = 'funding-extreme';
                    } else if (Math.abs(item.var_funding) > 0.01) {
                        varFundingClass = 'funding-high';
                    } else if (item.var_funding > 0) {
                        varFundingClass = 'funding-positive';
                    } else if (item.var_funding < 0) {
                        varFundingClass = 'funding-negative';
                    }

                    // BP 资金费率样式
                    let bpxFundingClass = '';
                    if (item.bpx_funding === 0) {
                        bpxFundingClass = 'status-no';
                    } else if (Math.abs(item.bpx_funding) > 0.02) {
                        bpxFundingClass = 'funding-extreme';
                    } else if (Math.abs(item.bpx_funding) > 0.01) {
                        bpxFundingClass = 'funding-high';
                    } else if (item.bpx_funding > 0) {
                        bpxFundingClass = 'funding-positive';
                    } else if (item.bpx_funding < 0) {
                        bpxFundingClass = 'funding-negative';
                    }

                    // 推荐信息
                    const recommendation = item.recommendation || {text: '-', class: 'rec-none'};
                    const recText = recommendation.text;
                    const recClass = recommendation.class;

                    // 判断是否为高费率差机会
                    const isOpportunity = Math.abs(item.funding_rate_diff) > 0.01;
                    const rowClass = isOpportunity ? 'opportunity' : '';

                    return `
                        <tr class="${rowClass}">
                            <td style="color: #888;">${index + 1}</td>
                            <td class="symbol">${item.symbol}</td>
                            <td class="${varFundingClass}">${varFunding}</td>
                            <td style="color: #aaa; font-size: 12px;">${varInterval}</td>
                            <td class="${bpxFundingClass}">${bpxFunding}</td>
                            <td style="color: #aaa; font-size: 12px;">${bpxInterval}</td>
                            <td class="${fundingDiffClass}">${fundingDiff}</td>
                            <td class="price">${varPrice}</td>
                            <td class="price">${bpxPrice}</td>
                            <td class="${priceSpreadClass}">${priceSpreadText}</td>
                            <td class="${recClass}">${recText}</td>
                        </tr>
                    `;
                }).join('');

                // 更新时间
                document.getElementById('update-time').textContent =
                    '最后更新: ' + new Date().toLocaleTimeString('zh-CN') +
                    ' | 数据更新: ' + data.stats.last_update;

            } catch (error) {
                console.error('更新数据失败:', error);
            }
        }

        // 初始加载
        updateData();

        // 每5秒更新一次
        setInterval(updateData, 5000);
    </script>
</body>
</html>
    """
    return web.Response(text=html, content_type='text/html')

async def handle_api_data(request):
    """API接口"""
    # 获取limit参数，默认None（显示全部）
    limit_param = request.query.get('limit', None)
    limit = int(limit_param) if limit_param else None
    data = {
        'summary': store.get_summary(limit=limit),
        'stats': store.get_stats()
    }
    return web.json_response(data)

async def start_web_server():
    """启动Web服务器"""
    app = web.Application()
    app.router.add_get('/', handle_index)
    app.router.add_get('/api/data', handle_api_data)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', WEB_PORT)
    await site.start()

    print(f"\n{'='*70}")
    print(f"✓ Web服务器已启动")
    print(f"✓ 访问地址: http://127.0.0.1:{WEB_PORT}")
    print(f"{'='*70}\n")

# ==================== 主函数 ====================
async def main():
    print("\n" + "="*70)
    print("VAR 资金费率监控器")
    print("实时监控VAR交易所的资金费率，对比Backpack价格")
    print("="*70)

    # 启动所有任务
    await asyncio.gather(
        update_funding_rates(),
        start_web_server(),
        return_exceptions=True
    )

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n程序退出")

import requests
import time
from datetime import datetime
import asyncio
import os
from dotenv import load_dotenv
from telegram import Bot
from telegram.constants import ParseMode


class BinanceFundingRateBot:
    def __init__(self, config):
        """
        初始化机器人
        :param config: 配置字典
        """
        self.telegram_token = config['telegram_bot_token']
        self.chat_id = config['telegram_chat_id']
        self.threshold = config['threshold']
        self.abnormal_growth_threshold = config['abnormal_growth_threshold']
        self.abnormal_change_threshold = config['abnormal_change_threshold']
        self.check_interval = config['check_interval_hours']
        self.max_display_items = config['max_display_items']
        self.send_when_no_alert = config['send_when_no_alert']

        self.bot = Bot(token=self.telegram_token)
        self.base_url = "https://fapi.binance.com"
        self.previous_rates = {}

    def get_funding_rates(self):
        """获取所有合约的资金费率"""
        try:
            url = f"{self.base_url}/fapi/v1/premiumIndex"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()

            funding_rates = {}
            for item in data:
                symbol = item['symbol']
                # 资金费率已经是小数形式，例如 0.0001 表示 0.01%
                funding_rate = float(item.get('lastFundingRate', 0))
                funding_rates[symbol] = funding_rate

            return funding_rates
        except Exception as e:
            print(f"获取资金费率失败: {e}")
            return {}

    def analyze_rates(self, current_rates):
        """分析资金费率，返回高费率和异常增长的合约"""
        high_rate_symbols = []
        abnormal_growth_symbols = []

        for symbol, rate in current_rates.items():
            # 检查是否超过阈值
            if abs(rate) >= self.threshold:
                high_rate_symbols.append({
                    'symbol': symbol,
                    'rate': rate,
                    'rate_percent': rate * 100
                })

            # 检查是否异常增长
            if symbol in self.previous_rates:
                prev_rate = self.previous_rates[symbol]
                # 计算增长率，避免除零错误
                if prev_rate != 0:
                    growth = (rate - prev_rate) / abs(prev_rate)
                    # 如果增长超过设定阈值或者绝对变化超过设定值
                    if abs(growth) > self.abnormal_growth_threshold or abs(
                            rate - prev_rate) > self.abnormal_change_threshold:
                        abnormal_growth_symbols.append({
                            'symbol': symbol,
                            'current_rate': rate,
                            'previous_rate': prev_rate,
                            'current_percent': rate * 100,
                            'previous_percent': prev_rate * 100,
                            'change': (rate - prev_rate) * 100
                        })
                elif rate != 0:  # 从0变为非0
                    abnormal_growth_symbols.append({
                        'symbol': symbol,
                        'current_rate': rate,
                        'previous_rate': prev_rate,
                        'current_percent': rate * 100,
                        'previous_percent': 0,
                        'change': rate * 100
                    })

        # 按费率绝对值排序
        high_rate_symbols.sort(key=lambda x: abs(x['rate']), reverse=True)
        # 按变化幅度排序
        abnormal_growth_symbols.sort(key=lambda x: abs(x['change']), reverse=True)

        return high_rate_symbols, abnormal_growth_symbols

    def format_message(self, high_rate_symbols, abnormal_growth_symbols):
        """格式化Telegram消息"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        message = f"📊 <b>币安资金费率预警</b>\n"
        message += f"🕐 {timestamp}\n\n"

        # 高费率合约列表
        if high_rate_symbols:
            message += f"🔴 <b>高费率合约 (≥{self.threshold * 100}%)</b>\n"
            message += "━━━━━━━━━━━━━━━━\n"
            for item in high_rate_symbols[:self.max_display_items]:
                symbol = item['symbol']
                rate_percent = item['rate_percent']
                emoji = "📈" if rate_percent > 0 else "📉"
                message += f"{emoji} <code>{symbol:12s}</code> {rate_percent:>7.4f}%\n"
            if len(high_rate_symbols) > self.max_display_items:
                message += f"... 还有 {len(high_rate_symbols) - self.max_display_items} 个合约\n"
            message += "\n"

        # 异常增长合约列表
        if abnormal_growth_symbols:
            message += f"⚠️ <b>异常变动合约</b>\n"
            message += "━━━━━━━━━━━━━━━━\n"
            for item in abnormal_growth_symbols[:self.max_display_items]:
                symbol = item['symbol']
                current = item['current_percent']
                change = item['change']
                emoji = "🔺" if change > 0 else "🔻"
                message += f"{emoji} <code>{symbol:12s}</code>\n"
                message += f"   当前: {current:>7.4f}% | 变化: {change:>+7.4f}%\n"
            if len(abnormal_growth_symbols) > self.max_display_items:
                message += f"... 还有 {len(abnormal_growth_symbols) - self.max_display_items} 个合约\n"

        if not high_rate_symbols and not abnormal_growth_symbols:
            message += "✅ 暂无异常合约\n"

        return message

    async def send_telegram_message(self, message):
        """发送Telegram消息"""
        try:
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode=ParseMode.HTML
            )
            print(f"消息已发送到Telegram")
        except Exception as e:
            print(f"发送Telegram消息失败: {e}")

    async def check_and_alert(self):
        """检查费率并发送预警"""
        print(f"\n{'=' * 50}")
        print(f"开始检查资金费率: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        current_rates = self.get_funding_rates()

        if not current_rates:
            print("未能获取资金费率数据")
            return

        print(f"成功获取 {len(current_rates)} 个合约的资金费率")

        high_rate_symbols, abnormal_growth_symbols = self.analyze_rates(current_rates)

        print(f"发现 {len(high_rate_symbols)} 个高费率合约")
        print(f"发现 {len(abnormal_growth_symbols)} 个异常变动合约")

        # 根据配置决定是否发送消息
        if high_rate_symbols or abnormal_growth_symbols:
            message = self.format_message(high_rate_symbols, abnormal_growth_symbols)
            await self.send_telegram_message(message)
        elif self.send_when_no_alert:
            message = self.format_message(high_rate_symbols, abnormal_growth_symbols)
            await self.send_telegram_message(message)
        else:
            print("无异常情况，不发送消息")

        # 更新历史费率
        self.previous_rates = current_rates

    async def run(self):
        """运行机器人，定期检查"""
        print(f"资金费率预警机器人已启动")
        print(f"阈值设置: {self.threshold * 100}%")
        print(f"异常增长阈值: {self.abnormal_growth_threshold * 100}%")
        print(f"异常变化阈值: {self.abnormal_change_threshold * 100}%")
        print(f"检查间隔: {self.check_interval} 小时")
        print(f"Telegram Chat ID: {self.chat_id}")

        # 首次运行
        await self.check_and_alert()

        # 定期检查
        while True:
            await asyncio.sleep(self.check_interval * 3600)
            await self.check_and_alert()


def load_config():
    """从环境变量加载配置"""
    # 加载 .env 文件
    load_dotenv()

    # 检查必需的环境变量
    telegram_bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    telegram_chat_id = os.getenv('TELEGRAM_CHAT_ID')

    if not telegram_bot_token:
        raise ValueError("错误：未设置 TELEGRAM_BOT_TOKEN 环境变量")

    if not telegram_chat_id:
        raise ValueError("错误：未设置 TELEGRAM_CHAT_ID 环境变量")

    # 构建配置字典
    config = {
        'telegram_bot_token': telegram_bot_token,
        'telegram_chat_id': telegram_chat_id,
        'threshold': float(os.getenv('THRESHOLD', '0.01')),
        'abnormal_growth_threshold': float(os.getenv('ABNORMAL_GROWTH_THRESHOLD', '0.5')),
        'abnormal_change_threshold': float(os.getenv('ABNORMAL_CHANGE_THRESHOLD', '0.001')),
        'check_interval_hours': float(os.getenv('CHECK_INTERVAL_HOURS', '1')),
        'max_display_items': int(os.getenv('MAX_DISPLAY_ITEMS', '10')),
        'send_when_no_alert': os.getenv('SEND_WHEN_NO_ALERT', 'false').lower() == 'true'
    }

    return config


def create_env_example():
    """创建 .env.example 示例文件"""
    example_content = """# Telegram Bot 配置
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here

# 预警参数配置
# 高费率阈值 (默认: 0.01 即 1%)
THRESHOLD=0.01

# 异常增长比例阈值 (默认: 0.5 即 50%)
ABNORMAL_GROWTH_THRESHOLD=0.5

# 异常绝对变化阈值 (默认: 0.001 即 0.1%)
ABNORMAL_CHANGE_THRESHOLD=0.001

# 检查间隔（小时）
CHECK_INTERVAL_HOURS=1

# 显示配置
# 每个列表最多显示的合约数量
MAX_DISPLAY_ITEMS=10

# 无异常时是否也发送消息 (true/false)
SEND_WHEN_NO_ALERT=false
"""

    if not os.path.exists('.env.example'):
        with open('.env.example', 'w', encoding='utf-8') as f:
            f.write(example_content)
        print("已创建 .env.example 示例文件")

    if not os.path.exists('.env'):
        print("\n⚠️  请按以下步骤配置：")
        print("1. 复制 .env.example 为 .env")
        print("2. 编辑 .env 文件，填入你的实际配置")
        print("3. 重新运行程序")


async def main():
    try:
        # 创建示例配置文件
        create_env_example()

        # 加载配置
        config = load_config()

        # 创建并运行机器人
        bot = BinanceFundingRateBot(config)
        await bot.run()

    except ValueError as e:
        print(f"\n{e}")
        print("\n请检查 .env 文件配置是否正确")
    except Exception as e:
        print(f"\n程序运行出错: {e}")


if __name__ == "__main__":
    asyncio.run(main())
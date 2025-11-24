# 币安资金费率预警机器人

一个基于 Python 的自动化机器人，用于监控币安合约的资金费率，并通过 Telegram 推送实时预警信息。

## ✨ 功能特性

- 📊 **实时监控**：每小时自动获取币安所有合约的资金费率
- 🔴 **高费率预警**：监控超过设定阈值的合约（默认 1%）
- ⚠️ **异常变动预警**：检测资金费率显著变化的合约
- 📱 **Telegram 推送**：通过 Telegram Bot 实时接收预警消息
- ⚙️ **灵活配置**：通过 `.env` 文件轻松配置所有参数
- 🔒 **安全可靠**：敏感信息与代码分离，避免泄露风险

## 📋 前置要求

- Python 3.7+
- 币安账户（用于访问 API，无需 API Key）
- Telegram 账户

## 🚀 快速开始

### 1. 克隆项目

```bash
git clone <your-repo-url>
cd binance-funding-rate-bot
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

或手动安装：

```bash
pip install requests python-telegram-bot python-dotenv
```

### 3. 创建 Telegram Bot

#### 3.1 获取 Bot Token

1. 在 Telegram 中搜索 `@BotFather`
2. 发送 `/newbot` 命令
3. 按提示设置机器人名称和用户名
4. 获得你的 Bot Token（格式：`123456789:ABCdefGHIjklMNOpqrsTUVwxyz`）

#### 3.2 获取 Chat ID

**方法一：使用 @userinfobot**
1. 在 Telegram 中搜索 `@userinfobot`
2. 向它发送任意消息
3. 它会返回你的 Chat ID

**方法二：通过 API 获取**
1. 先向你的 Bot 发送任意消息（如 `/start`）
2. 在浏览器访问：
   ```
   https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates
   ```
3. 在返回的 JSON 中找到 `"chat":{"id":123456789}`

### 4. 配置环境变量

首次运行程序会自动创建 `.env.example`：

```bash
python funding_rate_bot.py
```

然后复制并编辑配置文件：

```bash
cp .env.example .env
nano .env  # 或使用其他编辑器
```

在 `.env` 文件中填入你的配置：

```env
# 必填配置
TELEGRAM_BOT_TOKEN=你的Bot Token
TELEGRAM_CHAT_ID=你的Chat ID

# 可选配置（以下为默认值，可根据需要修改）
THRESHOLD=0.01
ABNORMAL_GROWTH_THRESHOLD=0.5
ABNORMAL_CHANGE_THRESHOLD=0.001
CHECK_INTERVAL_HOURS=1
MAX_DISPLAY_ITEMS=10
SEND_WHEN_NO_ALERT=false
```

### 5. 运行机器人

```bash
python binance_funding_rate_bot.py
```

## ⚙️ 配置说明

### 必需配置

| 配置项 | 说明 | 示例 |
|--------|------|------|
| `TELEGRAM_BOT_TOKEN` | Telegram Bot Token | `123456789:ABC...` |
| `TELEGRAM_CHAT_ID` | 接收消息的 Chat ID | `987654321` |

### 可选配置

| 配置项 | 说明 | 默认值 | 建议值 |
|--------|------|--------|--------|
| `THRESHOLD` | 高费率阈值（小数） | `0.01` (1%) | 0.005-0.02 |
| `ABNORMAL_GROWTH_THRESHOLD` | 异常增长比例阈值 | `0.5` (50%) | 0.3-1.0 |
| `ABNORMAL_CHANGE_THRESHOLD` | 异常绝对变化阈值 | `0.001` (0.1%) | 0.0005-0.002 |
| `CHECK_INTERVAL_HOURS` | 检查间隔（小时） | `1` | 0.5-2 |
| `MAX_DISPLAY_ITEMS` | 每个列表最多显示数量 | `10` | 5-20 |
| `SEND_WHEN_NO_ALERT` | 无异常时是否发送 | `false` | true/false |

### 配置示例

#### 保守型（减少误报）
```env
THRESHOLD=0.02                      # 2% 才预警
ABNORMAL_GROWTH_THRESHOLD=1.0       # 增长 100% 才预警
ABNORMAL_CHANGE_THRESHOLD=0.002     # 变化 0.2% 才预警
```

#### 激进型（更敏感）
```env
THRESHOLD=0.005                     # 0.5% 就预警
ABNORMAL_GROWTH_THRESHOLD=0.3       # 增长 30% 就预警
ABNORMAL_CHANGE_THRESHOLD=0.0005    # 变化 0.05% 就预警
```

## 📱 消息示例

机器人会发送格式化的预警消息：

```
📊 币安资金费率预警
🕐 2024-01-15 14:30:00

🔴 高费率合约 (≥1%)
━━━━━━━━━━━━━━━━
📈 BTCUSDT      1.2500%
📉 ETHUSDT     -1.1200%
📈 BNBUSDT      1.0800%

⚠️ 异常变动合约
━━━━━━━━━━━━━━━━
🔺 SOLUSDT
   当前:  0.8000% | 变化: +0.6000%
🔻 ADAUSDT
   当前: -0.5000% | 变化: -0.4500%
```

## 🔧 常见问题

### Q: 如何在后台运行？

**Linux/Mac 使用 nohup：**
```bash
nohup python funding_rate_bot.py > output.log 2>&1 &
```

**使用 screen：**
```bash
screen -S funding_bot
python funding_rate_bot.py
# 按 Ctrl+A，然后按 D 退出 screen
# 恢复：screen -r funding_bot
```

**使用 systemd 服务（推荐）：**

创建 `/etc/systemd/system/funding-bot.service`：

```ini
[Unit]
Description=Binance Funding Rate Alert Bot
After=network.target

[Service]
Type=simple
User=your_username
WorkingDirectory=/path/to/your/bot
ExecStart=/usr/bin/python3 /path/to/your/bot/funding_rate_bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

然后启动服务：
```bash
sudo systemctl daemon-reload
sudo systemctl enable funding-bot
sudo systemctl start funding-bot
sudo systemctl status funding-bot
```

### Q: 如何查看日志？

如果使用 systemd：
```bash
sudo journalctl -u funding-bot -f
```

如果使用 nohup：
```bash
tail -f output.log
```

### Q: 收不到消息怎么办？

1. 确认 Bot Token 和 Chat ID 正确
2. 确保已向 Bot 发送过 `/start` 命令
3. 检查是否阻止了 Bot
4. 查看程序运行日志，确认是否有错误信息

### Q: 如何修改检查频率？

修改 `.env` 文件中的 `CHECK_INTERVAL_HOURS`：
```env
CHECK_INTERVAL_HOURS=0.5  # 每 30 分钟检查一次
CHECK_INTERVAL_HOURS=2    # 每 2 小时检查一次
```

### Q: 资金费率是什么？

资金费率是永续合约特有的机制，用于保持合约价格与现货价格一致：
- **正费率**：多头支付给空头，说明做多情绪浓厚
- **负费率**：空头支付给多头，说明做空情绪浓厚
- **高费率**：通常意味着市场情绪极端，可能有反转风险

## 📁 项目结构

```
binance-funding-rate-bot/
├── funding_rate_bot.py    # 主程序
├── .env                   # 配置文件（需创建，不提交到 Git）
├── .env.example           # 配置示例（自动生成）
├── .gitignore            # Git 忽略文件
├── requirements.txt       # Python 依赖
└── README.md             # 本文档
```

## 🔒 安全建议

1. **永远不要提交 `.env` 文件到 Git**
   ```bash
   # 添加到 .gitignore
   echo ".env" >> .gitignore
   ```

2. **定期更换 Bot Token**
   - 如果 Token 泄露，通过 @BotFather 重新生成

3. **限制 Bot 权限**
   - 只给 Bot 必要的权限
   - 不要将 Bot 添加到公开群组

4. **备份配置**
   - 妥善保管 `.env` 文件的备份
   - 不要将备份存储在公共位置

## 🛠️ 开发与贡献

### 依赖包说明

- `requests`: 用于调用币安 API
- `python-telegram-bot`: Telegram Bot SDK
- `python-dotenv`: 加载环境变量

### 本地开发

1. Fork 本项目
2. 创建功能分支：`git checkout -b feature/your-feature`
3. 提交更改：`git commit -am 'Add some feature'`
4. 推送分支：`git push origin feature/your-feature`
5. 提交 Pull Request

## 📄 许可证

MIT License

## 🙏 致谢

- [币安 API 文档](https://binance-docs.github.io/apidocs/futures/cn/)
- [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot)

## 📞 联系方式

如有问题或建议，欢迎：
- 提交 Issue
- 发起 Pull Request
- 通过 Telegram 联系

---

⚠️ **免责声明**：本项目仅供学习交流使用，不构成任何投资建议。加密货币交易具有高风险，请谨慎投资。

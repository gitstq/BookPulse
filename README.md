<p align="center">
  <img src="https://img.shields.io/badge/Version-1.0.0-blue?style=flat-square" alt="Version">
  <img src="https://img.shields.io/badge/Python-3.8+-green?style=flat-square" alt="Python">
  <img src="https://img.shields.io/badge/License-MIT-orange?style=flat-square" alt="License">
  <img src="https://img.shields.io/badge/Dependencies-Zero-success?style=flat-square" alt="Zero Dependencies">
  <img src="https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-informational?style=flat-square" alt="Cross Platform">
</p>

<h1 align="center">📚 BookPulse</h1>

<p align="center">
  <strong>Lightweight Personal Book Library Management & Reading Tracker CLI Engine</strong><br>
  轻量级个人书籍管理与阅读追踪CLI引擎
</p>

<p align="center">
  <a href="#-简体中文">简体中文</a> ·
  <a href="#-繁體中文">繁體中文</a> ·
  <a href="#-english">English</a>
</p>

---

<a id="-简体中文"></a>

## 🎉 项目介绍 | 简体中文

**BookPulse** 是一款轻量级的个人书籍管理与阅读追踪命令行工具，专为热爱阅读的开发者和书籍爱好者打造。

### 💡 灵感来源

在GitHub Trending上观察到 **BookLore** 等书籍管理项目的高热度，我们意识到开发者社区对个人书籍管理工具有着强烈需求。然而，现有方案多为重量级的Web应用，需要数据库服务器或复杂的部署流程。**BookPulse** 以CLI工具的形式重新定义了书籍管理——零外部依赖、开箱即用、数据完全本地化。

### 🌟 自研差异化亮点

- **零外部依赖** — 纯Python标准库实现，无需安装任何第三方包
- **SQLite本地存储** — 数据完全掌控在本地，隐私无忧
- **终端原生体验** — 彩色输出、表格渲染、进度条，终端操作即所得
- **全功能阅读追踪** — 进度记录、阅读笔记、连续阅读统计、目标管理
- **智能分析引擎** — 月度趋势图表、分类分布、阅读报告、书籍排行
- **灵活书单系统** — 自定义书单，支持想读/在读/已读等多种分类
- **数据导入导出** — 支持CSV/JSON格式，轻松迁移和备份

---

## ✨ 核心特性

| 功能模块 | 核心能力 |
|---------|---------|
| 📚 **书籍管理** | 添加/删除/更新/搜索书籍，支持ISBN、分类、标签、评分 |
| 📖 **阅读追踪** | 记录阅读进度、添加笔记、查看阅读历史和连续阅读天数 |
| 📊 **智能分析** | 月度阅读趋势图表、分类分布统计、阅读报告生成 |
| 🎯 **目标管理** | 设置年度/月度阅读目标，实时追踪完成进度 |
| 📋 **书单系统** | 创建自定义书单，灵活管理想读/在读/已读书目 |
| 💾 **数据管理** | SQLite存储、自动备份、数据导入导出、数据库优化 |
| 🎨 **终端UI** | 彩色输出、表格渲染、进度条、交互式面板 |

---

## 🚀 快速开始

### 环境要求

- **Python** 3.8 或更高版本
- 无需任何第三方依赖

### 安装

```bash
# 克隆仓库
git clone https://github.com/gitstq/BookPulse.git
cd BookPulse

# 安装（可选）
pip install .
```

### 一键运行

```bash
# 直接运行
python -m bookpulse --help

# 查看版本
python -m bookpulse -v
```

### 快速上手

```bash
# 添加一本书
python -m bookpulse book add -t "深入理解计算机系统" -a "Randal E. Bryant" -c "计算机科学" --tags "经典,系统" --pages 988

# 查看所有书籍
python -m bookpulse book list

# 开始阅读
python -m bookpulse read start 1

# 更新阅读进度
python -m bookpulse read progress 1 -p 256

# 添加阅读笔记
python -m bookpulse read note 1 -t "第三章关于程序的机器级表示非常精彩"

# 查看当前在读
python -m bookpulse read current

# 查看阅读统计
python -m bookpulse analytics summary

# 生成阅读报告
python -m bookpulse analytics report
```

---

## 📖 详细使用指南

### 书籍管理

```bash
# 添加书籍（完整参数）
python -m bookpulse book add \
  -t "设计模式" \
  -a "Erich Gamma" \
  --isbn "978-7-111-07575-2" \
  --publisher "机械工业出版社" \
  --year 2000 \
  -c "软件工程" \
  --tags "经典,设计模式,Gang of Four" \
  --rating 5 \
  --pages 416

# 搜索书籍
python -m bookpulse book search "设计模式"
python -m bookpulse book search "Gamma" -f author

# 更新书籍信息
python -m bookpulse book update 1 --rating 4.5 -c "软件工程/经典"

# 按分类列出书籍
python -m bookpulse book list -c "计算机科学"

# 导出书籍数据
python -m bookpulse book export my_books.json
python -m bookpulse book export my_books.csv

# 从文件导入
python -m bookpulse book import books.json

# 查看书库统计
python -m bookpulse book stats
```

### 阅读追踪

```bash
# 开始阅读
python -m bookpulse read start 1

# 更新进度（按页码）
python -m bookpulse read progress 1 -p 256

# 更新进度（按百分比）
python -m bookpulse read progress 1 --percent 25

# 标记完成
python -m bookpulse read finish 1

# 查看阅读历史
python -m bookpulse read history
python -m bookpulse read history -b 1 --limit 50

# 查看连续阅读天数
python -m bookpulse read streak
```

### 智能分析

```bash
# 阅读总览
python -m bookpulse analytics summary

# 月度阅读趋势图
python -m bookpulse analytics chart -t monthly --months 12

# 分类分布图
python -m bookpulse analytics chart -t category

# 阅读状态分布
python -m bookpulse analytics chart -t status

# 设置阅读目标
python -m bookpulse analytics goal set --type yearly --target 52 --period 2025

# 查看目标进度
python -m bookpulse analytics goal show

# 生成阅读报告
python -m bookpulse analytics report

# 书籍排行榜
python -m bookpulse analytics ranking -s rating --limit 10
```

### 书单管理

```bash
# 创建书单
python -m bookpulse booklist create "2025必读书单" -d "今年计划读完的书"

# 添加书籍到书单
python -m bookpulse booklist add "2025必读书单" 1

# 查看书单
python -m bookpulse booklist show "2025必读书单"

# 列出所有书单
python -m bookpulse booklist list
```

### 数据管理

```bash
# 创建备份
python -m bookpulse data backup

# 恢复备份
python -m bookpulse data restore ~/.bookpulse/backups/bookpulse_20250518.db

# 查看数据库信息
python -m bookpulse data info

# 优化数据库
python -m bookpulse data vacuum
```

---

## 💡 设计思路与迭代规划

### 设计理念

BookPulse遵循 **"极简但不简陋"** 的设计哲学：
- **零依赖** — 降低使用门槛，任何Python环境都能直接运行
- **本地优先** — 数据存储在本地SQLite，无需网络连接，隐私完全可控
- **终端原生** — 充分利用终端能力，提供媲美GUI的操作体验

### 技术选型

| 组件 | 选型 | 原因 |
|-----|------|------|
| 语言 | Python 3.8+ | 生态成熟、跨平台、标准库丰富 |
| 存储 | SQLite | 零配置、嵌入式、标准库内置 |
| CLI | argparse | 标准库内置、功能完善 |
| UI | ANSI转义码 | 零依赖实现彩色终端输出 |

### 后续迭代计划

- [ ] 📡 **在线书籍信息获取** — 通过ISBN自动获取书籍元数据
- [ ] 🔄 **数据同步** — 支持多设备间数据同步
- [ ] 🌐 **Web仪表盘** — 提供可选的Web界面查看阅读统计
- [ ] 📱 **移动端适配** — 优化移动终端显示效果
- [ ] 🔔 **阅读提醒** — 定时提醒阅读目标和待读书籍

---

## 📦 安装与部署

### 从源码安装

```bash
git clone https://github.com/gitstq/BookPulse.git
cd BookPulse
pip install .
```

### 使用pip安装（计划中）

```bash
pip install bookpulse
```

### 数据存储位置

- **Linux/macOS**: `~/.bookpulse/bookpulse.db`
- **Windows**: `%USERPROFILE%\.bookpulse\bookpulse.db`

### 自定义数据库路径

```bash
python -m bookpulse --db /path/to/custom.db book list
```

---

## 🤝 贡献指南

欢迎任何形式的贡献！请遵循以下流程：

1. **Fork** 本仓库
2. 创建特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'feat: add amazing feature'`)
4. 推送分支 (`git push origin feature/amazing-feature`)
5. 创建 **Pull Request**

### 提交规范

- `feat:` 新增功能
- `fix:` 修复问题
- `docs:` 文档更新
- `refactor:` 代码重构
- `test:` 测试相关
- `chore:` 构建/工具变更

---

## 📄 开源协议

本项目基于 [MIT License](LICENSE) 开源。

---

<a id="-繁體中文"></a>

## 🎉 專案介紹 | 繁體中文

**BookPulse** 是一款輕量級的個人書籍管理與閱讀追蹤命令列工具，專為熱愛閱讀的開發者和書籍愛好者打造。

### 💡 靈感來源

在GitHub Trending上觀察到 **BookLore** 等書籍管理專案的高熱度，我們意識到開發者社群對個人書籍管理工具有著強烈需求。然而，現有方案多為重量級的Web應用，需要資料庫伺服器或複雜的部署流程。**BookPulse** 以CLI工具的形式重新定義了書籍管理——零外部依賴、開箱即用、資料完全本地化。

### 🌟 自研差異化亮點

- **零外部依賴** — 純Python標準庫實現，無需安裝任何第三方套件
- **SQLite本地儲存** — 資料完全掌控在本地，隱私無憂
- **終端原生體驗** — 彩色輸出、表格渲染、進度條，終端操作即所得
- **全功能閱讀追蹤** — 進度記錄、閱讀筆記、連續閱讀統計、目標管理
- **智慧分析引擎** — 月度趨勢圖表、分類分佈、閱讀報告、書籍排行
- **靈活書單系統** — 自訂書單，支援想讀/在讀/已讀等多種分類
- **資料匯入匯出** — 支援CSV/JSON格式，輕鬆遷移和備份

---

## ✨ 核心特性

| 功能模組 | 核心能力 |
|---------|---------|
| 📚 **書籍管理** | 新增/刪除/更新/搜尋書籍，支援ISBN、分類、標籤、評分 |
| 📖 **閱讀追蹤** | 記錄閱讀進度、新增筆記、查看閱讀歷史和連續閱讀天數 |
| 📊 **智慧分析** | 月度閱讀趨勢圖表、分類分佈統計、閱讀報告生成 |
| 🎯 **目標管理** | 設定年度/月度閱讀目標，即時追蹤完成進度 |
| 📋 **書單系統** | 建立自訂書單，靈活管理想讀/在讀/已讀書目 |
| 💾 **資料管理** | SQLite儲存、自動備份、資料匯入匯出、資料庫最佳化 |
| 🎨 **終端UI** | 彩色輸出、表格渲染、進度條、互動式面板 |

---

## 🚀 快速開始

### 環境需求

- **Python** 3.8 或更高版本
- 無需任何第三方依賴

### 安裝

```bash
# 克隆倉庫
git clone https://github.com/gitstq/BookPulse.git
cd BookPulse

# 安裝（可選）
pip install .
```

### 一鍵運行

```bash
# 直接運行
python -m bookpulse --help

# 查看版本
python -m bookpulse -v
```

### 快速上手

```bash
# 新增一本書
python -m bookpulse book add -t "深入理解計算機系統" -a "Randal E. Bryant" -c "計算機科學" --tags "經典,系統" --pages 988

# 查看所有書籍
python -m bookpulse book list

# 開始閱讀
python -m bookpulse read start 1

# 更新閱讀進度
python -m bookpulse read progress 1 -p 256

# 新增閱讀筆記
python -m bookpulse read note 1 -t "第三章關於程式的機器級表示非常精彩"

# 查看目前在讀
python -m bookpulse read current

# 查看閱讀統計
python -m bookpulse analytics summary

# 生成閱讀報告
python -m bookpulse analytics report
```

---

## 📖 詳細使用指南

### 書籍管理

```bash
# 新增書籍（完整參數）
python -m bookpulse book add \
  -t "設計模式" \
  -a "Erich Gamma" \
  --isbn "978-7-111-07575-2" \
  --publisher "機械工業出版社" \
  --year 2000 \
  -c "軟體工程" \
  --tags "經典,設計模式,Gang of Four" \
  --rating 5 \
  --pages 416

# 搜尋書籍
python -m bookpulse book search "設計模式"
python -m bookpulse book search "Gamma" -f author

# 更新書籍資訊
python -m bookpulse book update 1 --rating 4.5 -c "軟體工程/經典"

# 按分類列出書籍
python -m bookpulse book list -c "計算機科學"

# 匯出書籍資料
python -m bookpulse book export my_books.json
python -m bookpulse book export my_books.csv

# 從檔案匯入
python -m bookpulse book import books.json

# 查看書庫統計
python -m bookpulse book stats
```

### 閱讀追蹤

```bash
# 開始閱讀
python -m bookpulse read start 1

# 更新進度（按頁碼）
python -m bookpulse read progress 1 -p 256

# 更新進度（按百分比）
python -m bookpulse read progress 1 --percent 25

# 標記完成
python -m bookpulse read finish 1

# 查看閱讀歷史
python -m bookpulse read history
python -m bookpulse read history -b 1 --limit 50

# 查看連續閱讀天數
python -m bookpulse read streak
```

### 智慧分析

```bash
# 閱讀總覽
python -m bookpulse analytics summary

# 月度閱讀趨勢圖
python -m bookpulse analytics chart -t monthly --months 12

# 分類分佈圖
python -m bookpulse analytics chart -t category

# 閱讀狀態分佈
python -m bookpulse analytics chart -t status

# 設定閱讀目標
python -m bookpulse analytics goal set --type yearly --target 52 --period 2025

# 查看目標進度
python -m bookpulse analytics goal show

# 生成閱讀報告
python -m bookpulse analytics report

# 書籍排行榜
python -m bookpulse analytics ranking -s rating --limit 10
```

### 書單管理

```bash
# 建立書單
python -m bookpulse booklist create "2025必讀書單" -d "今年計畫讀完的書"

# 新增書籍到書單
python -m bookpulse booklist add "2025必讀書單" 1

# 查看書單
python -m bookpulse booklist show "2025必讀書單"

# 列出所有書單
python -m bookpulse booklist list
```

### 資料管理

```bash
# 建立備份
python -m bookpulse data backup

# 還原備份
python -m bookpulse data restore ~/.bookpulse/backups/bookpulse_20250518.db

# 查看資料庫資訊
python -m bookpulse data info

# 最佳化資料庫
python -m bookpulse data vacuum
```

---

## 💡 設計思路與迭代規劃

### 設計理念

BookPulse遵循 **「極簡但不簡陋」** 的設計哲學：
- **零依賴** — 降低使用門檻，任何Python環境都能直接運行
- **本地優先** — 資料儲存在本地SQLite，無需網路連接，隱私完全可控
- **終端原生** — 充分利用終端能力，提供媲美GUI的操作體驗

### 後續迭代計畫

- [ ] 📡 **線上書籍資訊獲取** — 透過ISBN自動獲取書籍元資料
- [ ] 🔄 **資料同步** — 支援多裝置間資料同步
- [ ] 🌐 **Web儀表板** — 提供可選的Web介面查看閱讀統計
- [ ] 📱 **行動端適配** — 最佳化行動終端顯示效果
- [ ] 🔔 **閱讀提醒** — 定時提醒閱讀目標和待讀書籍

---

## 🤝 貢獻指南

歡迎任何形式的貢獻！請遵循以下流程：

1. **Fork** 本倉庫
2. 建立特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交變更 (`git commit -m 'feat: add amazing feature'`)
4. 推送分支 (`git push origin feature/amazing-feature`)
5. 建立 **Pull Request**

---

## 📄 開源協議

本專案基於 [MIT License](LICENSE) 開源。

---

<a id="-english"></a>

## 🎉 Introduction

**BookPulse** is a lightweight personal book library management and reading tracker CLI engine, designed for developers and book lovers who live in the terminal.

### 💡 Inspiration

Observing the popularity of book management projects like **BookLore** on GitHub Trending, we recognized a strong demand for personal book management tools in the developer community. However, existing solutions are mostly heavyweight web applications requiring database servers or complex deployment. **BookPulse** reimagines book management as a CLI tool — zero external dependencies, ready to use out of the box, with fully local data storage.

### 🌟 Differentiation Highlights

- **Zero Dependencies** — Built entirely with Python standard library, no third-party packages needed
- **SQLite Local Storage** — Your data stays on your machine, privacy guaranteed
- **Native Terminal Experience** — Colorful output, table rendering, progress bars — everything works in your terminal
- **Full-featured Reading Tracker** — Progress tracking, reading notes, reading streaks, and goal management
- **Intelligent Analytics Engine** — Monthly trend charts, category distribution, reading reports, book rankings
- **Flexible Booklist System** — Create custom booklists for to-read, currently-reading, finished, and more
- **Data Import/Export** — CSV/JSON format support for easy migration and backup

---

## ✨ Core Features

| Module | Capabilities |
|--------|-------------|
| 📚 **Book Management** | Add/remove/update/search books with ISBN, category, tags, and ratings |
| 📖 **Reading Tracker** | Track reading progress, add notes, view history and reading streaks |
| 📊 **Analytics** | Monthly trend charts, category distribution, reading report generation |
| 🎯 **Goal Management** | Set yearly/monthly reading goals with real-time progress tracking |
| 📋 **Booklist System** | Create custom booklists for flexible reading organization |
| 💾 **Data Management** | SQLite storage, auto-backup, import/export, database optimization |
| 🎨 **Terminal UI** | Colored output, table rendering, progress bars, interactive panels |

---

## 🚀 Quick Start

### Requirements

- **Python** 3.8 or higher
- No third-party dependencies required

### Installation

```bash
# Clone the repository
git clone https://github.com/gitstq/BookPulse.git
cd BookPulse

# Install (optional)
pip install .
```

### Run

```bash
# Run directly
python -m bookpulse --help

# Check version
python -m bookpulse -v
```

### Quick Demo

```bash
# Add a book
python -m bookpulse book add -t "Clean Code" -a "Robert C. Martin" -c "Software Engineering" --tags "classic,clean-code" --pages 464

# List all books
python -m bookpulse book list

# Start reading
python -m bookpulse read start 1

# Update progress
python -m bookpulse read progress 1 -p 128

# Add a reading note
python -m bookpulse read note 1 -t "Chapter 5 on formatting is eye-opening"

# View currently reading
python -m bookpulse read current

# View reading summary
python -m bookpulse analytics summary

# Generate reading report
python -m bookpulse analytics report
```

---

## 📖 Detailed Usage Guide

### Book Management

```bash
# Add a book (full parameters)
python -m bookpulse book add \
  -t "Design Patterns" \
  -a "Erich Gamma" \
  --isbn "978-0-201-63361-0" \
  --publisher "Addison-Wesley" \
  --year 1994 \
  -c "Software Engineering" \
  --tags "classic,design-patterns,GoF" \
  --rating 5 \
  --pages 416

# Search books
python -m bookpulse book search "Design Patterns"
python -m bookpulse book search "Gamma" -f author

# Update book info
python -m bookpulse book update 1 --rating 4.5 -c "Software Engineering/Classic"

# List books by category
python -m bookpulse book list -c "Software Engineering"

# Export books
python -m bookpulse book export my_books.json
python -m bookpulse book export my_books.csv

# Import from file
python -m bookpulse book import books.json

# View library statistics
python -m bookpulse book stats
```

### Reading Tracker

```bash
# Start reading
python -m bookpulse read start 1

# Update progress (by page)
python -m bookpulse read progress 1 -p 256

# Update progress (by percentage)
python -m bookpulse read progress 1 --percent 25

# Mark as finished
python -m bookpulse read finish 1

# View reading history
python -m bookpulse read history
python -m bookpulse read history -b 1 --limit 50

# View reading streak
python -m bookpulse read streak
```

### Analytics

```bash
# Reading summary
python -m bookpulse analytics summary

# Monthly reading trend chart
python -m bookpulse analytics chart -t monthly --months 12

# Category distribution chart
python -m bookpulse analytics chart -t category

# Reading status distribution
python -m bookpulse analytics chart -t status

# Set reading goal
python -m bookpulse analytics goal set --type yearly --target 52 --period 2025

# View goal progress
python -m bookpulse analytics goal show

# Generate reading report
python -m bookpulse analytics report

# Book rankings
python -m bookpulse analytics ranking -s rating --limit 10
```

### Booklist Management

```bash
# Create a booklist
python -m bookpulse booklist create "2025 Must-Read" -d "Books I plan to finish this year"

# Add a book to booklist
python -m bookpulse booklist add "2025 Must-Read" 1

# View booklist
python -m bookpulse booklist show "2025 Must-Read"

# List all booklists
python -m bookpulse booklist list
```

### Data Management

```bash
# Create backup
python -m bookpulse data backup

# Restore from backup
python -m bookpulse data restore ~/.bookpulse/backups/bookpulse_20250518.db

# View database info
python -m bookpulse data info

# Optimize database
python -m bookpulse data vacuum
```

---

## 💡 Design Philosophy & Roadmap

### Design Principles

BookPulse follows the philosophy of **"Minimal but Not Minimalist"**:
- **Zero Dependencies** — Lower the barrier to entry, runs in any Python environment
- **Local First** — Data stored in local SQLite, no network required, full privacy control
- **Terminal Native** — Leverage terminal capabilities for a GUI-like experience

### Tech Stack

| Component | Choice | Reason |
|-----------|--------|--------|
| Language | Python 3.8+ | Mature ecosystem, cross-platform, rich standard library |
| Storage | SQLite | Zero-config, embedded, built into standard library |
| CLI | argparse | Built-in, feature-complete |
| UI | ANSI escape codes | Zero-dependency colored terminal output |

### Roadmap

- [ ] 📡 **Online Book Metadata** — Auto-fetch book info via ISBN
- [ ] 🔄 **Data Sync** — Cross-device data synchronization
- [ ] 🌐 **Web Dashboard** — Optional web interface for reading statistics
- [ ] 📱 **Mobile Optimization** — Better display on mobile terminals
- [ ] 🔔 **Reading Reminders** — Scheduled reminders for reading goals

---

## 📦 Installation & Deployment

### Install from Source

```bash
git clone https://github.com/gitstq/BookPulse.git
cd BookPulse
pip install .
```

### Install via pip (Coming Soon)

```bash
pip install bookpulse
```

### Data Storage Location

- **Linux/macOS**: `~/.bookpulse/bookpulse.db`
- **Windows**: `%USERPROFILE%\.bookpulse\bookpulse.db`

### Custom Database Path

```bash
python -m bookpulse --db /path/to/custom.db book list
```

---

## 🤝 Contributing

Contributions of all kinds are welcome! Please follow these steps:

1. **Fork** this repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'feat: add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Create a **Pull Request**

### Commit Convention

- `feat:` New features
- `fix:` Bug fixes
- `docs:` Documentation updates
- `refactor:` Code refactoring
- `test:` Test-related changes
- `chore:` Build/tooling changes

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).

---

<p align="center">
  Made with ❤️ by <a href="https://github.com/gitstq">gitstq</a>
</p>

# 历史事件档案馆 · Chronicle Atlas

一个基于 Web 的历史事件记录与检索系统。支持按时间、地点、人物、标签录入历史事件，并可附加文字、链接、图片/音频/视频等史料来源。

## 技术栈

| 层级 | 技术 |
|------|------|
| 后端 | Node.js + Express 5 |
| 数据库 | SQLite（better-sqlite3） |
| 文件上传 | Multer |
| 前端 | 原生 HTML / CSS / JavaScript |

---

## 快速开始

### 1. 安装依赖

```bash
npm install
```

### 2. 启动服务器

```bash
node server.js
```

启动成功后终端输出：

```
Server running at http://localhost:3000
```

### 3. 打开浏览器访问

```
http://localhost:3000
```

### 4. 停止服务器

在终端按 `Ctrl + C`。

---

## 常见问题

### 原生模块版本不匹配

如果启动时报错 `ERR_DLOPEN_FAILED` 或提示 `NODE_MODULE_VERSION` 不匹配，说明依赖中的原生模块（`better-sqlite3`）是在其他 Node.js 版本下编译的，需要针对当前版本重新编译：

```bash
npm rebuild
```

执行一次即可，之后正常用 `node server.js` 启动。

---

## 项目结构

```
operating-system/
├── server.js          # Express 后端 + REST API
├── public/
│   ├── index.html     # 主页面
│   ├── styles.css     # 样式
│   └── app.js         # 前端交互逻辑
├── data/
│   └── events.db      # SQLite 数据库（自动创建）
└── uploads/           # 上传的附件文件（自动创建）
```

---

## 功能说明

### 录入事件

填写以下字段后点击「提交事件」：

| 字段 | 说明 | 必填 |
|------|------|------|
| 时间类型 | 公元 / 公元前 | ✅ |
| 年份 | 整数，如 221、1949 | ✅ |
| 精确日期 | 可选，格式 YYYY-MM-DD | — |
| 地点 | 事件发生地点 | ✅ |
| 人物 | 相关人物 | ✅ |
| 事件标题 | 简短标题 | ✅ |
| 事件内容 | 详细描述 | ✅ |
| 标签 | 逗号分隔，如：政治, 战争 | — |
| 史料 | 可添加多条文字/链接 | — |
| 附件 | 可上传图片/音频/视频/文件（多选）| — |

### 筛选与检索

| 筛选条件 | 说明 |
|----------|------|
| 起始/结束年份 | 按年代范围过滤，支持负数（公元前）|
| 地点 | 模糊匹配 |
| 人物 | 模糊匹配 |
| 标签 | 精确匹配单个标签 |

点击「重置」清空所有筛选条件，恢复全量列表。

---

## API 接口

### 获取事件列表

```
GET /api/events
```

查询参数（均可选）：

| 参数 | 类型 | 说明 |
|------|------|------|
| startYear | number | 起始年份（含），公元前用负数 |
| endYear | number | 结束年份（含） |
| location | string | 地点（模糊匹配） |
| person | string | 人物（模糊匹配） |
| tag | string | 标签（模糊匹配） |

### 新增事件

```
POST /api/events
Content-Type: multipart/form-data
```

| 字段 | 类型 | 说明 |
|------|------|------|
| timeType | string | `ad`（公元）或 `bc`（公元前） |
| yearValue | number | 年份正整数 |
| exactDate | string | 精确日期，可选 |
| location | string | 地点 |
| person | string | 人物 |
| title | string | 事件标题 |
| description | string | 事件内容 |
| tags | string | 标签，逗号分隔 |
| sources | string | JSON 字符串，格式见下 |
| files | file[] | 附件文件，可多选 |

`sources` 格式示例：

```json
[
  { "type": "text", "content": "《史记》相关记载" },
  { "type": "image", "content": "https://example.com/image.jpg" }
]
```

`type` 可选值：`text` / `image` / `audio` / `video` / `file`

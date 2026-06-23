# Timeline API 接口文档（可落地）

## 1. 文档信息

- 基础路径：`/api/v1`
- 数据格式：`application/json; charset=utf-8`
- 时间格式：`ISO 8601`（如 `2026-04-09T12:00:00Z`）
- 日期字段（业务日期）：`YYYY-MM-DD`（如 `2025-11-03`）
- 字符编码：`UTF-8`

---

## 2. 鉴权与通用约定

### 2.1 鉴权

- 开发阶段可先不鉴权。
- 生产建议使用 Bearer Token：
  - Header: `Authorization: Bearer <token>`

### 2.2 通用响应结构

```json
{
  "code": 0,
  "message": "ok",
  "data": {}
}
```

- `code = 0` 表示成功
- `code != 0` 表示业务或参数错误

### 2.3 分页响应结构

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "items": [],
    "page": 1,
    "pageSize": 20,
    "total": 108
  }
}
```

### 2.4 错误响应结构

```json
{
  "code": 1001,
  "message": "validation failed",
  "details": [
    {
      "field": "title",
      "reason": "required"
    }
  ]
}
```

---

## 3. 数据模型

## 3.1 TimelineEntry

```json
{
  "id": 123,
  "title": "First light in Kyoto",
  "date": "2025-11-03",
  "type": "image",
  "content": "Early morning walk...",
  "image": "https://images.unsplash.com/xxx",
  "createdAt": "2026-04-09T12:00:00Z",
  "updatedAt": "2026-04-09T12:00:00Z"
}
```

字段说明：

- `id`: `number`，主键，后端生成
- `title`: `string`，必填，长度 `1-120`
- `date`: `string`，必填，格式 `YYYY-MM-DD`
- `type`: `string`，必填，枚举：`note | idea | event | image`
- `content`: `string`，可选，最大长度建议 `5000`
- `image`: `string`，可选，URL，最大长度建议 `1024`
- `createdAt`: `string`，后端生成
- `updatedAt`: `string`，后端生成

---

## 4. 接口清单

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/timeline-entries` | 获取时间线列表（支持筛选分页） |
| GET | `/timeline-entries/:id` | 获取单条详情 |
| POST | `/timeline-entries` | 创建条目 |
| PUT | `/timeline-entries/:id` | 全量更新条目 |
| PATCH | `/timeline-entries/:id` | 部分更新条目（可选实现） |
| DELETE | `/timeline-entries/:id` | 删除条目 |
| GET | `/timeline-entries/stats` | 统计信息（可选实现） |
| GET | `/health` | 健康检查 |

---

## 5. 详细接口定义

## 5.1 获取列表

- 方法：`GET`
- 路径：`/api/v1/timeline-entries`

Query 参数：

- `type`：可选，`note | idea | event | image`
- `year`：可选，4 位年份，如 `2025`
- `q`：可选，关键词，搜索 `title/content`
- `page`：可选，默认 `1`
- `pageSize`：可选，默认 `20`，最大 `100`
- `sort`：可选，默认 `date_desc`，可选：
  - `date_desc`
  - `date_asc`
  - `created_desc`
  - `created_asc`

请求示例：

```bash
curl -X GET "http://localhost:3000/api/v1/timeline-entries?type=note&page=1&pageSize=20&sort=date_desc"
```

响应示例：

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "items": [
      {
        "id": 4,
        "title": "Notes on Deep Work",
        "date": "2025-09-10",
        "type": "note",
        "content": "Cal Newport's core argument...",
        "image": "",
        "createdAt": "2026-04-09T09:00:00Z",
        "updatedAt": "2026-04-09T09:00:00Z"
      }
    ],
    "page": 1,
    "pageSize": 20,
    "total": 1
  }
}
```

---

## 5.2 获取详情

- 方法：`GET`
- 路径：`/api/v1/timeline-entries/:id`

请求示例：

```bash
curl -X GET "http://localhost:3000/api/v1/timeline-entries/4"
```

成功响应：

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "id": 4,
    "title": "Notes on Deep Work",
    "date": "2025-09-10",
    "type": "note",
    "content": "Cal Newport's core argument...",
    "image": "",
    "createdAt": "2026-04-09T09:00:00Z",
    "updatedAt": "2026-04-09T09:00:00Z"
  }
}
```

失败响应（不存在）：

```json
{
  "code": 1004,
  "message": "entry not found"
}
```

---

## 5.3 创建条目

- 方法：`POST`
- 路径：`/api/v1/timeline-entries`

请求体：

```json
{
  "title": "Ship the redesign",
  "date": "2025-09-27",
  "type": "event",
  "content": "Finally pushed the new dashboard to prod.",
  "image": ""
}
```

字段校验：

- `title` 必填，`1-120`
- `date` 必填，合法日期
- `type` 必填，且在枚举内
- `content` 可空，最长建议 `5000`
- `image` 可空；有值时需为合法 URL

请求示例：

```bash
curl -X POST "http://localhost:3000/api/v1/timeline-entries" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Ship the redesign",
    "date": "2025-09-27",
    "type": "event",
    "content": "Finally pushed the new dashboard to prod.",
    "image": ""
  }'
```

成功响应（建议 `201 Created`）：

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "id": 9,
    "title": "Ship the redesign",
    "date": "2025-09-27",
    "type": "event",
    "content": "Finally pushed the new dashboard to prod.",
    "image": "",
    "createdAt": "2026-04-09T12:30:00Z",
    "updatedAt": "2026-04-09T12:30:00Z"
  }
}
```

---

## 5.4 更新条目（PUT）

- 方法：`PUT`
- 路径：`/api/v1/timeline-entries/:id`

说明：

- `PUT` 按“全量覆盖”语义实现，前端应传完整字段。

请求体示例：

```json
{
  "title": "Ship the redesign v2",
  "date": "2025-09-28",
  "type": "event",
  "content": "Updated summary.",
  "image": "https://example.com/a.jpg"
}
```

成功响应：

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "id": 9,
    "title": "Ship the redesign v2",
    "date": "2025-09-28",
    "type": "event",
    "content": "Updated summary.",
    "image": "https://example.com/a.jpg",
    "createdAt": "2026-04-09T12:30:00Z",
    "updatedAt": "2026-04-09T12:45:00Z"
  }
}
```

---

## 5.5 部分更新（PATCH，可选）

- 方法：`PATCH`
- 路径：`/api/v1/timeline-entries/:id`

请求体示例：

```json
{
  "title": "Only change title"
}
```

说明：

- 仅更新请求体中出现的字段。
- 与 `PUT` 二选一也可；若团队不想维护两套语义，可只保留 `PUT`。

---

## 5.6 删除条目

- 方法：`DELETE`
- 路径：`/api/v1/timeline-entries/:id`

请求示例：

```bash
curl -X DELETE "http://localhost:3000/api/v1/timeline-entries/9"
```

成功响应：

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "deleted": true
  }
}
```

---

## 5.7 统计接口（可选）

- 方法：`GET`
- 路径：`/api/v1/timeline-entries/stats`

响应示例：

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "total": 8,
    "byType": {
      "note": 2,
      "idea": 2,
      "event": 2,
      "image": 2
    },
    "byYear": {
      "2025": 8
    }
  }
}
```

---

## 5.8 健康检查

- 方法：`GET`
- 路径：`/api/v1/health`

响应示例：

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "status": "UP",
    "timestamp": "2026-04-09T12:00:00Z"
  }
}
```

---

## 6. 错误码建议

| code | 含义 | HTTP 状态码 |
| --- | --- | --- |
| 0 | 成功 | 200/201 |
| 1001 | 参数校验失败 | 400 |
| 1002 | 未授权 | 401 |
| 1003 | 禁止访问 | 403 |
| 1004 | 资源不存在 | 404 |
| 1009 | 版本冲突（可选） | 409 |
| 1500 | 服务端错误 | 500 |

---

## 7. 与现有前端字段映射

当前前端 `timeline.html` 使用的核心字段：

- `id`
- `title`
- `date`
- `type`
- `content`
- `image`

后端保持同名字段可最小化前端改造成本。

---

## 8. 前后端联调建议

## 8.1 推荐调用顺序

1. 页面加载：`GET /timeline-entries`
2. 筛选：`GET /timeline-entries?type=...`
3. 新增：`POST /timeline-entries`
4. 查看：`GET /timeline-entries/:id`
5. 编辑：`PUT /timeline-entries/:id`
6. 删除：`DELETE /timeline-entries/:id`

## 8.2 最小联调清单

- 列表空态是否正确返回 `items: []`
- 日期格式错误是否返回 `1001`
- `type` 非法值是否返回 `1001`
- 删除不存在 ID 是否返回 `1004`
- 分页边界（`pageSize > 100`）是否被限制

---

## 9. 可直接用于实现的数据库草案（可选）

以 MySQL 为例：

```sql
CREATE TABLE timeline_entries (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  title VARCHAR(120) NOT NULL,
  date DATE NOT NULL,
  type ENUM('note','idea','event','image') NOT NULL,
  content TEXT,
  image VARCHAR(1024) DEFAULT '',
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX idx_type (type),
  INDEX idx_date (date)
);
```

如果后续要支持多用户，再增加：

- `user_id` 字段
- 复合索引：`(user_id, date)`、`(user_id, type)`


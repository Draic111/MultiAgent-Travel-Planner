# 多代理旅行规划系统 - 使用指南

## 📋 代码功能分析

这是一个基于 **LangChain** 和 **OpenAI GPT-4** 的多代理（Multi-Agent）智能旅行规划系统。系统通过三个专门的AI代理协同工作，为用户生成完整的旅行计划。

### 系统架构

#### 1. **主流程 (pipeline.py)**
- 协调整个规划流程
- 依次调用三个代理：规划代理 → 酒店代理 → 航班代理
- 整合所有结果并返回完整的旅行计划

#### 2. **规划代理 (planner_agent.py)**
- **功能**：根据目的地生成详细的每日行程
- **工具**：
  - `search_attractions`: 使用Google Maps API搜索目的地景点
  - `compute_distance_km`: 计算景点间距离，优化行程安排
- **输出**：包含每日上午、下午、晚上活动的JSON格式行程

#### 3. **酒店代理 (hotel_agent.py)**
- **功能**：基于行程和预算推荐合适的酒店
- **工具**：
  - `search_hotels`: 使用SerpAPI搜索酒店信息
  - `compute_itinerary_centroid`: 计算所有景点的中心位置
  - `compute_distance_km`: 计算酒店到行程中心的距离
- **输出**：推荐酒店列表，包含价格、评分、推荐理由

#### 4. **航班代理 (flight_agent.py)**
- **功能**：推荐往返航班
- **工具**：
  - `search_roundTrip_flights`: 使用SerpAPI搜索往返航班
- **输出**：去程和返程航班推荐，包含价格、航空公司、时间

#### 5. **工具模块 (tools.py)**
包含所有代理使用的工具函数：
- Google Maps API 集成（搜索景点）
- SerpAPI 集成（搜索航班和酒店）
- 距离计算（Haversine公式）
- 价格解析和数据处理

### 工作流程

```
用户输入（出发城市、目的地、日期、预算等）
    ↓
规划代理 → 生成每日行程（景点安排）
    ↓
酒店代理 → 基于行程推荐酒店
    ↓
航班代理 → 推荐往返航班
    ↓
整合结果 → 返回完整旅行计划
```

---

## 🚀 环境设置与运行指南

### 第一步：创建Python虚拟环境

#### Windows (PowerShell)
```powershell
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
.\venv\Scripts\Activate.ps1
```

如果遇到执行策略错误，先运行：
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

#### Windows (CMD)
```cmd
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
venv\Scripts\activate.bat
```

#### macOS/Linux
```bash
# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
source venv/bin/activate
```

### 第二步：安装依赖包

激活虚拟环境后，在项目根目录运行：

```bash
pip install -r requirements.txt
```

**主要依赖包说明：**
- `langchain` / `langchain-openai`: LangChain框架和OpenAI集成
- `openai`: OpenAI API客户端
- `google_search_results`: SerpAPI客户端（用于搜索航班和酒店）
- `haversine`: 计算地理距离
- `python-dotenv`: 读取环境变量
- `requests`: HTTP请求库

### 第三步：配置环境变量

1. 在项目根目录创建 `.env` 文件

2. 添加以下API密钥（需要先注册获取）：

```env
# OpenAI API密钥（必需）
OPENAI_API_KEY=your_openai_api_key_here

# Google Maps API密钥（用于搜索景点）
GOOGLE_MAPS_API_KEY=your_google_maps_api_key_here

# SerpAPI密钥（用于搜索航班和酒店）
SERPAPI_API_KEY=your_serpapi_key_here
```

#### 如何获取API密钥：

1. **OpenAI API Key**
   - 访问：https://platform.openai.com/api-keys
   - 注册/登录后创建新的API密钥

2. **Google Maps API Key**
   - 访问：https://console.cloud.google.com/
   - 创建项目 → 启用 "Places API" → 创建API密钥

3. **SerpAPI Key**
   - 访问：https://serpapi.com/
   - 注册账号 → 在Dashboard获取API密钥

### 第四步：运行代码

#### 方式1：运行完整流程（推荐）
```bash
python pipeline.py
```

这会执行完整的旅行规划流程，输出包含：
- 行程安排（每日景点）
- 酒店推荐
- 航班推荐

#### 方式2：单独测试各个代理

```bash
# 测试规划代理
python planner_agent.py

# 测试酒店代理
python hotel_agent.py

# 测试航班代理
python flight_agent.py
```

### 第五步：自定义旅行信息

编辑 `pipeline.py` 中的 `info` 字典来设置你的旅行需求：

```python
info = {
    "origin_city": "Seattle",        # 出发城市
    "destination_city": "New York",  # 目的地城市
    "check_in_date": "2026-01-10",   # 入住日期 (YYYY-MM-DD)
    "check_out_date": "2026-01-15",  # 退房日期 (YYYY-MM-DD)
    "num_people": 2,                 # 人数
    "total_budget": 2000,            # 总预算（美元）
}
```

**注意**：`flight_agent.py` 中定义了支持的城市及其机场代码：
- Seattle (SEA)
- New York (JFK)
- Los Angeles (LAX)
- San Francisco (SFO)
- Chicago (ORD)
- 等等...

如果使用其他城市，需要在 `flight_agent.py` 的 `CITY_TO_IATA` 字典中添加对应关系。

---

## ⚠️ 注意事项

1. **API费用**：使用OpenAI、Google Maps和SerpAPI都会产生费用，请注意使用量
2. **网络连接**：需要稳定的网络连接来调用各种API
3. **日期格式**：所有日期必须使用 `YYYY-MM-DD` 格式
4. **预算单位**：预算以美元（USD）为单位
5. **城市限制**：航班搜索目前仅支持预定义的城市列表

---

## 📝 输出示例

运行后会得到类似以下的JSON输出：

```json
{
  "trip_config": { ... },
  "itinerary": {
    "destination": "New York",
    "days": [
      {
        "day_index": 1,
        "date": "DAY 1",
        "morning": [{"name": "...", "lat": "...", "lng": "..."}],
        "afternoon": [...],
        "evening": [...]
      }
    ]
  },
  "hotels": {
    "recommended_hotels": [...]
  },
  "flights": {
    "outbound": {...},
    "return": {...}
  }
}
```

---

## 🛠️ 故障排除

1. **导入错误**：确保已激活虚拟环境并安装了所有依赖
2. **API密钥错误**：检查 `.env` 文件中的密钥是否正确
3. **网络超时**：某些API调用可能需要较长时间，请耐心等待
4. **JSON解析错误**：如果AI返回格式不正确，可能需要调整提示词或重试

---

祝您使用愉快！🎉



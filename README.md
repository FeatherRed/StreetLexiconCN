# 🏙️ 城市地址路名库生成器

基于 Overpass API 的全国城市道路名称结构化提取工具。  
用户可通过图形界面选择省份与城市，自动生成该城市的完整道路名称数据库，支持本地查询、导出等功能，广泛适用于中文地址解析、地理词库构建、地图辅助标注等场景。

---

## 📌 项目亮点

- 🌍 覆盖全国城市，基于 OpenStreetMap 开源数据；
- 🔎 支持关键词模糊查询、本地实时匹配；
- 🧩 自动解析行政区、街道、道路等层级关系；
- 💾 支持结构化数据导出（JSON）；
- 🖥️ 图形化界面，操作简洁，交互流畅；
- ⚠️ 内置异常处理，稳定性强，适合教学与项目部署。

---

## 🛠️ 项目结构

``` shell
project/
├── main.py
├── page/
├── resource/ 
├── china_admin_data.json 
├── output/
├── README.md # 项目说明文档
└── requirements.txt # 项目依赖
```

---

## 🚀 快速开始

### 📦 安装依赖

```bash
pip install -r requirements.txt
python main.py

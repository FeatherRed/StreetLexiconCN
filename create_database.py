import json
import numpy as np
from requests_futures.sessions import FuturesSession
import requests
import os
import time

base_id = 3600000000


def create_database(city_id, city_name, json_path="road_data.json"):
    json_data = {}  # 用来保存该city_name的道路数据
    # 这个函数是用来迭代创建
    url = "https://maps.mail.ru/osm/tools/overpass/api/interpreter"
    query = f"""
        [out:json];
        area({city_id + base_id})->.searchArea;
        (
        relation(area.searchArea)["boundary"="administrative"]["admin_level"="6"];
        );
        out tags;
    """
    response = requests.get(url, params={'data': query})
    data = response.json()
    # 提取区名

    districts = []
    for element in data['elements']:
        if 'tags' in element and 'name' in element['tags']:
            districts.append((element['tags']['name'], element['id']))

    # 循环每个区
    session = FuturesSession(max_workers=16)
    all_futures = []
    for district, district_id in districts:
        json_data[district] = {}
        query = f"""
            [out:json][timeout:90];
            area({district_id + base_id})->.searchArea;
            (
                relation(area.searchArea)["boundary"="administrative"]["admin_level"~"7|8"];
            );
            out tags;
        """
        response = requests.get(url, params={'data': query})
        data = response.json()
        # 得到街道名
        street = []
        for element in data['elements']:
            if 'tags' in element and 'name' in element['tags']:
                street.append((element['tags']['name'], element['id']))

        # 使用futures_session来异步请求街道数据
        # session = FuturesSession(max_workers=16)
        # all_futures = []
        # 对每个街道用 futures 并发请求 道路信息
        for i, (street_name, street_id) in enumerate(street):
            # time.sleep(np.random.uniform(0.5, 1.5))  # 随机延时，避免请求过快
            query = f"""
                [out:json][timeout:90];
                area({street_id + base_id})->.searchArea;
                (
                    way["highway"]["name"](area.searchArea);
                );
                out tags;
            """
            future = session.get(url, params={'data': query})
            # 记录未来对象和 street 名称（你可能会需要这个名）
            all_futures.append((future, street_name, district))

    # 等待所有请求完成
    for future, street_name, district in all_futures:
        try:
            response = future.result()
            if response.status_code == 200 and response.text.strip():
                data = response.json()
                roads = set()  # 使用 set 来避免重复的道路名
                # 提取道路名
                for element in data['elements']:
                    if 'tags' in element and 'name:zh' in element['tags']:
                        roads.add(element['tags']['name:zh'])
                    elif 'tags' in element and 'name' in element['tags']:
                        roads.add(element['tags']['name'])

                # print(f"[{district} - {street_name}] 道路数: {len(roads)}")
                # 可以保存 roads 数据
                json_data[district][street_name] = list(roads)

            else:
                print(f"[{district} - {street_name}] 响应为空或状态码错误: {response.status_code}")
        except Exception as e:
            print(f"[{district} - {street_name}] 请求失败: {e}")

    # 保存到 JSON 文件
    if os.path.exists(json_path):
        with open(json_path, 'r', encoding='utf-8') as f:
            existing_data = json.load(f)
    else:
        existing_data = {}

    # 合并新数据和旧数据
    existing_data.update(json_data)

    # 保存合并后的数据
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(existing_data, f, ensure_ascii=False, indent=4)


if __name__ == "__main__":
    # 示例调用
    with open("china_admin_data.json", 'r', encoding='utf-8') as f1:
        cities = json.load(f1)
    province = "香港特别行政区"
    for city_name in cities["id"][province]:
        start_time = time.time()
        #if city_name == "巴音郭楞蒙古自治州":
        create_database(cities["id"][province][city_name], city_name, "data/"+city_name+".json")
        end_time = time.time()
        print(f"{city_name}数据创建完成，耗时: {end_time - start_time:.2f}秒")
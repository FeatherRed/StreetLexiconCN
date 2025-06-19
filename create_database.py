import json
import numpy as np
from requests_futures.sessions import FuturesSession
import requests
import os
import time
from sortedcontainers import SortedList

base_id = 3600000000


def create_database(city_id, city_name, json_path):
    json_data = {}  # 用来保存该city_name的道路数据
    # 这个函数是用来迭代创建
    try:
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
            elif 'tags' in element and 'name:zh' in element['tags']:
                districts.append((element['tags']['name'], element['id']))

        query = f"""
            [out:json];
            area({city_id + base_id})->.searchArea;
            (
            way["highway"]["name"](area.searchArea);
            );
            out tags;
        """
        response = requests.get(url, params={'data': query})
        data = response.json()
        id_to_name = {}
        road_in_city = set()
        for element in data['elements']:
            if 'tags' in element and 'name:zh' in element['tags']:
                road_in_city.add(element['id'])
                id_to_name[element['id']] = element['tags']['name:zh']
            elif 'tags' in element and 'name' in element['tags']:
                road_in_city.add(element['id'])
                id_to_name[element['id']] = element['tags']['name']

        # 循环每个区
        session = FuturesSession(max_workers=16)
        all_futures = []
        road_in_district = {}
        for district, district_id in districts:
            #print(f"正在处理 {city_name} 的 {district} 区")
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
            road_in_district2 = set()
            query = f"""
                [out:json][timeout:90];
                area({district_id + base_id})->.searchArea;
                (
                way["highway"]["name"](area.searchArea);
                );
                out tags;
            """
            response = requests.get(url, params={'data': query})
            data1 = response.json()
            for element in data1['elements']:
                if 'tags' in element and 'name:zh' in element['tags']:
                    if element['id'] in road_in_city:
                        road_in_city.discard(element['id'])
                    road_in_district2.add(element['id'])
                elif 'tags' in element and 'name' in element['tags']:
                    if element['id'] in road_in_city:
                        road_in_city.discard(element['id'])
                    road_in_district2.add(element['id'])



            road_in_district[district] = road_in_district2
            for element in data['elements']:
                if 'tags' in element and 'name:zh' in element['tags']:
                    street.append((element['tags']['name:zh'], element['id']))

                elif 'tags' in element and 'name' in element['tags']:
                    street.append((element['tags']['name'], element['id']))

            # 使用futures_session来异步请求街道数据
            for i, (street_name, street_id) in enumerate(street):
                query = f"""
                    [out:json][timeout:90];
                    area({street_id + base_id})->.searchArea;
                    (
                        way["highway"]["name"](area.searchArea);
                    );
                    out tags;
                """
                future = session.get(url, params={'data': query})
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
                            road_in_district[district].discard(element['id'])
                        elif 'tags' in element and 'name' in element['tags']:
                            roads.add(element['tags']['name'])
                            road_in_district[district].discard(element['id'])

                    json_data[district][street_name] = list(roads)
                else:
                    return 0
            except Exception as e:
                print('Error in')
                return 0
    except Exception as e:
        print("error")
        return 0

    json_data["roads"] = []
    for ids in road_in_city:
        json_data["roads"].append(id_to_name[ids])
    json_data["roads"] = list(set(json_data["roads"]))
    for district in json_data:
        if district != "roads":
            json_data[district]["roads"] = []
            for ids in road_in_district[district]:
                json_data[district]["roads"].append(id_to_name[ids])
            json_data[district]["roads"] = list(set(json_data[district]["roads"]))
    #return json_data
    # # 保存合并后的数据
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, ensure_ascii=False, indent=4)


if __name__ == "__main__":
    # 示例调用
    with open("china_admin_data.json", 'r', encoding='utf-8') as f1:
        cities = json.load(f1)
    province = "广东省"
    for city_name in cities["id"][province]:
        start_time = time.time()
        if city_name == "汕尾市":
            create_database(cities["id"][province][city_name], city_name, "data/"+city_name+".json")
        end_time = time.time()
        print(f"{city_name}数据创建完成，耗时: {end_time - start_time:.2f}秒")
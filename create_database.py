import json
import numpy as np
from requests_futures.sessions import FuturesSession
import requests
import os
import time

base_id = 3600000000

def gen_road_query(id_list):
    # 多少个id 就补多少个520
    query_parts = '[out:json][timeout:90];'

    for id in id_list:
        query_parts += f"area({id + base_id})->.searchArea;(way['highway']['name'](area.searchArea););out tags;"
        # 补充一个 520
        query_parts += f"way(520);out tags;"
    return query_parts

def gen_city_query(id):
    # 一个id 补充 区域 6 和 road查询
    query_parts = '[out:json][timeout:90];'
    query_parts += f"area({id + base_id})->.searchArea;(relation(area.searchArea)['boundary'='administrative']['admin_level'='6'];);out tags;"
    query_parts += f"area({id + base_id})->.searchArea;(way['highway']['name'](area.searchArea););out tags;"
    return query_parts

def gen_district_query(id):
    # 一个id 补充 区域 7 和 road查询
    query_parts = '[out:json][timeout:90];'
    query_parts += f"area({id + base_id})->.searchArea;(relation(area.searchArea)['boundary'='administrative']['admin_level'~'7|8'];);out tags;"
    query_parts += f"area({id + base_id})->.searchArea;(way['highway']['name'](area.searchArea););out tags;"
    return query_parts

def split_data_city(data):
    # 将数据划分为 下一级 和 道路数据
    next_level = []

    # 一边处理下一级 一边确定way
    flag = 0
    for i, element in enumerate(data['elements']):
        if element['type'] == 'relation':
            if 'tags' in element and 'name:zh' in element['tags']:
                next_level.append((element['tags']['name:zh'], element['id']))
            elif 'tags' in element and 'name' in element['tags']:
                next_level.append((element['tags']['name'], element['id']))
        else:
            flag = i # 后面flag 都是 way了
            break

    ways = []
    id_to_name = {}
    id_in_level = set()
    for element in data['elements'][flag:]:
        if element['type'] == 'way':
            if 'tags' in element and 'name:zh' in element['tags']:
                ways.append((element['tags']['name:zh'], element['id']))
                id_to_name[element['id']] = element['tags']['name:zh']
                id_in_level.add(element['id'])
            elif 'tags' in element and 'name' in element['tags']:
                ways.append((element['tags']['name'], element['id']))
                id_to_name[element['id']] = element['tags']['name']
                id_in_level.add(element['id'])

    return next_level, ways, id_to_name, id_in_level

def split_data_district(data, id_in_city):
    # 对区域数据划分
    next_level_name = []
    next_level_id = []
    # 一边处理下一级 一边确定way
    flag = 0
    for i, element in enumerate(data['elements']):
        if element['type'] == 'relation':
            if 'tags' in element and 'name:zh' in element['tags']:
                next_level_name.append(element['tags']['name:zh'])
                next_level_id.append(element['id'])
            elif 'tags' in element and 'name' in element['tags']:
                next_level_name.append(element['tags']['name'])
                next_level_id.append(element['id'])
        else:
            flag = i # 后面flag 都是 way了
            break
    id_in_level = set()
    for element in data['elements'][flag:]:
        if "tags" in element and "name:zh" in element['tags']:
            if element['id'] in id_in_city:
                id_in_city.discard(element['id'])
            id_in_level.add(element['id'])
        elif "tags" in element and "name" in element['tags']:
            if element['id'] in id_in_city:
                id_in_city.discard(element['id'])
            id_in_level.add(element['id'])

    return next_level_name, next_level_id, id_in_level

def create_database(city_id, city_name, emitter):
    json_data = {}
    try:
        url = "https://maps.mail.ru/osm/tools/overpass/api/interpreter"
        # 拿到该城市的行政区数据
        query = gen_city_query(city_id)
        response = requests.get(url, params={'data': query})
        data = response.json()
        districts, roads, id_to_name, id_in_city = split_data_city(data)

        session = FuturesSession(max_workers=16)
        all_futures = []
        road_in_district = {}
        for district, district_id in districts:
            json_data[district] = {}
            query = gen_district_query(district_id)
            response = requests.get(url, params={'data': query})
            data = response.json()
            street_name_list, street_id_list, id_in_street = split_data_district(data, id_in_city)

            road_in_district[district] = id_in_street

            # 接着 异步 请求 获得街道数据
            street_query = gen_road_query(street_id_list)
            future = session.get(url, params={'data': street_query})
            all_futures.append((future, street_name_list, district))
            emitter.log.emit(district) # 告诉主线程

        # 等待所有请求完成
        for future, street_name_list, district in all_futures:
            try:
                response = future.result()
                if response.status_code == 200 and response.text.strip():
                    data = response.json()
                    
                    # 此时这里的data 是 集合请求 有多少个街道 就有多少个520
                    num_street = len(street_name_list)
                    roads = set()

                    street_index = 0 # 表示先处理第一个street
                    for element in data['elements']:
                        if element['id'] == 520:
                            json_data[district][street_name_list[street_index]] = list(roads)
                            roads = set() # 清空
                            street_index += 1
                            continue  # 跳过520的元素

                        if 'tags' in element and 'name:zh' in element['tags']:
                            roads.add(element['tags']['name:zh'])
                            if element['id'] in road_in_district[district]:
                                road_in_district[district].discard(element['id'])
                        elif 'tags' in element and 'name' in element['tags']:
                            roads.add(element['tags']['name'])
                            if element['id'] in road_in_district[district]:
                                road_in_district[district].discard(element['id'])
                else:
                    return 0
            except Exception as e:
                print('Error in processing district:', district, e)
                return 0

    except Exception as e:
        print('Error in processing district:', district, e)
        return 0
    
    # 最后处理剩余的道路
    json_data["roads"] = list({id_to_name[ids] for ids in id_in_city})  # 去重
    for district in json_data:
        if district != "roads":
            json_data[district]["roads"] = list({id_to_name[ids] for ids in road_in_district[district]})  # 去重
    return json_data

# def create_database(city_id, city_name, emitter):
#     json_data = {}  # 用来保存该city_name的道路数据
#     # 这个函数是用来迭代创建
#     try:
#         url = "https://maps.mail.ru/osm/tools/overpass/api/interpreter"
#         query = f"""
#             [out:json];
#             area({city_id + base_id})->.searchArea;
#             (
#             relation(area.searchArea)["boundary"="administrative"]["admin_level"="6"];
#             );
#             out tags;
#         """
#         response = requests.get(url, params={'data': query})
#         data = response.json()
#         # 提取区名
#
#         districts = []
#         for element in data['elements']:
#             if 'tags' in element and 'name' in element['tags']:
#                 districts.append((element['tags']['name'], element['id']))
#             elif 'tags' in element and 'name:zh' in element['tags']:
#                 districts.append((element['tags']['name'], element['id']))
#
#         query = f"""
#             [out:json];
#             area({city_id + base_id})->.searchArea;
#             (
#             way["highway"]["name"](area.searchArea);
#             );
#             out tags;
#         """
#         response = requests.get(url, params={'data': query})
#         data = response.json()
#         id_to_name = {}
#         road_in_city = set()
#         for element in data['elements']:
#             if 'tags' in element and 'name:zh' in element['tags']:
#                 road_in_city.add(element['id'])
#                 id_to_name[element['id']] = element['tags']['name:zh']
#             elif 'tags' in element and 'name' in element['tags']:
#                 road_in_city.add(element['id'])
#                 id_to_name[element['id']] = element['tags']['name']
#
#         # 循环每个区
#         session = FuturesSession(max_workers=16)
#         all_futures = []
#         road_in_district = {}
#         for district, district_id in districts:
#             #print(f"正在处理 {city_name} 的 {district} 区")
#             json_data[district] = {}
#             query = f"""
#                 [out:json][timeout:90];
#                 area({district_id + base_id})->.searchArea;
#                 (
#                     relation(area.searchArea)["boundary"="administrative"]["admin_level"~"7|8"];
#                 );
#                 out tags;
#             """
#             response = requests.get(url, params={'data': query})
#             data = response.json()
#             # 得到街道名
#             street = []
#             road_in_district2 = set()
#             query = f"""
#                 [out:json][timeout:90];
#                 area({district_id + base_id})->.searchArea;
#                 (
#                 way["highway"]["name"](area.searchArea);
#                 );
#                 out tags;
#             """
#             response = requests.get(url, params={'data': query})
#             data1 = response.json()
#             for element in data1['elements']:
#                 if 'tags' in element and 'name:zh' in element['tags']:
#                     if element['id'] in road_in_city:
#                         road_in_city.discard(element['id'])
#                     road_in_district2.add(element['id'])
#                 elif 'tags' in element and 'name' in element['tags']:
#                     if element['id'] in road_in_city:
#                         road_in_city.discard(element['id'])
#                     road_in_district2.add(element['id'])
#
#
#
#             road_in_district[district] = road_in_district2
#             for element in data['elements']:
#                 if 'tags' in element and 'name:zh' in element['tags']:
#                     street.append((element['tags']['name:zh'], element['id']))
#
#                 elif 'tags' in element and 'name' in element['tags']:
#                     street.append((element['tags']['name'], element['id']))
#
#             # 使用futures_session来异步请求街道数据
#             for i, (street_name, street_id) in enumerate(street):
#                 query = f"""
#                     [out:json][timeout:90];
#                     area({street_id + base_id})->.searchArea;
#                     (
#                         way["highway"]["name"](area.searchArea);
#                     );
#                     out tags;
#                 """
#                 future = session.get(url, params={'data': query})
#                 all_futures.append((future, street_name, district))
#             emitter.log.emit(district)
#
#         # 等待所有请求完成
#         for future, street_name, district in all_futures:
#             try:
#                 response = future.result()
#                 if response.status_code == 200 and response.text.strip():
#                     data = response.json()
#                     roads = set()  # 使用 set 来避免重复的道路名
#                     # 提取道路名
#                     for element in data['elements']:
#                         if 'tags' in element and 'name:zh' in element['tags']:
#                             roads.add(element['tags']['name:zh'])
#                             road_in_district[district].discard(element['id'])
#                         elif 'tags' in element and 'name' in element['tags']:
#                             roads.add(element['tags']['name'])
#                             road_in_district[district].discard(element['id'])
#
#                     json_data[district][street_name] = list(roads)
#                 else:
#                     return 0
#             except Exception as e:
#                 print('Error in')
#                 return 0
#     except Exception as e:
#         print("error")
#         return 0
#
#     json_data["roads"] = []
#     for ids in road_in_city:
#         json_data["roads"].append(id_to_name[ids])
#     json_data["roads"] = list(set(json_data["roads"]))
#     for district in json_data:
#         if district != "roads":
#             json_data[district]["roads"] = []
#             for ids in road_in_district[district]:
#                 json_data[district]["roads"].append(id_to_name[ids])
#             json_data[district]["roads"] = list(set(json_data[district]["roads"]))
#     return json_data

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
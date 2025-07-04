import json
import numpy as np
from requests_futures.sessions import FuturesSession
import requests
import os
import time

base_id = 3600000000
policy_city = ['东莞市', '中山市', '儋州市', '嘉峪关市', '新疆生产建设兵团', '新北市', '嘉義市', '連江縣', '南投縣', '澎湖縣', '臺東縣', '桃園市', '苗栗縣', '高雄市', '嘉義縣', '臺北市', '屏東縣', '臺南市', '金門縣', '雲林縣', '基隆市', '彰化縣', '新竹市', '宜蘭縣', '花蓮縣', '臺中市', '新竹縣', '氹仔', '路環']


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

def split_data_district(data, id_in_city, id_to_name):
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
            id_to_name[element['id']] = element['tags']['name:zh']
            if element['id'] in id_in_city:
                id_in_city.discard(element['id'])
            id_in_level.add(element['id'])
        elif "tags" in element and "name" in element['tags']:
            id_to_name[element['id']] = element['tags']['name']
            if element['id'] in id_in_city:
                id_in_city.discard(element['id'])
            id_in_level.add(element['id'])

    return next_level_name, next_level_id, id_in_level, id_to_name

def create_database(city_id, city_name, province_name, emitter):
    if city_name in policy_city:
        json_data = {}
        try:
            url = "https://maps.mail.ru/osm/tools/overpass/api/interpreter"
            #url = "https://overpass.private.coffee/api/interpreter"
            query = gen_district_query(city_id)
            response = requests.get(url, params={'data': query})
            data = response.json()
            if data is None:
                print("No data found for city:", city_name)
                return 0
            streets, roads, id_to_name, id_in_city = split_data_city(data)
            street_id_list = []
            street_name_list = []
            for street in streets:
                street_id_list.append(street[1])
                street_name_list.append(street[0])
            session = FuturesSession(max_workers=16)
            all_futures = []
            street_query = gen_road_query(street_id_list)
            future = session.get(url, params={'data': street_query})
            all_futures.append((future, street_name_list, city_name))
            emitter.log.emit(city_name)  # 告诉主线程
            try:
                response = future.result()
                if response.status_code == 200 and response.text.strip():    
                    data = response.json()
                    if data is None:
                        print("No data found for street in city:", city_name)
                        return 0
                    # 此时这里的data 是 集合请求 有多少个街道 就有多少个520
                    num_street = len(street_name_list)
                    roads = set()

                    street_index = 0  # 表示先处理第一个street
                    for element in data['elements']:
                        if element['id'] == 520:
                            json_data[street_name_list[street_index]] = list(roads)
                            roads = set()  # 清空
                            street_index += 1
                            continue  # 跳过520的元素

                        if 'tags' in element and 'name:zh' in element['tags']:
                            roads.add(element['tags']['name:zh'])
                            if element['id'] in id_in_city:
                                id_in_city.discard(element['id'])
                        elif 'tags' in element and 'name' in element['tags']:
                            roads.add(element['tags']['name'])
                            if element['id'] in id_in_city:
                                id_in_city.discard(element['id'])
                else:
                    return 0
            except Exception as e:
                return 0
        except Exception as e:
            return 0
        json_data["roads"] = list({id_to_name[ids] for ids in id_in_city})
        return json_data
    json_data = {}
    try:
        url = "https://maps.mail.ru/osm/tools/overpass/api/interpreter"
        #url = "https://overpass.private.coffee/api/interpreter"
        # 拿到该城市的行政区数据
        query = gen_city_query(city_id)
        response = requests.get(url, params={'data': query})
        if response.status_code != 200 or not response.text.strip():
            return 0

        data = response.json()
        if data is None:
            print("No data found for city:", city_name)
            return 0
        districts, roads, id_to_name, id_in_city = split_data_city(data)

        session = FuturesSession(max_workers=16)
        all_futures = []
        road_in_district = {}
        for district, district_id in districts:
            json_data[district] = {}
            query = gen_district_query(district_id)
            response = requests.get(url, params={'data': query})
            if response.status_code != 200 or not response.text.strip():
                return 0
            data = response.json()
            if data is None:
                print("No data found for district:", district)
                return 0
            street_name_list, street_id_list, id_in_street, id_to_name = split_data_district(data, id_in_city, id_to_name)

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
                    if data is None:
                        print("No data found for street in district:", district)
                        return 0
                    
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
                            id_to_name[element['id']] = element['tags']['name:zh']
                            roads.add(element['tags']['name:zh'])
                            if element['id'] in road_in_district[district]:
                                road_in_district[district].discard(element['id'])
                        elif 'tags' in element and 'name' in element['tags']:
                            id_to_name[element['id']] = element['tags']['name']
                            roads.add(element['tags']['name'])
                            if element['id'] in road_in_district[district]:
                                road_in_district[district].discard(element['id'])
                else:
                    return 0
            except Exception as e:
                print('Error in processing district:', district, e)
                return 0

    except Exception as e:
        #print('Error in processing district:', district, e)
        return 0
    
    # 最后处理剩余的道路
    json_data["roads"] = list({id_to_name[ids] for ids in id_in_city})  # 去重
    for district in json_data:
        if district != "roads":
            json_data[district]["roads"] = list({id_to_name[ids] for ids in road_in_district[district]})  # 去重
    return json_data

if __name__ == "__main__":
    # 示例调用
    ans = []
    with open("../china_admin_data.json", 'r', encoding='utf-8') as f1:
        cities = json.load(f1)
    for province in cities["id"]:
        for city_name in cities["id"][province]:
            start_time = time.time()
            url = "https://maps.mail.ru/osm/tools/overpass/api/interpreter"
            query = f"""
            [out:json];
            area({cities["id"][province][city_name]+base_id})->.searchArea;
            (
              relation(area.searchArea)["boundary"="administrative"]["admin_level"="6"];
            );
            out tags;
            """
            response = requests.get(url, params={'data': query})
            data = response.json()
            if data["elements"] == []:
                print(city_name)
                ans.append(city_name)
            end_time = time.time()
            #print(f"{city_name}数据创建完成，耗时: {end_time - start_time:.2f}秒")
    print(ans)
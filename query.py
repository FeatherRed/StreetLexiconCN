import json
import numpy as np
from requests_futures.sessions import FuturesSession
import requests
import os
import time

def query_road(road_name, city_name, data):#返回一个list，格式为:[(完整路名,所在街道，所在区，所在地级市)]，参数data为城市名对应json中的东西
    results = []
    for district in data:
        for street in data[district]:
            for road in data[district][street]:
                if road_name in road:
                    results.append((road, street, district, city_name))
    return results


def query_street(street_name, city_name, data):
    results = []
    for district in data:
        for street in data[district]:
            if street in street_name:
                for road in data[district][street]:
                    results.append((road, street, district, city_name))
    return results


def query_district(district_name, city_name, data):
    results = []
    for district in data:
        if district in district_name:
            for street in data[district]:
                for road in data[district][street]:
                    results.append((road, street, district, city_name))
    return results

def query_city(city_name, data):
    results = []
    for district in data:
        for street in data[district]:
            for road in data[district][street]:
                results.append((road, street, district, city_name))
    return results

if __name__ == '__main__':
    city_name = "成都市"
    with open("data/"+city_name+".json", 'r', encoding='utf-8') as f:
        data = json.load(f)
    print(query_road("道", city_name, data))
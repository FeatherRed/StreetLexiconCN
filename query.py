import json
from opencc import OpenCC


def query_road(road_name, city_name, province_name, data):#返回一个list，格式为:[(所在地级市，所在区，所在街道，道路名称)]，选择道路按钮时调用
    results = []
    cc = OpenCC('t2s')
    city_name = cc.convert(city_name)
    if province_name == "台湾省":
        for road in data["roads"]:
            if road_name in cc.convert(road):
                results.append((city_name, None, None, road))
        for street in data:
            if street != "roads":
                for road in data[street]:
                    if road_name in cc.convert(road):
                        results.append((city_name, None, street, road))
        return results
    for road in data["roads"]:
        if road_name in cc.convert(road):
            results.append((city_name, None, None, road))
    for district in data:
        if district != "roads":
            for road in data[district]["roads"]:
                if road_name in cc.convert(road):
                    results.append((city_name, district, None, road))
            for street in data[district]:
                if street != "roads":
                    for road in data[district][street]:
                        if road_name in cc.convert(road):
                            results.append((city_name, district, street, road))
    return results


def query_street(street_name, city_name, province_name, data):#返回一个list，格式为:[(所在地级市,所在区，所在街道，道路名称)]，选择街道按钮时调用
    results = []
    cc = OpenCC('t2s')
    street_name = cc.convert(street_name)
    if province_name == "台湾省":
        for street in data:
            if street != "roads" and street_name in cc.convert(street):
                for road in data[street]:
                    results.append((city_name, None, street, road))
        return results
    for district in data:
        if district != "roads":
            for street in data[district]:
                if street != "roads":
                    if street_name in cc.convert(street):
                        for road in data[district][street]:
                            results.append((city_name, district, street, road))
    return results


def query_district(district_name, city_name, province_name, data):#返回一个list，格式为:[(所在地级市,所在区，所在街道，道路名称)]，选择区按钮时调用
    results = []
    cc = OpenCC('t2s')
    district_name = cc.convert(district_name)
    if province_name == "台湾省":
        return results
    for district in data:
        if district != "roads":
            if district_name in cc.convert(district):
                for road in data[district]["roads"]:
                    results.append((city_name, district, None, road))
                for street in data[district]:
                    if street != "roads":
                        for road in data[district][street]:
                            results.append((city_name, district, street, road))
    return results

def query_city(city_name, province_name, data):#返回一个list，格式为:[(所在地级市,所在区，所在街道，道路名称)]，未选择按钮时调用
    results = []
    if province_name == "台湾省":
        for road in data["roads"]:
            results.append((city_name, None, None, road))
        for street in data:
            if street != "roads":
                for road in data[street]:
                    results.append((city_name, None, street, road))
        return results
    for road in data["roads"]:
        results.append((city_name, None, None, road))
    for district in data:
        if district != "roads":
            for road in data[district]["roads"]:
                results.append((city_name, district, None, road))
            for street in data[district]:
                if street != "roads":
                    for road in data[district][street]:
                        results.append((city_name, district, street, road))
    return results

if __name__ == '__main__':
    city_name = "臺北市"
    with open("output/"+city_name+".json", 'r', encoding='utf-8') as f:
        data = json.load(f)
    print(query_street("区", city_name,"台湾省", data))
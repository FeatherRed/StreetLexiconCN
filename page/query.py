import json
from opencc import OpenCC

policy_city = ['东莞市', '中山市', '儋州市', '嘉峪关市', '新疆生产建设兵团', '新北市', '嘉義市', '連江縣', '南投縣', '澎湖縣', '臺東縣', '桃園市', '苗栗縣', '高雄市', '嘉義縣', '臺北市', '屏東縣', '臺南市', '金門縣', '雲林縣', '基隆市', '彰化縣', '新竹市', '宜蘭縣', '花蓮縣', '臺中市', '新竹縣', '氹仔', '路環']


def query_road(road_name, city_name, province_name, data):#返回一个list，格式为:[(所在地级市，所在区，所在街道，道路名称)]，选择道路按钮时调用
    results = []
    cc = OpenCC('t2s')
    road_name = cc.convert(road_name)
    if city_name in policy_city:
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
    if city_name in policy_city:
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
    if city_name in policy_city:
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
    if city_name in policy_city:
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
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
import json
import os
def load_or_init_json(json_path):
    if not os.path.exists(json_path) or os.path.getsize(json_path) == 0:
        return {}
    with open(json_path, "r", encoding="utf-8") as f:
        return json.load(f)


def fetch_district_data(district):
    url = "https://overpass-api.de/api/interpreter"
    street = {}
    query = f"""
    [out:json][timeout:90];
    area[name="{district}"]->.searchArea;
    (
        relation(area.searchArea)["boundary"="administrative"]["admin_level"~"7|8"];
    );
    out tags;
    """
    response2 = requests.get(url, params={'data': query})
    data2 = response2.json()
    for element in data2['elements']:
        if 'tags' in element and 'name' in element['tags']:
            street[element['tags']['name']] = {"id": element['id'], "elements": []}
    for name in street:
        id = street[name]['id']
        query = f"""
        [out:json][timeout:90];
        area({id + 3600000000})->.searchArea;
        (
            way["highway"]["name"~"路$|大道$|巷$|街$|道$|里$|弄$|胡同$|径$|东$|西$|北$|南$"](area.searchArea);
        );
        out tags;
        """
        response3 = requests.post(url, data={"data": query})
        data3 = response3.json()

        for element in data3.get('elements', []):
            name1 = element.get('tags', {}).get('name')
            if name1 and name1 not in street[name]["elements"]:
                street[name]["elements"].append(name1)
    return street

def create_database(city_id, city_name):
    json_path = "road_data.json"
    data = load_or_init_json(json_path)
    if city_name in data:
        print(f"地级市 {city_id} 已存在，跳过")
        return
    if city_name not in data:
        data[city_name] = {}
    url = "https://overpass-api.de/api/interpreter"
    query = f"""
    [out:json];
    area[name="{city_name}"]->.searchArea;
    (
      relation(area.searchArea)["boundary"="administrative"]["admin_level"="6"];
    );
    out tags;
    """
    response1 = requests.get(url, params={'data': query})
    data1 = response1.json()
    districts = []
    for element in data1['elements']:
        if 'tags' in element and 'name' in element['tags']:
            data[city_name][element['tags']['name']]={"elements":{}}
            districts.append(element['tags']['name'])

    #for district in districts:
    #    street = fetch_district_data(district)
    #    data[city_name][district] = street

    results = []
    with ThreadPoolExecutor(max_workers=16) as executor:
        future_to_district = {executor.submit(fetch_district_data, dis): dis for dis in districts}
        for future in as_completed(future_to_district):
            result = future.result()
            results.append(result)
    i=0
    for street in results:
        data[city_name][districts[i]]["elements"] = street
        i += 1

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"地级市 {city_name}（{city_id}）数据已更新")

create_database(3287346, "广州市")

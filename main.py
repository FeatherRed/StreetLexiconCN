import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import json
import os

class RoadDatabaseApp:
    def __init__(self, root):
        self.root = root
        self.root.title("城市地址路名库生成器")
        self.root.geometry("500x300")
        
        # 省份数据
        self.provinces_data = {
            "北京市": ["北京市"],
            "天津市": ["天津市"],
            "河北省": ["石家庄市", "唐山市", "秦皇岛市", "邯郸市", "邢台市", "保定市", "张家口市", "承德市", "沧州市", "廊坊市", "衡水市"],
            "山西省": ["太原市", "大同市", "阳泉市", "长治市", "晋城市", "朔州市", "晋中市", "运城市", "忻州市", "临汾市", "吕梁市"],
            "内蒙古自治区": ["呼和浩特市", "包头市", "乌海市", "赤峰市", "通辽市", "鄂尔多斯市", "呼伦贝尔市", "巴彦淖尔市", "乌兰察布市"],
            "辽宁省": ["沈阳市", "大连市", "鞍山市", "抚顺市", "本溪市", "丹东市", "锦州市", "营口市", "阜新市", "辽阳市", "盘锦市", "铁岭市", "朝阳市", "葫芦岛市"],
            "吉林省": ["长春市", "吉林市", "四平市", "辽源市", "通化市", "白山市", "松原市", "白城市"],
            "黑龙江省": ["哈尔滨市", "齐齐哈尔市", "鸡西市", "鹤岗市", "双鸭山市", "大庆市", "伊春市", "佳木斯市", "七台河市", "牡丹江市", "黑河市", "绥化市"],
            "上海市": ["上海市"],
            "江苏省": ["南京市", "无锡市", "徐州市", "常州市", "苏州市", "南通市", "连云港市", "淮安市", "盐城市", "扬州市", "镇江市", "泰州市", "宿迁市"],
            "浙江省": ["杭州市", "宁波市", "温州市", "嘉兴市", "湖州市", "绍兴市", "金华市", "衢州市", "舟山市", "台州市", "丽水市"],
            "安徽省": ["合肥市", "芜湖市", "蚌埠市", "淮南市", "马鞍山市", "淮北市", "铜陵市", "安庆市", "黄山市", "滁州市", "阜阳市", "宿州市", "六安市", "亳州市", "池州市", "宣城市"],
            "福建省": ["福州市", "厦门市", "莆田市", "三明市", "泉州市", "漳州市", "南平市", "龙岩市", "宁德市"],
            "江西省": ["南昌市", "景德镇市", "萍乡市", "九江市", "新余市", "鹰潭市", "赣州市", "吉安市", "宜春市", "抚州市", "上饶市"],
            "山东省": ["济南市", "青岛市", "淄博市", "枣庄市", "东营市", "烟台市", "潍坊市", "济宁市", "泰安市", "威海市", "日照市", "临沂市", "德州市", "聊城市", "滨州市", "菏泽市"],
            "河南省": ["郑州市", "开封市", "洛阳市", "平顶山市", "安阳市", "鹤壁市", "新乡市", "焦作市", "濮阳市", "许昌市", "漯河市", "三门峡市", "南阳市", "商丘市", "信阳市", "周口市", "驻马店市"],
            "湖北省": ["武汉市", "黄石市", "十堰市", "宜昌市", "襄阳市", "鄂州市", "荆门市", "孝感市", "荆州市", "黄冈市", "咸宁市", "随州市"],
            "湖南省": ["长沙市", "株洲市", "湘潭市", "衡阳市", "邵阳市", "岳阳市", "常德市", "张家界市", "益阳市", "郴州市", "永州市", "怀化市", "娄底市"],
            "广东省": ["广州市", "韶关市", "深圳市", "珠海市", "汕头市", "佛山市", "江门市", "湛江市", "茂名市", "肇庆市", "惠州市", "梅州市", "汕尾市", "河源市", "阳江市", "清远市", "东莞市", "中山市", "潮州市", "揭阳市", "云浮市"],
            "广西壮族自治区": ["南宁市", "柳州市", "桂林市", "梧州市", "北海市", "防城港市", "钦州市", "贵港市", "玉林市", "百色市", "贺州市", "河池市", "来宾市", "崇左市"],
            "海南省": ["海口市", "三亚市", "三沙市", "儋州市"],
            "重庆市": ["重庆市"],
            "四川省": ["成都市", "自贡市", "攀枝花市", "泸州市", "德阳市", "绵阳市", "广元市", "遂宁市", "内江市", "乐山市", "南充市", "眉山市", "宜宾市", "广安市", "达州市", "雅安市", "巴中市", "资阳市"],
            "贵州省": ["贵阳市", "六盘水市", "遵义市", "安顺市", "毕节市", "铜仁市"],
            "云南省": ["昆明市", "曲靖市", "玉溪市", "保山市", "昭通市", "丽江市", "普洱市", "临沧市"],
            "西藏自治区": ["拉萨市", "日喀则市", "昌都市", "林芝市", "山南市", "那曲市", "阿里地区"],
            "陕西省": ["西安市", "铜川市", "宝鸡市", "咸阳市", "渭南市", "延安市", "汉中市", "榆林市", "安康市", "商洛市"],
            "甘肃省": ["兰州市", "嘉峪关市", "金昌市", "白银市", "天水市", "武威市", "张掖市", "平凉市", "酒泉市", "庆阳市", "定西市", "陇南市"],
            "青海省": ["西宁市", "海东市"],
            "宁夏回族自治区": ["银川市", "石嘴山市", "吴忠市", "固原市", "中卫市"],
            "新疆维吾尔自治区": ["乌鲁木齐市", "克拉玛依市", "吐鲁番市", "哈密市"],
            "台湾省": ["台北市", "高雄市", "台中市", "台南市", "新北市", "宜兰市", "桃园市", "新竹市", "苗栗市", "彰化市", "南投市", "云林市", "嘉义市", "屏东市", "台东市", "花莲市", "澎湖市"],
            "香港特别行政区": ["香港"],
            "澳门特别行政区": ["澳门"]
        }
        
        # 创建主框架
        main_frame = ttk.Frame(root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 创建标题
        title_label = ttk.Label(main_frame, text="城市地址路名库生成器", font=("黑体", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=2, pady=20)
        
        # 创建省份选择框
        province_frame = ttk.Frame(main_frame)
        province_frame.grid(row=1, column=0, columnspan=2, sticky="w", pady=10)
        
        province_label = ttk.Label(province_frame, text="选择省份:", font=("黑体", 12))
        province_label.pack(side=tk.LEFT, padx=(0, 10))
        
        self.province_var = tk.StringVar()
        self.province_combobox = ttk.Combobox(province_frame, textvariable=self.province_var, 
                                             width=20, state="readonly", font=("黑体", 12))
        self.province_combobox['values'] = list(self.provinces_data.keys())
        self.province_combobox.pack(side=tk.LEFT)
        self.province_combobox.bind("<<ComboboxSelected>>", self.update_cities)
        
        # 创建城市选择框
        city_frame = ttk.Frame(main_frame)
        city_frame.grid(row=2, column=0, columnspan=2, sticky="w", pady=10)
        
        city_label = ttk.Label(city_frame, text="选择城市:", font=("黑体", 12))
        city_label.pack(side=tk.LEFT, padx=(0, 10))
        
        self.city_var = tk.StringVar()
        self.city_combobox = ttk.Combobox(city_frame, textvariable=self.city_var, 
                                         width=20, state="readonly", font=("黑体", 12))
        self.city_combobox.pack(side=tk.LEFT)
        
        # 创建生成按钮
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=3, column=0, columnspan=2, pady=20)
        
        generate_button = ttk.Button(button_frame, text="生成地址路名数据库", command=self.generate_database)
        generate_button.pack()
        
        # 状态信息
        self.status_var = tk.StringVar()
        self.status_label = ttk.Label(main_frame, textvariable=self.status_var, font=("黑体", 10))
        self.status_label.grid(row=4, column=0, columnspan=2, pady=10)
        
        # 设置默认值
        if self.province_combobox['values']:
            self.province_combobox.current(0)
            self.update_cities(None)
    
    def update_cities(self, event):
        """根据选择的省份更新城市列表"""
        selected_province = self.province_var.get()
        if selected_province in self.provinces_data:
            cities = self.provinces_data[selected_province]
            self.city_combobox['values'] = cities
            if cities:
                self.city_combobox.current(0)
    
    def generate_database(self):
        """生成道路数据库"""
        province = self.province_var.get()
        city = self.city_var.get()
        
        if not province or not city:
            messagebox.showerror("错误", "请选择省份和城市")
            return
        
        # 创建数据目录
        data_dir = "road_database"
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)
        
        # 创建城市文件夹
        city_dir = os.path.join(data_dir, f"{province}_{city}")
        if not os.path.exists(city_dir):
            os.makedirs(city_dir)
        
        # 创建示例道路数据
        road_data = {
            "city": city,
            "province": province,
            "roads": [
                {"name": "中山路", "type": "主干道", "length": 5.2, "lanes": 6},
                {"name": "人民大道", "type": "主干道", "length": 8.7, "lanes": 8},
                {"name": "和平路", "type": "次干道", "length": 3.4, "lanes": 4},
                {"name": "建设街", "type": "支路", "length": 1.8, "lanes": 2}
            ]
        }
        
        # 保存数据到JSON文件
        with open(os.path.join(city_dir, "roads.json"), "w", encoding="utf-8") as f:
            json.dump(road_data, f, ensure_ascii=False, indent=4)
        
        # 创建README文件
        readme_content = f"# {province}{city}道路数据库\n\n"
        readme_content += f"本数据库包含{province}{city}的道路信息。\n\n"
        readme_content += "## 数据结构\n\n"
        readme_content += "- roads.json: 包含主要道路信息\n"
        readme_content += "- 数据字段说明:\n"
        readme_content += "  - name: 道路名称\n"
        readme_content += "  - type: 道路类型（主干道、次干道、支路）\n"
        readme_content += "  - length: 道路长度(km)\n"
        readme_content += "  - lanes: 车道数量\n"
        
        with open(os.path.join(city_dir, "README.md"), "w", encoding="utf-8") as f:
            f.write(readme_content)
        
        self.status_var.set(f"已成功创建{province}{city}道路数据库！")
        messagebox.showinfo("成功", f"已成功创建{province}{city}道路数据库！\n保存路径: {os.path.abspath(city_dir)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = RoadDatabaseApp(root)
    root.mainloop() 
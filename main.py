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
        
        # 读json china_admin_data.json
        with open("china_admin_data.json", "r", encoding="utf-8") as f:
            data = json.load(f)
        
        # 省份数据
        self.provinces_data = data['name']
        self.city_id = data['id']
        
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
import folium
import pandas as pd


def parse_neighbors(cell):
    s = str(cell).strip()
    # 去掉外层方括号
    if s.startswith('[') and s.endswith(']'):
        s = s[1:-1]
    # 统一分隔符为英文逗号
    parts = [p.strip().strip("'\"") for p in s.split('|') if p.strip()]
    return parts

# 读取数据
province_coords = pd.read_csv("data/province_capitals_coordinates.csv")
province_coords['neighbors_list'] = province_coords['neighbors'].apply(parse_neighbors)

# 为坐标查询建立字典
coord_map = province_coords.set_index('prov')[['lat','lgt']].to_dict(orient='index')
capt_coord_map = province_coords.set_index('capt')[['lat','lgt']].to_dict(orient='index')
capitals_coordinates = pd.read_csv( "data/capitals_coordinates.csv", encoding="utf-8-sig")



# 创建地图中心（北京）
m = folium.Map(location=[39.9042, 116.4074], zoom_start=4)

# 添加省会标记
for _, row in province_coords.iterrows():
    folium.Marker(
        location=[row["lat"], row["lgt"]],
        popup=f"{row['prov']}（省会：{row['capt']}）"
    ).add_to(m)

# 仅绘制相邻省份之间的连线，避免重复（A-B 与 B-A 只画一次）
drawn = set()  # 存储已绘制的无序边 frozenset({A,B})

for _, row in province_coords.iterrows():
    a = row['prov']
    a_coord = coord_map.get(a)
    if a_coord is None:
        continue
    for b in row['neighbors_list']:
        if b not in coord_map:
            # 若邻居在表中不存在，跳过
            continue
        edge = frozenset({a, b})
        if edge in drawn:
            continue
        drawn.add(edge)

        b_coord = coord_map[b]
        folium.PolyLine(
            locations=[[a_coord['lat'], a_coord['lgt']], [b_coord['lat'], b_coord['lgt']]],
            color='gray',
            weight=3,
            dash_array='5',
            opacity=0.8
        ).add_to(m)


for _, row in capitals_coordinates.iterrows():
    a, b = row["起点"], row["终点"]
    
    a_coord = capt_coord_map.get(a)
    b_coord = capt_coord_map.get(b)
    if a_coord is None or b_coord is None:
        continue

    a_lat, a_lon = a_coord['lat'], a_coord['lgt']
    b_lat, b_lon = b_coord['lat'], b_coord['lgt']

    hsr_time = str(row["最快高铁时间(hh:mm)"]).strip()
    drive_time = str(row["无直达则自驾时间(hh:mm)"]).strip()
    trains = str(row["往返车次示例(以;分割)"]).strip()
    notes = str(row.get("备注", "")).strip()

    if hsr_time and hsr_time.lower() != "nan":
        color = "blue"
        mode = "高铁"
        time_str = hsr_time
    elif drive_time and drive_time.lower() != "nan":
        color = "green"
        mode = "自驾"
        time_str = drive_time
    else:
        color = "red"
        mode = "不可达"
        time_str = ""

    label = f"{a}->{b}:{mode}"
    if time_str:
        label += f" {time_str}"
    if trains and trains.lower() != "nan":
        label += f"｜车次：{trains}"
    # if notes and notes.lower() != "nan":
    #     label += f"｜{notes}"

    folium.PolyLine(
        locations=[[a_lat, a_lon], [b_lat, b_lon]],
        color=color,
        weight=3,
        opacity=0.85,
        tooltip=label
    ).add_to(m)

    folium.Marker(
        [ (2*a_lat + b_lat)/3 , (2*a_lon + b_lon)/3 ],
        icon=folium.DivIcon(
            icon_size=(280, 32),
            icon_anchor=(0, 0),
            html=f'<div style="font-size:10pt;display: inline-block;background:rgba(255,255,255,0.85);padding:2px 6px;border:1px solid #777;border-radius:4px;">{label}</div>'
        )
    ).add_to(m)

m.save("static/china_capitals_map.html")

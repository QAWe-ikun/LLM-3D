from room_builder.main import build

# 配置房间参数
item_list = [
    ("raw_model.glb", "沙发", 1.0),           
    ("raw_model(1).glb", "椅子", 1.0),             
    ("raw_model(2).glb", "床", 1.0),        
    ("raw_model(6).glb", "书柜", 1.0),         
    ("raw_model(9).glb", "树", 1.0),           
]

# 调用 build 函数
room = build(
    room_type="卧室",
    length=5.0,
    width=4.0,
    height=3.0,
    room_theoretical_volume=60.0,
    item_list=item_list
)

print(f"\n房间构建完成！")
print(f"房间类型: {room.room_type}")
print(f"房间尺寸: {room.length} x {room.width} x {room.height}")
print(f"共放置 {room.get_item_count()} 个物体")
from Utils import *

class distance_map:
    def __init__(self, dirt: direction, x: int, y: int, z: int, height: int, width: int):
        """
        direction : 距离平面的方向
        x, y, z: 距离平面原点的坐标
        """
        self.dirt = dirt
        self.x = x
        self.y = y
        self.z = z
        self.height = height
        self.width = width
        self.distance = np.zeros((height, width), dtype=np.int16)
        self.color = np.zeros((height, width, 3), dtype=np.uint8)

    def set_dist_map(self, bias: np.ndarray):
        self.distance = bias

    def set_color_map(self, color_map: np.ndarray):
        self.color = color_map

    def move_dist_map(self, location: list[int]):
        self.x = location[0]
        self.y = location[1]
        self.z = location[2]

    def update(self, cover_dist_map: np.ndarray):
        self.distance = np.minimum(self.distance, cover_dist_map)

    def get_dist_map(self):
        return self.distance

class item:
    def __init__(self, item_name: str, item_description: str):
        """
        item_name : 物体名称
        item_description : 物体坐标
        x_up, x_down, y_up, y_down, z_up, z_down : 物体AABB包围盒
        """
        self.item_name = item_name
        self.item_description = item_description
        file_path = find_glb_model(item_name)
        vertices, colors, mesh = read_glb_vertices(file_path)
        self.vertices = vertices
        self.colors = colors
        self.mesh = mesh
        x, y, z, length, width, height, length_sample_num, width_sample_num, height_sample_num = get_model_size(item_vertices=vertices)
        self.x, self.y, self.z = x, y, z
        self.length, self.width, self.height = length, width, height
        self.length_sample_num, self.width_sample_num, self.height_sample_num = length_sample_num, width_sample_num, height_sample_num
        self.round_distance = self.get_round_distance()

    def get_round_distance(self):
        """
        get item sampling distance
        """
        round_distance = {}
        for dirt in direction:
            round_distance[dirt] = sample(self.mesh, self.colors, dirt)

        return round_distance

    def get_distance_map(self, dirt: direction):
        return self.round_distance[dirt]

    def set_item_location(self, location: list[int]):
        """
        location: origin x, y, z
        """
        for dirt in direction:
            if dirt == direction.up or dirt == direction.down:
                z = self.z if dirt == direction.down else self.z + self.height
                temp_location = location
                temp_location[2] = z
                self.round_distance[dirt].move_dist_map(location=temp_location)
            elif dirt == direction.left or dirt == direction.right:
                x = self.x if dirt == direction.left else self.x + self.length
                temp_location = location
                temp_location[0] = x
                self.round_distance[dirt].move_dist_map(location=temp_location)
            else:
                y = self.y if dirt == direction.backward else self.y + self.width
                temp_location = location
                temp_location[1] = y
                self.round_distance[dirt].move_dist_map(location=temp_location)


class plane_map:
    def __init__(self, plane_loc: list[int], dirt: direction, carry: list[str], description: list[str], item_list: list[item]):
        self.plane_loc = plane_loc
        self.carry = carry
        self.description = description
        self.item_list = item_list
        self.dirt = dirt
        self.distance = distance_map(dirt, plane_loc[0], plane_loc[1], plane_loc[2], plane_loc[3], plane_loc[4])


    def get_dirt(self):
        return self.dirt

    def update_distance(self, distance):
        self.distance.update(cover_dist_map=distance)

    def find_location(self, new_item: item):
        """
        TODO: place model to selection location
        """
        pass

    def add_item(self, new_item: item):
        self.carry.append(new_item.item_name)
        self.description.append(new_item.item_description)
        self.item_list.append(new_item)
        self.update_distance(new_item.get_distance_map(dirt=self.dirt))

class direction_map:
    def __init__(self, dirt: direction):
        self.dirt = dirt
        self.plane_map_list = []

    def add_plane_map(self, new_plane_map: plane_map):
        """
        TODO: LLM decide wither add new plane map or not

        call by choice plane map
        """
        self.plane_map_list.append(new_plane_map)

    def choice_plane_map(self, new_item: item):
        """
        TODO: word2vec + calculate relation to choice plane map

        call by choice direction map
        """
        pass

    def update_plane(self, new_item: item):
        for plane in self.plane_map_list:
            plane_dirt = plane.get_dirt()
            dirt = find_opposite_direction(plane_dirt)
            plane.update_distance(cover_dist_map=new_item.get_distance_map(dirt=dirt))

class room:
    def __init__(self, room_type: str):
        self.room_type = str
        self.direction_map_dict = {}

        for drit in direction:
            self.direction_map_dict[drit] = direction_map(dirt=drit)

    def choice_direction_map(self, new_item: item):
        """
        TODO: word2vec + calculate relation to choice direction map
        """
        pass

    def update_direction(self, new_item: item):
        for dirt_map in self.direction_map_dict.values():
            dirt_map.update_plane(new_item)




import math
import random
# Dictionary of object lengths in meters
UNITS = {
    "banana": 0.18,
    "coffee cup": 0.10,
    "pizza slice": 0.30,
    "hotdog": 0.15,
    "burger": 0.12,
    "chocolate bar": 0.13,
    "watermelon": 0.25,
    "loaf of bread": 0.25,
    "chicken nugget": 0.05,
    "soda can": 0.12,
    "blue whale": 30.0,
    "cat": 0.50,
    "dog": 1.0,
    "horse": 2.4,
    "elephant": 6.0,
    "penguin": 0.8,
    "giraffe": 5.5,
    "crocodile": 4.0,
    "honeybee": 0.012,
    "butterfly": 0.09,
    "laptop": 0.35,
    "smartphone": 0.15,
    "toothbrush": 0.18,
    "pen": 0.14,
    "chair": 0.9,
    "table": 1.5,
    "tv": 1.22,
    "refrigerator": 1.8,
    "toilet paper roll": 0.10,
    "ruler": 0.30,
    "car": 4.5,
    "motorbike": 2.0,
    "bicycle": 1.8,
    "bus": 10.0,
    "train carriage": 25.0,
    "airplane": 70.0,
    "ship": 300.0,
    "skateboard": 0.8,
    "scooter": 1.2,
    "shopping cart": 1.0,
    "eiffel tower": 324.0,
    "statue of liberty": 93.0,
    "big ben": 96.0,
    "burj khalifa": 828.0,
    "pyramid of giza": 139.0,
    "leaning tower of pisa": 56.0,
    "empire state building": 443.0,
    "golden gate bridge": 1280.0,
    "football field": 100.0,
    "tennis court": 23.77,
    "lightsaber": 1.2,
    "minion": 1.05,
    "minecraft block": 1.0,
    "paperclip": 0.033,
    "lego brick": 0.0318,
    "frisbee": 0.27,
    "umbrella": 1.0,
    "bowling pin": 0.38,
    "frisbee dog": 0.7,
    "santas sleigh": 4.0
}

def haversine(lat1, lon1, lat2, lon2):
    R = 6371000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c

def meters_to_units(meters, unit_name):
    unit_name = unit_name.lower()
    if unit_name not in UNITS:
        raise ValueError(f"Unit '{unit_name}' not found.")
    return round(meters / UNITS[unit_name], 2)

def get_random_unit():
    return random.choice(list(UNITS.keys()))
from typing import Optional
import numpy as np
import bezier
import string
import random
import zlib
import math
import time

class check_box:
    def __init__(self, rel_position: tuple) -> None:
        self.challenge = rectangle(302, 76)
        self.check_box = rectangle(30, 30)
        self.rel_position = rel_position

    def get_checkbox(self) -> tuple:
        return self.check_box.get_box(16 + self.rel_position[0], 23 + self.rel_position[1])

class Utils:
    @staticmethod
    def randint(a: int, b: int) -> int:
        return random.randint(min(a, b), max(a, b))

    @staticmethod
    def get_ms() -> int:
        return int(time.time() * 1000)
    
    @staticmethod
    def movements(start: tuple, goal: tuple, screen: tuple, max_points: int, rnd: int, polling: int) -> list:
        cp = 4  
        control = [start]
        for _ in range(cp - 2):
            rnd_x = Utils.randint(-rnd, rnd)
            rnd_y = Utils.randint(-rnd, rnd)
            int_point = (
                Utils.randint(min(start[0], goal[0]), max(start[0], goal[0])) + rnd_x,
                Utils.randint(min(start[1], goal[1]), max(start[1], goal[1])) + rnd_y
            )
            clamped = (
                np.clip(int_point[0], 0, screen[0]),
                np.clip(int_point[1], 0, screen[1])
            )
            control.append(clamped)
        control.append(goal)

        control_points = np.asfortranarray([[p[0] for p in control], [p[1] for p in control]])
        degree = min(3, len(control) - 1) 
        curve = bezier.Curve(control_points, degree=degree)
        
        distance = Utils.distance(start, goal)
        num_steps = min(max_points, max(20, int(distance / polling)))

        t = np.linspace(-3, 3, num_steps)
        velocity = np.exp(-t**2) 
        velocity /= np.sum(velocity) 
        u = np.cumsum(velocity)
        u /= u[-1]

        points = curve.evaluate_multi(u)
        motion = []
        pointer_mouse = []
        ts = 0
        prev_x, prev_y = start

        for x_val, y_val in zip(*(i.astype(int) for i in points)):
            delta_x = abs(x_val - prev_x)
            delta_y = abs(y_val - prev_y)
            max_delta = max(delta_x, delta_y)
            jitter_range = min(2, max(1, max_delta // 10)) 
            jitter_x = Utils.randint(-jitter_range, jitter_range)
            jitter_y = Utils.randint(-jitter_range, jitter_range)
            jittered_x = np.clip(x_val + jitter_x, 0, screen[0])
            jittered_y = np.clip(y_val + jitter_y, 0, screen[1])
            
            incre = int(np.random.normal(loc=30, scale=10)) 
            incre = max(10, incre)
            timestamp = int(Utils.get_ms() + ts)
            motion.append([int(jittered_x), int(jittered_y), timestamp])
            pointer_mouse.append([int(jittered_x), int(jittered_y), timestamp])
            
            ts += incre
            prev_x, prev_y = x_val, y_val

        return motion, pointer_mouse

    @staticmethod
    def theme(theme: str) -> int:
        return zlib.crc32(theme.encode()) & 0xFFFFFFFF

    @staticmethod
    def distance(a: tuple, b: tuple) -> float:
        return math.sqrt((b[0] - a[0]) ** 2 + (b[1] - a[1]) ** 2)

    @staticmethod
    def check_mm(start: tuple, goal: tuple, screen_width: int, screen_height: int) -> list:
        distance = math.hypot(goal[0] - start[0], goal[1] - start[1])
        peak_vel = 22000 + 0.2 * distance
        avg_speed = peak_vel / 4
        num_points = max(random.randint(16, 20), int(distance / (avg_speed / 65)))
        total_time = distance / avg_speed
        timestamp = int(time.time() * 1000)
        t = np.linspace(0, total_time, num_points)
        accel_time = total_time * 0.25
        velocity = (
            np.where(t <= accel_time, peak_vel * (t / accel_time) ** 2, 0) +
            np.where((t > accel_time), peak_vel * ((1 - (t - accel_time) / (total_time - accel_time)) ** 3), 0)
        )
        velocity = np.clip(velocity, 0, None)
        position = np.cumsum(velocity)
        position /= position[-1]
        control = [
            (min(max(start[0] + random.uniform(0.3, 0.8) * (goal[0] - start[0]) + random.uniform(-70, 70), 0), screen_width),
             min(max(start[1] + random.uniform(0.3, 0.8) * (goal[1] - start[1]) + random.uniform(-70, 70), 0), screen_height))
            for _ in range(3)
        ]
        points = [start] + control + [goal]
    
        def curve(t, points):
            n = len(points) - 1
            return sum(
                math.comb(n, i) * (t ** i) * ((1 - t) ** (n - i)) * (np.array(point) + np.random.normal(0, 0.3, size=len(point)))
                for i, point in enumerate(points)
            )
    
        positions = [curve(s, points) for s in position]
        deviation = distance * 0.003
        positions = np.array(positions) + np.random.uniform(-deviation, deviation, (num_points, 2))
        tremors = distance * 0.005 * np.sin(2 * np.pi * random.uniform(1.5, 3.5) * t[:, None])
        positions += tremors
        strength = distance * 0.01
        jitter = np.random.uniform(-strength, strength, positions.shape)
        positions += jitter
    
        positions = np.round(positions).astype(int)
        positions[0], positions[-1] = start, goal
        positions = np.clip(positions, [0, 0], [screen_width, screen_height])
        stamps = [timestamp + int(ti * 1000) for ti in t]
    
        return [[int(positions[i][0]), int(positions[i][1]), int(stamps[i])] for i in range(num_points)]

    @staticmethod
    def mean_periods(timestamps: list) -> float:
        periods = [timestamps[i + 1] - timestamps[i] for i in range(len(timestamps) - 1)]
        return sum(periods) / len(periods) if periods else 0

    @staticmethod
    def random_point(bbox: tuple) -> tuple:
        return Utils.randint(bbox[0][0], bbox[1][0]), Utils.randint(bbox[0][1], bbox[1][1])

    @staticmethod
    def get_center(bbox: tuple) -> tuple:
        x1, y1 = bbox[0]
        x2, y2 = bbox[1]

        return int(x1 + (x2 - x1) / 2), int(y1 + (y2 - y1) / 2)
    
    @staticmethod
    def rnd_point(bbox: tuple) -> tuple:
        return Utils.randint(bbox[0][0], bbox[1][0]), Utils.randint(bbox[0][1], bbox[1][1])

    @staticmethod
    def convert_answers(answers: dict, captcha_type: str) -> dict:
        result = {}
        match captcha_type:
            case "image_label_binary":
                answers = list(answers.values()) if isinstance(answers, dict) else answers
                result = {i: answer.lower() == 'true' if isinstance(answer, str) else answer for i, answer in enumerate(answers)}
            case "image_label_area_select":
                coords = [i for sub in answers.values() for i in sub]
                sorteds = sorted(coords, key=lambda x: x['entity_coords'][1])
                result = {i + 1: item['entity_coords'] for i, item in enumerate(sorteds)}

        return result
    
    @staticmethod
    def random_middle(bbox: tuple) -> tuple:
        mx, my = (sum(c) / 2 for c in zip(*bbox))
        wr, hr = ((e - s) * 0.1 for s, e in zip(*bbox))
        return (random.uniform(mx - wr, mx + wr), random.uniform(my - hr, my + hr))
    
class Widget:
    def __init__(self, rel_position: tuple) -> None:
        self.widget = rectangle(300, 75)
        self.check_box = rectangle(28, 28)
        self.rel_position = rel_position

    def get_check(self) -> tuple:
        return self.check_box.get_box(16 + self.rel_position[0], 23 + self.rel_position[1])

    def get_closest(self, position: tuple) -> tuple:
        corners = self.widget.get_corners(self.rel_position[0], self.rel_position[1])
        sorted_corners = sorted(corners, key=lambda c: Utils.distance(position, c))
        return sorted_corners[0], sorted_corners[1]

class rectangle:
    def __init__(self, width: int, height: int) -> None:
        self.width = width
        self.height = height

    def get_size(self) -> tuple:
        return self.width, self.height

    def get_box(self, rel_x: int, rel_y: int) -> tuple:
        return (rel_x, rel_y), (rel_x + self.width, rel_y + self.height)

    def get_corners(self, rel_x: int = 0, rel_y: int = 0) -> list:
        return [
            (rel_x, rel_y),
            (rel_x + self.width, rel_y),
            (rel_x, rel_y + self.height),
            (rel_x + self.width, rel_y + self.height)
        ]

class check_box:
    def __init__(self, rel_position: tuple) -> None:
        self.challenge = rectangle(302, 76)
        self.check_box = rectangle(30, 30)
        self.rel_position = rel_position

    def get_checkbox(self) -> tuple:
        return self.check_box.get_box(16 + self.rel_position[0], 23 + self.rel_position[1])

class binary_challenge:
    def __init__(self, box_centre: tuple, screen_size: tuple, has_example: bool = False) -> None:
        x = min(screen_size[0] / 2 - 200, box_centre[0] + 25)
        y = max(10, min(screen_size[1] - 610, box_centre[1] - 300))

        self.position = x, y
        self.challenge = rectangle(400, 600)
        self.button = rectangle(80, 35)
        self.image = rectangle(120, 120)
        self.images = {str(i): ((i % 3) * 130 + 10, (i // 3) * 130 + 130) for i in range(9)}

    def get_image(self, index: int) -> tuple:
        index = index % 9
        x, y = self.images.get(str(index))
        return self.image.get_box(x, y)

    def get_button(self) -> tuple:
        return self.button.get_box(340, 560)

class area_challenge:
    def __init__(self, box_centre: tuple, screen_size: tuple, has_examples: bool) -> None:
        hight = 686 if has_examples else 580
        x = min(screen_size[0] / 2 - 260, box_centre[0] + 25)
        y = max(10, min(screen_size[1] - hight - 10, box_centre[1] - hight / 2))
        self.position = x, y

        self.challenge = rectangle(520, hight)
        self.canvas = rectangle(500, 586 if has_examples else 480)
        self.button = rectangle(80, 35)

    def get_location(self, coords: list) -> tuple:
        canvas_x = (self.challenge.width - self.canvas.width) / 2 + coords[0]
        canvas_y = 10 + coords[1]
        return canvas_x, canvas_y

    def get_button(self) -> tuple:
        return self.button.get_box(self.challenge.width - 90, self.challenge.height - 40)

class text_challenge:
    def __init__(self, box_centre: tuple, screen_size: tuple, has_example: bool = False) -> None:
        x = min(screen_size[0] / 2 - 200, box_centre[0] + 25)
        y = max(10, min(screen_size[1] - 610, box_centre[1] - 300))

        self.position = x, y
        self.challenge = rectangle(500, 330)
        self.button = rectangle(84, 39)
        self.text_box = rectangle(444, 40)

    def get_text_box(self):
        return self.text_box.get_box(28, 165)
    
    def get_button(self) -> tuple:
        return self.button.get_box(280, 255)

class get_cap:
    def __init__(self, fp, url: str, pel: str, size: str, theme: Optional[str] = 'light') -> None:
        self.widget_id = '0' + ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
        self.fp = fp
        self.theme = Utils.theme(theme)
        self.user_agent = self.fp['components']['navigator']['user_agent']
        
        self.mobile = False

        if 'Mobile' in self.user_agent:
            self.mobile = True 

        computer_cores = random.choice([
            [2, 4], 
            [4, 4], 
            [4, 8],  
            [6, 12], 
            [8, 16],
            [16, 32],
        ])

        phone_cores = random.choice([
            [4, 4],  
            [6, 6], 
            [8, 8],  
        ])

        cores = computer_cores if not self.mobile else phone_cores

        self.hardware_concurrency = cores[0]
        self.device_memory = cores[1]
        self.platform = fp['components']['navigator']['platform']
        scr = fp['components']['screen']
        self.screen = [
            scr['width'],
            scr['height'],
            scr['avail_width'],
            scr['avail_height']
        ]

        self.screen_size = (self.screen[2], self.screen[3])

        self.depth = [
            scr['color_depth'],
            scr['pixel_depth']
        ]
        
        self.pel = pel
        self.size = size
        self.exec = 'm'

        self.appversion = self.user_agent.split('Mozilla/')[1]
        brands = {
            "chrome": {
                "brands": [
                    {
                        "brand": "Google Chrome",
                        "version": f"{self.user_agent.split('Chrome/')[1].split(' ')[0] if 'Chrome/' in self.user_agent else '131.0.0.0'}"
                    },
                    {
                        "brand": "Chromium",
                        "version": f"{self.user_agent.split('Chrome/')[1].split(' ')[0] if 'Chrome/' in self.user_agent else '131.0.0.0'}"
                    },
                    {
                        "brand": "Not_A Brand",
                        "version": "24"
                    }
                ],
                "mobile": self.mobile,
                "platform": self.platform
            },
            "safari": {
                "brands": [
                    {
                        "brand": "AppleWebKit",
                        "version": f"{self.user_agent.split('AppleWebKit/')[1].split(' ')[0] if 'AppleWebKit/' in self.user_agent else '537.36'}"
                    },
                    {
                        "brand": "Safari",
                        "version": f"{self.user_agent.split('Version/')[1].split(' ')[0] if 'Version/' in self.user_agent else '18.2'}"
                    }
                ],
                "mobile": self.mobile,
                "platform": self.platform
            }
        }

        if "Chrome" in self.user_agent:
            if fp['components']['chrome']:
                self.brand = brands.get("chrome")
            else:
                self.brand = brands.get("safari")
        elif "Safari" in self.user_agent:
            self.brand = brands.get("safari")
        else:
            self.brand = brands.get("chrome")

        self.url = url

        random_point = Utils.rnd_point(((0, 0), (self.screen[0] - 150, self.screen[1] - 38)))
        self.widget = Widget(random_point)
        self.challenge = self.widget
        self.position = Utils.rnd_point(((0, 0), self.screen))

        data = {
            "st": Utils.get_ms(),
            "pm": [],
            "pm-mp": 0,
            "mm": [],
            "mm-mp": 0,
            "md": [],
            "md-mp": 0,
            "mu": [],
            "mu-mp": 0,
            "v": 1,
            "topLevel": self.top_level(),
            "session": [],
            "widgetList": [
                self.widget_id
            ],
            "widgetId": self.widget_id,
            "href": self.url,
            "prev": {
                "escaped": False,
                "passed": False,
                "expiredChallenge": False,
                "expiredResponse": False
            }
        }

        goal = Utils.rnd_point(self.widget.get_check())
        self.mouse_movement, self.pointer_mouse_movement = Utils.movements(self.position, goal, self.screen, 20, 5, 10)
        data['pm'] = [[x - random_point[0], y - random_point[1], t] for x, y, t in self.pointer_mouse_movement]
        data['pm-mp'] = Utils.mean_periods([x[-1] for x in self.pointer_mouse_movement])
        data['mm'] = [[x - random_point[0], y - random_point[1], t] for x, y, t in self.mouse_movement]
        data['mm-mp'] = Utils.mean_periods([x[-1] for x in self.mouse_movement])
        data['md'].append(data['mm'][-1][:-1] + [Utils.get_ms()])
        data['mu'].append(data['mm'][-1][:-1] + [Utils.get_ms() + (1 / Utils.randint(3, 7))])
        self.data = data

    def top_level(self) -> dict:
        data = {
            "st": Utils.get_ms(),
            "sc": {
                "availWidth": self.screen[2],
                "availHeight": self.screen[3],
                "width": self.screen[0],
                "height": self.screen[1],
                "colorDepth": self.depth[0],
                "pixelDepth": self.depth[1],
                "availLeft": 0,
                "availTop": 0,
                "onchange": None,
                "isExtended": False
            },
            "wi": [
                self.screen[2],
                self.screen[3] - 87
            ],
            "nv": {
                "vendorSub": "",
                "productSub": "20030107",
                "vendor": "Google Inc.",
                "maxTouchPoints": 0 if not self.mobile else 10,
                "scheduling": {},
                "userActivation": {},
                "doNotTrack": "1",
                "geolocation": {},
                "connection": {},
                "pdfViewerEnabled": True,
                "webkitTemporaryStorage": {},
                "windowControlsOverlay": {},
                "hardwareConcurrency": self.hardware_concurrency,
                "cookieEnabled": True,
                "appCodeName": "Mozilla",
                "appName": "Netscape",
                "appVersion": self.user_agent.split("Mozilla/")[1],
                "platform": self.platform,
                "product": "Gecko",
                "userAgent": self.user_agent,
                "language": "en-US",
                "languages": [
                    "en-US",
                    "en"
                ],
                "onLine": True,
                "webdriver": False,
                "deprecatedRunAdAuctionEnforcesKAnonymity": False,
                "protectedAudience": {},
                "bluetooth": {},
                "storageBuckets": {},
                "clipboard": {},
                "credentials": {},
                "keyboard": {},
                "managed": {},
                "mediaDevices": {},
                "storage": {},
                "serviceWorker": {},
                "virtualKeyboard": {},
                "wakeLock": {},
                "deviceMemory": self.device_memory,
                "userAgentData": self.brand,
                "login": {},
                "ink": {},
                "mediaCapabilities": {},
                "hid": {},
                "locks": {},
                "gpu": {},
                "mediaSession": {},
                "permissions": {},
                "presentation": {},
                "usb": {},
                "xr": {},
                "serial": {},
                "plugins": [
                    "internal-pdf-viewer",
                    "internal-pdf-viewer",
                    "internal-pdf-viewer",
                    "internal-pdf-viewer",
                    "internal-pdf-viewer"
                ]
            },
            "dr": "",
            "inv": False,
            "theme": self.theme,
            "pel": self.pel,
            "exec": "m",
            "wn": [
                [
                    self.screen[2], 
                    self.screen[3], 
                    1, 
                    Utils.get_ms()
                ]
            ],
            "wn-mp": 0,
            "xy": [
                [
                    0, 
                    0, 
                    1, 
                    Utils.get_ms()
                ]
            ],
            "xy-mp": 0,
            "pm": [],
            "pm-mp": 0,
            "mm": [],
            "mm-mp": 0
        }

        goal = Utils.rnd_point(self.widget.get_closest(self.position))
        mouse_movement, pointer_mouse_movement = Utils.movements(self.position, goal, self.screen, 75, 5, 15)
        self.position = goal
        data['pm'] = pointer_mouse_movement
        data['pm-mp'] = Utils.mean_periods([x[-1] for x in pointer_mouse_movement])
        data['mm'] = mouse_movement
        data['mm-mp'] = Utils.mean_periods([x[-1] for x in mouse_movement])

        return data

class check_cap:
    def __init__(self, old_data: get_cap, answers: dict, captcha_type: str, has_examples: bool = False) -> None:
        self.old_data = old_data
        self.screen_size = old_data.screen_size
        challenge_center = Utils.get_center(old_data.challenge.get_check())
        captcha_types = {
            "image_label_binary": binary_challenge,
            "image_label_area_select": area_challenge,
            "text_free_entry": text_challenge
        }

        self.challenge = captcha_types.get(captcha_type)(challenge_center, self.screen_size, has_examples)
        position = (self.challenge.position[0], self.challenge.position[1])
        top = self.old_data.data["topLevel"]
        top['lpt'] = Utils.get_ms()+random.randint(10000, 13000)

        tc = {}

        for i in answers:
            tc[i] = [
                1.0212765957446808,
                10,
                93.63829787234042
            ]


        self.data = {
            "st": Utils.get_ms(),
            "dct": Utils.get_ms(),
            "pm": [],
            "pm-mp": 19.43137254901962,
            "mm": [],
            "mm-mp": 19.43137254901962,
            "md": [],
            "md-mp": 1604.3333333333333,
            "mu": [],
            "mu-mp": 1624.3333333333333,
            "topLevel": top,
            "v": 1,
            "tc": tc
        }

        match captcha_type:
            case "image_label_binary":
                answers = Utils.convert_answers(answers, captcha_type)
                count = len(answers)
                counter = 0
                for answer_key, is_correct in answers.items():
                    if is_correct:
                        goal = Utils.random_point(self.challenge.get_image(int(answer_key)))
                        mm = Utils.check_mm(position, goal, self.screen_size[0], self.screen_size[1])
                        self.data["mm"].extend(mm)
                        self.data["pm"].extend(mm)
                        self.data["md"].append(list(goal) + [Utils.get_ms()])
                        self.data["mu"].append(list(goal) + [Utils.get_ms()+100])
                        position = goal
                    counter += 1
                    if count == 18 and counter == 9:
                        goal = Utils.random_point(self.challenge.get_button())
                        mm = Utils.check_mm(position, goal, self.screen_size[0], self.screen_size[1])
                        self.data["mm"] += mm
                        self.data["pm"] += mm
                        self.data["md"].append(list(goal) + [Utils.get_ms()])
                        self.data["mu"].append(list(goal) + [Utils.get_ms()+100])
                        position = goal

                if count <= 9 or counter == 18:
                    goal = Utils.random_point(self.challenge.get_button())
                    mm = Utils.check_mm(position, goal, self.screen_size[0], self.screen_size[1])
                    self.data["mm"] += mm
                    self.data["pm"] += mm
                    self.data["md"].append(list(goal) + [Utils.get_ms()])
                    self.data["mu"].append(list(goal) + [Utils.get_ms()+100])
                    position = goal

            case "image_label_area_select": 
                coords = list(Utils.convert_answers(answers, captcha_type).items())
                for i, coord in coords:
                    goal = self.challenge.get_location(coord)
                    mm = Utils.check_mm(position, goal, self.screen_size[0], self.screen_size[1])
                    self.data["mm"].extend(mm)
                    self.data["pm"].extend(mm)
                    self.data["md"].append(list(goal) + [Utils.get_ms()])
                    self.data["mu"].append(list(goal) + [Utils.get_ms()+100])
                    position = goal

                    goal = Utils.random_point(self.challenge.get_button())
                    mm = Utils.check_mm(position, goal, self.screen_size[0], self.screen_size[1])
                    self.data["mm"] += mm
                    self.data["pm"] += mm
                    self.data["md"].append(list(goal) + [Utils.get_ms()])
                    self.data["mu"].append(list(goal) + [Utils.get_ms()+100])
                    position = goal
            
            case "text_free_entry":
                for i in ["wn", "xy", "pm", "mm"]:
                    self.data["topLevel"][i] = []
            
                for i in range(3):
                    goal = Utils.random_middle(self.challenge.get_text_box())
                    mm = Utils.check_mm(position, goal, self.screen_size[0], self.screen_size[1])
                    self.data["mm"].extend(mm)
                    self.data["pm"].extend(mm)
                    self.data["md"].append(list(goal) + [Utils.get_ms()])
                    self.data["mu"].append(list(goal) + [Utils.get_ms()+100])
                    position = goal

                    goal = Utils.random_point(self.challenge.get_button())
                    mm = Utils.check_mm(position, goal, self.screen_size[0], self.screen_size[1])
                    self.data["mm"] += mm
                    self.data["pm"] += mm
                    self.data["md"].append(list(goal) + [Utils.get_ms()])
                    self.data["mu"].append(list(goal) + [Utils.get_ms()+100])
                    position = goal

        for i in ["mm", "md", "mu", "pm"]:
            self.data[i + "-mp"] = Utils.mean_periods([i[-1] for i in self.data[i]])

class Motion:
    def __init__(self, fp: Optional[str], url: Optional[str], pel: Optional[str], size: Optional[str], custom_theme: Optional[str] = False) -> Optional[None]:  
        self.fp = fp
        self.url = url
        self.pel = pel
        self.size = size
        self.get_captcha_mm = get_cap(self.fp, self.url, self.pel, self.size, "dark" if custom_theme else 'light')

    def get_captcha(self) -> dict:
        return self.get_captcha_mm.data

    def check_captcha(self, answers: dict, captcha_type: str, has_examples: bool = False) -> dict:
        return check_cap(self.get_captcha_mm, answers, captcha_type, has_examples).data

def test():

    def create_sample_fingerprint():
        return {
            "components":{
                "navigator":{
                    "user_agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36",
                    "language":"en-US",
                    "languages":[
                        "en-US",
                        "en"
                    ],
                    "platform":"Win32",
                    "max_touch_points":0,
                    "webdriver":False,
                    "notification_query_permission":None,
                    "plugins_undefined":False
                },
                "screen":{
                    "color_depth":24,
                    "pixel_depth":24,
                    "width":1920,
                    "height":1080,
                    "avail_width":1920,
                    "avail_height":1040
                },
                "device_pixel_ratio":1.0,
                "has_session_storage":True,
                "has_local_storage":True,
                "has_indexed_db":True,
                "web_gl_hash":"-1",
                "canvas_hash":"7021875685296378361",
                "has_touch":False,
                "notification_api_permission":"Denied",
                "chrome":True,
                "to_string_length":33,
                "err_firefox":None,
                "pi":None,
                "r_bot_score":0,
                "r_bot_score_suspicious_keys":[
                    
                ],
                "r_bot_score_2":0,
                "audio_hash":"-1",
                "extensions":[
                    False
                ],
                "parent_win_hash":"4883931453396206889",
                "webrtc_hash":"-1",
                "performance_hash":"4874429083785836575",
                "unique_keys":"onExpire,0,grecaptcha,onSuccess,1,Raven,hcaptcha",
                "inv_unique_keys":"YoAH99j,fetchLater,BIBRRRT,FL0fi3W,L2Ue17x,CbbnvG,Ahi5ti,CjWy1K2,oncommand,EJBCFPi,s9zZT2T,Bhke5eG,NPDgjU,vhUQP5w,O_PCTOC,hhmFDk,Fqm7CfE,KAOs21P,kTOlHxx,__wdata,SvsDPjh,xagVpE,yKK3d3,KOERc0t,nSbBAT4,Z5BVmtW,vfz3_w,X9tKn4,hsw,iSlSvoq,cV4yyP4,wg7XZX,E2hVLAf,GYs5AY,zGpUjY,usPZYNU,g3XvU0_,Rw4WBNQ,B32tRc,P5EkGXu,LJ9kol2",
                "common_keys_hash":3990815276,
                "common_keys_tail":"setTimeout,stop,structuredClone,webkitCancelAnimationFrame,webkitRequestAnimationFrame,chrome,caches,cookieStore,ondevicemotion,ondeviceorientation,ondeviceorientationabsolute,launchQueue,sharedStorage,documentPictureInPicture,getScreenDetails,queryLocalFonts,showDirectoryPicker,showOpenFilePicker,showSaveFilePicker,originAgentCluster,onpageswap,onpagereveal,credentialless,fence,speechSynthesis,onscrollend,onscrollsnapchange,onscrollsnapchanging,webkitRequestFileSystem,webkitResolveLocalFileSystemURL",
                "features":{
                    "performance_entries":True,
                    "web_audio":True,
                    "web_rtc":True,
                    "canvas_2d":True,
                    "fetch":True
                }
            }
        }

    sample_fingerprint = create_sample_fingerprint()
    sample_url = "https://accounts.hcaptcha.com/demo"
    sample_pel = "<div id=\"hcaptcha-demo\" class=\"h-captcha\" data-sitekey=\"a5f74b19-9e45-40e0-b45d-47ff91b7a6c2\" data-callback=\"onSuccess\" data-expired-callback=\"onExpire\"></div>"
    sample_size = "normal"

    motion = Motion(sample_fingerprint, sample_url, sample_pel, sample_size)
    captcha_data = motion.get_captcha()

    import json
    print(json.dumps(captcha_data, indent=2))

    binary_answers = {0: 1, 1: 0, 2: 1}
    check_data = motion.check_captcha(binary_answers, "image_label_binary")
    print("\nCheck captcha result:")
    print(json.dumps(check_data, indent=2))

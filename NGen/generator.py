import random, json, pytz, datetime, secrets, time, re
from Decrypt import EncryptionSystem

try:
    from .helper import parse_jwt, stamp, rand_hash, xhash
    from .events import HcapEvents
except:
    from helper import parse_jwt, stamp, rand_hash, xhash
    from events import HcapEvents

try:
    with open("general_datas.json", "r", encoding="utf-8") as f:
        tzs = json.loads(f.read())
except: 
    with open("NGen/general_datas.json", "r") as f:
        tzs = json.loads(f.read())

fall_back_version = "136"

chrome_data = {
    "135": {
        "useragent_versions": ("135.0.7049.115", "135.0.7049.114"),
        "sechua": ["Google Chrome 135", "Not-A.Brand 8", "Chromium 135"],
        "useragent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36"
    },
    "136": {
        "useragent_versions": ("136.0.7103.114", "136.0.7103.49"),
        "sechua": ["Chromium 136", "Google Chrome 136", "Not.A/Brand 99"],
        "useragent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36"
    }
}

useragent_versions = ("136.0.7103.114", "136.0.7103.49")
sechua = ["Chromium 136", "Google Chrome 136", "Not.A/Brand 99"]
useragent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36"

def generate_secure_number():
    return str(secrets.randbits(64))

def dump_data(data) -> str:
    return json.dumps(data, separators=(",", ":"), ensure_ascii=False)

def Algorithm(value, decoded_key):
    if value is None:
        return None

    key_mapping = decoded_key[0]
    modified_string = decoded_key[1]
    key_q = decoded_key[2]
    valid_char_regex = re.compile(r"[a-z\d.,/#!$%^&*;:{}=\-_~()\s]", re.IGNORECASE)

    input_value = str(value) if not isinstance(value, str) else value
    input_length = len(input_value)

    if input_length == 83:
        input_value = input_value
    elif input_length > 83:
        input_value = input_value[-83:]
    else:
        input_value = input_value + modified_string[input_length:83]

    reversed_split = " ".join(reversed(input_value.split(" ")))
    reversed_chars = list(reversed(reversed_split))

    result = []
    for current_char in reversed_chars:
        if valid_char_regex.match(current_char):
            mapped_index = key_mapping.get(current_char, None)
            if mapped_index is not None:
                result.append(modified_string[(mapped_index + key_q) % 83])
            else:
                result.append(current_char)
        else:
            result.append(current_char)

    return dump_data("".join(result))

def generate_key(key_input, blob_integer, timezone_offset, hour, performance_metric, random_seed):
    intermediate_a = (timezone_offset + hour + performance_metric) * random_seed
    temp_fa = to_32bit_signed(intermediate_a + blob_integer)
    q_value = 1 + int((((~temp_fa + 1 if temp_fa < 0 else temp_fa) * 1664525 + 1013904223) & 0xFFFFFFFF) / 4294967296 * 82)
    constant_ea = 83
    g_value = to_32bit_signed(intermediate_a + blob_integer)

    positive_g = ~g_value + 1 if g_value < 0 else g_value
    positive_g = to_32bit_signed(positive_g)
    mapping_object = {}
    key_array = list(key_input)
    loop_index = constant_ea
    while loop_index:
        positive_g = to_js32(float(positive_g) * 1103515245 + 12345) & 0x7FFFFFFF
        intermediate_e = positive_g % loop_index
        loop_index -= 1
        intermediate_i = key_array[loop_index]
        key_array[loop_index] = key_array[intermediate_e]
        key_array[intermediate_e] = intermediate_i
        mapping_object[key_array[loop_index]] = (loop_index + q_value) % constant_ea

    mapping_object[key_array[0]] = (0 + q_value) % constant_ea
    return [mapping_object, ''.join(key_array), q_value]

def to_js32(value):
    value = int(value) & 0xFFFFFFFF
    if value >= 0x80000000:
        value -= 0x100000000
    return value

def to_32bit_signed(value):
    value = int(value) & 0xFFFFFFFF
    return value if value < 0x80000000 else value - 0x100000000

def random_perf() -> float:
    perf_value = random.uniform(0.00999996423721313, 0.00999999776482582) + round(random.uniform(0.1,0.9),2)
    
    chance_to_round = random.randint(1,8)
    
    if chance_to_round == 4:
        perf_value = round(int(perf_value) + random.uniform(0.1,0.8), 2)
    
    return perf_value

def get_fake_recursion_limit(min_val: int = 4000, max_val: int = 5294): # 17295 15151 | 17199 11558 | 18227 10465 | 16816 15110
    first_number = random.randint(min_val, max_val)
    second_number = (72 * first_number) // 80
    third_number = (second_number * 8) / (first_number - second_number)
    return [third_number,first_number, second_number]

def get_languages_from_tz(timezone_id: str):
    lgs = []
    for language in tzs:
        exp_tzs: list = tzs[language]["exp_tz"]
        
        languages:list = random.choice(tzs[language]["languages"])
        
        for exp_tz in exp_tzs:
            
            data = exp_tz
            
            if data[0] == timezone_id:
                lgs.append((language, languages))
    
    if len(lgs) == 0:            
        print(f"[-] !!!!!!!! TIMEZONE UNDETECTED --> {timezone_id} !!!!!!!!!!!")
        return "fr",["fr"]

    choiced = random.choice(lgs)
    
    return choiced[0], choiced[1]

def get_random_speech_from_language(language: str) -> list:
    bscsp = tzs[language]["speechs"]
    
    for d in bscsp:
        newd = d[0]
        
        if language in newd[0][1]:
            return d
        
    for languag in tzs:
        tzse = tzs[languag]["speechs"]
        
        for d in tzse:
            newd = d[0]
            
            if language in newd[0][1]:
                return d
    
    try:
        dat = random.choice(tzs[language]["speechs"])
        
    except: 
        dat = random.choice(tzs["en-US"]["speechs"])
        
    return dat
    
def find_expensive_timezone(tz, lang):
    exp = tzs[lang]["exp_tz"]
    
    founds = []
    for expesnive_timezone in exp:
        expesnive_timezone = expesnive_timezone
        if expesnive_timezone[0] == tz:
            founds.append(expesnive_timezone)
            
    if len(founds) == 0:
        print(F"TIMEZONE ERROR : didnt found for {tz}")
        return [tz,-60,-60,-3203647761000,'Central European Standard Time', 'en-US']
    
    good = None
    
    for i in founds:
        if i[5].lower() == lang or lang in i[5].lower():
            good = i 
            break 
        
            
    if good is None:
        good = random.choice(founds)

    return good

def r(A, Q, B=False):
    if B or len(locals()) == 2:  # Equivalent to `arguments.length === 2`
        g = None
        D = 0
        while D < len(Q):
            if g is not None or D not in range(len(Q)):  # `D in Q` isn't directly translatable
                if g is None:
                    g = Q[:D]  # Equivalent to `Array.prototype.slice.call(Q, 0, D)`
                g[D:D + 1] = [Q[D]]  # Ensure assignment works correctly for indexable Q
            D += 1
    return A + (g if g is not None else Q[:])

def NQ(A):
    if len(A) == 0:
        return 0

    I = sorted(r([], A, True))

    C = len(I) // 2
    if len(I) % 2 != 0:
        return I[C]
    else:
        return (I[C - 1] + I[C]) / 2

def get_average(request_history: list):
    history_x = [] 
    history_y = []
        
    for i in request_history:
        x = i[1]
        y = i[2]
            
        if x > 0:
            history_x.append(x)
        if y > 0:
            history_y.append(y)

    return NQ(history_x), NQ(history_y)

def chrome_version(userAgent):
    chrome_version = re.search(r"Chrome/(\d+)\.", userAgent)

    if chrome_version:
        return chrome_version.group(1)
    
    return fall_back_version

class N:
    def __init__(self, timezone: str, link: str, sitekey: str, v2_api: bool, fingerprint, system: EncryptionSystem) -> None:
        global useragent_versions, sechua, useragent, chrome_data, fall_back_version

        self.system = system

        self.events_order =['performance_now', 'function_tostring_length', 'math_fingerprint_and_errors', 'proxy_check', 'performance_mark', 'no_performance_caveat', 'gpu_information', 'encoded_gpu_information', 'hashed_gpu_and_extensions', 'hashed_gpu_bits', 'gpu_array_expression_num_0', 'gpu_array_expression_num_1', 'gpu_array_expression_num_2', 'gpu_array_expression_num_3', 'gpu_array_expression_num_4', 'gpu_array_expression_num_5', 'gpu_array_expression_num_6', 'gpu_array_expression_num_7', 'gpu_array_expression_num_8', 'hashed_gpu_extensions', 'small_canvas', 'performance_compare', 'time_origin', 'request_history', 'average_response_start', 'average_response_end', 'timezone', 'timezone_array', 'encoded_timezone', 'timezone_hours_array', 'navigator_properties', 'encoded_user_agent', 'screen_information', 'supported_matches', 'hashed_html_structure', 'styles_and_js_array', 'triangle_canvas_fingerprint', 'supported_media_types', 'emoji_canvas_fingerprint', 'small_square_data', 'bounding_box_information', 'unique_text_metrics', 'random_pixel_data', 'hashed_window_keys', 'window_keys_length', 'windows_chrome_related_array', 'windows_css_related_array', 'computed_styles', 'computed_styles_length', 'client_reacts', 'audio_triangle_fingerprint', 'user_agent', 'post_message_user_agent_values', 'recursion_array', 'user_agent_entropy_values', 'font_indexes', 'hashed_speech_synthesis', 'sliced_three_speech_synthesis', 'web_rtc', 'performance_array_with_sevice_worker', 'encoded_quota', 'worker_recursion_array', 'worker_user_agent', 'worker_language_timezone', 'worker_hc_memory_array', 'worker_gpu_vendors', 'worker_gpu_depths_hashed', 'worker_gpu_names', 'worker_gpu_shits', 'performance_difference']
        self.events_order_other = ['performance_now', 'function_tostring_length', 'math_fingerprint_and_errors',"performance_compare", 'navigator_properties', 'encoded_user_agent', 'timezone', 'timezone_array', 'encoded_timezone', 'timezone_hours_array', 'time_origin', 'request_history', 'average_response_start', 'average_response_end', 'screen_information', 'proxy_check', 'performance_mark', 'web_rtc', 'performance_array_with_sevice_worker', 'encoded_quota', 'hashed_speech_synthesis', 'sliced_three_speech_synthesis', 'recursion_array', 'audio_triangle_fingerprint', 'user_agent', 'post_message_user_agent_values', 'user_agent_entropy_values', 'font_indexes', 'worker_user_agent', 'worker_language_timezone', 'worker_hc_memory_array', 'worker_gpu_vendors', 'worker_gpu_depths_hashed', 'worker_gpu_names', 'worker_gpu_shits', 'no_performance_caveat', 'gpu_information', 'encoded_gpu_information', 'hashed_gpu_and_extensions', 'hashed_gpu_bits', 'gpu_array_expression_num_0', 'gpu_array_expression_num_1', 'gpu_array_expression_num_2', 'gpu_array_expression_num_3', 'gpu_array_expression_num_4', 'gpu_array_expression_num_5', 'gpu_array_expression_num_6', 'gpu_array_expression_num_7', 'gpu_array_expression_num_8', 'hashed_gpu_extensions', 'client_reacts', 'small_canvas', 'hashed_html_structure', 'styles_and_js_array', 'supported_media_types', 'supported_matches', 'emoji_canvas_fingerprint', 'small_square_data', 'bounding_box_information', 'unique_text_metrics', 'random_pixel_data', 'triangle_canvas_fingerprint', 'computed_styles', 'computed_styles_length', 'hashed_window_keys', 'window_keys_length', 'windows_chrome_related_array', 'windows_css_related_array', 'performance_difference']

        self.n = None 
        
        self.unique_keys1 = None
        self.unique_keys2 = None
        self.parent_win_hash = None
        
        self.inv =  None
        self.exec = None
        self.pel = None 
        self.theme = None
        
        self.common_keys_hash = None 
        self.common_keys_tail = None
        
        self.siteke = sitekey

        try:
            with open("entreprises.json", "r",encoding="utf-8") as f:
                entreprises = json.loads(f.read())
        except: 
            with open("NGen/entreprises.json", "r") as f:
                entreprises = json.loads(f.read())
        
        try:
            sites : dict = entreprises[sitekey]
            
            siteskeys = list(sites.keys())
            if link in siteskeys:
                self.unique_keys1 = sites[link]["unique_keys"]
                self.unique_keys2 = sites[link]["unique_keys2"]
                self.parent_win_hash = sites[link]["parent_win_hash"]
                self.inv = sites[link]["invisible"]
                self.exec = sites[link]["exec"]
                self.theme = sites[link]["theme"]
                self.pel = sites[link]["pel"]
                
                try:
                    self.common_keys_hash = sites[link]["common_keys_hash"]
                    self.common_keys_tail = sites[link]["common_keys_tail"]
                except:
                    pass
                
            else:
                for url in sites:
                    if "*" in url:
                        if link.startswith(url.replace("*","")):
                            self.unique_keys1 = sites[url]["unique_keys"]
                            self.unique_keys2 = sites[url]["unique_keys2"]
                            self.parent_win_hash = sites[url]["parent_win_hash"]
                            self.inv = sites[url]["invisible"]
                            self.exec = sites[url]["exec"]
                            self.theme = sites[url]["theme"]
                            self.pel = sites[url]["pel"]
                            try:
                                self.common_keys_hash = sites[url]["common_keys_hash"]
                                self.common_keys_tail = sites[url]["common_keys_tail"]
                            except:
                                pass
        except:
            pass
        
        if sitekey in entreprises:
            sites = entreprises[sitekey]
            self.unique_keys1 = sites["unique_keys"]
            self.unique_keys2 = sites["unique_keys2"]
            self.parent_win_hash = sites["parent_win_hash"]
            self.inv = sites["invisible"]
            self.exec = sites["exec"]
            self.theme = sites["theme"]
            self.pel = sites["pel"]
        elif self.parent_win_hash is None:
            sites = entreprises["default"]
            self.unique_keys1 = sites["unique_keys"]
            self.unique_keys2 = sites["unique_keys2"]
            self.parent_win_hash = sites["parent_win_hash"]
            self.inv = sites["invisible"]
            self.exec = sites["exec"]
            self.theme = sites["theme"]
            self.pel = sites["pel"]
            
        if self.common_keys_hash is None or self.common_keys_tail is None:
            self.common_keys_hash = 2915477231
            self.common_keys_tail = "setTimeout,stop,structuredClone,webkitCancelAnimationFrame,webkitRequestAnimationFrame,chrome,caches,cookieStore,ondevicemotion,ondeviceorientation,ondeviceorientationabsolute,launchQueue,sharedStorage,documentPictureInPicture,getScreenDetails,queryLocalFonts,showDirectoryPicker,showOpenFilePicker,showSaveFilePicker,originAgentCluster,onpageswap,onpagereveal,credentialless,fence,speechSynthesis,onscrollend,onscrollsnapchange,onscrollsnapchanging,webkitRequestFileSystem,webkitResolveLocalFileSystemURL,Raven"
            
        if self.parent_win_hash == "random":
            th = xhash(secrets.token_bytes(333))
            self.parent_win_hash = th

        if "recaptcha_render_" in self.pel:
            self.pel = f"<div id=\"recaptcha_render_{random.randint(11927930075810000, 11927930075820000)}\"></div>"

        self.link = link

        self.events, self.components = fingerprint

        self.navigator = self.components["navigator"]

        fpChromeVersion = chrome_version(self.navigator["user_agent"])
        if fpChromeVersion in chrome_data:
            chromeData = chrome_data[fpChromeVersion]
            useragent_versions = chromeData['useragent_versions']
            sechua = chromeData['sechua']
            useragent = chromeData['useragent']

        self.useragent_versions = useragent_versions
        self.sechua = sechua
        self.useragent = useragent

        self.navigator["user_agent"] = self.useragent

        self.entropy = ["Windows",json.loads(self.get_event("user_agent_entropy_values"))[1],None,"64","x86", random.choice(self.useragent_versions)]

        self.screen = self.components["screen"]
        
        scr = {}
        
        for screen_orde in ["avail_height", "avail_width", "color_depth", "height", "pixel_depth","width"]:
            scr[screen_orde] = self.screen[screen_orde]
        
        self.screen = scr
        
        language, languages = get_languages_from_tz(timezone_id=timezone)

        self.navigator["languages"] = languages
        self.navigator["language"]  = language
        
        self.speechs:list = get_random_speech_from_language(language=language)
        
        if isinstance(self.speechs[1], list):
            self.speechs[1] = xhash(dump_data(self.speechs[1]).encode())
        
        self.tz = timezone # Format ex: "Europe/Paris"
        
        self.exp_tz = find_expensive_timezone(tz=timezone, lang=language)
        
        self.bsic = json.loads(self.get_event("performance_array_with_sevice_worker"))
        
        self.browser_info = json.loads(self.get_event("navigator_properties"))

        self.screen_data_event = json.loads(self.get_event("screen_information"))
 
        self.dpr = self.screen_data_event[8]
              
        self.v2_api = v2_api
 
        self.gcs =  float(random.randint(30,36))
        
        self.vendor_renderer = json.loads(self.get_event("gpu_information"))
        
        self.csc = random.randint(100,400) + random_perf()

        self.memory, self.cpu = self.browser_info[2],self.browser_info[3]
    
    def get_event(self, event: str):
        try:
            data = self.events[event]
            
            return data
        except Exception as e:

            if event == "worker_gpu_shits":
                print("\nWarning: Using default worker gpu shits")
                return "[14,2,11,12,1,3,16,10,8,15,13,9]"
            
            if event == "worker_gpu_depths_hashed":
                print("\nWarning: Using default worker gpu depths hashed")
                return "4860234189560885575"
            
            if event == "worker_gpu_names":
                if "worker_gpu_vendors" in self.events:
                    if "NVIDIA" in self.events["worker_gpu_vendors"]:
                        print("\nWarning: Using default worker gpu names")
                        return random.choice(["[\"nvidia\",\"pascal\",\"\",\"\"]", "[\"nvidia\",\"ampere\",\"\",\"\"]", "[\"nvidia\",\"kepler\",\"\",\"\"]"])
                    
                    if "Intel" in self.events["worker_gpu_vendors"]:
                        print("\nWarning: Using default worker gpu names")
                        return random.choice(["[\"intel\",\"gen-12lp\",\"\",\"\"]", "[\"intel\",\"gen-9\",\"\",\"\"]", "[\"intel\",\"gen-7\",\"\",\"\"]"])
                    
                    if "AMD" in self.events["worker_gpu_vendors"]:
                        print("\nWarning: Using default worker gpu names")
                        return random.choice(["[\"amd\",\"gcn-5\",\"\",\"\"]", "[\"amd\",\"gcn-4\",\"\",\"\"]"])
                    
                    raise Exception("Arch not supported: " + self.events["worker_gpu_vendors"])
                else:
                    raise Exception("Not located worker_gpu_vendors")
                     
            raise Exception("Event not found: " + event)
    
    def re_make_n(self, jwt:str, req_type:str) -> str:
        jwt_parsed = parse_jwt(jwt)
        
        self.HcaptchaEvents = HcapEvents(events=self.system.events)
                
        self.n["proof_spec"] ={
            "difficulty":jwt_parsed["s"],
            "fingerprint_type":jwt_parsed["f"],
            "_type":jwt_parsed["t"],
            "data":jwt_parsed["d"],
            "_location":jwt_parsed["l"],
            "timeout_value":float(jwt_parsed["c"]),
            "tup_": self.system.order["proof_tup"]
        }

        proofrea = []

        for orde in self.system.order["proof_order"]:
            proofrea.append(self.n["proof_spec"][orde])
        
        self.n["proof_spec"] = proofrea
        
        self.n["rand"] = [random.random()]
        self.n["stamp"] = stamp(data=jwt_parsed["d"],difficulty=jwt_parsed["s"])
        self.n["stack_data"] = [
            "Array.forEach (<anonymous>)\nArray.forEach (<anonymous>)",
            "Array.forEach (<anonymous>)",
            "TypeError: _1_2 read-only",
            "new Promise (<anonymous>)"
        ]
        if self.v2_api:
            self.n["components"]["performance_hash"] = "5480068218625584110"

        self.n["components"]["unique_keys"] = self.unique_keys2
        
        if req_type == "image_label_binary":
            self.n["components"]["inv_unique_keys"] = "hsw,image_label_binary,__wdata,_sharedLibs"
        elif req_type == "image_drag_drop":
            self.n["components"]["inv_unique_keys"] = "hsw,image_drag_drop,__wdata,_sharedLibs"
        else:
            self.n["components"]["inv_unique_keys"] = "image_label_area_select,hsw,__wdata,_sharedLibs"
        
        if self.siteke == "a9b5fb07-92ff-493f-86fe-352a2803b3df":
            if req_type == "image_label_binary":
                self.n["components"]["inv_unique_keys"] = "_sharedLibs,sessionStorage,localStorage,__wdata,image_label_binary,hsw"
            elif req_type == "image_drag_drop":
                self.n["components"]["inv_unique_keys"] ="hsw,_sharedLibs,sessionStorage,image_drag_drop,__wdata,localStorage"
            else:
                self.n["components"]["inv_unique_keys"] = "image_label_area_select,sessionStorage,hsw,__wdata,_sharedLibs,localStorage"

        self.n["perf"][0][1] += float(random.randint(-2,0))
        
        self.n["perf"][1][1] += float(random.randint(-2,0))
               
        self.rh.insert(0, ["img:imgs3.hcaptcha.com",0,random.randint(26,35) + random_perf()])
        if req_type == "image_label_area_select":
            self.rh.insert(0, ["css:imgs3.hcaptcha.com",0,random.randint(26,35) + random_perf()])
        
        if self.v2_api:
            self.rh.insert(len(self.rh)-2, ["xmlhttprequest:api.hcaptcha.com",0,random.randint(100,400) + random_perf()])
        
        avg_speed_start, avg_speed_end = get_average(request_history=self.rh)
        
        for dat in self.event_hcap:
            match dat[0]:
 
                case self.HcaptchaEvents.request_history:
                    pos = self.event_hcap.index(dat)  

                    self.event_hcap[pos] = [self.HcaptchaEvents.request_history,dump_data(self.rh)]

                case self.HcaptchaEvents.performance_now:
                    pos = self.event_hcap.index(dat)  
                    
                    mol = int(float(dat[1])) + random_perf() + random.randint(4000,7500)
                    
                    self.event_hcap[pos] = [self.HcaptchaEvents.performance_now,str(mol)]
        
                case self.HcaptchaEvents.performance_difference:
                    pos = self.event_hcap.index(dat)

                    mol = str(random.randint(25,28) +random_perf())

                    self.event_hcap[pos] = [self.HcaptchaEvents.performance_difference, mol ]
                
                case self.HcaptchaEvents.average_response_start:
                    pos = self.event_hcap.index(dat)  
                    
                    self.event_hcap[pos] = [self.HcaptchaEvents.average_response_start, str(avg_speed_start)]
                    
                case self.HcaptchaEvents.average_response_end:
                    pos = self.event_hcap.index(dat)  
                    
                    self.event_hcap[pos] = [self.HcaptchaEvents.average_response_end,str(avg_speed_end)]
                case self.HcaptchaEvents.performance_compare:
                    pos = self.event_hcap.index(dat)  

                    mol = str(random.randint(1000,4000) +random_perf())

                    self.event_hcap[pos] = [self.HcaptchaEvents.performance_compare, mol ]

        self.n["fingerprint_blob"] = self.system.encrypt_blob(dump_data(self.event_hcap))
        self.n["rand"].append(rand_hash(self.n))

        fatn = []
        for orde in self.system.order["basic_order"]:
            fatn.append(self.n[orde])

        return self.system.encrypt_n(dump_data(fatn))

    def make_n(self, jwt: str, req_type: str = None) -> str:
        if self.n is not None:
            if req_type is None:
                req_type = "image_label_area_select"
            
            new_n = self.re_make_n(jwt=jwt, req_type=req_type)
            
            return new_n
        
        jwt_parsed = parse_jwt(jwt)
                
        self.HcaptchaEvents = HcapEvents(events=self.system.events)
        
        rand = random.randint(1, 254)
        mol = json.loads(self.get_event("random_pixel_data"))
        mol[0] = [rand, [rand, rand, rand, 255, rand, rand, rand, 255, rand, rand, rand, 255, rand, rand, rand, 255]]

        self.more_font_mesurements = mol

        if self.siteke == "a9b5fb07-92ff-493f-86fe-352a2803b3df":
            inv_u_k = "_sharedLibs,sessionStorage,hsw,__wdata,localStorage"
        else:
            inv_u_k = "__wdata,hsw,_sharedLibs"
            
        if self.siteke == "a9b5fb07-92ff-493f-86fe-352a2803b3df":
            loadtimes = "[[\"loadTimes\",\"csi\",\"app\"],35,34,null,false,false,true,37,true,true,true,true,true,[\"Raven\",\"_sharedLibs\",\"__wdata\",\"hsw\"],[[\"getElementsByClassName\",[]],[\"getElementById\",[]],[\"querySelector\",[]],[\"querySelectorAll\",[]]],[],true]"
        else:
            loadtimes =  "[[\"loadTimes\",\"csi\",\"app\"],35,34,null,false,false,true,37,true,true,true,true,true,[\"Raven\",\"_sharedLibs\",\"hsw\"],[],[],true]"
            
        self.timestamp_init =  float(f"{time.time() * 1000:.1f}")
        
        self.hour = datetime.datetime.now(pytz.timezone(self.tz)).hour
        
        self.decoded_key = generate_key(
            key_input=self.system.blob_decoding_string, 
            blob_integer=self.system.blob_decoding_integer,
            timezone_offset=self.exp_tz[3],
            hour=self.hour,
            performance_metric=self.timestamp_init,
            random_seed=rand,
        )
 
        self.rh = [
            ["navigation:newassets.hcaptcha.com", random.randint(17,30) + random_perf(), random.randint(30,64) + random_perf()],
            ["script:newassets.hcaptcha.com",random.randint(10,20) + random_perf(),random.randint(20,33) + random_perf()],
            ["xmlhttprequest:api2.hcaptcha.com" if self.v2_api else "xmlhttprequest:api.hcaptcha.com",0,self.csc]
        ]
        
        avg_speed_start, avg_speed_end = get_average(request_history=self.rh)

        recur = random.randint(10376, 10380)

        recur = 10372

        self.event_hcap = [
            [
                self.HcaptchaEvents.encoded_user_agent,
                Algorithm(self.useragent, self.decoded_key)
            ],
            [
                self.HcaptchaEvents.encoded_timezone,
                Algorithm(self.tz, self.decoded_key)
            ],
            [
                self.HcaptchaEvents.encoded_gpu_information,
                Algorithm(self.vendor_renderer[1], self.decoded_key)
            ],
            [
                self.HcaptchaEvents.encoded_quota,
                Algorithm(self.bsic[0], self.decoded_key)
            ],
            [
                self.HcaptchaEvents.no_performance_caveat,
                self.get_event("no_performance_caveat")
            ],
            [
                self.HcaptchaEvents.function_tostring_length,
                "57"
            ],
            [
                self.HcaptchaEvents.hashed_gpu_extensions,
                self.get_event("hashed_gpu_extensions")
            ],
            [
                self.HcaptchaEvents.hashed_gpu_bits,
                self.get_event("hashed_gpu_bits")
            ],
            [
                self.HcaptchaEvents.gpu_information,
                dump_data(self.vendor_renderer)
            ],
            [
                self.HcaptchaEvents.worker_gpu_vendors,
                dump_data(self.vendor_renderer)
            ],
            [
                self.HcaptchaEvents.hashed_gpu_and_extensions,
                self.get_event("hashed_gpu_and_extensions")
            ],
            [
                self.HcaptchaEvents.gpu_array_expression_num_0,
                self.get_event("gpu_array_expression_num_0")
            ],
            [
                self.HcaptchaEvents.gpu_array_expression_num_1,
                self.get_event("gpu_array_expression_num_1")
            ],
            [
                self.HcaptchaEvents.gpu_array_expression_num_2,
                self.get_event("gpu_array_expression_num_2")
            ],
            [
                self.HcaptchaEvents.gpu_array_expression_num_3,
                self.get_event("gpu_array_expression_num_3")
            ],
            [
                self.HcaptchaEvents.gpu_array_expression_num_4,
                self.get_event("gpu_array_expression_num_4")
            ],
            [
                self.HcaptchaEvents.gpu_array_expression_num_5,
                self.get_event("gpu_array_expression_num_5")
            ],
            [
                self.HcaptchaEvents.gpu_array_expression_num_6,
                self.get_event("gpu_array_expression_num_6")
            ],
            [
                self.HcaptchaEvents.gpu_array_expression_num_7,
                self.get_event("gpu_array_expression_num_7")
            ],
            [
                self.HcaptchaEvents.gpu_array_expression_num_8,
                self.get_event("gpu_array_expression_num_8")
            ],
            [
                self.HcaptchaEvents.supported_matches,
                "[1,4,5,7,9,12,20,21,24,25,29,31]"
            ],
            [
                self.HcaptchaEvents.windows_css_related_array,
                "9345374751420407194"
            ],
            [
                self.HcaptchaEvents.font_indexes,
                "[0,2,3,4,8,17,18,20]"
            ],
            [
                self.HcaptchaEvents.performance_now,               #performance.now
                str(random.randint(2400,4100) + random_perf())
            ],
            [
                self.HcaptchaEvents.performance_difference,        # navigation:newassets.hcaptcha.com  how much time it took to exec all events      
                str(random.randint(25,28) +random_perf())
            ],
            [
                self.HcaptchaEvents.average_response_start,        # navigation:newassets.hcaptcha.com first       
                str(avg_speed_start)
            ],
            [
                self.HcaptchaEvents.average_response_end,          # navigation:newassets.hcaptcha.com second
                str(avg_speed_end)
            ],
            [
                self.HcaptchaEvents.request_history,
                dump_data(self.rh),
            ],
            [
                self.HcaptchaEvents.screen_information,
                self.get_event("screen_information")
            ],
            [
                self.HcaptchaEvents.small_square_data,
                "4932383211497360507"
            ],
            [
                self.HcaptchaEvents.small_canvas,
                self.get_event("small_canvas")
            ],
            [
                self.HcaptchaEvents.triangle_canvas_fingerprint,
                self.get_event("triangle_canvas_fingerprint")  
            ],
            [
                self.HcaptchaEvents.emoji_canvas_fingerprint,
                self.get_event("emoji_canvas_fingerprint")
            ],
            [
                self.HcaptchaEvents.bounding_box_information,
                self.get_event("bounding_box_information") 
            ],
            [
                self.HcaptchaEvents.proxy_check,
                "4631229088072584217"
            ],
            [
                self.HcaptchaEvents.performance_mark,
                "[[277114314453,277114314460,277114314451,357114314456,277114314452,554228628898,57114314443,717114314371391,554228628897,277114314456,1108457257862,277114314450,554228628919,277114314460,277114314451],false]"
            ],                
            [
                self.HcaptchaEvents.hashed_html_structure,
                "10810014756690535659"
            ],
            [
                self.HcaptchaEvents.hashed_window_keys,
                "7639267751943678301"
            ],
            [
                self.HcaptchaEvents.window_keys_length,
                "1181"
            ],
            [
                self.HcaptchaEvents.computed_styles,
                "14712683473729405703"
            ],
            [
                self.HcaptchaEvents.computed_styles_length,
                "657"
            ],
            [
                self.HcaptchaEvents.styles_and_js_array,
                "[[[\"\",421849,1]],[[\"*\",84,9]]]"
            ],    
            [
                self.HcaptchaEvents.windows_chrome_related_array,
                loadtimes
            ],
            [
                self.HcaptchaEvents.hashed_speech_synthesis,
                self.speechs[1]
            ],
            [
                self.HcaptchaEvents.sliced_three_speech_synthesis,
                dump_data(self.speechs[0])
            ],
            [
                self.HcaptchaEvents.timezone_array,
                dump_data(self.exp_tz)
            ],
            [
                self.HcaptchaEvents.timezone,
                dump_data(str(self.tz))
            ],
            [
                self.HcaptchaEvents.timezone_hours_array,
                dump_data([self.hour])
            ],
            [
                self.HcaptchaEvents.time_origin,
                dump_data(self.timestamp_init)
            ],
            [
                self.HcaptchaEvents.worker_gpu_shits,
                self.get_event("worker_gpu_shits")
            ],
            [
                self.HcaptchaEvents.client_reacts,
                "[-6.172840118408203,-20.710678100585938,120.71067810058594,-20.710678100585938,141.42135620117188,120.71067810058594,-20.710678100585938,141.42135620117188,-20.710678100585938,-20.710678100585938,0,0,300,150,false]"
            ],
            [
                self.HcaptchaEvents.random_pixel_data,
                dump_data(self.more_font_mesurements)
            ],
            [
                self.HcaptchaEvents.math_fingerprint_and_errors,
                "756874611071873095"
            ],
            [
                self.HcaptchaEvents.supported_media_types,
                self.get_event("supported_media_types")
            ],
            [
                self.HcaptchaEvents.performance_array_with_sevice_worker,
                dump_data(self.bsic)
            ],
            [
                self.HcaptchaEvents.user_agent_entropy_values,
                    dump_data(self.entropy)
            ],
            [
                self.HcaptchaEvents.navigator_properties,
                json.dumps([self.useragent.replace('Mozilla/', ''), self.useragent,self.browser_info[2],self.browser_info[3],self.navigator["language"],self.navigator["languages"],"Win32",None,self.sechua,False,"Windows",2,5,True,False,self.browser_info[15],False,False,True,"[object Keyboard]",False,False], separators=(",", ":"), ensure_ascii=False)
            ],
            [
                self.HcaptchaEvents.worker_gpu_names,
                self.get_event("worker_gpu_names")
            ],
            [
                self.HcaptchaEvents.worker_gpu_depths_hashed,
                self.get_event("worker_gpu_depths_hashed")
            ],
            [
                self.HcaptchaEvents.worker_hc_memory_array,
                self.get_event("worker_hc_memory_array")
            ],
            [
                self.HcaptchaEvents.worker_language_timezone,
                dump_data([self.navigator["language"], self.navigator["languages"],self.exp_tz[5], self.tz])
            ],
            [
                self.HcaptchaEvents.user_agent,
                dump_data(self.useragent)
            ],
            [
                self.HcaptchaEvents.worker_user_agent,
                dump_data(self.useragent)
            ],
            [
                self.HcaptchaEvents.post_message_user_agent_values,
                dump_data([self.memory, self.cpu, self.sechua, self.entropy])
            ],
            [
                self.HcaptchaEvents.web_rtc,
                self.get_event("web_rtc")
            ],
            [
                self.HcaptchaEvents.audio_triangle_fingerprint,
                self.get_event("audio_triangle_fingerprint")
            ],
            [
                self.HcaptchaEvents.unique_text_metrics,
                self.get_event("unique_text_metrics")
            ],
            [
                self.HcaptchaEvents.performance_compare,
                str(random_perf() + random.randint(1700,2400))
            ],
            
            [
                self.HcaptchaEvents.recursion_array,
                f"[0,{recur},{recur}]"
            ],
            [
                self.HcaptchaEvents.worker_recursion_array,
                "[48.02116402116402,5294,4538]"
            ]
        ]

        tempshit = self.system.events
        try:
            orderstemp = [tempshit[i] for i in self.events_order]
        except:
            orderstemp = [tempshit[i] for i in self.events_order_other]
        
        random.shuffle(self.event_hcap)

        data_ids = {item[0] for item in self.event_hcap}

        missing_ids = [id for id in orderstemp if id not in data_ids]

        self.event_hcap = [next(item for item in self.event_hcap if item[0] == id) for id in orderstemp if id in data_ids]

        if missing_ids:
            print(f"Missing IDs: {missing_ids}")

        self.n = {
            "proof_spec": {
                "difficulty":jwt_parsed["s"],
                "fingerprint_type":jwt_parsed["f"],
                "_type":jwt_parsed["t"],
                "data":jwt_parsed["d"],
                "_location":jwt_parsed["l"],
                "timeout_value":float(jwt_parsed["c"]),
                "tup_": self.system.order["proof_tup"]
            },
            "rand": [
                random.random()
            ],
            "components": {
                "audio_hash": "0",
                "canvas_hash": self.components["canvas_hash"],
                "chrome": True,
                "common_keys_hash": self.common_keys_hash,
                "common_keys_tail":  self.common_keys_tail,
                "device_pixel_ratio": float(self.dpr),
                "err_firefox": None,
                "extensions": [
                    False
                ],
                "features": {
                    "performance_entries": True,
                    "web_audio": True,
                    "web_rtc":True,
                    "canvas_2d": True,
                    "fetch": True
                },
                "has_indexed_db": self.components["has_indexed_db"],
                "has_local_storage": self.components["has_local_storage"],
                "has_session_storage": self.components["has_session_storage"],
                "has_touch": self.components["has_touch"],
                "inv_unique_keys":  inv_u_k,
                "navigator": {
                    "language": self.navigator["language"],
                    "languages": self.navigator["languages"],
                    "max_touch_points": self.navigator["max_touch_points"],
                    "notification_query_permission": None,
                    "platform": "Win32",
                    "plugins_undefined": False,
                    "user_agent": self.navigator["user_agent"],
                    "webdriver": False,
                },
                "notification_api_permission": "Denied",
                "parent_win_hash":  self.parent_win_hash,
                "performance_hash":   "11097854906383886648" if self.v2_api else "4140103483592612201",
                "pi": None,
                "r_bot_score": 0,
                "r_bot_score_2": 0,
                "r_bot_score_suspicious_keys": [],
                "screen": self.screen,
                "to_string_length": 33,
                "unique_keys": self.unique_keys1,
                "web_gl_hash": "0",
                "webrtc_hash": "0",
            },
            "fingerprint_blob": self.system.encrypt_blob(dump_data(self.event_hcap)),
            "messages": None,
            "stack_data": [
                "Array.forEach (<anonymous>)\nArray.forEach (<anonymous>)",
                "Array.forEach (<anonymous>)",
                "TypeError: _1_2 read-only"
            ],
            "stamp": stamp(data=jwt_parsed["d"],difficulty=jwt_parsed["s"]),
            "href": self.link,
            "ardata": None,
            "errs": {
                "list": []
            },
            "perf": [
                [
                    1,
                    float(random.randint(13,16))
                ],
                [
                    2,
                    self.gcs
                ],
               [
                   3,
                   0.0
               ]
            ],
            "tup_" : self.system.order["basic_tup"]
        }

        self.n["rand"].append(rand_hash(self.n))
            
        proofrea = []

        for orde in self.system.order["proof_order"]:
            proofrea.append(self.n["proof_spec"][orde])
        
        self.n["proof_spec"] = proofrea
            
        fatn = []
        for orde in self.system.order["basic_order"]:
            fatn.append(self.n[orde])
        
        def test_file_output():
            shit = {}
            
            for order in self.system.order["basic_order"]:
                if order == "fingerprint_blob":
                    shit[order] = self.event_hcap
                else:
                    shit[order] = self.n[order]
                    
            json.dump(shit, open("n_1_.json", "w", encoding="utf-8"), ensure_ascii=False, indent=4)
        
        return self.system.encrypt_n(dump_data(fatn))

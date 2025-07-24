import random
import json
import ast
import os
import re

def get_end_substring(body: str, begin: str, end: str) -> str:
    start_index = body.rfind(begin)
    if start_index == -1:
        return "-1"
    
    start_index += len(begin)
    
    end_index = body.find(end, start_index)
    
    if end_index == -1:
        return "-1"
    
    return body[start_index:end_index]

def get_substring(body: str, begin: str, end: str) -> str:
    start_index = body.find(begin)
    if start_index == -1:
        return "-1"
    
    start_index += len(begin)
    end_index = body.find(end, start_index)
    
    if end_index == -1:
        return "-1"
    
    return body[start_index:end_index]

def parse_proxy(proxy_string):
    try:
        host, port, username, password = proxy_string.split(':')
        return host, port, username, password
    except:
        return "", "", "", ""

def getProxy():
    proxies = None

    if not os.path.exists("misc/proxies.txt"):
        print("Error: 'misc/proxies.txt' not found.")
        return
    with open("misc/proxies.txt", "r") as file:
        proxies = [line.strip() for line in file if line.strip()]

    proxy = None
    if proxies:
        proxy = random.choice(proxies) if proxies else None
        host, port, username, password = parse_proxy(proxy)
        proxy=f"http://{username}:{password}@{host}:{port}"
    
    return proxy

def parse_response_json(input_string):

    # {
    #     "key":"E0_eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJkYXRhIjoiVytKQ1NsTUJXYlFyYkdMSnVKQU5ZblA0VHNBUEJyVklsTTlidFZZdDBsa3l6WDR2YUZONFM2bVg1T0N0Uk9veXlXMzdrUGZES0NUMUQ4OUxmSzh6MjhqcERBaTU3Qm5NWmZVeXVhcHlMV0UyVkNxQUFqRFRtazlVd0VuVFpjSWZHVm9WYzJ2VEtid1pCV1pURkVwRGhQeThFZi9kcHFYQ2RvcXdSTGc0aWtnK3dvMUEwbzd4bjBLd2F1NWxVY1dyNUtyL1haNWRUemp5UFdKVGIxcXFwbjBuMDQ1aXloYkdPWmZjT09Xdm1ra2Zjb1Z3ZjA3ZXhkaWtUWmhhVXlWMkQ3QVZlTzM5SVBJPUkyYVhwK2VmbXRwUVM0MHciLCJleHAiOjE3NDU3NzY5NjAsImtyIjoiNWQ4NjdmNSJ9.qP-NyyDFqgGzrFTsAeUzMSbQeRGmN90VHOdXEZndYIg",
    #     "request_config":{
    #         "version":0,
    #         "shape_type":"None",
    #         "min_points":"None",
    #         "max_points":"None",
    #         "min_shapes_per_image":"None",
    #         "max_shapes_per_image":"None",
    #         "restrict_to_coords":"None",
    #         "minimum_selection_area_per_shape":"None",
    #         "multiple_choice_max_choices":1,
    #         "multiple_choice_min_choices":1,
    #         "overlap_threshold":"None",
    #         "answer_type":"str",
    #         "max_value":"None",
    #         "min_value":"None",
    #         "max_length":"None",
    #         "min_length":"None",
    #         "sig_figs":"None",
    #         "keep_answers_order":"None",
    #         "ignore_case":false,
    #         "new_translation":true
    #     },
    #     "request_type":"image_label_binary",
    #     "requester_question":{
    #         "en":"Select images with animals doing the same thing as in the example"
    #     },
    #     "requester_question_example":"https://imgs3.hcaptcha.com/tip/460f4be3f46e03d3403aaabd5da0ca693d0ee2ffb53e007e7e05ac9f7320c5b4/e8c01600d9abf874c98cf62f2d53c39ecd5ca4920ace722be3f56eea8ef87012.jpeg",
    #     "tasklist":[
    #         {
    #             "datapoint_uri":"https://imgs3.hcaptcha.com/tip/5f7401850b3a0785a136ca0985c42a791f836f4b635ee2695b3e2d94059a6e02/3ed2c7a6c5d78629b78a8602a3ca36ec5b22513c51372c0c28d50d2c939f806b.jpeg",
    #             "task_key":"6899a669-d699-42b3-82bd-ff79f3a61746",
    #             "entities":[
                    
    #             ]
    #         },
    #         {
    #             "datapoint_uri":"https://imgs3.hcaptcha.com/tip/4c9c01ddf0e9edb024b3a81b9f11be2b7e03372bb469557a22783c4b7065a37d/ed66000c5b98a76645c885539a5e19ab784d96bb502e700811148890165d5807.jpeg",
    #             "task_key":"5eb8470c-cb2e-4a23-a091-c0fac49e9d84",
    #             "entities":[
                    
    #             ]
    #         },
    #         {
    #             "datapoint_uri":"https://imgs3.hcaptcha.com/tip/4bbf906c7adb80e85e56cbf96c0daa89f358ac486af5e7f21728ef2b5eb04c77/97c89f348eaaddeb45de9b692ab8a1ce4ac21ba80cbdcd5cd865946c06156960.jpeg",
    #             "task_key":"f1af1819-c2ae-427d-9941-c53c58d12796",
    #             "entities":[
                    
    #             ]
    #         },
    #         {
    #             "datapoint_uri":"https://imgs3.hcaptcha.com/tip/95e8ec755d08a607ac9076ff09a71956f8042a747c466f267ba6e7dd3da7fe1b/04b9eb0513b5bb7d22b28e580921eae5c47eeb1345f43dceb077023dda42e3fc.jpeg",
    #             "task_key":"55d0efdb-0db5-40d9-b77f-1adc543b56bf",
    #             "entities":[
                    
    #             ]
    #         },
    #         {
    #             "datapoint_uri":"https://imgs3.hcaptcha.com/tip/b054b7b187dd4a88bbd89cbac6f12d0f474ac1e990151f0d7bc4d84a189c91dd/206e199d397d244488e4c5a8cad4cddfa758f1eca77e3ae492991498d000097a.jpeg",
    #             "task_key":"acffcf8c-4421-4e2b-ae03-73efd4350811",
    #             "entities":[
                    
    #             ]
    #         },
    #         {
    #             "datapoint_uri":"https://imgs3.hcaptcha.com/tip/ff0e89e93ae7ad2a15625a2ef7c0f92b244d95f81267718f85670f4aeb3bb36d/c4ba38b907545354206c2cb324a8d0422fc60d1b4946e6390e7ed2c6393ec798.jpeg",
    #             "task_key":"0bb6fba9-52f8-415a-8d8c-daee7d9647e3",
    #             "entities":[
                    
    #             ]
    #         },
    #         {
    #             "datapoint_uri":"https://imgs3.hcaptcha.com/tip/285e3ac860dbce454140e06c345794ce02c5a2947e8c45134940dd9e596ab2bd/8d6f859b5ad67d18b8b0a96bf0707ac4e14330766be4083eca08c6f0cc1f562d.jpeg",
    #             "task_key":"2aad199b-fb02-4fdb-bf75-6d92cc4cec30",
    #             "entities":[
                    
    #             ]
    #         },
    #         {
    #             "datapoint_uri":"https://imgs3.hcaptcha.com/tip/7219f02b8f59ab9b4cb9101b03564ba2889f2e37fb83767c9dae0aa5444d273c/2a59d78e1c7a3137c804623d376dc63074726a17e3cc253ec56863bbae490eea.jpeg",
    #             "task_key":"01339ffe-7691-47e4-b188-8f16025d27d1",
    #             "entities":[
                    
    #             ]
    #         },
    #         {
    #             "datapoint_uri":"https://imgs3.hcaptcha.com/tip/00b7399851bbbf527ce941d47de8a00980ea7e159c5b4ef28b6a7d13ac952f57/79bd110c24d9d5d2300b553d8f4e430e383dddf2289e786ae7ac081b11464125.jpeg",
    #             "task_key":"24b5d27d-44f8-4dc4-b77b-c3a3b52b71a4",
    #             "entities":[
                    
    #             ]
    #         }
    #     ],
    #     "oby":"v2:fWebJUtQDEjDDt8Bk2YtiWQzOTU5MTgyuZxU+/WWqOFdc9R0ircAvYpr7BIhc7eewyoSz9e/aILhsBmtavGx6ZZZFKDv3DYaOp7PQi2UakpkbXhYYhDTvhcD3DSawlvTa5LWiGql71IGqo5ZT29mhoQ9chXtp7BU1wRfuLKFxKWdgrAUs7WVZcIlmhuWc2oOr7+dE2vMalc=",
    #     "normalized":true,
    #     "c":{
    #         "type":"hsw",
    #         "req":"eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJmIjowLCJzIjoyLCJ0IjoidyIsImQiOiJiSU1FT0Rva0tIYTZxYk4yZXhTL3BvemtaZEpORzB3cStRSkZ4OUZqK3pjSDFjSnVqUEZzNkhJbWNMWGtHc2tqVmpQckwrY05tQjN2N2ZPNnk1TzdmV2RtMFlZd1BHUTN0K1ZtM2hwS1pMdEx4Y1pKQ3JHUkhtUlprM2sybGNLb2F4YnhvYjhicHRaUVFZTWJaQnJrcUUvTzVVQUZZa0xDZk5wZXV1U1lhUUJBVE5WZk1NcTU0YVlmRTMwS2RGQTAwM1JBejllR0IycysyWUlPcitadTg4LzEyS1YraURsMmxiU0FCZm1MVnVpRE02dldncmRyeTkzeUp3ci94SUU9RndWQXBkZnl2b1ZWRU1RaCIsImwiOiIvYy8zNDI3MTFmZjM0YzMzOGQzMjNhYjk4NmNlOGI4MjM1NGZkMThhOWNhMTE4ZWY1OTE2ZWVhYjQzZmJkYjFhYjM2IiwiaSI6InNoYTI1Ni1yWHY3ZWRidlpxbnlFVDBmNVQwdTBIYjJNaGxlSDJrTE1EdU9qUkh1WkgwPSIsImUiOjE3NDU3Nzg2NzEsIm4iOiJoc3ciLCJjIjoxMDAwfQ.Agl8437lctB8qcUKiC8hiooGPWjCm_a0t7uHSmwk2Gg"
    #     }
    # }

    data = json.loads(input_string)
    
    # Extract the specific fields
    key = data.get('key', '')
    request_type = data.get('request_type', '')
    en = data.get('requester_question', {}).get('en', '')
    requester_question_example = data.get('requester_question_example', '')
    
    # Extract the array of images with datapoint_uri and task_key
    images_info = [{'datapoint_uri': task['datapoint_uri'], 'task_key': task['task_key']}
                   for task in data.get('tasklist', [])]
    
    # Extract 'oby' and 'req' from the dictionary
    oby = data.get('oby', '')
    req = data.get('c', {}).get('req', '')

    return {
        'key': key,
        'request_type': request_type,
        'en': en,
        'requester_question_example': requester_question_example,
        'images_info': images_info,
        'oby': oby,
        'req': req
    }

def extract_and_convert_int_array(s):
    pattern = r'\[\s*\d+\s*(?:,\s*\d+\s*)*\]'

    match = re.search(pattern, s)
    if match:
        array_str = match.group()
        try:
            result = ast.literal_eval(array_str)
            return result
        except SyntaxError as e:
            print(f"Error converting string to list: {e}")
            return None
    return None

def formatGptSolution(respString, imageClassifications):
    indiceArray = extract_and_convert_int_array(respString)

    if not indiceArray:
        return None

    finalSolution = []

    for i, (key, _) in enumerate(imageClassifications):
        if i in indiceArray:
            solutionElement = (key, True)
            finalSolution.append(solutionElement)
        else:
            solutionElement = (key, False)
            finalSolution.append(solutionElement)

    return finalSolution

def trim_prefix(string, prefix):
    if string.startswith(prefix):
        return string[len(prefix):]
    return string

def drop_first_chars(s: str, x: int) -> str:
    if x < 0:
        raise ValueError("x must be non-negative")
    return s[x:] if x <= len(s) else ""

def safe_str_to_int(s: str) -> int | None:
    try:
        return int(s)
    except ValueError:
        return None

def parseBlobDecoders(hsw):
    subStr = get_end_substring(hsw, "=~~(", ")")
    blobInt = drop_first_chars(subStr, 3)
    blobInt = safe_str_to_int(blobInt)

    if blobInt is None:
        blobInt = 0

    return blobInt

def print_green(text):
    print(f"\033[92m{text}\033[0m")

def print_red(text):
    print(f"\033[91m{text}\033[0m")

def print_blue(text):
    print(f"\033[94m{text}\033[0m")

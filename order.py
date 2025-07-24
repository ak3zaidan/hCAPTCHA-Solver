import json

order = []
porder = []
tup_proof  = ""
tup_basic = ""

def spec_order(array):
    global order, porder, tup_basic, tup_proof
    
    for data in array:
        if isinstance(data, str) and len(data) == 67: 
            porder.append("_location")
        elif isinstance(data, str)  and len(data) > 190:
            porder.append("data")
        elif isinstance(data, str) and "tup_" in data:
            porder.append("tup_")
            tup_proof = data
        elif isinstance(data, int) and data == 2 or data == 16:
            porder.append("difficulty")
        elif isinstance(data, float):
            porder.append("timeout_value")
        elif isinstance(data,int) and data == 0:
            porder.append("fingerprint_type")
        elif isinstance(data,str) and data == "w":
            porder.append("_type")

def map_order(data: list):
    global order, porder, tup_basic, tup_proof

    for item in data:
        if item is None:
            order.append("ardata")
        elif item == "messages":
            order.append("messages")
        elif isinstance(item, str) and "1:2:202" in item:
            order.append("stamp")
        elif isinstance(item, str) and (len(item) > 1000 or item == "<blob>"):
            order.append("fingerprint_blob")
        elif isinstance(item, list) and len(item) == 3 and isinstance(item[0], list) and isinstance(item[1], list) and item[0][0] == 1 and item[1][0] == 2:
            order.append("perf")
        elif isinstance(item, dict) and "list" in item:
            order.append("errs")
        elif isinstance(item, list) and len(item) == 2 and isinstance(item[0], float):
            order.append("rand")
        elif isinstance(item, str) and "http" in item:
            order.append("href")
        elif isinstance(item, str) and "tup_" in item:
            order.append("tup_")
            tup_basic = item
        elif isinstance(item, list) and len(item) == 7:
            order.append("proof_spec")
            spec_order(item)
        elif isinstance(item, dict) and item.get("audio_hash") == "0":
            order.append("components")
        elif isinstance(item, list):
            for s in item:
                if isinstance(s, str) and "read-only" in s:
                    order.append("stack_data")
                    break

def get_order(N_RAW):
    global order, porder, tup_basic, tup_proof

    data = json.loads(N_RAW)
    map_order(data)

    if len(order) != len(data):
        raise Exception(f'Mismatch order: {len(order)}, {len(data)}')

    dataf = {
        "basic_order": order,
        "proof_order": porder,
        "proof_tup": tup_proof,
        "basic_tup": tup_basic
    }

    return dataf

# N_RAW = """["https://accounts.hcaptcha.com/demo",{"audio_hash":"0","canvas_hash":"12474863279772557427","chrome":true,"common_keys_hash":1028655694,"common_keys_tail":"setTimeout,stop,structuredClone,webkitCancelAnimationFrame,webkitRequestAnimationFrame,chrome,caches,cookieStore,ondevicemotion,ondeviceorientation,ondeviceorientationabsolute,launchQueue,sharedStorage,documentPictureInPicture,fetchLater,getScreenDetails,queryLocalFonts,showDirectoryPicker,showOpenFilePicker,showSaveFilePicker,originAgentCluster,onpageswap,onpagereveal,credentialless,fence,speechSynthesis,oncommand,onscrollend,onscrollsnapchange,onscrollsnapchanging,webkitRequestFileSystem,webkitResolveLocalFileSystemURL,Raven","device_pixel_ratio":1.0,"err_firefox":null,"extensions":[false],"features":{"canvas_2d":true,"fetch":true,"performance_entries":true,"web_audio":true,"web_rtc":true},"has_indexed_db":true,"has_local_storage":true,"has_session_storage":true,"has_touch":false,"inv_unique_keys":"_sharedLibs,hsw,__wdata","navigator":{"language":"en-US","languages":["en-US","en"],"max_touch_points":0,"notification_query_permission":null,"platform":"Win32","plugins_undefined":false,"user_agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36","webdriver":false},"notification_api_permission":"Denied","parent_win_hash":"8517649968055551809","performance_hash":"4140103483592612201","pi":null,"r_bot_score":0,"r_bot_score_2":0,"r_bot_score_suspicious_keys":[],"screen":{"avail_height":879,"avail_width":1470,"color_depth":24,"height":919,"pixel_depth":24,"width":1470},"to_string_length":33,"unique_keys":"hcaptcha,0,onExpire,grecaptcha,1,onSuccess","web_gl_hash":"0","webrtc_hash":"0"},"messages",[2,1000.0,"/c/f398bf333fbfbd4fe999402c51bb7c4a3f2036bd376313fc2666be84553a6949","w","53fVg5Z3BtPDuLSy4bbIU5F9UeQqJV6z7Bs/ilW/WswzAN5vX7oMaP9Jo7OF6iuigXtNxttVjZR6ir/Vu1QoRtom8xeAkdeR+L0d6AUNLv/OcTreRNhyirzu69IRH4sbpwGVgRbWZDAFlzhmIazcGaMmhpNgM59Ukrx7hB7U1Tt2ltkyVvj6/SH7eScuYU8Vd77zoViUIDQIcCWaKXsYAsRPV3unIANirTQuMq/ESjI16lr7o1YXtdS4ydOZjnA=jhbFE6mxO8gRUDmw",0,"tup_8d5c3dfb77bf9d62a031f80eb68dd1d90d00b26d1c858f173206fbe95848e3821d02b564115666fe20c71ff5003476a68915980f33b60e100a475b86851da21988cd08b2b86495b531193c938ecfb58e4f2de3fcbd9aad33c10b"],null,"1:2:2025-05-28:53fVg5Z3BtPDuLSy4bbIU5F9UeQqJV6z7Bs/ilW/WswzAN5vX7oMaP9Jo7OF6iuigXtNxttVjZR6ir/Vu1QoRtom8xeAkdeR+L0d6AUNLv/OcTreRNhyirzu69IRH4sbpwGVgRbWZDAFlzhmIazcGaMmhpNgM59Ukrx7hB7U1Tt2ltkyVvj6/SH7eScuYU8Vd77zoViUIDQIcCWaKXsYAsRPV3unIANirTQuMq/ESjI16lr7o1YXtdS4ydOZjnA=jhbFE6mxO8gRUDmw::aSmVa7QA:16",["TypeError: _0_1 read-only"],"<blob>",[[1,38.0],[2,102.0],[3,0.0]],[0.5577997424917944,0.7072537411004305],{"list":[]},"tup_f270d61521f47f711e5a5c73168c0efda1ed944b31ddfbda337b6798c2392f5104c60bb05afed99584caf403d6037e26add08e0a38f46a18ebaeabcc4cd0fee81e867be4b4267e8e82705b6f6cd47565158c2ecb0d26565c756ad207b1b5bc65bcb5f391eb8ffac8a611ec4290f9fb41eee88c33237a49"]"""

# get_order()

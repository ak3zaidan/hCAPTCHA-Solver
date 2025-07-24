from NGen.generator import N as NGen
from Motion import Motion
import Decrypt
import json
import time

class Request_Payload:
    def __init__(self, system: Decrypt.EncryptionSystem, fingerprint, jwt_token, version, tokenData, v1Path, siteKey, timezone, referer, last_response=None, old_ekey=None):
        self.system = system
        self.fingerprint = fingerprint
        self.jwt_token = jwt_token
        self.version = version
        self.tokenData = tokenData
        self.v1Path = v1Path
        self.siteKey = siteKey
        self.referer = referer
        self.last_response = last_response
        self.old_ekey = old_ekey

        self.class_N = NGen(
            timezone=timezone, 
            link=referer, 
            sitekey=siteKey, 
            v2_api=False, 
            fingerprint=convert_fingerprint(fingerprint),
            system=system
        )

    def gen_request_payload(self):
        if self.old_ekey:
            plaintext = {
                'v': self.v1Path,
                'sitekey': self.siteKey,
                'host': 'accounts.hcaptcha.com',
                'hl': 'en',
                "action": "challenge-skip",
                "extraData": json.dumps(self.last_response),
                'motionData': self.gen_request_motion(),
                'pdc': json.dumps({"s": int(time.time() * 1000), "n": 0, "p": 0, "gcs": int(self.class_N.gcs) + 2}, separators=(",", ":")),
                'pem': json.dumps({"csc": self.class_N.csc, "csch": "api.hcaptcha.com", "cscrt": 0, "cscrt": self.class_N.csc}, separators=(",", ":")),
                "old_ekey": self.old_ekey,
                'n': self.gen_n_payload(),
                'pst': False
            }
        else:
            plaintext = {
                'v': self.v1Path,
                'sitekey': self.siteKey,
                'host': 'accounts.hcaptcha.com',
                'hl': 'en',
                'motionData': self.gen_request_motion(),
                'pdc': json.dumps({"s": int(time.time() * 1000), "n": 0, "p": 0, "gcs": int(self.class_N.gcs) + 2}, separators=(",", ":")),
                'pem': json.dumps({"csc": self.class_N.csc, "csch": "api.hcaptcha.com", "cscrt": 0, "cscrt": self.class_N.csc}, separators=(",", ":")),
                'n': self.gen_n_payload(),
                'pst': False
            }

        plaintextString = json.dumps(plaintext)

        config = {'type': 'hsw', 'req': self.jwt_token}

        return self.system.encrypt_request_payload(plaintextString, config)

    def gen_request_motion(self):
        size = "normal"

        motion = Motion(self.fingerprint, self.referer, self.class_N.pel, size)

        motion_data = motion.get_captcha()

        return json.dumps(motion_data)

    def gen_n_payload(self):
        ndata = self.class_N.make_n(
            jwt=self.jwt_token, 
            req_type=None
        )

        return ndata

def convert_fingerprint(fingerprint):
    return [fingerprint["events"], fingerprint["components"]]

# Usable format

# [
#    {
#       "performance_now":"505.89999997615814",
#       "function_tostring_length":"57",
#       "user_agent":"\"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36\"",
#       "post_message_user_agent_values":"[8,12,[\"Google Chrome 131\",\"Chromium 131\",\"Not_A Brand 24\"],[\"Windows\",\"15.0.0\",null,\"64\",\"x86\",\"131.0.6778.140\"]]",
#       "worker_user_agent":"\"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36\"",
#       "worker_language_timezone":"[\"de-DE\",[\"de-DE\",\"de\",\"en-US\",\"en\"],\"de\",\"Europe/Zurich\"]",
#       "worker_hc_memory_array":"[8,12]",
#       "worker_gpu_vendors":"[\"Google Inc. (Intel)\",\"ANGLE (Intel, Intel(R) Iris(R) Xe Graphics (0x000046A8) Direct3D11 vs_5_0 ps_5_0, D3D11)\"]",
#       "worker_gpu_depths_hashed":"5511659897071332320",
#       "worker_gpu_names":"[\"intel\",\"gen-12lp\",\"\",\"\"]",
#       "worker_gpu_shits":"[2,11,12,1,3,16,10,8,15,13,9]",
#       "performance_difference":"747.8999999761581"
#    },
#    {
#       "navigator":{
#          "user_agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
#          "language":"de-DE",
#          "languages":[
#             "de-DE",
#             "de",
#             "en-US",
#             "en"
#          ],
#          "platform":"Win32",
#          "max_touch_points":0,
#          "webdriver":false,
#          "notification_query_permission":"None",
#          "plugins_undefined":false
#       },
#       "screen":{
#          "color_depth":24,
#          "pixel_depth":24,
#          "width":1536,
#          "height":864,
#          "avail_width":1536,
#          "avail_height":816
#       },
#       "device_pixel_ratio":1.25,
#       "has_session_storage":true,
#       "has_local_storage":true,
#       "has_indexed_db":true,
#       "web_gl_hash":"-1",
#       "canvas_hash":"17725215832999159817",
#       "has_touch":false,
#       "notification_api_permission":"Denied",
#       "chrome":true,
#       "to_string_length":33,
#       "err_firefox":"None",
#       "r_bot_score":0,
#       "r_bot_score_suspicious_keys":[
         
#       ],
#       "r_bot_score_2":0,
#       "audio_hash":"-1",
#       "extensions":[
#          false
#       ],
#       "parent_win_hash":"4883931453396206889",
#       "webrtc_hash":"-1",
#       "performance_hash":"5667013066222601909",
#       "unique_keys":"onExpire,0,grecaptcha,onSuccess,1,Raven,hcaptcha",
#       "inv_unique_keys":"__wdata,hsw",
#       "common_keys_hash":3990815276,
#       "common_keys_tail":"setTimeout,stop,structuredClone,webkitCancelAnimationFrame,webkitRequestAnimationFrame,chrome,caches,cookieStore,ondevicemotion,ondeviceorientation,ondeviceorientationabsolute,launchQueue,sharedStorage,documentPictureInPicture,getScreenDetails,queryLocalFonts,showDirectoryPicker,showOpenFilePicker,showSaveFilePicker,originAgentCluster,onpageswap,onpagereveal,credentialless,fence,speechSynthesis,onscrollend,onscrollsnapchange,onscrollsnapchanging,webkitRequestFileSystem,webkitResolveLocalFileSystemURL",
#       "features":{
#          "performance_entries":true,
#          "web_audio":true,
#          "web_rtc":true,
#          "canvas_2d":true,
#          "fetch":true
#       }
#    }
# ]

# Collector format

# {
#    "components":{
#       "navigator":{
#          "user_agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36",
#          "language":"en-US",
#          "languages":[
#             "en-US",
#             "en"
#          ],
#          "platform":"Win32",
#          "max_touch_points":0,
#          "webdriver":false,
#          "notification_query_permission":null,
#          "plugins_undefined":false
#       },
#       "screen":{
#          "color_depth":24,
#          "pixel_depth":24,
#          "width":1920,
#          "height":1080,
#          "avail_width":1920,
#          "avail_height":1040
#       },
#       "device_pixel_ratio":1.0,
#       "has_session_storage":true,
#       "has_local_storage":true,
#       "has_indexed_db":true,
#       "web_gl_hash":"-1",
#       "canvas_hash":"7021875685296378361",
#       "has_touch":false,
#       "notification_api_permission":"Denied",
#       "chrome":true,
#       "to_string_length":33,
#       "err_firefox":null,
#       "pi":null,
#       "r_bot_score":0,
#       "r_bot_score_suspicious_keys":[
         
#       ],
#       "r_bot_score_2":0,
#       "audio_hash":"-1",
#       "extensions":[
#          false
#       ],
#       "parent_win_hash":"4883931453396206889",
#       "webrtc_hash":"-1",
#       "performance_hash":"4874429083785836575",
#       "unique_keys":"onExpire,0,grecaptcha,onSuccess,1,Raven,hcaptcha",
#       "inv_unique_keys":"YoAH99j,fetchLater,BIBRRRT,FL0fi3W,L2Ue17x,CbbnvG,Ahi5ti,CjWy1K2,oncommand,EJBCFPi,s9zZT2T,Bhke5eG,NPDgjU,vhUQP5w,O_PCTOC,hhmFDk,Fqm7CfE,KAOs21P,kTOlHxx,__wdata,SvsDPjh,xagVpE,yKK3d3,KOERc0t,nSbBAT4,Z5BVmtW,vfz3_w,X9tKn4,hsw,iSlSvoq,cV4yyP4,wg7XZX,E2hVLAf,GYs5AY,zGpUjY,usPZYNU,g3XvU0_,Rw4WBNQ,B32tRc,P5EkGXu,LJ9kol2",
#       "common_keys_hash":3990815276,
#       "common_keys_tail":"setTimeout,stop,structuredClone,webkitCancelAnimationFrame,webkitRequestAnimationFrame,chrome,caches,cookieStore,ondevicemotion,ondeviceorientation,ondeviceorientationabsolute,launchQueue,sharedStorage,documentPictureInPicture,getScreenDetails,queryLocalFonts,showDirectoryPicker,showOpenFilePicker,showSaveFilePicker,originAgentCluster,onpageswap,onpagereveal,credentialless,fence,speechSynthesis,onscrollend,onscrollsnapchange,onscrollsnapchanging,webkitRequestFileSystem,webkitResolveLocalFileSystemURL",
#       "features":{
#          "performance_entries":true,
#          "web_audio":true,
#          "web_rtc":true,
#          "canvas_2d":true,
#          "fetch":true
#       }
#    },
#    "events":{
#       "performance_now":"6881.600000000006",
#       "function_tostring_length":"57",
#       "math_fingerprint_and_errors":"756874611071873095",
#       "navigator_properties":"[\"5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36\",\"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36\",8,6,\"en-US\",[\"en-US\",\"en\"],\"Win32\",null,[\"Google Chrome 135\",\"Not-A.Brand 8\",\"Chromium 135\"],false,\"Windows\",2,5,true,false,150,false,false,true,\"[object Keyboard]\",false,false]",
#       "encoded_user_agent":"\"#K#g3r!yKHg3QK3O/oO2tZ!b}UyUY::7KR.fF-bDKUI!YKHGI4U1K9/9/9/2OPtUCGAc&K3O/oO2t!AedeL\"",
#       "proxy_check":"4631229088072584217",
#       "performance_mark":"[[277114314453,277114314460,277114314451,357114314456,277114314452,554228628898,57114314443,717114314371391,554228628897,277114314456,1108457257862,277114314450,554228628919,277114314460,277114314451],false]",
#       "user_agent":"\"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36\"",
#       "post_message_user_agent_values":"[8,6,[\"Google Chrome 135\",\"Not-A.Brand 8\",\"Chromium 135\"],[\"Windows\",\"10.0.0\",null,\"64\",\"x86\",\"135.0.7049.115\"]]",
#       "worker_user_agent":"\"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36\"",
#       "worker_language_timezone":"[\"en-US\",[\"en-US\",\"en\"],\"en-US\",\"America/Havana\"]",
#       "worker_hc_memory_array":"[8,6]",
#       "worker_gpu_vendors":"[\"Google Inc. (AMD)\",\"ANGLE (AMD, Radeon (TM) RX 460 (0x000067EF) Direct3D11 vs_5_0 ps_5_0, D3D11)\"]",
#       "worker_gpu_depths_hashed":"4860234189560885575",
#       "worker_gpu_names":"[\"amd\",\"gcn-4\",\"\",\"\"]",
#       "worker_gpu_shits":"[14,2,11,12,1,3,16,8,15,13,9]",
#       "performance_difference":"946"
#    },
#    "unknow_events":{
      
#    }
# }

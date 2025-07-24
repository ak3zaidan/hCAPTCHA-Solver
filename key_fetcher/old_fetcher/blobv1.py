from javascript import require
from functools import wraps
import jsbeautifier
import requests
import sys, os

def suppress(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        stdout = sys.stdout
        stderr = sys.stderr
        try:
            sys.stdout = open(os.devnull, 'w') 
            sys.stderr = open(os.devnull, 'w')
            return func(*args, **kwargs) 

        finally:
            sys.stdout = stdout
            sys.stderr = stderr

    return wrapper

class Fetcher:
    def __init__(self, v, hswText):
        self.v = v
        self.modify(hswText)

    def modify(self, hswText=None, v=1):
        if hswText is None:
            hsw = requests.get(f"https://newassets.hcaptcha.com/c/{self.v}/hsw.js").text
        else:
            hsw = hswText

        checker = "try{crypto" + hsw.split("try{crypto")[1].split("){}")[0] + "){}"
        hsw = hsw.replace(checker, '')
        hsw = hsw.replace("var hsw=", "var blob_key = []; var hsw=")
        var = hsw.split("{if(0===")[1].split(")")[0]
        hsw = hsw.replace(f"){{if(0==={var})return ", f"){{if (2==={var}) return blob_key;if(0==={var})return ")        
        hsw = hsw + 'hsw("eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJmIjowLCJzIjoyLCJ0IjoidyIsImQiOiJsbktpdjBtOTZRTGV0d1NnelNabG5YRHowZTB3b0VhQ2s5THVMc2pFc1MvU3Fyb3NNYVBCaUdqSFhHeHJoZWEyK3NJelFOY0hjZjlxbmp2eHZGUFhKbElNeS9uaTRvNCszU1ZUNm5vbC9lU1F0dHE2L2tJMmRtd3ozWHVGSnZpakRBWE1yT0ZoVDZDdmNWSG5TRlNMZmNQOW9sMjZ3MklWNFo0VkhYSjdsTk1OdXFaLzV4Z1dldjVoMXBBc0JLcEpMWXlqdTBJK0N1OFZrSWhyVE0wRTZBdHBwTGd1Z2tqTXRFYjBocGo0bWxUYityTDIvakR4V3BTdVIzbVdVaTA9dkczRmxtTmx0WHY0R3loMyIsImwiOiIvYy82YjEyM2RjOWUwYjA5YmM5NmU5YmZlNDk5MGFmZGVlNWI3MWRjZWJjMjFjMjliZDBlY2JiYmU3ZDU4MDNiY2U4IiwiaSI6InNoYTI1Ni1BZUhGZHJSNnRuazhkWXNHV0hBOUUxa1RXTkt6VC9LWU1GM0VVYWk3U2VzPSIsImUiOjE3MzU0NjAyNjEsIm4iOiJoc3ciLCJjIjoxMDAwfQ.1GErl9giPp0OQAbA6ycqEPS2865n7qoQF6Xz6IZ1wIk")'
       
        hsw = jsbeautifier.beautify(hsw)

        if v == 2:
            for line in hsw.split("\n"):
                if ')] ^= ' in line:
                    if ',' in line and ';' in line:
                        bigint = line.split(")] ^= ")[1].split(",")[0]
                        sec = line.split(f"{bigint}")[1]
                        hsw = hsw.replace(f"{bigint},", f"{bigint}, blob_key.length < 4 && blob_key.push({bigint}),")
                        if ")] ^=" in sec:
                            bigint = sec.split(")] ^=")[1].split(";")[0]
                            hsw = hsw.replace(f"{bigint};", f"{bigint}, blob_key.length < 4 && blob_key.push({bigint});")
                    
                    elif ',' in line:
                        bigint = line.split(")] ^= ")[1].split(",")[0]
                        hsw = hsw.replace(f"{bigint},", f"{bigint}, blob_key.length < 4 && blob_key.push({bigint}),")
                    
                    elif ';' in line:
                        bigint = line.split(")] ^= ")[1].split(";")[0]
                        hsw = hsw.replace(f"{bigint};", f"{bigint}, blob_key.length < 4 && blob_key.push({bigint});")

        if v == 1:
            for line in hsw.split("\n"):
                if ')] ^= ' in line:
                    if ',' in line and ';' in line:
                        parts = line.split(",")
                        for part in parts:
                            if ")] ^=" in part:
                                try:
                                    bigint = part.split(")] ^= ")[1].split(",")[0]
                                    hsw = hsw.replace(f"{bigint},", f"{bigint}, blob_key.length < 4 && blob_key.push({bigint}),")
                                    
                                    sec = part.split(f"{bigint}")[1]
                                    if ")] ^=" in sec:
                                        sec_bigint = sec.split(")] ^= ")[1].split(",")[0]
                                        hsw = hsw.replace(f"{sec_bigint};", f"{sec_bigint}, blob_key.length < 4 && blob_key.push({sec_bigint});")
                                except IndexError:
                                    continue

                    elif ',' in line:
                        try:
                            bigint = line.split(")] ^= ")[1].split(",")[0]
                            hsw = hsw.replace(f"{bigint},", f"{bigint}, blob_key.length < 4 && blob_key.push({bigint}),")
                        except IndexError:
                            continue

                    elif ';' in line:
                        try:
                            bigint = line.split(")] ^= ")[1].split(";")[0]
                            hsw = hsw.replace(f"{bigint};", f"{bigint}, blob_key.length < 4 && blob_key.push({bigint});")
                        except IndexError:
                            continue

        self.hsw = hsw
    
    @suppress
    def bigints(self):
        self.jsdom = require('jsdom')
        self.evaluate = require("vm").Script
        self.vm = self.jsdom.JSDOM("<title></title>", {"runScripts": "dangerously"}).getInternalVMContext()
        self.evaluate(self.hsw).runInContext(self.vm)
        bigints = self.evaluate(f"hsw(2)").runInContext(self.vm)
        return bigints
    
    def key(self):
        bigints = self.bigints()
        dupe = False

        seen = set()

        for bigint in bigints:
            if bigint in seen or len(str(bigint)) < 7:
                dupe = True
                break
            seen.add(bigint)

        if dupe:
            self.modify(v=2)
            bigints = self.bigints()

        key = list(b''.join((num & 0xFFFFFFFF).to_bytes(4, byteorder='big') for num in bigints))
        key = key[:16]

        print(f"Fetched Blob Key -> {key}")
        return key

Fetcher('b5d09cd7e83c902f4de373bd20874a7bfb78d62542dc17cab9e39ab17493925e', None).key()

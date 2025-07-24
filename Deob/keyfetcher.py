import sys 

sys.dont_write_bytecode = True

import re, subprocess, tempfile, jsbeautifier, json, httpx
from Deob.utils import JsdomRuntime

def remove_crypto_lines(js_code):
    lines = js_code.splitlines()  # Split code into lines
    in_try_block = False
    cleaned_lines = []

    for line in lines:
        stripped_line = line.strip()

        if stripped_line.startswith("try "):
            in_try_block = True

        # If "catch" is encountered, exit the try-catch block
        if stripped_line.startswith("catch"):
            in_try_block = False

        # Skip the line if it contains "crypto" and is in a try-catch block
        if in_try_block and "crypto" in stripped_line:
            continue

        cleaned_lines.append(line)

    return "\n".join(cleaned_lines)

class KeyFetcher:
    def __init__(self, version: str) -> None:
        self.hsw = jsbeautifier.beautify(httpx.Client().get(f"https://newassets.hcaptcha.com/c/{version}/hsw.js").text)

        with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False, encoding="utf-8") as temp_file:
            temp_file.write(self.hsw)
            temp_file.flush()
            self.temp_hsw_file = temp_file

        self.runtime = JsdomRuntime()     
        self.version = version

    def find_second_tilde_line(self,text):
        count = 0  
        for line_number, line in enumerate(text.strip().split("\n"), start=1):
            if " ~~" in line:
                count += 1
                if count == 2:
                    return line.strip()
        return None

    def fetch_blob_and_event_ids(self):
        lines = self.hsw.split('\n')
        for i, line in enumerate(lines):
            if i == 0:
                lines[i] = 'window.event_mapping = []; \n window.blob_key = []\n' + line

            if "5575352424011909552" in line: # finding xxhash function lowkey
                theline = lines[i - 6]
                all_func = theline.split('= ')[1].split(';')[0]
                sandbox_function = all_func.split('(')[0]

                lines[i - 6] = lines[i - 6] + "window.sandbox = " + sandbox_function + ";"
                
        self.hsw = '\n'.join(lines)

        xor_pattern = r'\s\^=\s([^,;]+)(,|;)?'
        matches = re.finditer(xor_pattern, self.hsw)

        for i, match in enumerate(matches):
            if i >= 4:
                break
            value, delimiter = match.groups()

            self.hsw = self.hsw.replace(f" ^= {value}{delimiter}",
                                      f" ^= {value}{delimiter}\n  window.blob_key.push({value}){delimiter}")

        process = subprocess.Popen(
        ['node', 'Deob/mapper.mjs', self.temp_hsw_file.name],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        result, stderr = process.communicate()

        if not result:
            print(stderr)
        
        result = result.replace(b"[Error]\n", b"")
        result = result.decode()
        result = json.loads(result)
        
        try:
            self.vm_data = result["vmdata"]["vm_value"]
        except:
            self.vm_data = None 
            
        self.hsw = remove_crypto_lines(self.hsw)
        
        self.runtime.update_hsw(self.hsw)
        self.runtime.eval("hsw('eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJmIjowLCJzIjoyLCJ0IjoidyIsImQiOiJLM2hIWFdVYU92ZjdydVJEZk5GWjF0ckZjYi8zZ0FJVllqZXd4eUJBMEF3WnRBSWJoN2FEUy9janMraU9uSXc5dnpGVDdGTDJka2x6TEcrY2xTY2l6T1ZDWnI2KzhnTS9hWEJDUENUVzA3MUxZdGp0OTdYRS9IQnFNWUhSdnk0UGtxQ2t1N1d5Uy9EamIrb0JIVDdMUUNIVVUwbndoMHdac203dWVWd1B4dWNoMzk1c1ZGVkVXMlNDQzlxV1p3RkppUlVDRFhlU3ZuMXBqMEtQNjZ2ZDcyTVJsSGMvODVPMERUNmdNM08vT3lhOGZoMllnSEhQamRvZkNwQzNmalU9ZXFLTzJsNUtrcWNkTGh3ayIsImwiOiIvYy8wOTVlYTRlOWIwMDJhNjNhODQ0NWNmYjFiYWU2ZjIzN2E1NWI1ZWZiZmM1ZDc4MzhkNmYxNzMyYTlhOTgyMjAzIiwiaSI6InNoYTI1Ni1nazlFYUdETk9zc2Qzd0Iwdk1qKzZMOHVlR1h0aisrMDlpVFZIWkx1cnRjPSIsImUiOjE3MzMyNzY3MjEsIm4iOiJoc3ciLCJjIjoxMDAwfQ.96KBbQeURxEP5atM5nYFtf3MkhMQ6B1mlzi__UwMR3M')")

        blob_mapping = result["events"]
        for key, value in blob_mapping.items():
            blob_mapping[key] = self.runtime.eval(f"window.sandbox('{value}')")[0]

        deobfuscated_hsw = open(self.temp_hsw_file.name, 'r').read()
            
        found_line = self.find_second_tilde_line(deobfuscated_hsw)
        blob_decoding_integer = int(found_line.split(" + ")[1].split(")")[0])    
        
        blob_decoding_string = re.search(r'"([^"]+)"\s*(?:\.split|\["split"\])', deobfuscated_hsw).group(1)

        key = self.blob_key()
        
        return list(key)[:16], blob_mapping, blob_decoding_integer, blob_decoding_string

    def blob_key(self) -> list[int]:
        key = subprocess.run(["node", "Deob/blob.js", self.version], capture_output=True, text=True).stdout
        return json.loads(key)

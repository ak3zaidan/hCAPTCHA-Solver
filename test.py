from Decrypt import EncryptionSystem
from order import get_order
import json
import ast
import re

version = "f21494094c3c0dd7bcff14aba835d5fea0234ef82e9fea2684be17956c94a27e"

remove_messages = True

system = EncryptionSystem(version, {}, False)

def extract_blob(n_data):
    quoted_strings = re.findall(r'"(.*?)"', n_data)

    blob = max(quoted_strings, key=len)

    n_data = n_data.replace(blob, "<blob>")

    return n_data, blob

def get_substring(body: str, begin: str, end: str) -> str:
    start_index = body.find(begin)
    if start_index == -1:
        return "-1"
    
    start_index += len(begin)
    end_index = body.find(end, start_index)
    
    if end_index == -1:
        return "-1"
    
    return body[start_index:end_index]

def decryptRequest():
    with open("misc/req1", "rb") as file:
        encrypted_req = file.read()

    try:
        decrypted_main_data = str(system.decrypt_request_payload(encrypted_req))
    except Exception as e:
        print("Decryption request failed:", str(e))

    n_data = get_substring(decrypted_main_data, "'n': '", "',")

    if n_data == "-1":
        print("\n\n\nN data is -1")
        return
    
    motion_data = get_substring(decrypted_main_data, "'motionData': '", "', 'pdc'")
    
    if motion_data == "-1":
        print("\n\n\nMotion data is -1")
        return
    
    decrypted_main_data = decrypted_main_data.replace(n_data, "")
    decrypted_main_data = decrypted_main_data.replace(motion_data, "")

    try:
        decrypted_n_data = str(system.decrypt_n(n_data))
    except Exception as e:
        print("Decryption n failed:", str(e))

    if remove_messages:
        messages = get_substring(decrypted_n_data, '[["https:', "]]]")

        if messages != "-1":
            messages = '[["https:' + messages + "]]]"

            decrypted_n_data = decrypted_n_data.replace(messages, '"messages"')
        else:
            print("Failed to remove messages")

    decrypted_n_data, blob = extract_blob(decrypted_n_data)

    print("\n\nMain Data:")
    data = ast.literal_eval(decrypted_main_data)
    print(json.dumps(data, indent=4))

    print("\n\nn Data:")
    print(decrypted_n_data)

    print("\n\nmotion Data:")
    print(motion_data)

    decryptBlob(blob)

    print("\n\norder:")
    print(get_order(decrypted_n_data))

def decryptResp():
    with open("misc/resp1", "rb") as file:
        encrypted_resp = file.read()

    try:
        decrypted_data = str(system.decrypt_response(encrypted_resp))
        data = ast.literal_eval(decrypted_data)
        print("Decrypted response Data")
        print(json.dumps(data, indent=4))
    except Exception as e:
        print("Decryption response failed:", str(e))

def decryptSolution():
    with open("misc/req2", "rb") as file:
        encrypted_req = file.read()

    decrypted_main_data = encrypted_req.decode('utf-8')

    n_data = get_substring(decrypted_main_data, '"n":"', '",')

    if n_data == "-1":
        print("\n\n\nN data is -1")
        return
    
    motion_data = get_substring(decrypted_main_data, '"motionData":"', '","n"')

    if motion_data == "-1":
        print("\n\n\nMotion data is -1")
        return
    
    decrypted_main_data = decrypted_main_data.replace(n_data, "")
    decrypted_main_data = decrypted_main_data.replace(motion_data, "")

    try:
        decrypted_n_data = str(system.decrypt_n(n_data))
    except Exception as e:
        print("Decryption n failed:", str(e))

    if remove_messages:
        messages = get_substring(decrypted_n_data, '[["https:', "]]]")

        if messages != "-1":
            messages = '[["https:' + messages + "]]]"

            decrypted_n_data = decrypted_n_data.replace(messages, '"messages"')
        else:
            print("Failed to remove messages")

    decrypted_n_data, blob = extract_blob(decrypted_n_data)

    print("\n\nMain Data:")
    data = ast.literal_eval(decrypted_main_data)
    print(json.dumps(data, indent=4))

    print("\n\nn Data:")
    print(decrypted_n_data)

    print("\n\nmotion Data:")
    print(motion_data)

    decryptBlob(blob)

    print("\n\norder:")
    print(get_order(decrypted_n_data))

def decryptBlob(blob):
    try:
        decrypted_data = system.decrypt_blob(blob)
        print("\n\nblob Data")
        print(decrypted_data)
    except Exception as e:
        print("Decryption blob failed:", str(e))

# decryptRequest()

# decryptResp()

# decryptSolution()

from typing_extensions import Literal, TypeAlias
from Crypto.Util.Padding import unpad, pad
from Crypto.Random import get_random_bytes
from time import strftime, localtime
from string import ascii_letters
from Crypto.Cipher import AES
import zlib, json, numpy
import hashlib
import random
import base64
import xxhash
import time
import math

def mint_stamp(challenge: str, bits: int) -> str:
        counter = 0
        hex_digits = int(math.ceil(bits / 4.0))
        zeros = '0' * hex_digits
        while 1:
            digest = hashlib.sha1((challenge + hex(counter)[2:]).encode()).hexdigest()
            if digest[:hex_digits] == zeros:
                return hex(counter)[2:]
            counter += 1

def get_salt(salt_length: int) -> str:
        charset = ascii_letters + "+/="
        return ''.join([random.choice(charset) for _ in range(salt_length)])

def mint(resource: str, bits: int = 2, ext: str = '', salt_chars: int = 8) -> str:
        timestamp = strftime("%Y-%m-%d", localtime(time.time()))
        challenge = f"1:{bits}:{timestamp}:{resource}:{ext}:{get_salt(salt_chars)}:"
        return f"{challenge}{mint_stamp(challenge, bits)}"

def stamp(difficulty, data):
    return mint(data, difficulty)

# rand.py

def rand_hash(n:dict | list):
    return  float(numpy.uint32(zlib.crc32(json.dumps(n, separators=(",", ":"), ensure_ascii=False).encode())) * 2.3283064365386963e-10)

# jwt.py

def parse_jwt(jwt:str):
    vb = jwt.split(".")[1]
    if not vb.endswith("="):
        vb += "=="
        
    jwt = json.loads(base64.b64decode(vb.encode()))
    return jwt

# hasher.py

def xhash(data:bytes) -> str:
    x = xxhash.xxh64(seed=5575352424011909552)
    x.update(data)
    return str(x.intdigest())

# encryption.py

ActionType : TypeAlias = Literal[
    "n_data_key",
    "encrypt_body_key",
    "decrypt_body_key"
]

class Encryption:
    def __init__(self, action: ActionType, version: dict) -> None:
        self.key = bytes(version[action])
        self.action = action
        
    def encrypt(self, data: bytes) -> str:
        iv = get_random_bytes(12)
        cipher = AES.new(self.key, AES.MODE_GCM, nonce=iv)
        
        encrypted_bytes,gcm_checksum = cipher.encrypt_and_digest(data)
        encrypted_bytes += gcm_checksum
        
        encrypted_data = encrypted_bytes + iv + b"\x00"
        
        return base64.b64encode(encrypted_data).decode()

    def decrypt(self, data: str | bytes) -> str:
        data_decoded = base64.b64decode(data)
            
        iv = bytes(data_decoded[-13:-1])
        data_decoded = data_decoded[:-13]
        data_decoded, tag = data_decoded[:-16], data_decoded[-16:]
        cipher = AES.new(self.key, AES.MODE_GCM, nonce=iv)
            
        decrypted_bytes = cipher.decrypt_and_verify(data_decoded,received_mac_tag=tag)
            
        return decrypted_bytes.decode()
    
    def decrypt_get_payload(self, data: bytes):
        iv = bytes(data[:12])
        data = data[12:]
        data, tag = data[:-16], data[-16:]
        cipher = AES.new(self.key, AES.MODE_GCM, nonce=iv)
                
        decrypted_bytes = cipher.decrypt_and_verify(data,received_mac_tag=tag)
                
        return decrypted_bytes
        
    def encrypt_send_payload(self, data: bytes):
        iv = get_random_bytes(12)
        cipher = AES.new(self.key, AES.MODE_GCM, nonce=iv)
        
        encrypted_bytes,gcm_checksum = cipher.encrypt_and_digest(data)
        encrypted_bytes += gcm_checksum
        
        return  iv + encrypted_bytes 
    
    def decrypt_send_payload(self, data): 
        iv = bytes(data[:12])
        data = data[12:]
        data, tag = data[:-16], data[-16:]
        cipher = AES.new(self.key, AES.MODE_GCM, nonce=iv)
                
        decrypted_bytes = cipher.decrypt_and_verify(data,received_mac_tag=tag)
                
        #unpacked = msgpack.unpackb(decrypted_bytes)
        
        return decrypted_bytes

class BlobEncryption:
    def __init__(self, version: dict):
        self.key = bytes(version["blob_key"])

    def decrypt(self, data: str) -> str:
        iv, ciphertext = map(base64.b64decode, data.split('.'))
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        decrypted = unpad(cipher.decrypt(ciphertext), AES.block_size)
        return decrypted.decode('utf-8')

    def encrypt(self, data: str) -> str:
        iv = get_random_bytes(16)
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        encrypted = cipher.encrypt(pad(data.encode(), AES.block_size))
        return base64.b64encode(iv).decode() + '.' + base64.b64encode(encrypted).decode()

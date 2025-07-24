from firebase_admin import credentials, firestore
from Utils.Helpers import getProxy, get_substring
from Crypto.Random import get_random_bytes
from Deob.keyfetcher import KeyFetcher
from Crypto.Util.Padding import unpad
from Crypto.Util.Padding import pad
from Crypto.Cipher import AES
from typing import Optional
import firebase_admin
import tls_client
import subprocess
import threading
import binascii
import msgpack
import base64
import json
import os

os.environ["GRPC_VERBOSITY"] = "NONE"
os.environ["GRPC_LOG_SEVERITY_LEVEL"] = "ERROR"

# Constants

SKIP_DB = False
SKIP_LOCAL = False
client_identifier = "chrome136"
api_key = ""
KEYS_FILE_PATH = "misc/keys.json"
service_account_path = "misc/service.json"
secChUa = '"Chromium";v="136", "Google Chrome";v="136", "Not.A/Brand";v="99"'
userAgent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36"

# Class structure to store key bytes

class EncryptionKeys:
    def __init__(self, key_n, key_response, key_request, blobKey, blob_decoding_integer, blob_decoding_string, events, v1Path, order):
        self.key_n = key_n
        self.key_response = key_response
        self.key_request = key_request
        self.blobKey = blobKey
        self.blob_decoding_integer = blob_decoding_integer
        self.blob_decoding_string = blob_decoding_string
        self.events = events
        self.v1Path = v1Path
        self.order = order if order else {}

# Class gets called by EncryptionSystem. This call gets encryption keys for HSW version

class GetKeys:
    def __init__(self, version, order={}, shouldSave=True, disableExtraction=False):
        if not version:
            raise ValueError("Version cannot be empty")
        
        self.version = version
        self.order = order
        self.shouldSave = shouldSave
        self.disableExtraction = disableExtraction

        cred = credentials.Certificate(service_account_path)

        if not firebase_admin._apps:
            firebase_admin.initialize_app(cred)
            
        self.db = firestore.client()
    
    def get_keys(self) -> EncryptionKeys:
        # 1. Check local
        if not SKIP_LOCAL:
            keys = self.check_local_keys()
            if keys:
                return keys
        
        # 2. Check DB
        if not SKIP_DB:
            keys = self.check_firebase_keys()
            if keys:
                self.save_keys_to_local(keys)

                return keys
        
        if self.disableExtraction:
            return None
        
        # 3. Manually parse
        try:
            keys = self.extract_keys()

            if keys and self.shouldSave:
                self.save_keys_to_local(keys)

                upload_thread = threading.Thread(target=self.upload_keys, args=(keys,), daemon=True)
                upload_thread.start()

            return keys
        except Exception as e:
            print(f"First attempt to extract keys failed: {e}")

            try:
                keys = self.extract_keys()

                if keys and self.shouldSave:
                    self.save_keys_to_local(keys)
                    
                    upload_thread = threading.Thread(target=self.upload_keys, args=(keys,), daemon=True)
                    upload_thread.start()

                return keys
            except Exception as e:
                print(f"Retry attempt to extract keys failed: {e}")
                raise RuntimeError(f"Failed to extract keys after retry: {e}")

    def upload_keys(self, keys: EncryptionKeys) -> bool:
        try:
            keys_data = {
                "blob_key": list(keys.blobKey),
                "decrypt_body_key": base64.b64encode(keys.key_response).decode(),
                "encrypt_body_key": base64.b64encode(keys.key_request).decode(),
                "n_data_key": base64.b64encode(keys.key_n).decode(),
                "blob_decoding_integer": keys.blob_decoding_integer,
                "blob_decoding_string": keys.blob_decoding_string,
                "events": keys.events,
                "v1Path": keys.v1Path,
                "order": keys.order
            }
            self.db.collection('keys').document(self.version).set(keys_data)
            print(f"Successfully uploaded keys for version {self.version}")
            return True
        except Exception as e:
            print(f"Error uploading keys: {e}")
            return False

    def check_firebase_keys(self) -> Optional[EncryptionKeys]:
        try:
            keys_ref = self.db.collection('keys').document(self.version)
            doc = keys_ref.get()
            if not doc.exists:
                print(f"No db keys found for version {self.version}")
                return None
            
            doc_data = doc.to_dict()

            blob_key = bytes(doc_data.get("blob_key", []))

            decrypt_body_key = base64.b64decode(doc_data.get("decrypt_body_key", ""))
            encrypt_body_key = base64.b64decode(doc_data.get("encrypt_body_key", ""))
            n_data_key = base64.b64decode(doc_data.get("n_data_key", ""))

            blob_decoding_integer = doc_data.get("blob_decoding_integer", 0)
            blob_decoding_string = doc_data.get("blob_decoding_string", "")
            events = doc_data.get("events", {})

            v1Path = doc_data.get("v1Path", "")

            order = doc_data.get("order", {})

            if not v1Path:
                v1Path = self.getV1Path(True)
            
            return EncryptionKeys(
                key_n=n_data_key,
                key_response=decrypt_body_key,
                key_request=encrypt_body_key,
                blobKey=blob_key,
                blob_decoding_integer=blob_decoding_integer,
                blob_decoding_string=blob_decoding_string,
                events=events,
                v1Path=v1Path,
                order=order
            )
        except Exception as e:
            print(f"Error checking Firebase keys: {e}")
            return None

    def extract_keys(self) -> EncryptionKeys:
        bridgeData = None

        try:
            result = subprocess.run(
                ['node', 'key_fetcher/bridge.js', self.version],
                capture_output=True, text=True, check=True
            )

            bridgeData = json.loads(result.stdout)
        except subprocess.CalledProcessError as e:
            raise Exception(f"Error running Node.js script: {e}")
        
        keys = bridgeData['keys']
        nKey = base64.b64decode(keys[0])
        requestKey = base64.b64decode(keys[1])
        respKey = base64.b64decode(keys[2])

        blob_key, events, blob_decoding_integer, blob_decoding_string = KeyFetcher(version=self.version).fetch_blob_and_event_ids()

        v1Path = self.getV1Path(True)
        
        return EncryptionKeys(
            key_n=nKey,
            key_response=respKey,
            key_request=requestKey,
            blobKey=blob_key,
            blob_decoding_integer=blob_decoding_integer,
            blob_decoding_string=blob_decoding_string,
            events=events,
            v1Path=v1Path,
            order=self.order
        )

    def check_local_keys(self) -> Optional[EncryptionKeys]:
        if not os.path.exists(KEYS_FILE_PATH):
            return None
        
        try:
            with open(KEYS_FILE_PATH, "r") as f:
                all_keys = json.load(f)

            if self.version not in all_keys:
                print(f"No local keys found for version {self.version}")
                return None

            doc_data = all_keys[self.version]

            blob_key = bytes(doc_data.get("blob_key", []))

            decrypt_body_key = base64.b64decode(doc_data.get("decrypt_body_key", ""))
            encrypt_body_key = base64.b64decode(doc_data.get("encrypt_body_key", ""))
            n_data_key = base64.b64decode(doc_data.get("n_data_key", ""))

            blob_decoding_integer = doc_data.get("blob_decoding_integer", 0)
            blob_decoding_string = doc_data.get("blob_decoding_string", "")
            events = doc_data.get("events", {})

            v1Path = doc_data.get("v1Path", "")

            order = doc_data.get("order", {})

            if not v1Path:
                v1Path = self.getV1Path(True)
            
            return EncryptionKeys(
                key_n=n_data_key,
                key_response=decrypt_body_key,
                key_request=encrypt_body_key,
                blobKey=blob_key,
                blob_decoding_integer=blob_decoding_integer,
                blob_decoding_string=blob_decoding_string,
                events=events,
                v1Path=v1Path,
                order=order
            )
        except Exception as e:
            print(f"Error reading local keys.json: {e}")
            return None

    def save_keys_to_local(self, keys: EncryptionKeys):
        try:
            if os.path.exists(KEYS_FILE_PATH):
                with open(KEYS_FILE_PATH, "r") as f:
                    all_keys = json.load(f)
            else:
                all_keys = {}

            all_keys[self.version] = {
                "blob_key": list(keys.blobKey),
                "decrypt_body_key": base64.b64encode(keys.key_response).decode(),
                "encrypt_body_key": base64.b64encode(keys.key_request).decode(),
                "n_data_key": base64.b64encode(keys.key_n).decode(),
                "blob_decoding_integer": keys.blob_decoding_integer,
                "blob_decoding_string": keys.blob_decoding_string,
                "events": keys.events,
                "v1Path": keys.v1Path,
                "order": keys.order
            }

            with open(KEYS_FILE_PATH, "w") as f:
                json.dump(all_keys, f, indent=2)
            
            print(f"Successfully saved keys locally for version {self.version}")
        except Exception as e:
            print(f"Error saving keys to local file: {e}")

    def getV1Path(self, retry):
        endpoint = "https://js.hcaptcha.com/1/api.js?reportapi=https%3A%2F%2Faccounts.hcaptcha.com&custom=False&pstissuer=https://pst-issuer.hcaptcha.com"

        session = tls_client.Session(
            client_identifier=client_identifier,
            random_tls_extension_order=True
        )

        session.header_order = [
            "sec-ch-ua-platform",
            "user-agent",
            "sec-ch-ua",
            "sec-ch-ua-mobile",
            "accept",
            "sec-fetch-site",
            "sec-fetch-mode",
            "sec-fetch-dest",
            "referer",
            "accept-encoding",
            "accept-language",
        ]

        headers = {
            "sec-ch-ua-platform": '"Windows"',
            "user-agent": userAgent,
            "sec-ch-ua": secChUa,
            "sec-ch-ua-mobile": "?0",
            "accept": "*/*",
            "sec-fetch-site": "same-site",
            "sec-fetch-mode": "no-cors",
            "sec-fetch-dest": "script",
            "referer": "https://accounts.hcaptcha.com/",
            "accept-encoding": "gzip, deflate, br, zstd",
            "accept-language": "en-US,en;q=0.9"
        }

        if not retry:
            response = session.get(
                endpoint,
                headers=headers,
                proxy=getProxy()
            )
        else:
            response = session.get(
                endpoint,
                headers=headers
            )

        print(f'Get V1Path status: {response.status_code}')

        v1Path = get_substring(response.text, "https://newassets.hcaptcha.com/captcha/v1/", "/static")

        if not v1Path or v1Path == "-1":
            v1Path = get_substring(response.text, 'be="', '"')

            if not v1Path or v1Path == "-1":
                if retry:
                    return self.getV1Path(False)
                else:
                    return ""

        return v1Path

    def manual_save(self, keys: EncryptionKeys):
        self.save_keys_to_local(keys)
        self.upload_keys(keys)

# Class to encrypt/decrypt payloads

class EncryptionSystem:
    def __init__(self, version, order={}, shouldSave=True, disableExtraction=False):
        key_manager = GetKeys(version, order, shouldSave, disableExtraction)
        keys = key_manager.get_keys()
        self.history = keys
        self.version = version

        if firebase_admin._apps:
            firebase_admin.delete_app(firebase_admin.get_app())
        
        if not keys:
            raise ValueError(f"Failed to retrieve keys for version {version}")
        
        self.key_response = keys.key_response
        self.key_request = keys.key_request
        self.key_n = keys.key_n
        self.blobKey = keys.blobKey
        self.blob_decoding_integer = keys.blob_decoding_integer
        self.blob_decoding_string = keys.blob_decoding_string
        self.events = keys.events
        self.v1Path = keys.v1Path
        self.order = keys.order
            
        print(f"Successfully initialized EncryptionSystem with keys for version {version}")

    def save_system(self, order):
        self.history.order = order
        GetKeys(self.version, order).manual_save(self.history)

    # Response
    def decrypt_response(self, data, decodeBase64=False):
        if decodeBase64:
            data = base64.b64decode(data)
        iv, encrypted_data, tag = data[:12], data[12:-16], data[-16:]
        cipher = AES.new(self.key_response, AES.MODE_GCM, nonce=iv)
        return msgpack.unpackb(cipher.decrypt_and_verify(encrypted_data, tag), strict_map_key=False)

    # Request
    def encrypt_request_payload(self, data, config):
        config = json.dumps(config, separators=(',', ':'))
        iv = get_random_bytes(12)
        cipher = AES.new(self.key_request, AES.MODE_GCM, nonce=iv)
        enc, checksum = cipher.encrypt_and_digest(msgpack.packb(data))
        encrypted_data = msgpack.ExtType(18, iv + enc + checksum)
        return msgpack.packb([config, encrypted_data])

    def decrypt_request_payload(self, encrypted_data):
        packed_config, packed_encrypted_data = msgpack.unpackb(encrypted_data)
        config = json.loads(packed_config)

        print(f'\nConfig: {config}\n')

        iv, enc, checksum = packed_encrypted_data.data[:12], packed_encrypted_data.data[12:-16], packed_encrypted_data.data[-16:]
        
        cipher = AES.new(self.key_request, AES.MODE_GCM, nonce=iv)
        
        try:
            decrypted_data = cipher.decrypt_and_verify(enc, checksum)
            data = msgpack.unpackb(decrypted_data)
            return data
        except ValueError as e:
            raise ValueError(e)

    # N data
    def encrypt_n(self, plaintext):
        iv = get_random_bytes(12)
        cipher = AES.new(self.key_n, AES.MODE_GCM, nonce=iv)
        ciphertext, tag = cipher.encrypt_and_digest(plaintext.encode())
        encoded = base64.b64encode(ciphertext + tag + iv + b"\x00")
        return encoded.decode()

    def decrypt_n(self, encrypted_data):
        decoded = base64.b64decode(encrypted_data)
        encrypted_data, tag, iv = decoded[:-29], decoded[-29:-13], decoded[-13:-1]
        cipher = AES.new(self.key_n, AES.MODE_GCM, nonce=iv)
        return cipher.decrypt_and_verify(encrypted_data, tag).decode()

    # Blob
    def encrypt_blob(self, data):
        try:
            # Generate a random IV
            iv = get_random_bytes(AES.block_size)

            # Create a cipher object using the random iv
            cipher = AES.new(self.blobKey, AES.MODE_CBC, iv)

            # Pad the data to be encrypted
            padded_data = pad(data.encode('utf-8'), AES.block_size)

            # Encrypt the data
            ciphertext = cipher.encrypt(padded_data)

            # Encode the iv and ciphertext to base64 to make it safe to transmit
            iv_b64 = base64.b64encode(iv).decode('utf-8')
            ciphertext_b64 = base64.b64encode(ciphertext).decode('utf-8')

            # Return the base64 encoded iv and ciphertext, separated by a dot
            return iv_b64 + '.' + ciphertext_b64

        except Exception as e:
            raise Exception('Encryption failed: ' + str(e))

    def decrypt_blob(self, data):
        try:
            iv_b64, ciphertext_b64 = data.split('.')
            iv = base64.b64decode(iv_b64)
            ciphertext = base64.b64decode(ciphertext_b64)

            cipher = AES.new(self.blobKey, AES.MODE_CBC, iv)
            decrypted = unpad(cipher.decrypt(ciphertext), AES.block_size)

            return decrypted.decode('utf-8')

        except (binascii.Error, ValueError, IndexError) as e:
            raise Exception('Decryption failed: ' + str(e))

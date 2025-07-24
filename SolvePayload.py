from NGen.generator import N as NGen
from Motion import Motion
import Decrypt
import json

class Solve_Payload:
    def __init__(self, system: Decrypt.EncryptionSystem, fingerprint, jwt_token, version, tokenData, v1Path, siteKey, timezone, referer, answer, challenge_type):
        self.system = system
        self.fingerprint = fingerprint
        self.jwt_token = jwt_token
        self.version = version
        self.tokenData = tokenData
        self.v1Path = v1Path
        self.siteKey = siteKey
        self.referer = referer
        self.answer = answer
        self.challenge_type = challenge_type

        self.class_N = NGen(
            timezone=timezone, 
            link=referer, 
            sitekey=siteKey, 
            v2_api=False, 
            fingerprint=convert_fingerprint(fingerprint),
            system=system
        )

    def gen_request_payload(self):
        payload = {
            "v": self.v1Path,
            "job_mode": self.challenge_type,
            "answers": self.answer,
            "serverdomain": server_domain(self.siteKey),
            "sitekey": self.siteKey,
            "motionData": self.gen_request_motion(),
            "n": self.gen_n_payload(),
            "c": "{\"type\":\"hsw\",\"req\":\"" + self.jwt_token +  "\"}"
        }

        return payload

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

def server_domain(siteKey):
    if siteKey == "a5f74b19-9e45-40e0-b45d-47ff91b7a6c2":
        return "accounts.hcaptcha.com"
    else:
        return "accounts.hcaptcha.com"

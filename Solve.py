from sagemaker.huggingface.model import HuggingFacePredictor
from ReqestPayload import Request_Payload
from FingerprintManager import FpManager
from dataclasses import dataclass
from autoUpdate import save_data
from curl_cffi import requests
from Utils.Helpers import *
import threading
import sagemaker
import Decrypt
import time
import json
import jwt
import sys

# Constants

HCAP_VERSION = "f21494094c3c0dd7bcff14aba835d5fea0234ef82e9fea2684be17956c94a27e"
SKIP_SITEKEY = True
ENABLE_LOGGING = True
USE_CHARLES_PROXY = False
DISABLE_COOKIES = True

@dataclass(frozen=True)
class Config:
    # Hcap constants

    demo_sitekey = "a5f74b19-9e45-40e0-b45d-47ff91b7a6c2"
    shopify_sitekey = ""
    pokemon_sitekey = ""
    site_key_url: str = "https://accounts.hcaptcha.com/demo"
    referer: str = "https://www.google.com/"
    timezone: str = "America/New_York"

    # Solve constants

    max_retries: int = 0
    max_skips: int = 3

    # Ai constants

    iam_role_name: str = "ai"
    sagemaker_endpoint: str = "huggingface-pytorch-inference-2025-03-17-01-55-03-255"
    classification_prompt: str = "Describe the image in 1 sentence."
    ai_model: str = "gpt-4o-mini"
    openai_api_key: str = ""
    system_message: str = (
        "Only return an int array that contains the indices of the right answers. "
        "Return the array by itself with nothing else."
    )

    # Tls constants

    impersonate: str = "chrome133a"
    sec_ch_ua: str = '"Chromium";v="136", "Google Chrome";v="136", "Not.A/Brand";v="99"'
    user_agent: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36"

# Main

class Solver:
    def __init__(self, proxy, userAgent, secChUa, referer):
        self.config = Config()

        self.userAgent = userAgent
        self.secChUa = secChUa
        self.referer = referer
        self.retries = 0
        self.skips = 0
        self.response = None
        self.challengeData = None
        self.siteKey = self.config.demo_sitekey
        self.one_click_token = None

        self.session = requests.Session(impersonate=self.config.impersonate)

        if USE_CHARLES_PROXY:
            charles = "http://localhost:8888"
            self.session.proxies = {"http": charles, "https": charles}
        elif proxy:
            self.session.proxies = {"http": proxy, "https": proxy}
        
        self.fingerprint = FpManager(userAgent).getFingerprint(True)

        self.encryptionSystem = None

    def setEncryption(self):
        try:
            self.encryptionSystem = Decrypt.EncryptionSystem(HCAP_VERSION, {}, False, True)
        except Exception as e:
            print(f'Background: failed encryption system: {str(e)}')

    def session_setup(self):
        if SKIP_SITEKEY:
            if not self.encryptionSystem:
                self.setEncryption()
        else:
            # Setup encryption system in background
            background_thread = None
            if not self.encryptionSystem:
                background_thread = threading.Thread(target=self.setEncryption)
                background_thread.start()

            if not self.siteKey:
                self.siteKey = self.getSiteKey()

            # Block for encryption system
            if background_thread:
                background_thread.join()

    def update_version(new_version: str):

        def version_exists_locally(version: str, json_file_path: str) -> bool:
            try:
                with open(json_file_path, 'r') as f:
                    data = json.load(f)
                return version in data
            except FileNotFoundError:
                print(f"File not found: {json_file_path}")
                return False
            except json.JSONDecodeError:
                print(f"Invalid JSON format in file: {json_file_path}")
                return False

        if version_exists_locally(new_version, "misc/keys.json"):
            print("Entry already present in keys.json for version -> " + new_version)
            return
        
        save_data(new_version)

    # Requests

    def getSiteKey(self) -> str:
        headers = {
            "sec-ch-ua": self.secChUa,
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "upgrade-insecure-requests": "1",
            "user-agent": self.userAgent,
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "sec-fetch-site": "none",
            "sec-fetch-mode": "navigate",
            "sec-fetch-user": "?1",
            "sec-fetch-dest": "document",
            "referer": self.referer,
            "accept-encoding": "gzip, deflate, br, zstd",
            "accept-language": "en-US,en;q=0.9",
            "priority": "u=0, I"
        }

        if DISABLE_COOKIES:
            self.session.cookies.clear()

        response = self.session.get(
            self.config.site_key_url,
            headers=headers,
            default_headers=False,
            verify=False if USE_CHARLES_PROXY else True
        )

        if ENABLE_LOGGING:
            print_blue(f'\n\nCode = {response.status_code} | Response = {response.text}')

        if response.status_code != 200:
            raise Exception(f'SiteKey: failed with resp code {response.status_code}')
        
        siteKey = get_substring(response.text, 'data-sitekey="', '"')

        if ENABLE_LOGGING:
            print_blue(f'\n\nGot sitekey = {siteKey}')

        if siteKey == "-1":
            raise Exception("Failed parsing site key")

        return siteKey

    def postCheckConfig(self):
        endpoint = f'https://api.hcaptcha.com/checksiteconfig?v={self.encryptionSystem.v1Path}&host=accounts.hcaptcha.com&sitekey={self.siteKey}&sc=1&swa=1&spst=1'

        headers = {
            "content-length": "0",
            "sec-ch-ua-platform": '"Windows"',
            "user-agent": self.userAgent,
            "accept": "application/json",
            "sec-ch-ua": self.secChUa,
            "content-type": "text/plain",
            "sec-ch-ua-mobile": "?0",
            "origin": "https://newassets.hcaptcha.com",
            "sec-fetch-site": "same-site",
            "sec-fetch-mode": "cors",
            "sec-fetch-dest": "empty",
            "referer": "https://newassets.hcaptcha.com/",        
            "accept-encoding": "gzip, deflate, br, zstd",
            "accept-language": "en-US,en;q=0.9",
            "priority": "u=0, I"
        }

        if DISABLE_COOKIES:
            self.session.cookies.clear()

        response = self.session.post(
            endpoint,
            headers=headers,
            default_headers=False,
            verify=False if USE_CHARLES_PROXY else True
        )

        if ENABLE_LOGGING:
            print_blue(f'\n\nCode = {response.status_code} | Response = {response.text}')

        if response.status_code != 200:
            raise Exception(f'Site Config: failed with resp code {response.status_code}')
            
        config = json.loads(response.text)

        self.jwt_token = config["c"]["req"]

        decoded_Token = jwt.decode(self.jwt_token, options={"verify_signature": False})

        if HCAP_VERSION not in decoded_Token["l"]:
            parsed_version = decoded_Token["l"].replace("/c/", "")
            self.update_version(parsed_version)
            print("ERROR: version mismatch, rerun on new version: " + parsed_version)
            sys.exit(1)
        
        self.tokenData = decoded_Token["d"]

    def getCaptcha(self, payload):
        endpoint = f'https://api.hcaptcha.com/getcaptcha/{self.siteKey}'

        headers = {
            "content-length": len(payload),
            "sec-ch-ua-platform": '"Windows"',
            "user-agent": self.userAgent,
            "accept": "application/json, application/octet-stream",
            "sec-ch-ua": self.secChUa,
            "content-type": "application/octet-stream",
            "sec-ch-ua-mobile": "?0",
            "origin": "https://newassets.hcaptcha.com",
            "sec-fetch-site": "same-site",
            "sec-fetch-mode": "cors",
            "sec-fetch-dest": "empty",
            "referer": "https://newassets.hcaptcha.com/",
            "accept-encoding": "gzip, deflate, br, zstd",
            "accept-language": "en-US,en;q=0.9",
            "priority": "u=1, i"
        }

        if DISABLE_COOKIES:
            self.session.cookies.clear()

        response = self.session.post(
            endpoint,
            headers=headers,
            data=payload,
            default_headers=False,
            verify=False if USE_CHARLES_PROXY else True
        )

        if ENABLE_LOGGING:
            print_blue(f'\n\nCode = {response.status_code} | Response = {response.text}')

        if response.status_code != 200:
            raise Exception(f'Get Captcha: failed with resp code {response.status_code}')
        
        try:
            oneClickData = response.json()

            if 'pass' in oneClickData:
                if oneClickData['pass'] == True:
                    self.one_click_token = oneClickData['generated_pass_UUID']
                    return
                else:
                    raise Exception("Blocked on get captcha")
        except:
            pass
        
        self.response = self.encryptionSystem.decrypt_response(response.text)
        self.e_key = self.response['key']

        if ENABLE_LOGGING:
            print_blue(f'\n\nDecrypted Response = {self.response}')

    def postSubmission(self, payload):
        endpoint = f'https://api.hcaptcha.com/checkcaptcha/{self.siteKey}/{self.e_key}'

        headers = {
            "content-length": len(payload),
            "sec-ch-ua-platform": '"Windows"',
            "user-agent": self.userAgent,
            "sec-ch-ua": self.secChUa,
            "content-type": "application/json;charset=UTF-8",
            "sec-ch-ua-mobile": "?0",
            "accept": "*/*",        
            "origin": "https://newassets.hcaptcha.com",
            "sec-fetch-site": "same-site",
            "sec-fetch-mode": "cors",
            "sec-fetch-dest": "empty",
            "referer": "https://newassets.hcaptcha.com/",
            "accept-encoding": "gzip, deflate, br, zstd",
            "accept-language": "en-US,en;q=0.9",
            "priority": "u=1, i"
        }

        if DISABLE_COOKIES:
            self.session.cookies.clear()

        response = self.session.post(
            endpoint,
            headers=headers,
            data=payload,
            default_headers=False,
            verify=False if USE_CHARLES_PROXY else True
        )

        if ENABLE_LOGGING:
            print_blue(f'\n\nCode = {response.status_code} | Response = {response.text}')

        if response.status_code != 200:
            raise Exception(f'Post Submission: failed with resp code {response.status_code}')

        return response.json()

    # Captcha Helpers

    def askGPT(self, actionPrompt):
        url = "https://api.openai.com/v1/completions"
        
        headers = {
            "Authorization": f"Bearer {self.config.openai_api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.config.ai_model,
            "messages": [
                {"role": "system", "content": self.config.system_message},
                {"role": "user", "content": actionPrompt}
            ],
            "temperature": 0.7
        }

        response = requests.post(url, headers=headers, json=payload)

        if response.status_code == 200:
            return str(response.json()["choices"][0]["message"]["content"])
        else:
            print(f"Error GPT: {response.status_code}, {response.text}")
            return None

    def llavaClassifier(self, predictor, imageUrl):
        data = {
            "image": imageUrl,
            "question": self.config.classification_prompt
        }

        return str(predictor.predict(data))

    def solveChallenge(self, images, exampleImage, prompt):
        sess = sagemaker.Session()

        predictor = HuggingFacePredictor(
            endpoint_name=self.config.sagemaker_endpoint,
            sagemaker_session=sess
        )

        exampleClassification = None
        imageClassifications = []

        def classify_example_image(tries):
            nonlocal exampleClassification

            try:
                exampleClassification = self.llavaClassifier(predictor, exampleImage)

                if not exampleClassification and tries < 2:
                    classify_example_image(tries + 1)
            except:
                if tries < 2:
                    classify_example_image(tries + 1)

        def classify_image(image_info, tries):
            nonlocal imageClassifications

            imageUrl = image_info['datapoint_uri']
            imageId = image_info['task_key']

            try:
                predictedClass = self.llavaClassifier(predictor, imageUrl)

                if predictedClass:
                    for i, (key, _) in enumerate(imageClassifications):
                        if key == imageId:
                            imageClassifications[i] = (key, predictedClass)
                            break
                elif tries < 2:
                    classify_image(image_info, tries + 1)
            except:
                if tries < 2:
                    classify_image(image_info, tries + 1)

        threads = []
        for image in images:
            newElement = (image['task_key'], "")
            imageClassifications.append(newElement)

            thread = threading.Thread(target=classify_image, args=(image, 0,))
            threads.append(thread)
            thread.start()

        example_thread = threading.Thread(target=classify_example_image, args=(0,))
        threads.append(example_thread)
        example_thread.start()

        # Await all classifications
        for thread in threads:
            thread.join()
        
        # Assert data
        if not exampleClassification:
            print("Failed to classify example image")
            return None
        if len(imageClassifications) != 9:
            print("Incorrect image count, this error should not happen. Image count is " + str(len(imageClassifications)))
            return None
        misses = 0
        for _, (_, predicted) in enumerate(imageClassifications):
            if predicted == "":
                if misses == 2:
                    print("Failed to classify atleast 3 images")
                    return None
                else:
                    misses += 1

        def gptSolution(tries):
            elements = [f'"{item[1]}"' for item in imageClassifications]
            options = f"[{', '.join(elements)}]"
            actionPrompt = f'The prompt is "{prompt}", and the class of the example image is "{exampleClassification}". The following array contains 9 options for the challenge. Pick the correct solutions and return only an int array that contains the indices of the right answers: {options}'

            try:
                gptResponse = self.askGPT(actionPrompt)
            
                if gptResponse:
                    formatedSolution = formatGptSolution(gptResponse, imageClassifications)

                    if formatedSolution:
                        return formatedSolution
                    elif tries < 2:
                        return gptSolution(tries + 1)
                    else:
                        return None
                elif tries < 2:
                    return gptSolution(tries + 1)
                else:
                    return None
            except:
                if tries < 2:
                    return gptSolution(tries + 1)
                else:
                    return None

        return gptSolution(0)

    # Challenges: returns solution payload

    def solve_image_label_binary():
        pass

    def solve_image_label_area_select():
        pass

    def solve_image_drag_drop():
        pass
    
    # Skips to supported challenge: returns solution payload

    def skip_solver(self):
        if ENABLE_LOGGING:
            print_blue("\n\nSolving with skip method")

        try:
            while self.retries < self.config.max_retries:
                self.retries += 1

                # Get challenge
                self.getCaptcha(
                    Request_Payload(
                        self.encryptionSystem, 
                        self.fingerprint, 
                        self.jwt_token, 
                        HCAP_VERSION, 
                        self.tokenData, 
                        self.encryptionSystem.v1Path, 
                        self.siteKey,
                        self.config.timezone,
                        self.config.site_key_url,
                        self.response,
                        self.e_key
                    ).gen_request_payload()
                )

                # Check one-click
                if self.one_click_token:
                    return None

                # Solve
                if self.response["request_type"] == "image_label_binary":
                    return self.solve_image_label_binary()
                elif self.response["request_type"] == "image_label_area_select":
                    return self.solve_image_label_area_select()
                elif self.response["request_type"] == "image_drag_drop":
                    return self.solve_image_drag_drop()
                
                time.sleep(3)

            print_red("Failed skip solve with no matches")
            return None

        except Exception as e:
            print_red(f'Failed skip solve with {str(e)}')
            return None

    # Returns P1 token
    def solve(self) -> str:
        # try:
            # Sets up cookies + encryption system
            self.session_setup()

            # Set jwt token
            self.postCheckConfig()

            # Get challenge
            self.getCaptcha(
                Request_Payload(
                    self.encryptionSystem, 
                    self.fingerprint, 
                    self.jwt_token, 
                    HCAP_VERSION, 
                    self.tokenData, 
                    self.encryptionSystem.v1Path, 
                    self.siteKey,
                    self.config.timezone,
                    self.config.site_key_url
                ).gen_request_payload()
            )

            # Check one-click
            if self.one_click_token:
                print_green("H-cap solved [ONE-CLICK] -> " + self.one_click_token[:30])
                return self.one_click_token

            # Solve
            if self.response["request_type"] == "image_label_binary":
                solution = self.solve_image_label_binary()
            elif self.response["request_type"] == "image_label_area_select":
                solution = self.solve_image_label_area_select()
            elif self.response["request_type"] == "image_drag_drop":
                solution = self.solve_image_drag_drop()
            else:
                if self.skips < self.config.max_skips:
                    solution = self.skip_solver()

                    # Check one-click
                    if self.one_click_token:
                        print_green("H-cap solved [ONE-CLICK] -> " + self.one_click_token[:30])
                        return self.one_click_token
                else:
                    print("Max skips exceeded")
                    return None
            if not solution:
                return None
            
            # Submit
            result = self.postSubmission(solution)

            if result.get("pass", False):
                print_green("H-cap solved -> " + result['generated_pass_UUID'][:30])
                return result['generated_pass_UUID']
            else:
                print_red("Failed to solve")
                return None

        # except Exception as e:
        #     if self.retries < self.config.max_retries:
        #         self.retries += 1
        #         print(f'Retrying due to: {str(e)}')
        #         return self.solve()
        #     else:
        #         print(f'Exceeded max retries with error: {str(e)}')
        #         return None

# Test

def testSolve():
    config = Config()

    print(
        Solver(
            getProxy(), 
            config.user_agent, 
            config.sec_ch_ua, 
            config.referer
        ).solve()
    )

if __name__ == "__main__":
    testSolve()

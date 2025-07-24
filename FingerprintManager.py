from firebase_admin import credentials, firestore
import firebase_admin
import random
import json
import re
import os

MAX_FINGERPRINTS = 160

# Constants
currentVersionUa = "136"
service_account_path = "misc/service.json"
cache_file_path = "misc/fingerprint_cache.json"

class FpManager:
    def __init__(self, userAgent):
        self.versionUA = currentVersionUa
        try:
            chrome_version = re.search(r"Chrome/(\d+)\.", userAgent)
            if chrome_version:
                self.versionUA = chrome_version.group(1)
        except:
            print("Error FpManager INIT: Version failed parse")
        
        self.db = None
        self._initialize_firebase()
    
    def _initialize_firebase(self):
        """Initialize Firebase connection if not already done"""
        if not firebase_admin._apps:
            cred = credentials.Certificate(service_account_path)
            firebase_admin.initialize_app(cred)
        self.db = firestore.client()
    
    def _load_cache(self):
        """Load fingerprints from local cache file"""
        try:
            if os.path.exists(cache_file_path):
                with open(cache_file_path, 'r') as f:
                    cache_data = json.load(f)
                    version_key = f'fingerprints{self.versionUA}'
                    return cache_data.get(version_key, [])
            return []
        except Exception as e:
            print(f"Warning: Error loading cache: {e}")
            return []
    
    def _save_cache(self, fingerprints):
        """Save fingerprints to local cache file"""
        try:
            # Load existing cache data
            cache_data = {}
            if os.path.exists(cache_file_path):
                with open(cache_file_path, 'r') as f:
                    cache_data = json.load(f)
            
            # Update cache with new fingerprints for this version
            version_key = f'fingerprints{self.versionUA}'
            cache_data[version_key] = fingerprints
            
            # Save back to file
            with open(cache_file_path, 'w') as f:
                json.dump(cache_data, f, indent=2)
            
            print(f"Cached {len(fingerprints)} fingerprints for version {self.versionUA}")
        except Exception as e:
            print(f"Warning: Error saving cache: {e}")
    
    def _fetch_all_fingerprints(self):
        """Fetch all fingerprints from Firebase collection"""
        try:
            collection_name = f'fingerprints{self.versionUA}'
            collection_ref = self.db.collection(collection_name)
            docs = collection_ref.stream()
            
            fingerprints = []
            for doc in docs:
                doc_data = doc.to_dict()
                if 'data' in doc_data:
                    try:
                        fingerprint_data = json.loads(doc_data['data'])

                        if "worker_gpu_vendors" in fingerprint_data["events"] and "Vulkan" not in fingerprint_data["events"]["worker_gpu_vendors"]:
                            fingerprints.append(fingerprint_data)
                    except json.JSONDecodeError as e:
                        print(f"Warning: Invalid JSON in document {doc.id}: {e}")
                else:
                    print(f"Warning: Document {doc.id} missing 'data' field")
            
            print(f"Fetched {len(fingerprints)} fingerprints from Firebase")
            return fingerprints
        except Exception as e:
            print(f"Error fetching fingerprints from Firebase: {e}")
            raise e
    
    def getFingerprint(self, retry=True):
        """Get a random fingerprint, using cache first, then Firebase if needed"""
        # Try to load from cache first
        cached_fingerprints = self._load_cache()
        
        if cached_fingerprints:
            # Return random fingerprint from cache
            return random.choice(cached_fingerprints)
        
        # Cache is empty or doesn't exist, fetch from Firebase
        print("Cache empty or missing, fetching all fingerprints from Firebase...")
        
        try:
            all_fingerprints = self._fetch_all_fingerprints()
            
            if not all_fingerprints:
                raise Exception(f"No fingerprints found in Firebase collection fingerprints{self.versionUA}")
            
            # Save to cache
            self._save_cache(all_fingerprints)
            
            # Return random fingerprint
            return random.choice(all_fingerprints)
            
        except Exception as e:
            if retry:
                print("Warning: Fp attempt 1 failed, retrying")
                return self.getFingerprint(False)
            else:
                raise Exception(f"Failed to get fingerprint: {e}")
    
    def refresh_cache(self):
        """Manually refresh the cache by fetching all fingerprints from Firebase"""
        print("Manually refreshing fingerprint cache...")
        try:
            all_fingerprints = self._fetch_all_fingerprints()
            self._save_cache(all_fingerprints)
            return len(all_fingerprints)
        except Exception as e:
            print(f"Error refreshing cache: {e}")
            raise e

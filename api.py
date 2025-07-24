from flask import Flask, request, jsonify
from google.oauth2 import service_account
from google.cloud import firestore
from Solve import Solver
import time
import os

app = Flask(__name__)

creds = service_account.Credentials.from_service_account_file("misc/service.json")

db = firestore.Client(credentials=creds)

def authUser(api_key):
    try:
        user_doc_ref = db.collection('api_keys').document(api_key)
        user_doc = user_doc_ref.get()
        
        if not user_doc.exists:
            return False
        
        user_data = user_doc.to_dict()

        credits_left = user_data.get('left', 0)

        if credits_left <= 0:
            return False
                
        request_count_ref = db.collection('api_keys').document(api_key)
        request_count_ref.set(
            {'left': firestore.Increment(-1)}, 
            merge=True
        )
        
        return True
    
    except Exception as e:
        return False

# Main

@app.route('/solve', methods=['GET', 'POST'])
def solve():
    try:
        if request.method == 'GET':
            params = request.args
        else:
            params = request.json if request.is_json else request.form
        
        proxy = params.get('proxy')
        referer = params.get('referer')
        ua = params.get('ua')
        sec_ch_ua = params.get('secChUa')
        key = params.get('key')
        
        if not all([proxy, referer, ua, sec_ch_ua, key]):
            return jsonify({"error": "Missing required parameters"}), 400
        
        if not authUser(key):
            return jsonify({"error": "Not authorized"}), 400
        
        start_time = time.time()
        
        P1_token = Solver(
            proxy, 
            ua, 
            sec_ch_ua, 
            referer
        ).solve()

        end_time = time.time()
        
        if not P1_token:
            return jsonify({"error": "An error occured"}), 400

        result = {
            "token": P1_token,
            "time_taken": round(end_time - start_time, 4)
        }
        
        return jsonify(result), 200
        
    except Exception as e:
        print("Exception caught in Solve: " + str(e))
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

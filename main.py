import os
import uuid
from flask import Flask, make_response, request, jsonify, send_from_directory
from flask_restful import Api, Resource
from flask_pymongo import PyMongo
import random
import string
from config import MONGO_URI
from flask_cors import CORS
from werkzeug.utils import secure_filename
from bson import json_util
from datetime import datetime

app = Flask(__name__)
CORS(app)

app.config['MONGO_URI'] = MONGO_URI
api = Api(app)
mongo = PyMongo(app)
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


class ClientRegister(Resource):
    def post(self):
        data = request.get_json()
        client_id = self.generate_client_id()

        client_data = {
            'client_id': client_id,
            'name': data['name'],
            "user_name":data['user_name'],
            "password":data['password'],
            'school': data['school'],
            'place': data['place']
        }
        mongo.db.clients.insert_one(client_data)

        return jsonify(client_id=client_id)

    def generate_client_id(self):
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))
    
class ClientLogin(Resource):
    def post(self):
        data = request.get_json()
        user_data = mongo.db.clients.find_one({'user_name': data['user_name'], 'password': data['password']})

        if user_data:
            return jsonify(client_id=user_data['client_id'])
        else:
            return jsonify(message='Invalid username or password'), 401
        
class UserRegister(Resource):
    def post(self):
        data = request.get_json()

        user_id = str(uuid.uuid4())

        user_data = {
            'user_id': user_id,
            'user_name': data['user_name'],
            'password': data['password']
        }
        mongo.db.users.insert_one(user_data)
        return jsonify(user_id=user_id)
    
class UserLogin(Resource):
    def post(self):
        data = request.get_json()

        user_data = mongo.db.users.find_one({'user_name': data['user_name'], 'password': data['password']})

        if user_data:
            return jsonify(user_id=user_data['user_id'])
        else:
            return jsonify(message='Invalid username or password'), 401
        
class PrintAd(Resource):
    def post(self):
        data = request.get_json()
        current_datetime = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        print_ad_data = {
            'user_id': data['user_id'],
            'client_id': data['client_id'],
            'ad_id': data['ad_id'],
            'Amount_paid': data['Amount_paid'],
            'files': data.get('files', []),
            'status': "'status', 'Pending'",  # Default status to 'Pending' if not provided
            'created_at': current_datetime
        }
        mongo.db.printad.insert_one(print_ad_data) 
        return jsonify(message="Print ad details successfully added")
    
class updateStatus(Resource):
    def put(self,ad_id):
        query = {'ad_id': ad_id}
        update = {'$set': {'status': 'Done'}}
        result = mongo.db.printad.update_one(query, update)
        if result.modified_count > 0:
            return jsonify(message=f"Status for ad with app ID {ad_id} set to 'Done'")
        else:
            return jsonify(message=f"No ad found with app ID {ad_id}")
        
class client_Tarif(Resource):
    def post(self,client_id):
        data = request.get_json()
        tarif = {
            'client_id': client_id,
            "Black_by_qty" :data['Black_by_qty'],
            "Color_by_qty":data['Color_by_qty'],
            "binding_soft_qty":data['binding_soft_qty'],
            "binfing_hard_qty": data['binfing_hard_qty'],
        }
        mongo.db.tarif.update_one(tarif) 
        return jsonify(message="Print ad details successfully added")

class VisualByClient(Resource):
    def get(self, client_id):
        ads_cursor = mongo.db.printad.find({'client_id': client_id})
        ads_list = [{'Amount_paid': ad['Amount_paid'], 'created_at': ad['created_at']} for ad in ads_cursor]
        response = make_response(ads_list)
        response.headers['Content-Type'] = 'application/json'
        return response

class PrintAdsByClient(Resource):
    def get(self, client_id):
        ads = mongo.db.printad.find({'client_id': client_id})
        ads_list = list(ads)
        for ad in ads_list:
            ad['_id'] = str(ad['_id'])
        ads_dict = {ad['_id']: ad for ad in ads_list}
        return jsonify(ads_dict)
class PrintAdsByUser(Resource):
    def get(self, user_id):
        ads = mongo.db.printad.find({'user_id': user_id})
        ads_list = list(ads)
        for ad in ads_list:
            ad['_id'] = str(ad['_id'])
        ads_dict = {ad['_id']: ad for ad in ads_list}
        return jsonify(ads_dict)
class FileUpload(Resource):
    def post(self):
        if not os.path.exists(UPLOAD_FOLDER):
            os.makedirs(UPLOAD_FOLDER)
        files = request.files.getlist('files')
        response_data = {}
        for file in files:
            new_filename = str(uuid.uuid4()) + os.path.splitext(file.filename)[-1]
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(new_filename))
            file.save(file_path)
            response_data[file.filename] = new_filename
        return jsonify(response_data)
class fileget(Resource):
    def get(self, filename):
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        if os.path.exists(file_path):
            try:
                return send_from_directory(app.config['UPLOAD_FOLDER'], filename)
            except FileNotFoundError:
                return jsonify({'error': 'File not found'}), 404
        else:
            return jsonify({'error': 'File not found'}), 404

api.add_resource(fileget, '/getfile/<string:filename>')
api.add_resource(FileUpload, '/upload')
api.add_resource(PrintAd, '/printad')
api.add_resource(PrintAdsByClient, '/printad/<string:client_id>')
api.add_resource(PrintAdsByUser, '/printad_user/<string:user_id>')
api.add_resource(ClientRegister, '/clientRegister')
api.add_resource(ClientLogin, '/clientLogin')
api.add_resource(UserRegister, '/UserRegister')
api.add_resource(UserLogin, '/UserLogin')
api.add_resource(VisualByClient, '/visualbyclient/<string:client_id>')
api.add_resource(client_Tarif, '/client_tarif/<string:client_id>')
api.add_resource(updateStatus, '/updatestatus/<string:ad_id>')

if __name__ == '__main__':
    app.run(debug=True, port=os.getenv("PORT", default=5000))

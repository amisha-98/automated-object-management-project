from flask import Flask, request, jsonify
from flask_cors import CORS
from google.cloud import storage, pubsub_v1
from werkzeug.utils import secure_filename
import os
import json
from datetime import datetime, timedelta

app = Flask(__name__)
CORS(app)

# GCP Configuration
PROJECT_ID = "atom-project-438605"
storage_client = storage.Client()
publisher = pubsub_v1.PublisherClient()
topic_path = publisher.topic_path(PROJECT_ID, 'file-uploads')

# Bucket Configuration
BUCKET_MAPPING = {
    'jpg': 'atom-jpg-bucket',
    'jpeg': 'atom-jpeg-bucket',
    'mp3': 'atom-mp3-bucket',
    'mp4': 'atom-mp4-bucket',
    'gif': 'atom-gif-bucket',
    'pdf': 'atom-pdf-bucket',
    'raw': 'atom-raw-bucket',
    'txt': 'atom-txt-bucket',
    'png': 'atom-png-bucket'
}

ALLOWED_EXTENSIONS = set(BUCKET_MAPPING.keys())

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_bucket_name(filename):
    if '.' not in filename:
        return 'miscellaneous-files-bucket'
    extension = filename.rsplit('.', 1)[1].lower()
    return BUCKET_MAPPING.get(extension, 'miscellaneous-files-bucket')

def generate_signed_url(bucket_name, blob_name):
    try:
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(blob_name)
        
        # Generate signed URL with maximum expiration (7 days is the maximum allowed)
        url = blob.generate_signed_url(
            version="v4",
            expiration=timedelta(days=7),
            method="GET",
        )
        
        if not url:
            raise Exception("Failed to generate signed URL")
            
        return url
    except Exception as e:
        print(f"Error generating signed URL: {str(e)}")
        raise Exception(f"Error generating signed URL: {str(e)}")

def publish_upload_event(upload_info):
    try:
        upload_info['uploaded_at'] = upload_info['uploaded_at'].isoformat()
        message_json = json.dumps(upload_info)
        message_bytes = message_json.encode('utf-8')
        
        publish_future = publisher.publish(topic_path, data=message_bytes)
        publish_future.result()
        return True
    except Exception as e:
        print(f"Error publishing message: {str(e)}")
        return False

@app.route('/upload', methods=['POST'])
def upload_file():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file part'}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        filename = secure_filename(file.filename)
        bucket_name = get_bucket_name(filename)
        
        try:
            bucket = storage_client.bucket(bucket_name)
            blob = bucket.blob(filename)
            
            # Upload file
            blob.upload_from_file(
                file,
                content_type=file.content_type,
                num_retries=3
            )
            
            # Generate signed URL
            try:
                signed_url = generate_signed_url(bucket_name, filename)
            except Exception as url_error:
                return jsonify({'error': str(url_error)}), 500
            
            upload_info = {
                'filename': filename,
                'bucket': bucket_name,
                'content_type': file.content_type,
                'size': blob.size,
                'uploaded_at': datetime.utcnow(),
                'signed_url': signed_url
            }
            
            publish_success = publish_upload_event(upload_info)
            
            return jsonify({
                'message': 'File uploaded successfully',
                'bucket': bucket_name,
                'filename': filename,
                'signed_url': signed_url,
                'event_published': publish_success
            }), 200
            
        except Exception as e:
            return jsonify({'error': f'Error uploading to GCS: {str(e)}'}), 500
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat()
    })

@app.route('/buckets', methods=['GET'])
def get_buckets():
    try:
        buckets = {
            'supported': BUCKET_MAPPING,
            'miscellaneous': 'miscellaneous-files-bucket'
        }
        return jsonify(buckets), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/', methods=['GET'])
def home():
    return jsonify({
        'message': 'ATOM Backend Server is running',
        'available_endpoints': {
            'health_check': '/health',
            'file_upload': '/upload',
            'bucket_list': '/buckets'
        }
    })

if __name__ == '__main__':
    if not os.environ.get('GOOGLE_APPLICATION_CREDENTIALS'):
        print("Warning: GOOGLE_APPLICATION_CREDENTIALS environment variable not set")
    
    debug_mode = os.environ.get('FLASK_ENV') == 'development'
    
    app.run(
        host='0.0.0.0',
        port=int(os.environ.get('PORT', 5000)),
        debug=debug_mode
    )
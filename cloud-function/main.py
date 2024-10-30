from google.cloud import storage
from google.cloud import pubsub_v1
import json
import functions_framework
import logging
import os
from datetime import datetime

# Initialize clients
storage_client = storage.Client()
publisher = pubsub_v1.PublisherClient()

# Configure logging
logging.basicConfig(level=logging.INFO)

# Define bucket mapping
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

@functions_framework.http
def process_upload(request):
    """
    HTTP Cloud Function to handle file uploads.
    Args:
        request (flask.Request): The request object
    Returns:
        The response text, or any set of values that can be turned into a
        Response object using make_response
    """
    try:
        # Check if file is present in request
        if 'file' not in request.files:
            return {'error': 'No file provided'}, 400

        uploaded_file = request.files['file']
        if uploaded_file.filename == '':
            return {'error': 'No file selected'}, 400

        # Get file extension and determine bucket
        file_extension = uploaded_file.filename.rsplit('.', 1)[1].lower()
        bucket_name = BUCKET_MAPPING.get(file_extension, 'miscellaneous-files-bucket')

        # Generate unique filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        safe_filename = f"{timestamp}_{uploaded_file.filename}"

        # Get bucket and create blob
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(safe_filename)

        # Upload file
        blob.upload_from_string(
            uploaded_file.read(),
            content_type=uploaded_file.content_type
        )

        # Prepare message for Pub/Sub
        message_data = {
            'filename': safe_filename,
            'original_filename': uploaded_file.filename,
            'bucket': bucket_name,
            'content_type': uploaded_file.content_type,
            'size': blob.size,
            'upload_time': timestamp
        }

        # Publish message to Pub/Sub
        project_id = os.getenv('PROJECT_ID')
        topic_path = publisher.topic_path(project_id, 'file-uploads')
        
        # Convert message data to JSON string and encode
        message_str = json.dumps(message_data)
        publisher.publish(topic_path, message_str.encode('utf-8'))

        # Log the successful upload
        logging.info(f"File {safe_filename} uploaded to {bucket_name}")

        # Return success response
        return {
            'message': 'File uploaded successfully',
            'bucket': bucket_name,
            'filename': safe_filename,
            'metadata': message_data
        }, 200

    except Exception as e:
        # Log the error
        logging.error(f"Error processing upload: {str(e)}")
        return {'error': str(e)}, 500

@functions_framework.cloud_event
def process_pubsub_message(cloud_event):
    """
    Cloud Function triggered by Pub/Sub message.
    Args:
        cloud_event (CloudEvent): The CloudEvent that triggered this function
    """
    try:
        # Extract message data
        pubsub_message = json.loads(cloud_event.data["message"]["data"])
        
        # Log file processing
        logging.info(f"Processing file: {pubsub_message['filename']}")
        
        # Get file metadata
        bucket_name = pubsub_message['bucket']
        filename = pubsub_message['filename']
        
        # Get bucket and blob
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(filename)
        
        # Add metadata to the file
        metadata = {
            'upload_time': pubsub_message['upload_time'],
            'original_filename': pubsub_message['original_filename'],
            'content_type': pubsub_message['content_type'],
            'processed': 'true'
        }
        blob.metadata = metadata
        blob.patch()
        
        logging.info(f"Successfully processed file {filename} in bucket {bucket_name}")
        
    except Exception as e:
        logging.error(f"Error processing message: {str(e)}")
        raise
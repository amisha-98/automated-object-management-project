# ATOM (Automated Object Management) Project

A file management system that automatically sorts uploaded files into appropriate Google Cloud Storage buckets based on their file types.

## Setup Instructions
1. Clone the repository
2. Set up GCP credentials
3. Install dependencies
4. Start the application

## Dependencies
- Frontend: React.js
- Backend: Flask
- Cloud: Google Cloud Storage, Google Cloud Functions, Google CLoud Pub/Sub, and Cloud IAM (for authentication) 

### Frontend
1. cd frontend
2. npm install
3. npm start

### Backend
1. cd backend
2. python -m venv venv
3. source venv/bin/activate
4. pip install -r requirements.txt
5. Add your service-account.json file
6. python app.py

### Cloud
1. Install Google Cloud SDK
2. Create a new project
3. Set project ID
4. Enable required APIs
5. Create GCS buckets
6. Create Pub/Sub topic
import React, { useState, useRef } from 'react';
import { Upload, CheckCircle, AlertCircle } from 'lucide-react';

const FileUpload = () => {
  const [selectedFile, setSelectedFile] = useState(null);
  const [uploadStatus, setUploadStatus] = useState('');
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [signedUrl, setSignedUrl] = useState('');
  const fileInputRef = useRef(null);
  
  const handleFileSelect = (event) => {
    const file = event.target.files[0];
    if (file) {
      setSelectedFile(file);
      setUploadStatus('');
      setUploadProgress(0);
      setSignedUrl('');
    }
  };

  const handleUpload = async () => {
    if (!selectedFile) {
      setUploadStatus('Please select a file');
      return;
    }

    const formData = new FormData();
    formData.append('file', selectedFile);

    try {
      setUploading(true);
      setUploadProgress(0);

      // Create XMLHttpRequest to track upload progress
      const xhr = new XMLHttpRequest();
      
      // Setup Promise to handle the upload
      const uploadPromise = new Promise((resolve, reject) => {
        xhr.upload.addEventListener('progress', (event) => {
          if (event.lengthComputable) {
            const progress = Math.round((event.loaded / event.total) * 100);
            setUploadProgress(progress);
          }
        });

        xhr.addEventListener('load', () => {
          if (xhr.status >= 200 && xhr.status < 300) {
            resolve(JSON.parse(xhr.responseText));
          } else {
            reject(new Error(`Upload failed with status ${xhr.status}`));
          }
        });

        xhr.addEventListener('error', () => {
          reject(new Error('Upload failed'));
        });
      });

      // Start the upload
      xhr.open('POST', 'http://localhost:5000/upload');
      xhr.send(formData);

      const response = await uploadPromise;
      
      setUploadStatus('File uploaded successfully!');
      setSignedUrl(response.signed_url);
    } catch (error) {
      setUploadStatus(`Upload failed: ${error.message}`);
      setUploadProgress(0);
    } finally {
      setUploading(false);
    }
  };

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  return (
    <div className="max-w-2xl mx-auto p-8 bg-gradient-to-br from-blue-50 to-white rounded-xl shadow-lg">
      <h1 className="text-3xl font-bold mb-8 text-center bg-gradient-to-r from-blue-600 to-purple-600 text-transparent bg-clip-text">
        Automated Object Management (ATOM) System
      </h1>

      <div 
        className={`border-3 border-dashed rounded-xl p-10 mb-6 text-center cursor-pointer
          transition-all duration-300 transform hover:scale-[1.02]
          ${uploading ? 'border-blue-400 bg-blue-50' : 'border-gray-300 hover:border-blue-400 hover:bg-blue-50'}`}
        onClick={() => fileInputRef.current?.click()}
      >
        <Upload 
          className={`mx-auto mb-4 transition-colors duration-300 ${
            uploading ? 'text-blue-500' : 'text-gray-400'
          }`} 
          size={48} 
        />
        <input
          type="file"
          onChange={handleFileSelect}
          className="hidden"
          ref={fileInputRef}
        />
        <p className="text-lg text-gray-600 mb-2">
          {selectedFile ? selectedFile.name : 'Click or drag files to upload'}
        </p>
        {selectedFile && (
          <p className="text-sm text-gray-500">
            Size: {formatFileSize(selectedFile.size)}
          </p>
        )}
      </div>

      {selectedFile && (
        <div className="mb-6">
          <div className="flex justify-between mb-2">
            <span className="text-sm text-gray-600">Upload Progress</span>
            <span className="text-sm font-medium text-blue-600">{uploadProgress}%</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-3">
            <div 
              className="bg-gradient-to-r from-blue-500 to-purple-500 rounded-full h-3 transition-all duration-300 ease-out"
              style={{ width: `${uploadProgress}%` }}
            >
            </div>
          </div>
        </div>
      )}

      <button
        onClick={handleUpload}
        disabled={!selectedFile || uploading}
        className={`w-full py-3 px-4 rounded-xl text-white font-medium text-lg
          transition-all duration-300 transform hover:scale-[1.02] hover:shadow-lg
          ${!selectedFile || uploading
            ? 'bg-gray-400 cursor-not-allowed'
            : 'bg-gradient-to-r from-blue-500 to-purple-500 hover:from-blue-600 hover:to-purple-600'
          }`}
      >
        {uploading ? (
          <div className="flex items-center justify-center">
            <span className="animate-pulse">Uploading...</span>
          </div>
        ) : 'Upload File'}
      </button>

      {uploadStatus && (
        <div className={`mt-4 p-4 rounded-xl flex items-center transition-all duration-300 ${
          uploadStatus.includes('successfully') 
            ? 'bg-green-100 text-green-700'
            : 'bg-red-100 text-red-700'
        }`}>
          {uploadStatus.includes('successfully') ? (
            <CheckCircle className="mr-2 animate-bounce" size={20} />
          ) : (
            <AlertCircle className="mr-2 animate-pulse" size={20} />
          )}
          {uploadStatus}
        </div>
      )}

      {signedUrl && (
        <div className="mt-4 p-4 bg-blue-50 rounded-xl">
          <p className="text-sm text-blue-700">
            File uploaded successfully! You can access it using this signed URL:
          </p>
          <a 
            href={signedUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="text-blue-600 hover:text-blue-800 underline text-sm mt-2 block"
          >
            View uploaded file
          </a>
        </div>
      )}
    </div>
  );
};

export default FileUpload;
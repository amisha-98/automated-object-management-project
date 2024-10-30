import React from 'react';
import './index.css';
import './App.css';
import FileUpload from './components/FileUpload'; // Adjust the path based on your file location

function App() {
  return (
    <div className="min-h-screen bg-gray-100 py-8">
      <FileUpload />
    </div>
  );
}

export default App;

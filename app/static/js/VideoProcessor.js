import React, { useState, useCallback } from 'react';
import { Upload, Link, Globe2, Settings, Cog, FileVideo } from 'lucide-react';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend } from 'recharts';

const VideoProcessor = () => {
  const [activeTab, setActiveTab] = useState('upload');
  const [processing, setProcessing] = useState(false);
  const [progress, setProgress] = useState(0);
  const [results, setResults] = useState([]);
  const [error, setError] = useState(null);

  const processVideo = useCallback(async (data) => {
    setProcessing(true);
    setProgress(0);
    setError(null);

    try {
      const response = await fetch('/api/process', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
      });

      const reader = response.body.getReader();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += new TextDecoder().decode(value);
        const lines = buffer.split('\n');
        buffer = lines.pop();

        for (const line of lines) {
          if (!line.trim()) continue;
          const message = JSON.parse(line);
          
          switch (message.status) {
            case 'processing':
              setProgress(message.progress || 0);
              break;
            case 'clip_ready':
              setResults(prev => [message.data.clip, ...prev]);
              break;
            case 'error':
              setError(message.message);
              break;
          }
        }
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setProcessing(false);
    }
  }, []);

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Navigation */}
      <nav className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <FileVideo className="h-8 w-8 text-blue-500" />
              <span className="ml-2 text-xl font-semibold">Video Analyzer Pro</span>
            </div>
            <div className="flex items-center space-x-4">
              <Settings className="h-6 w-6 text-gray-500 cursor-pointer hover:text-gray-700" />
              <Globe2 className="h-6 w-6 text-gray-500 cursor-pointer hover:text-gray-700" />
            </div>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        {/* Processing Options */}
        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <div className="flex space-x-4 mb-6">
            <button
              className={`flex items-center px-4 py-2 rounded-md ${
                activeTab === 'upload' ? 'bg-blue-500 text-white' : 'bg-gray-100'
              }`}
              onClick={() => setActiveTab('upload')}
            >
              <Upload className="h-5 w-5 mr-2" />
              Upload Video
            </button>
            <button
              className={`flex items-center px-4 py-2 rounded-md ${
                activeTab === 'url' ? 'bg-blue-500 text-white' : 'bg-gray-100'
              }`}
              onClick={() => setActiveTab('url')}
            >
              <Link className="h-5 w-5 mr-2" />
              Video URL
            </button>
          </div>

          {activeTab === 'upload' ? (
            <div className="space-y-4">
              <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center">
                <input
                  type="file"
                  className="hidden"
                  accept="video/*"
                  onChange={(e) => {
                    const file = e.target.files[0];
                    if (file) {
                      const formData = new FormData();
                      formData.append('video', file);
                      processVideo({ type: 'upload', data: formData });
                    }
                  }}
                  id="video-upload"
                />
                <label htmlFor="video-upload" className="cursor-pointer">
                  <Upload className="mx-auto h-12 w-12 text-gray-400" />
                  <p className="mt-1 text-sm text-gray-600">
                    Click to upload or drag and drop
                  </p>
                </label>
              </div>
            </div>
          ) : (
            <div className="space-y-4">
              <input
                type="url"
                placeholder="Enter video URL"
                className="w-full px-4 py-2 border border-gray-300 rounded-md"
                onKeyPress={(e) => {
                  if (e.key === 'Enter') {
                    processVideo({ type: 'url', data: { url: e.target.value } });
                  }
                }}
              />
            </div>
          )}
        </div>

        {/* Processing Status */}
        {processing && (
          <div className="bg-white rounded-lg shadow p-6 mb-6">
            <div className="space-y-4">
              <div className="h-2 bg-gray-200 rounded">
                <div
                  className="h-full bg-blue-500 rounded transition-all duration-300"
                  style={{ width: `${progress}%` }}
                />
              </div>
              <p className="text-center text-sm text-gray-600">
                Processing video... {progress}%
              </p>
            </div>
          </div>
        )}

        {/* Error Display */}
        {error && (
          <Alert variant="destructive">
            <AlertTitle>Error</AlertTitle>
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        {/* Results */}
        <div className="space-y-6">
          {results.map((result, index) => (
            <div key={index} className="bg-white rounded-lg shadow p-6">
              <div className="aspect-w-16 aspect-h-9 mb-4">
                <video
                  src={result.videoUrl}
                  controls
                  className="rounded-lg w-full"
                />
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <h3 className="text-lg font-semibold mb-2">Speech Analysis</h3>
                  <p className="text-gray-700">{result.speech_text}</p>
                  <p className="text-sm text-gray-500 mt-2">
                    Translation: {result.speech_translated}
                  </p>
                </div>
                
                <div>
                  <h3 className="text-lg font-semibold mb-2">Visual Analysis</h3>
                  <div className="space-y-2">
                    {result.image_recognition?.detections.map((detection, idx) => (
                      <div
                        key={idx}
                        className="flex justify-between items-center bg-gray-50 p-2 rounded"
                      >
                        <span>{detection.class}</span>
                        <span className="text-sm text-gray-500">
                          {Math.round(detection.confidence * 100)}%
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              {/* Analytics Chart */}
              <div className="mt-6">
                <h3 className="text-lg font-semibold mb-4">Detection Timeline</h3>
                <LineChart width={600} height={200} data={result.detectionData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="timestamp" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Line
                    type="monotone"
                    dataKey="confidence"
                    stroke="#8884d8"
                    activeDot={{ r: 8 }}
                  />
                </LineChart>
              </div>
            </div>
          ))}
        </div>
      </main>
    </div>
  );
};

export default VideoProcessor;
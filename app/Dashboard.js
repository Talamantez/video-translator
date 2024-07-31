import React, { useState, useEffect } from 'react';
import { BarChart, Bar, XAxis, YAxis, ResponsiveContainer } from 'recharts';
import { Card, CardHeader, CardContent } from '@/components/ui/card';
import MovieEmojiGame from './MovieEmojiGame';

const generateData = () => [...Array(12)].map((_, i) => ({
  month: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'][i],
  revenue: Math.floor(Math.random() * 5000) + 1000
}));

const MetricCard = ({ title, value, change }) => (
  <Card>
    <CardHeader>{title}</CardHeader>
    <CardContent>
      <div className="text-2xl font-bold">{value}</div>
      <div className={`text-sm ${change >= 0 ? 'text-green-500' : 'text-red-500'}`}>
        {change >= 0 ? '↑' : '↓'} {Math.abs(change)}%
      </div>
    </CardContent>
  </Card>
);

const Dashboard = () => {
  const [data, setData] = useState(generateData());
  const [isProcessing, setIsProcessing] = useState(false);
  const [showGame, setShowGame] = useState(false);

  useEffect(() => {
    const intervalId = setInterval(() => {
      setData(generateData());
    }, 5000);

    return () => clearInterval(intervalId);
  }, []);

  const handleProcessVideo = () => {
    setIsProcessing(true);
    setShowGame(true);
    // Simulating video processing
    setTimeout(() => {
      setIsProcessing(false);
      setShowGame(false);
    }, 30000); // 30 seconds simulation
  };

  return (
    <div className="p-4">
      <h1 className="text-2xl font-bold mb-4">Video Analysis Dashboard</h1>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
        <MetricCard title="Total Videos" value="1,234" change={5.7} />
        <MetricCard title="Processing Time" value="2.3s" change={-3.2} />
        <MetricCard title="Accuracy" value="98.6%" change={1.5} />
      </div>
      <div className="mb-4">
        <h2 className="text-xl font-semibold mb-2">Monthly Processed Videos</h2>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={data}>
            <XAxis dataKey="month" />
            <YAxis />
            <Bar dataKey="revenue" fill="#8884d8" />
          </BarChart>
        </ResponsiveContainer>
      </div>
      <div className="mb-4">
        <button
          onClick={handleProcessVideo}
          disabled={isProcessing}
          className="bg-blue-500 text-white px-4 py-2 rounded disabled:bg-gray-400"
        >
          {isProcessing ? 'Processing...' : 'Process Video'}
        </button>
      </div>
      <MovieEmojiGame isVisible={showGame} onClose={() => setShowGame(false)} />
    </div>
  );
};

export default Dashboard;
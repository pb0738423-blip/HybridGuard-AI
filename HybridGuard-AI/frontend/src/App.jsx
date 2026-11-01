import React, { useState } from 'react';
import Navbar from './components/Navbar';
import Footer from './components/Footer';
import Dashboard from './pages/Dashboard';
import NewsDetection from './pages/NewsDetection';
import FactChecking from './pages/FactChecking';
import VideoAnalysis from './pages/VideoAnalysis';
import ModelDashboard from './pages/ModelDashboard';
import LiveSpeech from './pages/LiveSpeech';
import AboutMethodology from './pages/AboutMethodology';

export default function App() {
  const [activeTab, setActiveTab] = useState('dashboard');

  return (
    <div className="min-h-screen flex flex-col bg-slate-950 text-slate-100">
      {/* Global Navigation Bar */}
      <Navbar activeTab={activeTab} setActiveTab={setActiveTab} />

      {/* Main Application Container */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 sm:py-10">
        {activeTab === 'dashboard' && <Dashboard onNavigate={setActiveTab} />}
        {activeTab === 'news' && <NewsDetection />}
        {activeTab === 'factcheck' && <FactChecking />}
        {activeTab === 'video' && <VideoAnalysis />}
        {activeTab === 'models' && <ModelDashboard />}
        {activeTab === 'speech' && <LiveSpeech />}
        {activeTab === 'about' && <AboutMethodology />}
      </main>

      {/* Global Footer */}
      <Footer onNavigate={setActiveTab} />
    </div>
  );
}


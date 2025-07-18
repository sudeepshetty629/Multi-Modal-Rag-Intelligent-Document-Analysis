import React, { useState, useEffect } from 'react';
import { Toaster } from 'react-hot-toast';
import Sidebar from './components/Sidebar';
import MainChat from './components/MainChat';
import NeuralBackground from './components/NeuralBackground';
import LoadingScreen from './components/LoadingScreen';
import APIKeyModal from './components/APIKeyModal';
import { useStore } from './store/useStore';
import './App.css';

function App() {
  const [isLoading, setIsLoading] = useState(true);
  const [showAPIModal, setShowAPIModal] = useState(false);
  const { initialize, isInitialized } = useStore();

  useEffect(() => {
    const initializeApp = async () => {
      try {
        await initialize();
        setTimeout(() => setIsLoading(false), 2000);
      } catch (error) {
        console.error('Failed to initialize app:', error);
        setIsLoading(false);
      }
    };

    initializeApp();
  }, [initialize]);

  if (isLoading) {
    return <LoadingScreen />;
  }

  return (
    <div className="App h-screen bg-neural-900 text-white overflow-hidden">
      <Toaster 
        position="top-right"
        toastOptions={{
          style: {
            background: '#1e293b',
            color: '#f1f5f9',
            border: '1px solid #334155',
          },
        }}
      />
      
      <NeuralBackground />
      
      <div className="relative z-10 flex h-full">
        <Sidebar onOpenAPIModal={() => setShowAPIModal(true)} />
        <MainChat />
      </div>

      {showAPIModal && (
        <APIKeyModal onClose={() => setShowAPIModal(false)} />
      )}
    </div>
  );
}

export default App;
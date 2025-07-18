import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { XMarkIcon, KeyIcon, CheckCircleIcon } from '@heroicons/react/24/outline';
import { useStore } from '../store/useStore';
import toast from 'react-hot-toast';

const APIKeyModal = ({ onClose }) => {
  const { apiKey, setApiKey, testAI } = useStore();
  const [tempApiKey, setTempApiKey] = useState(apiKey);
  const [isTestingConnection, setIsTestingConnection] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState(null);

  const handleSave = () => {
    setApiKey(tempApiKey);
    toast.success('API key saved successfully!');
    onClose();
  };

  const handleTestConnection = async () => {
    if (!tempApiKey.trim()) {
      toast.error('Please enter an API key first');
      return;
    }

    setIsTestingConnection(true);
    setConnectionStatus(null);

    try {
      // Save temporarily to test
      setApiKey(tempApiKey);
      await testAI();
      setConnectionStatus('success');
      toast.success('Connection successful!');
    } catch (error) {
      setConnectionStatus('error');
      toast.error('Connection failed. Please check your API key.');
    } finally {
      setIsTestingConnection(false);
    }
  };

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4"
        onClick={onClose}
      >
        <motion.div
          initial={{ scale: 0.9, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          exit={{ scale: 0.9, opacity: 0 }}
          className="bg-neural-800 rounded-2xl p-6 w-full max-w-md border border-neural-700/50"
          onClick={(e) => e.stopPropagation()}
        >
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 bg-accent-500/20 rounded-xl flex items-center justify-center">
                <KeyIcon className="w-6 h-6 text-accent-500" />
              </div>
              <div>
                <h3 className="text-xl font-display font-bold text-white">API Settings</h3>
                <p className="text-neural-400 text-sm">Configure your Gemini API key</p>
              </div>
            </div>
            <button
              onClick={onClose}
              className="p-2 hover:bg-neural-700/50 rounded-lg transition-colors"
            >
              <XMarkIcon className="w-5 h-5 text-neural-400" />
            </button>
          </div>

          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-neural-300 mb-2">
                Google Gemini API Key
              </label>
              <div className="relative">
                <input
                  type="password"
                  value={tempApiKey}
                  onChange={(e) => setTempApiKey(e.target.value)}
                  placeholder="Enter your Gemini API key..."
                  className="w-full p-3 bg-neural-900/50 border border-neural-700/50 rounded-xl text-white placeholder-neural-500 focus:border-accent-500 focus:outline-none focus:ring-2 focus:ring-accent-500/20 pr-12"
                />
                {connectionStatus === 'success' && (
                  <CheckCircleIcon className="absolute right-3 top-3 w-6 h-6 text-green-500" />
                )}
              </div>
            </div>

            <div className="bg-neural-900/50 rounded-xl p-4">
              <h4 className="text-sm font-medium text-neural-300 mb-2">How to get your API key:</h4>
              <ol className="text-sm text-neural-400 space-y-1">
                <li>1. Go to <a href="https://aistudio.google.com/app/apikey" target="_blank" rel="noopener noreferrer" className="text-accent-400 hover:text-accent-300">Google AI Studio</a></li>
                <li>2. Create a new API key</li>
                <li>3. Copy and paste it above</li>
              </ol>
            </div>

            <div className="flex space-x-3">
              <button
                onClick={handleTestConnection}
                disabled={isTestingConnection || !tempApiKey.trim()}
                className="flex-1 p-3 bg-neural-700/50 hover:bg-neural-700/70 disabled:bg-neural-700/20 disabled:cursor-not-allowed rounded-xl text-white text-sm font-medium transition-colors flex items-center justify-center space-x-2"
              >
                {isTestingConnection ? (
                  <>
                    <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                    <span>Testing...</span>
                  </>
                ) : (
                  <span>Test Connection</span>
                )}
              </button>
              
              <button
                onClick={handleSave}
                disabled={!tempApiKey.trim()}
                className="flex-1 p-3 bg-accent-500 hover:bg-accent-600 disabled:bg-accent-500/50 disabled:cursor-not-allowed rounded-xl text-white text-sm font-medium transition-colors"
              >
                Save API Key
              </button>
            </div>
          </div>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
};

export default APIKeyModal;
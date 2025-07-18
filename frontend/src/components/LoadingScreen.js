import React from 'react';
import { motion } from 'framer-motion';

const LoadingScreen = () => {
  return (
    <div className="h-screen bg-neural-900 flex items-center justify-center">
      <div className="text-center">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
          className="mb-8"
        >
          <div className="w-20 h-20 mx-auto mb-6 relative">
            <div className="absolute inset-0 rounded-full border-4 border-neural-700"></div>
            <div className="absolute inset-0 rounded-full border-4 border-accent-500 border-t-transparent animate-spin"></div>
            <div className="absolute inset-2 rounded-full bg-accent-500/10 animate-pulse"></div>
          </div>
          
          <h1 className="text-3xl font-display font-bold text-white mb-2">
            Multi-Modal RAG
          </h1>
          <p className="text-neural-400 text-lg font-medium">
            Intelligent Document Analysis System
          </p>
        </motion.div>
        
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.5, duration: 0.8 }}
          className="space-y-4"
        >
          <div className="flex items-center justify-center space-x-2">
            <div className="w-2 h-2 bg-accent-500 rounded-full animate-bounce"></div>
            <div className="w-2 h-2 bg-accent-500 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
            <div className="w-2 h-2 bg-accent-500 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
          </div>
          
          <p className="text-neural-500 text-sm">
            Initializing AI systems...
          </p>
        </motion.div>
      </div>
    </div>
  );
};

export default LoadingScreen;
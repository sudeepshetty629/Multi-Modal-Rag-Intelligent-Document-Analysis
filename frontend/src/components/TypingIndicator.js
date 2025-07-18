import React from 'react';
import { motion } from 'framer-motion';
import { SparklesIcon } from '@heroicons/react/24/outline';

const TypingIndicator = () => {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
      className="flex items-start space-x-4"
    >
      <div className="w-10 h-10 bg-neural-700 rounded-xl flex items-center justify-center flex-shrink-0">
        <SparklesIcon className="w-6 h-6 text-white" />
      </div>

      <div className="flex-1">
        <div className="flex items-center space-x-2 mb-2">
          <span className="text-neural-400 text-sm font-medium">AI Assistant</span>
          <span className="text-neural-600 text-xs">typing...</span>
        </div>

        <div className="bg-neural-800/50 border border-neural-700/50 rounded-xl p-4">
          <div className="flex items-center space-x-2">
            <div className="flex space-x-1">
              <motion.div
                animate={{ scale: [1, 1.2, 1] }}
                transition={{ duration: 0.8, repeat: Infinity, delay: 0 }}
                className="w-2 h-2 bg-accent-500 rounded-full"
              />
              <motion.div
                animate={{ scale: [1, 1.2, 1] }}
                transition={{ duration: 0.8, repeat: Infinity, delay: 0.2 }}
                className="w-2 h-2 bg-accent-500 rounded-full"
              />
              <motion.div
                animate={{ scale: [1, 1.2, 1] }}
                transition={{ duration: 0.8, repeat: Infinity, delay: 0.4 }}
                className="w-2 h-2 bg-accent-500 rounded-full"
              />
            </div>
            <span className="text-neural-400 text-sm">Analyzing your request...</span>
          </div>
        </div>
      </div>
    </motion.div>
  );
};

export default TypingIndicator;
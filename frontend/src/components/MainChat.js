import React, { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  PaperAirplaneIcon, 
  Bars3Icon,
  SparklesIcon,
  DocumentTextIcon,
  ChartBarIcon,
  PhotoIcon
} from '@heroicons/react/24/outline';
import { useStore } from '../store/useStore';
import MessageBubble from './MessageBubble';
import TypingIndicator from './TypingIndicator';

const MainChat = () => {
  const [inputValue, setInputValue] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);
  
  const { 
    messages, 
    sendMessage, 
    isLoading, 
    currentDocument, 
    sidebarOpen, 
    toggleSidebar,
    clearMessages 
  } = useStore();

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!inputValue.trim() || isLoading) return;

    const message = inputValue.trim();
    setInputValue('');
    setIsTyping(true);

    try {
      await sendMessage(message);
    } catch (error) {
      console.error('Failed to send message:', error);
    } finally {
      setIsTyping(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  const suggestedQuestions = [
    "What are the key findings in this document?",
    "Summarize the main points from the research",
    "What charts and figures are present?",
    "Extract the important data and statistics",
    "What methodology was used in this study?",
    "What are the conclusions and recommendations?"
  ];

  return (
    <div className="flex-1 flex flex-col h-full">
      {/* Header */}
      <header className="flex items-center justify-between p-4 bg-neural-900/95 backdrop-blur-xl border-b border-neural-700/50">
        <div className="flex items-center space-x-4">
          {!sidebarOpen && (
            <button
              onClick={toggleSidebar}
              className="p-2 hover:bg-neural-800/50 rounded-lg transition-colors"
            >
              <Bars3Icon className="w-6 h-6 text-neural-400" />
            </button>
          )}
          
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-gradient-to-br from-accent-500 to-accent-600 rounded-xl flex items-center justify-center">
              <SparklesIcon className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-xl font-display font-bold text-white">
                Multi-Modal RAG Assistant
              </h1>
              <p className="text-neural-400 text-sm">
                {currentDocument 
                  ? `Analyzing: ${currentDocument.filename}` 
                  : 'Ready to analyze your documents'
                }
              </p>
            </div>
          </div>
        </div>

        <div className="flex items-center space-x-2">
          <div className="flex items-center space-x-1 px-3 py-1 bg-neural-800/50 rounded-full">
            <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
            <span className="text-neural-400 text-sm">AI Online</span>
          </div>
          
          {messages.length > 0 && (
            <button
              onClick={clearMessages}
              className="px-4 py-2 text-neural-400 hover:text-white text-sm transition-colors"
            >
              Clear Chat
            </button>
          )}
        </div>
      </header>

      {/* Chat Area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 ? (
          <div className="h-full flex items-center justify-center">
            <div className="text-center max-w-2xl mx-auto">
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.8 }}
              >
                <div className="w-24 h-24 bg-gradient-to-br from-accent-500 to-accent-600 rounded-3xl flex items-center justify-center mx-auto mb-6">
                  <SparklesIcon className="w-12 h-12 text-white" />
                </div>
                
                <h2 className="text-3xl font-display font-bold text-white mb-4">
                  Ready to Analyze Your Documents
                </h2>
                
                <p className="text-neural-400 text-lg mb-8">
                  Upload a PDF and ask me anything about its content, charts, tables, or data.
                </p>

                {currentDocument && (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-8">
                    {suggestedQuestions.map((question, index) => (
                      <motion.button
                        key={index}
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: index * 0.1 }}
                        onClick={() => setInputValue(question)}
                        className="p-4 bg-neural-800/30 hover:bg-neural-800/50 rounded-xl text-left transition-all duration-200 border border-neural-700/30 hover:border-neural-600/50"
                      >
                        <p className="text-white text-sm font-medium">{question}</p>
                      </motion.button>
                    ))}
                  </div>
                )}
              </motion.div>
            </div>
          </div>
        ) : (
          <div className="max-w-4xl mx-auto space-y-6">
            <AnimatePresence>
              {messages.map((message, index) => (
                <motion.div
                  key={message.id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -20 }}
                  transition={{ duration: 0.3, delay: index * 0.1 }}
                >
                  <MessageBubble message={message} />
                </motion.div>
              ))}
            </AnimatePresence>
            
            {(isLoading || isTyping) && <TypingIndicator />}
            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {/* Input Area */}
      <div className="p-4 bg-neural-900/95 backdrop-blur-xl border-t border-neural-700/50">
        <div className="max-w-4xl mx-auto">
          <form onSubmit={handleSubmit} className="flex items-end space-x-4">
            <div className="flex-1 relative">
              <textarea
                ref={inputRef}
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder={
                  currentDocument 
                    ? "Ask me anything about this document..." 
                    : "Upload a document first, then ask me anything..."
                }
                disabled={isLoading || !currentDocument}
                className="w-full p-4 bg-neural-800/50 border border-neural-700/50 rounded-xl text-white placeholder-neural-500 focus:border-accent-500 focus:outline-none focus:ring-2 focus:ring-accent-500/20 transition-all duration-200 resize-none min-h-[60px] max-h-[200px]"
                rows="1"
              />
              
              {inputValue && (
                <div className="absolute right-3 top-3 text-neural-500 text-sm">
                  {inputValue.length}/2000
                </div>
              )}
            </div>
            
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              type="submit"
              disabled={!inputValue.trim() || isLoading || !currentDocument}
              className="p-4 bg-accent-500 hover:bg-accent-600 disabled:bg-neural-700 disabled:cursor-not-allowed rounded-xl transition-all duration-200 flex items-center justify-center"
            >
              {isLoading ? (
                <div className="w-6 h-6 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
              ) : (
                <PaperAirplaneIcon className="w-6 h-6 text-white" />
              )}
            </motion.button>
          </form>
        </div>
      </div>
    </div>
  );
};

export default MainChat;
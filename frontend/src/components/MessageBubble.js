import React from 'react';
import { motion } from 'framer-motion';
import { 
  UserIcon, 
  SparklesIcon, 
  ExclamationTriangleIcon,
  DocumentTextIcon,
  ChartBarIcon,
  PhotoIcon
} from '@heroicons/react/24/outline';
import ReactMarkdown from 'react-markdown';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { atomDark } from 'react-syntax-highlighter/dist/esm/styles/prism';

const MessageBubble = ({ message }) => {
  const isUser = message.type === 'user';
  const isError = message.type === 'error';
  const isAI = message.type === 'ai';

  const getIcon = () => {
    if (isUser) return <UserIcon className="w-6 h-6" />;
    if (isError) return <ExclamationTriangleIcon className="w-6 h-6" />;
    return <SparklesIcon className="w-6 h-6" />;
  };

  const getBgColor = () => {
    if (isUser) return 'bg-accent-500';
    if (isError) return 'bg-red-500';
    return 'bg-neural-700';
  };

  const formatTimestamp = (timestamp) => {
    return new Date(timestamp).toLocaleTimeString([], { 
      hour: '2-digit', 
      minute: '2-digit' 
    });
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className={`flex items-start space-x-4 ${isUser ? 'flex-row-reverse space-x-reverse' : ''}`}
    >
      {/* Avatar */}
      <div className={`w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0 ${getBgColor()}`}>
        {getIcon()}
      </div>

      {/* Message Content */}
      <div className={`flex-1 ${isUser ? 'text-right' : ''}`}>
        <div className={`max-w-3xl ${isUser ? 'ml-auto' : ''}`}>
          {/* Message Header */}
          <div className={`flex items-center space-x-2 mb-2 ${isUser ? 'justify-end' : ''}`}>
            <span className="text-neural-400 text-sm font-medium">
              {isUser ? 'You' : isError ? 'Error' : 'AI Assistant'}
            </span>
            <span className="text-neural-600 text-xs">
              {formatTimestamp(message.timestamp)}
            </span>
          </div>

          {/* Message Body */}
          <div className={`p-4 rounded-xl ${
            isUser 
              ? 'bg-accent-500/20 border border-accent-500/30' 
              : isError 
                ? 'bg-red-500/20 border border-red-500/30'
                : 'bg-neural-800/50 border border-neural-700/50'
          }`}>
            {isUser ? (
              <p className="text-white whitespace-pre-wrap">{message.content}</p>
            ) : (
              <div className="prose prose-invert max-w-none">
                <ReactMarkdown
                  components={{
                    code({ node, inline, className, children, ...props }) {
                      const match = /language-(\w+)/.exec(className || '');
                      return !inline && match ? (
                        <SyntaxHighlighter
                          style={atomDark}
                          language={match[1]}
                          PreTag="div"
                          className="rounded-lg"
                          {...props}
                        >
                          {String(children).replace(/\n$/, '')}
                        </SyntaxHighlighter>
                      ) : (
                        <code className="bg-neural-900 px-1 py-0.5 rounded text-accent-400" {...props}>
                          {children}
                        </code>
                      );
                    }
                  }}
                >
                  {message.content}
                </ReactMarkdown>
              </div>
            )}
          </div>

          {/* Sources and Visuals */}
          {isAI && (message.sources?.length > 0 || message.visuals?.length > 0) && (
            <div className="mt-4 space-y-3">
              {/* Sources */}
              {message.sources?.length > 0 && (
                <div className="bg-neural-800/30 rounded-lg p-3">
                  <h4 className="text-neutral-300 text-sm font-medium mb-2 flex items-center space-x-2">
                    <DocumentTextIcon className="w-4 h-4" />
                    <span>Sources</span>
                  </h4>
                  <div className="space-y-1">
                    {message.sources.map((source, index) => (
                      <div key={index} className="text-neutral-400 text-xs">
                        Page {source.page}: {source.text.substring(0, 100)}...
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Visuals */}
              {message.visuals?.length > 0 && (
                <div className="bg-neural-800/30 rounded-lg p-3">
                  <h4 className="text-neutral-300 text-sm font-medium mb-3 flex items-center space-x-2">
                    <PhotoIcon className="w-4 h-4" />
                    <span>Related Visuals</span>
                  </h4>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    {message.visuals.map((visual, index) => (
                      <div key={index} className="bg-neural-700/50 rounded-lg p-3">
                        <div className="flex items-center space-x-2 mb-2">
                          <ChartBarIcon className="w-4 h-4 text-accent-400" />
                          <span className="text-neutral-300 text-sm font-medium">
                            {visual.type || 'Figure'}
                          </span>
                        </div>
                        {visual.image && (
                          <img 
                            src={visual.image} 
                            alt={visual.caption || 'Visual content'}
                            className="w-full h-32 object-cover rounded-lg mb-2"
                          />
                        )}
                        <p className="text-neutral-400 text-xs">
                          {visual.caption || visual.description}
                        </p>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </motion.div>
  );
};

export default MessageBubble;
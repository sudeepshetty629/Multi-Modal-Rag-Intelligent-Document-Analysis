import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  DocumentTextIcon, 
  PlusIcon, 
  CogIcon, 
  FolderIcon,
  ChartBarIcon,
  AcademicCapIcon,
  DocumentArrowUpIcon
} from '@heroicons/react/24/outline';
import { useStore } from '../store/useStore';
import FileUpload from './FileUpload';

const Sidebar = ({ onOpenAPIModal }) => {
  const { documents, currentDocument, selectDocument, sidebarOpen, toggleSidebar } = useStore();

  const getDocumentIcon = (filename) => {
    const ext = filename.split('.').pop().toLowerCase();
    switch (ext) {
      case 'pdf':
        return <DocumentTextIcon className="w-5 h-5" />;
      default:
        return <DocumentTextIcon className="w-5 h-5" />;
    }
  };

  const getDocumentType = (filename) => {
    if (filename.toLowerCase().includes('research') || filename.toLowerCase().includes('paper')) {
      return { icon: <AcademicCapIcon className="w-4 h-4" />, label: 'Research' };
    }
    if (filename.toLowerCase().includes('financial') || filename.toLowerCase().includes('report')) {
      return { icon: <ChartBarIcon className="w-4 h-4" />, label: 'Financial' };
    }
    return { icon: <FolderIcon className="w-4 h-4" />, label: 'Document' };
  };

  return (
    <AnimatePresence>
      {sidebarOpen && (
        <motion.div
          initial={{ x: -300, opacity: 0 }}
          animate={{ x: 0, opacity: 1 }}
          exit={{ x: -300, opacity: 0 }}
          transition={{ duration: 0.3, ease: 'easeInOut' }}
          className="w-80 bg-neural-900/95 backdrop-blur-xl border-r border-neural-700/50 flex flex-col h-full"
        >
          {/* Header */}
          <div className="p-6 border-b border-neural-700/50">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center space-x-3">
                <div className="w-10 h-10 bg-gradient-to-br from-accent-500 to-accent-600 rounded-xl flex items-center justify-center">
                  <DocumentArrowUpIcon className="w-6 h-6 text-white" />
                </div>
                <div>
                  <h2 className="text-xl font-display font-bold text-white">Documents</h2>
                  <p className="text-neural-400 text-sm">Multi-modal analysis</p>
                </div>
              </div>
              <button
                onClick={toggleSidebar}
                className="p-2 hover:bg-neural-800/50 rounded-lg transition-colors"
              >
                <svg className="w-5 h-5 text-neural-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            
            <FileUpload />
          </div>

          {/* Documents List */}
          <div className="flex-1 overflow-y-auto p-4">
            <div className="space-y-2">
              {documents.length > 0 ? (
                documents.map((doc, index) => {
                  const docType = getDocumentType(doc.filename);
                  const isActive = currentDocument?.id === doc.id;
                  
                  return (
                    <motion.div
                      key={doc.id}
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: index * 0.1 }}
                      onClick={() => selectDocument(doc)}
                      className={`p-4 rounded-xl cursor-pointer transition-all duration-200 ${
                        isActive 
                          ? 'bg-accent-500/20 border border-accent-500/30' 
                          : 'bg-neural-800/30 hover:bg-neural-800/50 border border-neural-700/30'
                      }`}
                    >
                      <div className="flex items-start space-x-3">
                        <div className={`p-2 rounded-lg ${isActive ? 'bg-accent-500/20' : 'bg-neural-700/50'}`}>
                          {getDocumentIcon(doc.filename)}
                        </div>
                        <div className="flex-1 min-w-0">
                          <h3 className="font-medium text-white truncate text-sm">
                            {doc.filename}
                          </h3>
                          <div className="flex items-center space-x-2 mt-1">
                            {docType.icon}
                            <span className="text-neural-400 text-xs">{docType.label}</span>
                          </div>
                          <p className="text-neural-500 text-xs mt-1">
                            {doc.upload_time ? new Date(doc.upload_time).toLocaleDateString() : 'Recently uploaded'}
                          </p>
                          <div className="flex items-center space-x-2 mt-2">
                            <div className={`w-2 h-2 rounded-full ${
                              doc.processing_status === 'completed' ? 'bg-green-500' :
                              doc.processing_status === 'processing' ? 'bg-yellow-500' :
                              'bg-neural-500'
                            }`}></div>
                            <span className="text-neural-400 text-xs capitalize">
                              {doc.processing_status || 'pending'}
                            </span>
                          </div>
                        </div>
                      </div>
                    </motion.div>
                  );
                })
              ) : (
                <div className="text-center py-12">
                  <div className="w-16 h-16 bg-neural-800/50 rounded-full flex items-center justify-center mx-auto mb-4">
                    <FolderIcon className="w-8 h-8 text-neural-500" />
                  </div>
                  <p className="text-neural-400 text-sm">No documents uploaded yet</p>
                  <p className="text-neural-500 text-xs mt-1">Upload your first PDF to get started</p>
                </div>
              )}
            </div>
          </div>

          {/* Footer */}
          <div className="p-4 border-t border-neural-700/50">
            <button
              onClick={onOpenAPIModal}
              className="w-full flex items-center justify-center space-x-2 p-3 bg-neural-800/50 hover:bg-neural-800/70 rounded-xl transition-colors"
            >
              <CogIcon className="w-5 h-5 text-neural-400" />
              <span className="text-neural-400 text-sm font-medium">API Settings</span>
            </button>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
};

export default Sidebar;
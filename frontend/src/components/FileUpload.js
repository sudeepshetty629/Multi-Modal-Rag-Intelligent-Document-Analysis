import React, { useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { motion } from 'framer-motion';
import { CloudArrowUpIcon, DocumentTextIcon } from '@heroicons/react/24/outline';
import { useStore } from '../store/useStore';
import toast from 'react-hot-toast';

const FileUpload = () => {
  const { uploadDocument, isLoading } = useStore();

  const onDrop = useCallback(async (acceptedFiles) => {
    const file = acceptedFiles[0];
    if (!file) return;

    if (file.type !== 'application/pdf') {
      toast.error('Please upload a PDF file');
      return;
    }

    if (file.size > 50 * 1024 * 1024) { // 50MB limit
      toast.error('File size must be less than 50MB');
      return;
    }

    try {
      await uploadDocument(file);
      toast.success('Document uploaded successfully!');
    } catch (error) {
      toast.error('Failed to upload document');
      console.error('Upload error:', error);
    }
  }, [uploadDocument]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf']
    },
    maxFiles: 1,
    disabled: isLoading
  });

  return (
    <div
      {...getRootProps()}
      className={`relative p-6 border-2 border-dashed rounded-xl cursor-pointer transition-all duration-300 ${
        isDragActive 
          ? 'border-accent-500 bg-accent-500/10' 
          : 'border-neural-600 hover:border-neural-500 hover:bg-neural-800/30'
      } ${isLoading ? 'opacity-50 cursor-not-allowed' : ''}`}
    >
      <input {...getInputProps()} />
      
      <div className="text-center">
        <motion.div
          animate={{ 
            scale: isDragActive ? 1.1 : 1,
            rotate: isDragActive ? 5 : 0
          }}
          transition={{ type: 'spring', stiffness: 300, damping: 20 }}
          className="w-12 h-12 mx-auto mb-3 p-3 bg-neural-800/50 rounded-xl"
        >
          {isLoading ? (
            <div className="w-6 h-6 border-2 border-accent-500 border-t-transparent rounded-full animate-spin"></div>
          ) : (
            <CloudArrowUpIcon className="w-6 h-6 text-accent-500" />
          )}
        </motion.div>
        
        <p className="text-white text-sm font-medium mb-1">
          {isDragActive ? 'Drop your PDF here' : 'Upload PDF Document'}
        </p>
        
        <p className="text-neural-400 text-xs">
          {isLoading ? 'Uploading...' : 'Drag & drop or click to select'}
        </p>
        
        <div className="mt-3 flex items-center justify-center space-x-4 text-xs text-neural-500">
          <div className="flex items-center space-x-1">
            <DocumentTextIcon className="w-3 h-3" />
            <span>PDF only</span>
          </div>
          <div className="w-1 h-1 bg-neural-500 rounded-full"></div>
          <span>Max 50MB</span>
        </div>
      </div>
    </div>
  );
};

export default FileUpload;
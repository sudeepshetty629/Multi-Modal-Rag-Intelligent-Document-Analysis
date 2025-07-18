import { create } from 'zustand';
import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

const useStore = create((set, get) => ({
  // State
  documents: [],
  messages: [],
  isLoading: false,
  isInitialized: false,
  currentDocument: null,
  apiKey: localStorage.getItem('gemini_api_key') || '',
  sidebarOpen: true,
  
  // Actions
  initialize: async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/health`);
      set({ isInitialized: true });
      return response.data;
    } catch (error) {
      console.error('Failed to initialize:', error);
      throw error;
    }
  },

  // Document management
  uploadDocument: async (file) => {
    set({ isLoading: true });
    try {
      const formData = new FormData();
      formData.append('file', file);
      
      const response = await axios.post(`${API_BASE_URL}/api/documents/upload`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      
      // Refresh documents list
      await get().fetchDocuments();
      
      set({ isLoading: false });
      return response.data;
    } catch (error) {
      set({ isLoading: false });
      throw error;
    }
  },

  fetchDocuments: async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/documents`);
      set({ documents: response.data.documents || [] });
      return response.data;
    } catch (error) {
      console.error('Failed to fetch documents:', error);
      throw error;
    }
  },

  selectDocument: (document) => {
    set({ currentDocument: document });
  },

  // Chat management
  sendMessage: async (message) => {
    const userMessage = {
      id: Date.now(),
      type: 'user',
      content: message,
      timestamp: new Date().toISOString(),
    };

    // Add user message immediately
    set(state => ({
      messages: [...state.messages, userMessage],
      isLoading: true
    }));

    try {
      const response = await axios.post(`${API_BASE_URL}/api/query`, {
        query: message,
        document_id: get().currentDocument?.id,
      });

      const aiMessage = {
        id: Date.now() + 1,
        type: 'ai',
        content: response.data.response,
        sources: response.data.sources || [],
        visuals: response.data.visuals || [],
        timestamp: new Date().toISOString(),
      };

      set(state => ({
        messages: [...state.messages, aiMessage],
        isLoading: false
      }));

      return response.data;
    } catch (error) {
      const errorMessage = {
        id: Date.now() + 1,
        type: 'error',
        content: 'Sorry, I encountered an error processing your request. Please try again.',
        timestamp: new Date().toISOString(),
      };

      set(state => ({
        messages: [...state.messages, errorMessage],
        isLoading: false
      }));

      throw error;
    }
  },

  clearMessages: () => {
    set({ messages: [] });
  },

  // API Key management
  setApiKey: (key) => {
    localStorage.setItem('gemini_api_key', key);
    set({ apiKey: key });
  },

  // UI state
  toggleSidebar: () => {
    set(state => ({ sidebarOpen: !state.sidebarOpen }));
  },

  // Test AI connection
  testAI: async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/test-ai`);
      return response.data;
    } catch (error) {
      throw error;
    }
  },
}));

export { useStore };
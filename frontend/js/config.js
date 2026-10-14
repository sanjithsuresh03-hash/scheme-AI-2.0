/**
 * SchemeAI — Frontend Configuration (Phase 1)
 * Smart India Hackathon: AI-Driven Funding & Scheme Matching
 * 
 * STRICT SECURITY POLICY:
 * 1. Only the Supabase Publishable / Anon key is permitted in the browser.
 * 2. NEVER put the Supabase Service-Role Key or Google Gemini API key here!
 *    Service-role keys and Gemini API keys must strictly live on the Python backend (.env).
 */

(function () {
  'use strict';

  // Default placeholders — replace with your Supabase Project settings
  // Supabase Dashboard -> Project Settings -> API
  const DEFAULT_SUPABASE_URL = 'https://your-project-id.supabase.co';
  const DEFAULT_SUPABASE_ANON_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.your-anon-key-here';

  // Read environment overrides from window runtime or localStorage
  const runtimeEnv = (typeof window !== 'undefined' && window.__ENV__) || {};
  const isLocalHost = typeof window !== 'undefined' && 
    (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1' || window.location.protocol === 'file:');

  const envSupabaseUrl = window.SCHEMEAI_SUPABASE_URL || runtimeEnv.SUPABASE_URL || '';
  const envSupabaseAnonKey = window.SCHEMEAI_SUPABASE_ANON_KEY || runtimeEnv.SUPABASE_ANON_KEY || '';
  const envBackendUrl = window.SCHEMEAI_BACKEND_URL || runtimeEnv.BACKEND_API_URL || '';

  // Backend API URL: local default is http://127.0.0.1:8000, production defaults to origin
  const DEFAULT_BACKEND_API_URL = isLocalHost ? 'http://127.0.0.1:8000' : (window.location.origin || 'http://127.0.0.1:8000');

  // Read overrides from localStorage if configured via the UI Settings modal
  const storedUrl = localStorage.getItem('schemeai_supabase_url');
  const storedAnonKey = localStorage.getItem('schemeai_supabase_anon_key');
  const storedBackendUrl = localStorage.getItem('schemeai_backend_url');

  const SUPABASE_URL = (storedUrl && storedUrl.trim()) ? storedUrl.trim() : 
                       (envSupabaseUrl && envSupabaseUrl.trim()) ? envSupabaseUrl.trim() : DEFAULT_SUPABASE_URL;
  const SUPABASE_ANON_KEY = (storedAnonKey && storedAnonKey.trim()) ? storedAnonKey.trim() : 
                            (envSupabaseAnonKey && envSupabaseAnonKey.trim()) ? envSupabaseAnonKey.trim() : DEFAULT_SUPABASE_ANON_KEY;
  const BACKEND_API_URL = (storedBackendUrl && storedBackendUrl.trim()) ? storedBackendUrl.trim() : 
                          (envBackendUrl && envBackendUrl.trim()) ? envBackendUrl.trim() : DEFAULT_BACKEND_API_URL;

  // Check if live Supabase credentials have been configured by the developer
  const isConfigured = Boolean(
    SUPABASE_URL && 
    SUPABASE_URL !== DEFAULT_SUPABASE_URL && 
    !SUPABASE_URL.includes('your-project-id') &&
    SUPABASE_ANON_KEY && 
    SUPABASE_ANON_KEY !== DEFAULT_SUPABASE_ANON_KEY &&
    !SUPABASE_ANON_KEY.includes('your-anon-key')
  );

  // Security guard against accidental exposure of service-role key
  if (SUPABASE_ANON_KEY.toLowerCase().includes('service_role') || 
      SUPABASE_ANON_KEY.toLowerCase().includes('secret')) {
    console.error('CRITICAL SECURITY ERROR: A service-role or secret key was detected in the frontend config! Immediately replace it with your public anon key.');
    alert('Security Warning: A private secret key was detected in frontend config. Please use the public anon key only.');
  }

  // Export configuration globally to window
  window.SchemeAIConfig = {
    SUPABASE_URL,
    SUPABASE_ANON_KEY,
    BACKEND_API_URL,
    isConfigured,
    // Method to save custom runtime credentials from the browser UI
    saveCustomConfig: function (url, anonKey, backendUrl) {
      if (url) localStorage.setItem('schemeai_supabase_url', url.trim());
      if (anonKey) localStorage.setItem('schemeai_supabase_anon_key', anonKey.trim());
      if (backendUrl) localStorage.setItem('schemeai_backend_url', backendUrl.trim());
      window.location.reload();
    },
    // Reset back to defaults
    resetConfig: function () {
      localStorage.removeItem('schemeai_supabase_url');
      localStorage.removeItem('schemeai_supabase_anon_key');
      localStorage.removeItem('schemeai_backend_url');
      window.location.reload();
    }
  };

  console.info(`[SchemeAI] Config initialized. Backend: ${BACKEND_API_URL} | Supabase Configured: ${isConfigured}`);
})();

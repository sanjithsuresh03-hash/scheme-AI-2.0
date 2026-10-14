/**
 * SchemeAI — Supabase JavaScript Client Initializer (Phase 1)
 * AI-Driven Funding & Scheme Matching for Marginalized Entrepreneurs
 * 
 * Uses the official Supabase JavaScript SDK (@supabase/supabase-js)
 * strictly using the public anon/publishable key and project URL.
 */

(function () {
  'use strict';

  let clientInstance = null;

  // Initialize or retrieve the Supabase Client (Singleton Guard)
  function initSupabaseClient() {
    // SINGLETON GUARD: Prevent multiple initializations of GoTrueClient
    if (clientInstance) {
      const config = window.SchemeAIConfig || {};
      if (clientInstance._isMock && config.isConfigured && window.supabase && typeof window.supabase.createClient === 'function') {
        console.info('[SchemeAI] Upgrading fallback mock client to official Supabase client...');
      } else {
        return clientInstance;
      }
    }

    const config = window.SchemeAIConfig || {};
    const { SUPABASE_URL, SUPABASE_ANON_KEY, isConfigured } = config;

    // 1. Live Supabase Client Initialization
    if (isConfigured && window.supabase && typeof window.supabase.createClient === 'function') {
      try {
        clientInstance = window.supabase.createClient(SUPABASE_URL, SUPABASE_ANON_KEY, {
          auth: {
            persistSession: true,
            autoRefreshToken: true,
            detectSessionInUrl: true,
            storage: window.localStorage
          }
        });
        clientInstance._isMock = false;
        console.log('[SchemeAI] Official Supabase client initialized (singleton) connected to:', SUPABASE_URL);
        return clientInstance;
      } catch (err) {
        console.error('[SchemeAI] Failed to create official Supabase client:', err);
      }
    }

    // 2. Demo / Fallback Mock Client
    // This allows Hackathon judges & evaluators to test all UI flows
    // even before remote Supabase credentials are added to config.js.
    console.warn('[SchemeAI] Using Hackathon Demo Mock Client. (Live Supabase keys not detected or invalid)');
    
    // In-memory / localStorage mock store
    const MOCK_STORAGE_KEY = 'schemeai_demo_user_session';
    const MOCK_PROFILES_KEY = 'schemeai_demo_profiles_db';
    const MOCK_USERS_KEY = 'schemeai_demo_auth_users';

    function getStoredProfiles() {
      try {
        return JSON.parse(localStorage.getItem(MOCK_PROFILES_KEY) || '{}');
      } catch {
        return {};
      }
    }

    function saveStoredProfiles(profiles) {
      localStorage.setItem(MOCK_PROFILES_KEY, JSON.stringify(profiles));
    }

    function getStoredUsers() {
      try {
        return JSON.parse(localStorage.getItem(MOCK_USERS_KEY) || '{}');
      } catch {
        return {};
      }
    }

    function saveStoredUsers(users) {
      localStorage.setItem(MOCK_USERS_KEY, JSON.stringify(users));
    }

    // Seed initial demo profile if empty
    const currentProfiles = getStoredProfiles();
    if (!currentProfiles['demo-entrepreneur-001']) {
      currentProfiles['demo-entrepreneur-001'] = {
        id: 'demo-entrepreneur-001',
        full_name: 'Pooja Rameshwaram',
        email: 'demo.entrepreneur@schemeai.gov.in',
        mobile_number: '9876543210',
        age: 28,
        gender: 'Female',
        community: 'SC',
        annual_income: 240000.00,
        district: 'Coimbatore',
        state: 'Tamil Nadu',
        education: 'Degree',
        is_student: false,
        is_registered_company: true,
        is_dpiit_recognised: true,
        existing_govt_funding_lakhs: 0.00,
        is_first_time_entrepreneur: true,
        is_woman_led: true,
        preferred_stage: 'Stage 2',
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString()
      };
      saveStoredProfiles(currentProfiles);
    }

    clientInstance = {
      _isMock: true,
      auth: {
        signUp: async function ({ email, password, options = {} }) {
          await new Promise(r => setTimeout(r, 100));
          const cleanEmail = (email || '').trim().toLowerCase();
          const profiles = getStoredProfiles();
          const users = getStoredUsers();
          
          // Check duplicate email
          for (const uid in users) {
            if (users[uid].email && users[uid].email.toLowerCase() === cleanEmail) {
              return { data: { user: null, session: null }, error: { message: 'User already registered with this email address.' } };
            }
          }
          for (const pid in profiles) {
            if (profiles[pid].email && profiles[pid].email.toLowerCase() === cleanEmail) {
              return { data: { user: null, session: null }, error: { message: 'User already registered with this email address.' } };
            }
          }

          const mockId = 'user_' + Math.random().toString(36).substring(2, 11);
          const mockUser = {
            id: mockId,
            email: cleanEmail,
            user_metadata: options.data || {},
            aud: 'authenticated',
            created_at: new Date().toISOString()
          };
          const mockSession = {
            access_token: 'mock-demo-token-' + mockId,
            token_type: 'bearer',
            user: mockUser
          };

          // Record registered user
          users[mockId] = mockUser;
          saveStoredUsers(users);

          // Save session
          sessionStorage.setItem(MOCK_STORAGE_KEY, JSON.stringify(mockSession));
          return { data: { user: mockUser, session: mockSession }, error: null };
        },

        signInWithPassword: async function ({ email, password }) {
          await new Promise(r => setTimeout(r, 150));
          const cleanEmail = (email || '').trim().toLowerCase();
          const profiles = getStoredProfiles();
          const users = getStoredUsers();
          let matchedProfile = null;

          // Demo predefined login
          if (cleanEmail === 'demo@schemeai.in' || cleanEmail === 'demo.entrepreneur@schemeai.gov.in') {
            matchedProfile = profiles['demo-entrepreneur-001'];
          } else {
            for (const pid in profiles) {
              if (profiles[pid].email && profiles[pid].email.toLowerCase() === cleanEmail) {
                matchedProfile = profiles[pid];
                break;
              }
            }
            if (!matchedProfile) {
              for (const uid in users) {
                if (users[uid].email && users[uid].email.toLowerCase() === cleanEmail) {
                  matchedProfile = { id: uid, email: cleanEmail };
                  break;
                }
              }
            }
          }

          if (!matchedProfile && email !== 'demo@schemeai.in') {
            return { data: { user: null, session: null }, error: { message: 'Invalid login credentials. User not found.' } };
          }

          const userId = matchedProfile ? matchedProfile.id : 'demo-entrepreneur-001';
          const userEmail = matchedProfile ? matchedProfile.email : email;
          const mockUser = {
            id: userId,
            email: userEmail,
            aud: 'authenticated'
          };
          const mockSession = {
            access_token: 'mock-demo-token-' + userId,
            token_type: 'bearer',
            user: mockUser
          };

          sessionStorage.setItem(MOCK_STORAGE_KEY, JSON.stringify(mockSession));
          return { data: { user: mockUser, session: mockSession }, error: null };
        },

        signOut: async function () {
          sessionStorage.removeItem(MOCK_STORAGE_KEY);
          return { error: null };
        },

        getSession: async function () {
          const raw = sessionStorage.getItem(MOCK_STORAGE_KEY);
          if (raw) {
            try {
              return { data: { session: JSON.parse(raw) }, error: null };
            } catch {
              return { data: { session: null }, error: null };
            }
          }
          return { data: { session: null }, error: null };
        },

        getUser: async function () {
          const { data } = await this.getSession();
          return { data: { user: data.session ? data.session.user : null }, error: null };
        },

        resetPasswordForEmail: async function (email) {
          await new Promise(r => setTimeout(r, 300));
          return { data: {}, error: null };
        },

        onAuthStateChange: function (callback) {
          return { data: { subscription: { unsubscribe: () => {} } } };
        }
      },

      from: function (table) {
        return {
          insert: async function (records) {
            await new Promise(r => setTimeout(r, 200));
            if (table === 'profiles') {
              const profiles = getStoredProfiles();
              const items = Array.isArray(records) ? records : [records];
              items.forEach(item => {
                profiles[item.id] = { ...item, updated_at: new Date().toISOString() };
              });
              saveStoredProfiles(profiles);
              return { data: items, error: null };
            }
            return { data: records, error: null };
          },
          upsert: async function (records, options = {}) {
            await new Promise(r => setTimeout(r, 200));
            if (table === 'profiles') {
              const profiles = getStoredProfiles();
              const items = Array.isArray(records) ? records : [records];
              items.forEach(item => {
                const existing = profiles[item.id] || {};
                profiles[item.id] = { ...existing, ...item, updated_at: new Date().toISOString() };
              });
              saveStoredProfiles(profiles);
              return { data: items, error: null };
            }
            return { data: records, error: null };
          },
          select: function () {
            return {
              eq: function (field, value) {
                return {
                  single: async function () {
                    const profiles = getStoredProfiles();
                    if (profiles[value]) {
                      return { data: profiles[value], error: null };
                    }
                    return { data: null, error: { message: 'Profile not found' } };
                  }
                };
              }
            };
          },
          update: function (updates) {
            return {
              eq: function (field, value) {
                const profiles = getStoredProfiles();
                if (profiles[value]) {
                  profiles[value] = { ...profiles[value], ...updates, updated_at: new Date().toISOString() };
                  saveStoredProfiles(profiles);
                  return Promise.resolve({ data: profiles[value], error: null });
                }
                return Promise.resolve({ data: null, error: { message: 'Profile not found' } });
              }
            };
          }
        };
      }
    };

    window.supabaseClient = clientInstance;
    return clientInstance;
  }

  // Export client getter (Singleton Accessor)
  window.getSupabaseClient = function () {
    if (!clientInstance) {
      clientInstance = initSupabaseClient();
    }
    window.supabaseClient = clientInstance;
    return clientInstance;
  };

  // Export client status helper for diagnostics
  window.getSupabaseStatus = function () {
    const config = window.SchemeAIConfig || {};
    return {
      isConfigured: Boolean(config.isConfigured),
      isMock: Boolean(clientInstance ? clientInstance._isMock : !config.isConfigured),
      supabaseUrl: config.SUPABASE_URL || null,
      isInitialized: Boolean(clientInstance)
    };
  };

  // Auto initialize on DOMContentLoaded or immediate execution (Guaranteed Single Execution)
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initSupabaseClient, { once: true });
  } else {
    initSupabaseClient();
  }
})();

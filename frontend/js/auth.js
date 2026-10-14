/**
 * SchemeAI — Authentication Module (Phase 1)
 * AI-Driven Funding & Scheme Matching for Marginalized Entrepreneurs
 * 
 * Handles Supabase Auth registration, login, session persistence,
 * password reset, and route protection.
 */

(function () {
  'use strict';

  // Toast notification utility
  function showToast(message, type = 'info') {
    let container = document.getElementById('toastContainer');
    if (!container) {
      container = document.createElement('div');
      container.id = 'toastContainer';
      container.className = 'toast-container';
      document.body.appendChild(container);
    }

    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    
    let icon = 'ℹ️';
    if (type === 'success') icon = '✅';
    if (type === 'error') icon = '⚠️';
    if (type === 'warning') icon = '🔔';

    toast.innerHTML = `
      <div style="display: flex; align-items: center; gap: 0.5rem;">
        <span>${icon}</span>
        <span>${message}</span>
      </div>
      <button style="background:none; border:none; color:#94a3b8; cursor:pointer;" onclick="this.parentElement.remove()">×</button>
    `;

    container.appendChild(toast);
    setTimeout(() => {
      if (toast.parentElement) toast.remove();
    }, 4500);
  }

  const SchemeAIAuth = {
    showToast,

    /**
     * Signs up an entrepreneur with email, password, and metadata.
     * Handles email confirmation scenario appropriately.
     */
    signUp: async function (email, password, userMetadata = {}) {
      const supabase = window.getSupabaseClient();
      if (!supabase) throw new Error('Supabase client is not available.');

      const cleanEmail = (email || '').trim().toLowerCase();
      if (!cleanEmail || !cleanEmail.includes('@')) {
        return {
          success: false,
          error: 'A valid email address is required for registration.'
        };
      }

      if (!password || typeof password !== 'string' || password.length < 8) {
        return {
          success: false,
          error: 'Password must be at least 8 characters long.'
        };
      }

      console.info('[SchemeAI Auth] Executing supabase.auth.signUp for:', cleanEmail, '(password length:', password.length, ')');

      try {
        const { data, error } = await supabase.auth.signUp({
          email: cleanEmail,
          password: password,
          options: {
            data: userMetadata
          }
        });

        if (error) {
          console.warn('[SchemeAI Auth] supabase.auth.signUp returned error:', error);
          const errMsg = error.message || 'Registration failed.';
          const isExisting = errMsg.toLowerCase().includes('already registered') || 
                             errMsg.toLowerCase().includes('already exists') ||
                             errMsg.toLowerCase().includes('user already exists');
          return {
            success: false,
            isExistingUser: isExisting,
            error: isExisting ? 'An account with this email address already exists. Please sign in instead.' : errMsg,
            rawError: error
          };
        }

        const user = data?.user;
        const session = data?.session;

        // In Supabase GoTrue Auth:
        // When email confirmations are enabled, if an email is ALREADY registered,
        // GoTrue returns a user object with an EMPTY identities array to protect against enumeration.
        if (user && Array.isArray(user.identities) && user.identities.length === 0) {
          console.warn('[SchemeAI Auth] Detected existing user via empty identities array from GoTrue Auth.');
          return {
            success: false,
            isExistingUser: true,
            error: 'An account with this email address already exists. Please sign in instead.'
          };
        }

        // When a new user signs up and email confirmation is required:
        const needsEmailConfirmation = !session && Boolean(user);

        console.info('[SchemeAI Auth] SignUp successful. User ID:', user?.id, 'Session active:', Boolean(session), 'Needs email confirmation:', needsEmailConfirmation);

        return {
          success: true,
          user: user,
          session: session,
          needsEmailConfirmation: Boolean(needsEmailConfirmation)
        };
      } catch (err) {
        console.error('[SchemeAI Auth] SignUp unexpected exception:', err);
        return { success: false, error: err.message || 'Network error during registration.', exception: err };
      }
    },

    /**
     * Authenticates an existing user.
     */
    signIn: async function (email, password) {
      const supabase = window.getSupabaseClient();
      if (!supabase) throw new Error('Supabase client is not available.');

      try {
        const { data, error } = await supabase.auth.signInWithPassword({
          email: email.trim(),
          password: password
        });

        if (error) {
          // Provide friendly message for unconfirmed emails
          if (error.message.toLowerCase().includes('email not confirmed')) {
            return {
              success: false,
              isUnconfirmed: true,
              error: 'Please verify your email address. Check your inbox for the confirmation link.'
            };
          }
          return { success: false, error: error.message };
        }

        return {
          success: true,
          user: data.user,
          session: data.session
        };
      } catch (err) {
        console.error('[SchemeAI Auth] SignIn exception:', err);
        return { success: false, error: err.message || 'Unable to communicate with authentication server.' };
      }
    },

    /**
     * Signs out the user and cleans up sessions.
     */
    signOut: async function (redirectUrl = 'login.html') {
      const supabase = window.getSupabaseClient();
      try {
        if (supabase) {
          await supabase.auth.signOut();
        }
      } catch (err) {
        console.warn('SignOut warning:', err);
      } finally {
        sessionStorage.removeItem('schemeai_demo_user_session');
        showToast('Signed out successfully', 'info');
        if (redirectUrl) {
          setTimeout(() => {
            window.location.href = redirectUrl;
          }, 300);
        }
      }
    },

    /**
     * Sends password reset email.
     */
    resetPassword: async function (email) {
      const supabase = window.getSupabaseClient();
      if (!supabase) throw new Error('Supabase client is not available.');

      try {
        const redirect = window.location.origin + window.location.pathname.replace(/[^/]*$/, 'login.html');
        const { data, error } = await supabase.auth.resetPasswordForEmail(email.trim(), {
          redirectTo: redirect
        });

        if (error) {
          return { success: false, error: error.message };
        }
        return { success: true };
      } catch (err) {
        return { success: false, error: err.message };
      }
    },

    /**
     * Returns current active session.
     */
    getSession: async function () {
      const supabase = window.getSupabaseClient();
      if (!supabase) return null;
      try {
        const { data } = await supabase.auth.getSession();
        return data.session;
      } catch (e) {
        return null;
      }
    },

    /**
     * Returns current active user.
     */
    getUser: async function () {
      const session = await this.getSession();
      return session ? session.user : null;
    },

    /**
     * Returns current Bearer access token string for backend calls.
     */
    getAccessToken: async function () {
      const session = await this.getSession();
      return session ? session.access_token : null;
    },

    /**
     * Route protection guard for dashboard.
     * Redirects unauthenticated users to login page.
     */
    requireAuth: async function (redirectUrl = 'login.html') {
      const session = await this.getSession();
      if (!session) {
        console.warn('[SchemeAI Auth] Unauthenticated access attempt. Redirecting to login.');
        window.location.replace(redirectUrl);
        return null;
      }
      return session;
    },

    /**
     * Route guard for auth pages: if already signed in, redirect to dashboard.
     */
    redirectIfAuthenticated: async function (redirectUrl = 'dashboard.html') {
      const session = await this.getSession();
      if (session) {
        window.location.replace(redirectUrl);
      }
    }
  };

  window.SchemeAIAuth = SchemeAIAuth;
})();

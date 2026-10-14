/**
 * SchemeAI — Login & Password Reset Controller (Phase 1)
 * Smart India Hackathon: AI-Driven Funding & Scheme Matching
 * 
 * Handles entrepreneur authentication via Supabase Auth,
 * password reset requests, and handles email verification edge cases.
 */

(function () {
  'use strict';

  // Toggle Password Visibility
  function setupPasswordToggle() {
    const toggleBtn = document.getElementById('togglePasswordBtn');
    const pwdInput = document.getElementById('password');
    if (toggleBtn && pwdInput) {
      toggleBtn.addEventListener('click', () => {
        const type = pwdInput.getAttribute('type') === 'password' ? 'text' : 'password';
        pwdInput.setAttribute('type', type);
        toggleBtn.textContent = type === 'password' ? '👁️' : '🔒';
      });
    }
  }

  // Open & Close Forgot Password Modal
  function setupForgotPasswordModal() {
    const openBtn = document.getElementById('btnForgotPassword');
    const modal = document.getElementById('forgotPasswordModal');
    const closeBtn = document.getElementById('btnCloseForgotModal');
    const submitBtn = document.getElementById('btnSendResetLink');

    if (openBtn && modal) {
      openBtn.addEventListener('click', (e) => {
        e.preventDefault();
        modal.classList.add('open');
        const resetEmailInput = document.getElementById('resetEmail');
        const currentEmail = document.getElementById('email')?.value;
        if (resetEmailInput && currentEmail) {
          resetEmailInput.value = currentEmail;
        }
      });
    }

    if (closeBtn && modal) {
      closeBtn.addEventListener('click', () => {
        modal.classList.remove('open');
      });
    }

    if (submitBtn) {
      submitBtn.addEventListener('click', async () => {
        const resetEmail = document.getElementById('resetEmail')?.value.trim();
        if (!resetEmail || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(resetEmail)) {
          alert('Please enter a valid registered email address.');
          return;
        }

        submitBtn.disabled = true;
        submitBtn.textContent = 'Sending link...';

        const result = await window.SchemeAIAuth.resetPassword(resetEmail);
        submitBtn.disabled = false;
        submitBtn.textContent = 'Send Reset Link';

        if (result.success) {
          modal.classList.remove('open');
          window.SchemeAIAuth.showToast(`Password reset link sent to ${resetEmail}!`, 'success');
        } else {
          window.SchemeAIAuth.showToast(`Error: ${result.error}`, 'error');
        }
      });
    }
  }

  // Quick-Fill Demo Credentials for Hackathon Judges
  function setupDemoQuickFill() {
    const demoBtn = document.getElementById('btnFillDemoLogin');
    if (demoBtn) {
      demoBtn.addEventListener('click', () => {
        const emailInput = document.getElementById('email');
        const pwdInput = document.getElementById('password');
        if (emailInput && pwdInput) {
          emailInput.value = 'demo.entrepreneur@schemeai.gov.in';
          pwdInput.value = 'DemoPass@2026';
          window.SchemeAIAuth.showToast('Demo credentials prefilled! Click Sign In.', 'info');
        }
      });
    }
  }

  // Handle Login Form Submission
  async function handleLoginSubmit(e) {
    e.preventDefault();

    const email = document.getElementById('email')?.value.trim();
    const password = document.getElementById('password')?.value;
    const errorBox = document.getElementById('loginAlertBox');
    const submitBtn = document.getElementById('btnLoginSubmit');

    if (!email || !password) {
      if (errorBox) {
        errorBox.textContent = 'Please provide both your registered email and password.';
        errorBox.style.display = 'block';
      }
      return;
    }

    if (errorBox) errorBox.style.display = 'none';

    if (submitBtn) {
      submitBtn.disabled = true;
      submitBtn.innerHTML = '<span>⏳ Authenticating...</span>';
    }

    try {
      const result = await window.SchemeAIAuth.signIn(email, password);

      if (!result.success) {
        if (submitBtn) {
          submitBtn.disabled = false;
          submitBtn.textContent = 'Sign In to Dashboard';
        }

        if (errorBox) {
          errorBox.textContent = result.error || 'Authentication failed. Please verify credentials.';
          errorBox.style.display = 'block';
        }

        window.SchemeAIAuth.showToast(result.error || 'Invalid email or password.', 'error');
        return;
      }

      window.SchemeAIAuth.showToast('Authentication verified! Redirecting to Dashboard...', 'success');

      // Remember me
      const rememberMe = document.getElementById('rememberMe')?.checked;
      if (rememberMe) {
        localStorage.setItem('schemeai_remembered_email', email);
      } else {
        localStorage.removeItem('schemeai_remembered_email');
      }

      setTimeout(() => {
        window.location.href = 'dashboard.html';
      }, 600);

    } catch (err) {
      console.error('Login error:', err);
      if (submitBtn) {
        submitBtn.disabled = false;
        submitBtn.textContent = 'Sign In to Dashboard';
      }
      if (errorBox) {
        errorBox.textContent = 'Network or system error. Please try again.';
        errorBox.style.display = 'block';
      }
    }
  }

  // Init
  document.addEventListener('DOMContentLoaded', async () => {
    // If already signed in, go directly to dashboard
    await window.SchemeAIAuth.redirectIfAuthenticated();

    // Prefill remembered email if available
    const savedEmail = localStorage.getItem('schemeai_remembered_email');
    if (savedEmail) {
      const emailInput = document.getElementById('email');
      const rememberCheckbox = document.getElementById('rememberMe');
      if (emailInput) emailInput.value = savedEmail;
      if (rememberCheckbox) rememberCheckbox.checked = true;
    }

    setupPasswordToggle();
    setupForgotPasswordModal();
    setupDemoQuickFill();

    const form = document.getElementById('loginForm');
    if (form) {
      form.addEventListener('submit', handleLoginSubmit);
    }
  });

})();

/**
 * SchemeAI — Registration Form Controller (Phase 1)
 * Smart India Hackathon: AI-Driven Funding & Scheme Matching
 * 
 * Manages multi-step entrepreneur registration, field validations,
 * mock OTP verification demo, and Supabase profile creation.
 */

(function () {
  'use strict';

  // Indian States & Union Territories
  const INDIAN_STATES = [
    "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh",
    "Goa", "Gujarat", "Haryana", "Himachal Pradesh", "Jharkhand", "Karnataka",
    "Kerala", "Madhya Pradesh", "Maharashtra", "Manipur", "Meghalaya", "Mizoram",
    "Nagaland", "Odisha", "Punjab", "Rajasthan", "Sikkim", "Tamil Nadu",
    "Telangana", "Tripura", "Uttar Pradesh", "Uttarakhand", "West Bengal",
    "Andaman and Nicobar Islands", "Chandigarh", "Dadra and Nagar Haveli and Daman and Diu",
    "Delhi", "Jammu and Kashmir", "Ladakh", "Lakshadweep", "Puducherry"
  ];

  let currentStep = 1;
  let mockGeneratedOtp = "582491";

  // Password Strength Checker
  function evaluatePassword(pwd) {
    const checks = {
      length: pwd.length >= 8,
      uppercase: /[A-Z]/.test(pwd),
      lowercase: /[a-z]/.test(pwd),
      numberOrSpecial: /[0-9!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]/.test(pwd)
    };

    const count = Object.values(checks).filter(Boolean).length;
    let score = 'weak';
    if (count >= 4) score = 'strong';
    else if (count >= 2) score = 'medium';

    return { score, checks };
  }

  // Populate State Dropdown
  function populateStateDropdown() {
    const stateSelect = document.getElementById('state');
    if (!stateSelect) return;
    
    // Clear existing options except default
    stateSelect.innerHTML = '<option value="">Select State / UT</option>';
    INDIAN_STATES.forEach(st => {
      const opt = document.createElement('option');
      opt.value = st;
      opt.textContent = st;
      stateSelect.appendChild(opt);
    });
  }

  // Multi-step Navigation
  function showStep(stepNum) {
    currentStep = stepNum;
    
    // Update step containers
    for (let i = 1; i <= 3; i++) {
      const el = document.getElementById(`formStep${i}`);
      if (el) {
        el.style.display = (i === stepNum) ? 'block' : 'none';
      }
      
      const indicator = document.getElementById(`stepIndicator${i}`);
      if (indicator) {
        indicator.classList.remove('active', 'completed');
        if (i === stepNum) indicator.classList.add('active');
        else if (i < stepNum) indicator.classList.add('completed');
      }
    }

    window.scrollTo({ top: 120, behavior: 'smooth' });
  }

  // Field Validation Helpers
  function setFieldError(fieldId, errorMsg) {
    const input = document.getElementById(fieldId);
    const feedback = document.getElementById(`${fieldId}Feedback`);
    if (input) {
      input.classList.add('is-invalid');
    }
    if (feedback) {
      feedback.textContent = errorMsg;
      feedback.className = 'form-feedback invalid';
    }
  }

  function clearFieldError(fieldId) {
    const input = document.getElementById(fieldId);
    const feedback = document.getElementById(`${fieldId}Feedback`);
    if (input) {
      input.classList.remove('is-invalid');
    }
    if (feedback) {
      feedback.textContent = '';
      feedback.className = 'form-feedback';
    }
  }

  // Validate Step 1: Account & Credentials
  function validateStep1() {
    let isValid = true;

    // Full name
    const fullName = document.getElementById('fullName')?.value.trim();
    if (!fullName || fullName.length < 2) {
      setFieldError('fullName', 'Full name must be at least 2 characters.');
      isValid = false;
    } else {
      clearFieldError('fullName');
    }

    // Email
    const email = document.getElementById('email')?.value.trim();
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!email || !emailRegex.test(email)) {
      setFieldError('email', 'Enter a valid email address.');
      isValid = false;
    } else {
      clearFieldError('email');
    }

    // Mobile Number (10 digits)
    const mobile = document.getElementById('mobileNumber')?.value.trim();
    const mobileRegex = /^[0-9]{10}$/;
    if (!mobile || !mobileRegex.test(mobile)) {
      setFieldError('mobileNumber', 'Enter a valid 10-digit mobile number.');
      isValid = false;
    } else {
      clearFieldError('mobileNumber');
    }

    // Password
    const password = document.getElementById('password')?.value || '';
    const { score } = evaluatePassword(password);
    if (password.length < 8) {
      setFieldError('password', 'Password must be at least 8 characters long.');
      isValid = false;
    } else {
      clearFieldError('password');
    }

    // Confirm Password
    const confirmPassword = document.getElementById('confirmPassword')?.value || '';
    if (password !== confirmPassword) {
      setFieldError('confirmPassword', 'Passwords do not match.');
      isValid = false;
    } else {
      clearFieldError('confirmPassword');
    }

    return isValid;
  }

  // Validate Step 2: Demographics
  function validateStep2() {
    let isValid = true;

    // Age
    const ageVal = parseInt(document.getElementById('age')?.value, 10);
    if (isNaN(ageVal) || ageVal < 18 || ageVal > 120) {
      setFieldError('age', 'Age must be between 18 and 120.');
      isValid = false;
    } else {
      clearFieldError('age');
    }

    // Gender
    const gender = document.getElementById('gender')?.value;
    if (!gender) {
      setFieldError('gender', 'Please select gender.');
      isValid = false;
    } else {
      clearFieldError('gender');
    }

    // Community
    const community = document.getElementById('community')?.value;
    if (!community) {
      setFieldError('community', 'Please choose your social category / community.');
      isValid = false;
    } else {
      clearFieldError('community');
    }

    // Annual Income
    const incomeVal = parseFloat(document.getElementById('annualIncome')?.value);
    if (isNaN(incomeVal) || incomeVal < 0) {
      setFieldError('annualIncome', 'Enter valid annual family income (minimum 0).');
      isValid = false;
    } else {
      clearFieldError('annualIncome');
    }

    // State
    const state = document.getElementById('state')?.value;
    if (!state) {
      setFieldError('state', 'Please select state or Union Territory.');
      isValid = false;
    } else {
      clearFieldError('state');
    }

    // District
    const district = document.getElementById('district')?.value.trim();
    if (!district || district.length < 2) {
      setFieldError('district', 'Enter your district name.');
      isValid = false;
    } else {
      clearFieldError('district');
    }

    // Education
    const education = document.getElementById('education')?.value;
    if (!education) {
      setFieldError('education', 'Please select highest education level.');
      isValid = false;
    } else {
      clearFieldError('education');
    }

    return isValid;
  }

  // Validate Step 3: Enterprise Details
  function validateStep3() {
    let isValid = true;

    // Funding received in lakhs
    const fundingVal = parseFloat(document.getElementById('existingGovtFunding')?.value);
    if (isNaN(fundingVal) || fundingVal < 0) {
      setFieldError('existingGovtFunding', 'Enter valid funding received (0 if none).');
      isValid = false;
    } else {
      clearFieldError('existingGovtFunding');
    }

    // Preferred stage
    const stage = document.getElementById('preferredStage')?.value;
    if (!stage) {
      setFieldError('preferredStage', 'Please select your preferred stage.');
      isValid = false;
    } else {
      clearFieldError('preferredStage');
    }

    return isValid;
  }

  // Gather All Form Data
  function collectFormData() {
    const getRadioBool = (name) => {
      const checked = document.querySelector(`input[name="${name}"]:checked`);
      return checked ? checked.value === 'yes' : false;
    };

    return {
      full_name: document.getElementById('fullName').value.trim(),
      email: document.getElementById('email').value.trim(),
      password: document.getElementById('password').value,
      mobile_number: document.getElementById('mobileNumber').value.trim(),
      age: parseInt(document.getElementById('age').value, 10),
      gender: document.getElementById('gender').value,
      community: document.getElementById('community').value,
      annual_income: parseFloat(document.getElementById('annualIncome').value),
      state: document.getElementById('state').value,
      district: document.getElementById('district').value.trim(),
      education: document.getElementById('education').value,
      is_student: getRadioBool('isStudent'),
      is_registered_company: getRadioBool('isRegisteredCompany'),
      is_dpiit_recognised: getRadioBool('isDpiitRecognised'),
      existing_govt_funding_lakhs: parseFloat(document.getElementById('existingGovtFunding').value || 0),
      is_first_time_entrepreneur: getRadioBool('isFirstTimeEntrepreneur'),
      is_woman_led: getRadioBool('isWomanLed'),
      preferred_stage: document.getElementById('preferredStage').value
    };
  }

  // Open Mock OTP Verification Modal
  function openOtpModal(mobile) {
    const modal = document.getElementById('otpDemoModal');
    if (modal && modal.classList.contains('open')) {
      return;
    }
    const mobileSpan = document.getElementById('demoMobileDisplay');
    const otpCodeSpan = document.getElementById('demoOtpCode');
    
    // Generate fresh 6-digit mock OTP
    mockGeneratedOtp = Math.floor(100000 + Math.random() * 900000).toString();
    
    if (mobileSpan) mobileSpan.textContent = `+91 ${mobile}`;
    if (otpCodeSpan) otpCodeSpan.textContent = mockGeneratedOtp;
    
    // Clear previous inputs
    const inputs = document.querySelectorAll('.otp-digit');
    inputs.forEach(i => i.value = '');

    if (modal) {
      modal.classList.add('open');
      const firstInput = document.getElementById('otp1');
      if (firstInput) setTimeout(() => firstInput.focus(), 200);
    }
  }

  function closeOtpModal() {
    const modal = document.getElementById('otpDemoModal');
    if (modal) modal.classList.remove('open');
  }

  // UI Error Banner & Structured Console Diagnostics
  function showRegisterError(message, details = null) {
    const alertBox = document.getElementById('registerAlertBox');
    const successBox = document.getElementById('registerSuccessBox');
    if (successBox) successBox.style.display = 'none';

    if (alertBox) {
      alertBox.style.display = 'block';
      alertBox.className = 'alert-banner alert-danger';
      alertBox.innerHTML = `
        <div style="display: flex; align-items: flex-start; gap: 0.75rem;">
          <span style="font-size: 1.25rem; line-height: 1.2;">⚠️</span>
          <div style="flex: 1;">
            <strong>Registration Notice:</strong>
            <div style="margin-top: 0.25rem;">${message}</div>
          </div>
          <button type="button" style="background: none; border: none; color: inherit; font-size: 1.2rem; cursor: pointer; opacity: 0.7;" onclick="this.closest('.alert-banner').style.display='none'">×</button>
        </div>
      `;
      alertBox.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }

    if (window.SchemeAIAuth && typeof window.SchemeAIAuth.showToast === 'function') {
      window.SchemeAIAuth.showToast(message.replace(/<[^>]*>/g, ''), 'error');
    }

    // Structured Diagnostic Console Log
    console.group('[SchemeAI Registration Diagnostics]');
    console.error('Registration Flow Error:', message.replace(/<[^>]*>/g, ''));
    if (details) {
      console.info('Diagnostic Context:', details);
    }
    console.info('Supabase Client Status:', (typeof window.getSupabaseStatus === 'function') ? window.getSupabaseStatus() : 'Unavailable');
    console.info('Timestamp:', new Date().toISOString());
    console.groupEnd();
  }

  // UI Success Banner
  function showRegisterSuccess(message) {
    const alertBox = document.getElementById('registerAlertBox');
    const successBox = document.getElementById('registerSuccessBox');
    if (alertBox) alertBox.style.display = 'none';

    if (successBox) {
      successBox.style.display = 'block';
      successBox.className = 'alert-banner alert-success';
      successBox.innerHTML = `
        <div style="display: flex; align-items: flex-start; gap: 0.75rem;">
          <span style="font-size: 1.25rem; line-height: 1.2;">✅</span>
          <div style="flex: 1;">
            <strong>Registration Update:</strong>
            <div style="margin-top: 0.25rem;">${message}</div>
          </div>
        </div>
      `;
      successBox.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
  }

  // Final Registration & Supabase Profile Save (Decoupled Stage 1 Auth & Stage 2 Profile)
  async function completeRegistration() {
    const submitBtn = document.getElementById('btnVerifyAndRegister');
    if (submitBtn) {
      submitBtn.disabled = true;
      submitBtn.innerHTML = '<span>⏳ Step 1/2: Creating Secure Credentials...</span>';
    }

    const formData = collectFormData();
    const cleanEmail = (formData.email || '').trim().toLowerCase();
    const cleanPassword = formData.password;
    const { email: _, password: __, ...profileFields } = formData;

    if (!cleanEmail || !cleanPassword) {
      if (submitBtn) {
        submitBtn.disabled = false;
        submitBtn.textContent = 'Verify & Complete Registration';
      }
      showRegisterError('Email and password are required to complete registration.', {
        hasEmail: Boolean(cleanEmail),
        hasPassword: Boolean(cleanPassword)
      });
      return;
    }

    console.info('[SchemeAI Registration] Beginning decoupled registration flow for:', cleanEmail);

    // ====================================================================
    // STAGE 1: Supabase Authentication SignUp
    // ====================================================================
    let authResult;
    try {
      authResult = await window.SchemeAIAuth.signUp(cleanEmail, cleanPassword, {
        full_name: profileFields.full_name,
        mobile_number: profileFields.mobile_number,
        community: profileFields.community
      });
    } catch (authEx) {
      console.error('[SchemeAI Registration] Unexpected exception in Stage 1 Auth:', authEx);
      closeOtpModal();
      if (submitBtn) {
        submitBtn.disabled = false;
        submitBtn.textContent = 'Verify & Complete Registration';
      }
      showRegisterError(`Authentication error: ${authEx.message || 'Unable to connect to authentication server.'}`, {
        stage: 'Stage 1: Supabase Auth SignUp',
        email: cleanEmail,
        exception: authEx
      });
      return;
    }

    // Handle Stage 1 authentication failure
    if (!authResult || !authResult.success) {
      closeOtpModal();
      if (submitBtn) {
        submitBtn.disabled = false;
        submitBtn.textContent = 'Verify & Complete Registration';
      }

      if (authResult?.isExistingUser) {
        showRegisterError(
          `An account with <strong>${cleanEmail}</strong> already exists. ` +
          `<a href="login.html" style="color: var(--teal-300); text-decoration: underline; font-weight: 600; margin-left: 0.35rem;">Sign in here →</a>`,
          { stage: 'Stage 1: Supabase Auth SignUp', email: cleanEmail, reason: 'Duplicate user account detected' }
        );
      } else {
        showRegisterError(
          `Unable to create account: ${authResult?.error || 'Authentication failed.'}`,
          { stage: 'Stage 1: Supabase Auth SignUp', email: cleanEmail, error: authResult?.error, rawError: authResult?.rawError }
        );
      }
      return;
    }

    // Stage 1 Auth SUCCEEDED! User is now created.
    const user = authResult.user;
    const session = authResult.session;
    const userId = user?.id;

    // Queue profile in localStorage immediately for resilient offline/deferred recovery
    const pendingProfileRecord = {
      ...profileFields,
      id: userId,
      email: cleanEmail,
      queued_at: new Date().toISOString()
    };
    localStorage.setItem('schemeai_pending_profile', JSON.stringify(pendingProfileRecord));

    // Check if project requires email verification before creating an active session
    if (authResult.needsEmailConfirmation || !session) {
      closeOtpModal();
      console.info('[SchemeAI Registration] Stage 1 Auth succeeded. Email confirmation required. Profile saved to local recovery queue.');
      const confModal = document.getElementById('emailConfirmationModal');
      if (confModal) {
        const emailTarget = document.getElementById('confirmedEmailTarget');
        if (emailTarget) emailTarget.textContent = cleanEmail;
        confModal.classList.add('open');
      } else {
        showRegisterSuccess(`Account created! A confirmation email has been sent to <strong>${cleanEmail}</strong>. Please check your inbox and verify before logging in.`);
      }
      return;
    }

    // ====================================================================
    // STAGE 2: Entrepreneur Profile Creation in PostgreSQL / FastAPI Backend
    // (Handled separately so profile issues never report full registration failure)
    // ====================================================================
    if (submitBtn) {
      submitBtn.innerHTML = '<span>⏳ Step 2/2: Registering Entrepreneur Profile...</span>';
    }

    const supabase = window.getSupabaseClient();
    const profileRecord = {
      id: userId,
      ...profileFields,
      email: cleanEmail
    };

    let profileSaved = false;
    let profileErrorDetails = null;

    // 1. Attempt direct Supabase upsert (handles inserts and duplicate key on conflict)
    try {
      const { data, error: profileError } = await supabase
        .from('profiles')
        .upsert(profileRecord, { onConflict: 'id' });

      if (!profileError) {
        profileSaved = true;
        console.info('[SchemeAI Registration] Stage 2: Profile record successfully saved via Supabase upsert.');
      } else {
        profileErrorDetails = profileError;
        console.warn('[SchemeAI Registration] Direct Supabase profile upsert returned error:', profileError);
      }
    } catch (insertErr) {
      profileErrorDetails = insertErr;
      console.warn('[SchemeAI Registration] Exception during direct profile upsert:', insertErr);
    }

    // 2. Sync with FastAPI backend (always attempted if session token is available or in mock mode)
    if (session?.access_token) {
      try {
        const config = window.SchemeAIConfig || {};
        const backendUrl = config.BACKEND_API_URL || 'http://127.0.0.1:8000';
        const backendRes = await fetch(`${backendUrl}/api/profile/me`, {
          method: 'PUT',
          headers: {
            'Authorization': `Bearer ${session.access_token}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify(profileFields)
        });

        if (backendRes.ok) {
          profileSaved = true;
          console.info('[SchemeAI Registration] Stage 2: Profile successfully synced via FastAPI backend.');
        } else {
          console.info(`[SchemeAI Registration] FastAPI backend sync responded with status ${backendRes.status}`);
        }
      } catch (bErr) {
        console.warn('[SchemeAI Registration] Backend sync fallback was unavailable:', bErr);
      }
    }

    if (profileSaved) {
      localStorage.removeItem('schemeai_pending_profile');
    }

    closeOtpModal();

    // Handle Stage 2 outcome without falsely reporting that the entire registration failed
    if (profileSaved) {
      showRegisterSuccess('Account and entrepreneur profile registered successfully! Redirecting to your dashboard...');
      if (window.SchemeAIAuth && typeof window.SchemeAIAuth.showToast === 'function') {
        window.SchemeAIAuth.showToast('Profile created successfully! Welcome to SchemeAI.', 'success');
      }
      setTimeout(() => {
        window.location.href = 'dashboard.html';
      }, 800);
    } else {
      // Stage 1 succeeded, Stage 2 deferred/queued locally
      console.group('[SchemeAI Registration Diagnostics]');
      console.warn('Stage 1 (Auth): SUCCEEDED. Stage 2 (Profile): DEFERRED/QUEUED.');
      if (profileErrorDetails) {
        console.info('Stage 2 Profile Error Details:', profileErrorDetails);
      }
      console.info('Pending Profile queued in localStorage for auto-synchronization on dashboard load.');
      console.groupEnd();

      showRegisterSuccess(
        `Account created successfully! Your entrepreneur details have been safely queued and will be finalized on your dashboard. ` +
        `<a href="dashboard.html" style="color: var(--teal-300); text-decoration: underline; font-weight: 600; margin-left: 0.35rem;">Proceed to Dashboard →</a>`
      );
      if (window.SchemeAIAuth && typeof window.SchemeAIAuth.showToast === 'function') {
        window.SchemeAIAuth.showToast('Account created! Finalizing profile setup...', 'warning');
      }
      setTimeout(() => {
        window.location.href = 'dashboard.html';
      }, 1800);
    }
  }

  // DOM Content Loaded Handler
  document.addEventListener('DOMContentLoaded', async () => {
    // If already logged in, redirect to dashboard
    await window.SchemeAIAuth.redirectIfAuthenticated();

    populateStateDropdown();

    // Prevent default form submission and handle keyboard navigation (Enter key)
    const formEl = document.getElementById('registrationForm');
    if (formEl) {
      formEl.addEventListener('submit', (e) => {
        e.preventDefault();
        if (currentStep === 1) {
          if (validateStep1()) showStep(2);
        } else if (currentStep === 2) {
          if (validateStep2()) showStep(3);
        } else if (currentStep === 3) {
          if (!validateStep1()) { showStep(1); return; }
          if (!validateStep2()) { showStep(2); return; }
          if (!validateStep3()) return;
          const mobile = document.getElementById('mobileNumber').value.trim();
          openOtpModal(mobile);
        }
      });
    }

    // Password live strength meter
    const pwdInput = document.getElementById('password');
    const pwdMeter = document.getElementById('pwdMeterBar');
    if (pwdInput && pwdMeter) {
      pwdInput.addEventListener('input', (e) => {
        const val = e.target.value;
        const { score } = evaluatePassword(val);
        pwdMeter.className = `password-meter-bar meter-${score}`;
      });
    }

    // Step 1 -> Next
    document.getElementById('btnStep1Next')?.addEventListener('click', () => {
      if (validateStep1()) showStep(2);
    });

    // Step 2 -> Back & Next
    document.getElementById('btnStep2Back')?.addEventListener('click', () => showStep(1));
    document.getElementById('btnStep2Next')?.addEventListener('click', () => {
      if (validateStep2()) showStep(3);
    });

    // Step 3 -> Back & Submit (Triggers Mock OTP Modal)
    document.getElementById('btnStep3Back')?.addEventListener('click', () => showStep(2));
    document.getElementById('btnStep3Submit')?.addEventListener('click', (e) => {
      e.preventDefault();
      if (!validateStep1()) { showStep(1); return; }
      if (!validateStep2()) { showStep(2); return; }
      if (!validateStep3()) return;

      const mobile = document.getElementById('mobileNumber').value.trim();
      openOtpModal(mobile);
    });

    // OTP Modal Controls
    document.getElementById('btnCloseOtpModal')?.addEventListener('click', closeOtpModal);
    
    // Quick-Fill Demo OTP Button
    document.getElementById('btnFillDemoOtp')?.addEventListener('click', () => {
      for (let i = 0; i < 6; i++) {
        const box = document.getElementById(`otp${i + 1}`);
        if (box && mockGeneratedOtp[i]) box.value = mockGeneratedOtp[i];
      }
    });

    // Verify & Register Button inside Modal
    document.getElementById('btnVerifyAndRegister')?.addEventListener('click', () => {
      completeRegistration();
    });

    // Auto-advance OTP Inputs
    const otpBoxes = document.querySelectorAll('.otp-digit');
    otpBoxes.forEach((box, idx) => {
      box.addEventListener('input', (e) => {
        if (e.target.value && idx < otpBoxes.length - 1) {
          otpBoxes[idx + 1].focus();
        }
      });
      box.addEventListener('keydown', (e) => {
        if (e.key === 'Backspace' && !e.target.value && idx > 0) {
          otpBoxes[idx - 1].focus();
        }
      });
    });
  });

})();

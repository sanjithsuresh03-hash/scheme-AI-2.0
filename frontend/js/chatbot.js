/**
 * SchemeAI — Phase 5 Gemini AI Scheme Assistant Chatbot Controller
 * AI-Driven Funding & Scheme Matching for Marginalized Entrepreneurs
 * 
 * Capabilities:
 * - Session authentication via Supabase Auth
 * - Multi-conversation thread management (New conversation, load previous threads)
 * - Safe DOM construction (Strictly zero untrusted innerHTML injection)
 * - Safe markdown-style bolding and structure parsing via DOM nodes
 * - Interactive suggested inquiries (English, தமிழ், Tanglish)
 * - Multi-language selector (Auto, English, தமிழ், Tanglish)
 * - Grounded referenced scheme chips with verified dates and official portals
 * - Loading typing indicator and friendly error retry states
 * - Mobile responsive drawer handling
 */

(function () {
  'use strict';

  let currentToken = null;
  let currentUser = null;
  let currentConversationId = null;
  let isSending = false;
  let lastFailedMessage = null;

  // Safe DOM Element Factory
  function el(tag, className, textContent, attributes = {}) {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (textContent !== undefined && textContent !== null) node.textContent = String(textContent);
    for (const [key, val] of Object.entries(attributes)) {
      if (val !== undefined && val !== null) {
        node.setAttribute(key, String(val));
      }
    }
    return node;
  }

  // Safe Text Formatter (Parses linebreaks and **bold** into safe DOM nodes)
  function renderFormattedText(container, text) {
    if (!text) return;

    const lines = text.split('\n');
    lines.forEach((line, lineIdx) => {
      const trimmed = line.trim();
      if (!trimmed) {
        // Empty line creates a small spacing break
        if (lineIdx < lines.length - 1) {
          const spacer = el('div', null, null, { style: 'height: 0.5rem;' });
          container.appendChild(spacer);
        }
        return;
      }

      const p = el('div', null, null, { style: 'margin-bottom: 0.25rem;' });

      // Safe parser for **bold** segments
      const parts = line.split('**');
      parts.forEach((part, idx) => {
        if (!part) return;
        if (idx % 2 === 1) {
          // Odd indices are between ** -> bold
          const boldNode = el('strong', null, part);
          p.appendChild(boldNode);
        } else {
          p.appendChild(document.createTextNode(part));
        }
      });

      container.appendChild(p);
    });
  }

  // Format Time Helper
  function formatTime(isoString) {
    if (!isoString) return '';
    try {
      const date = new Date(isoString);
      return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    } catch (e) {
      return '';
    }
  }

  // Format Date Helper
  function formatDate(isoString) {
    if (!isoString) return 'Recent';
    try {
      const date = new Date(isoString);
      return date.toLocaleDateString([], { month: 'short', day: 'numeric' });
    } catch (e) {
      return 'Recent';
    }
  }

  // Scroll Chat to Bottom
  function scrollToBottom() {
    const scrollContainer = document.getElementById('chatMessagesScroll');
    if (scrollContainer) {
      scrollContainer.scrollTop = scrollContainer.scrollHeight;
    }
  }

  // ============================================================================
  // Message Rendering (Safe DOM)
  // ============================================================================

  function appendUserMessage(content, timestamp = new Date().toISOString()) {
    const scrollContainer = document.getElementById('chatMessagesScroll');
    if (!scrollContainer) return;

    // Hide welcome box once discussion starts
    const welcomeBox = document.getElementById('chatWelcomeBox');
    if (welcomeBox) welcomeBox.style.display = 'none';

    const row = el('div', 'chat-message-row user-row');

    const avatar = el('div', 'msg-avatar', '👤');
    const bodyWrapper = el('div', 'msg-body-wrapper');
    const bubble = el('div', 'msg-bubble', content);
    const timeEl = el('span', 'msg-timestamp', formatTime(timestamp));

    bodyWrapper.appendChild(bubble);
    bodyWrapper.appendChild(timeEl);

    row.appendChild(avatar);
    row.appendChild(bodyWrapper);

    scrollContainer.appendChild(row);
    scrollToBottom();
  }

  function appendAssistantMessage(content, referencedSchemes = [], timestamp = new Date().toISOString()) {
    const scrollContainer = document.getElementById('chatMessagesScroll');
    if (!scrollContainer) return;

    const row = el('div', 'chat-message-row assistant-row');

    const avatar = el('div', 'msg-avatar', '🤖');
    const bodyWrapper = el('div', 'msg-body-wrapper');
    const bubble = el('div', 'msg-bubble');

    // Parse text safely
    renderFormattedText(bubble, content);

    // If response referenced verified schemes, render interactive chips
    if (referencedSchemes && referencedSchemes.length > 0) {
      const chipsContainer = el('div', 'msg-schemes-chips');
      const chipsHeader = el('div', null, '📌 Referenced Verified Schemes:', {
        style: 'font-size: 0.76rem; font-weight: 700; color: var(--teal-300); text-transform: uppercase; letter-spacing: 0.04em;'
      });
      chipsContainer.appendChild(chipsHeader);

      referencedSchemes.forEach(s => {
        const chip = el('div', 'referenced-scheme-chip');

        const titleWrap = el('div', 'chip-title-wrap');
        const nameText = el('span', 'chip-name', s.name || s.id);
        const metaText = el('span', 'chip-meta', `${s.government || 'Central'} • Verified: ${s.last_verified || 'Check portal'}`);
        titleWrap.appendChild(nameText);
        titleWrap.appendChild(metaText);

        const url = s.official_url || s.official_link || '#';
        const portalBtn = el('a', 'chip-url-link', null, {
          href: url,
          target: '_blank',
          rel: 'noopener noreferrer'
        });
        portalBtn.appendChild(el('span', null, 'Official Portal'));
        portalBtn.appendChild(el('span', null, '↗'));

        chip.appendChild(titleWrap);
        chip.appendChild(portalBtn);
        chipsContainer.appendChild(chip);
      });

      bubble.appendChild(chipsContainer);
    }

    const timeEl = el('span', 'msg-timestamp', formatTime(timestamp));

    bodyWrapper.appendChild(bubble);
    bodyWrapper.appendChild(timeEl);

    row.appendChild(avatar);
    row.appendChild(bodyWrapper);

    scrollContainer.appendChild(row);
    scrollToBottom();
  }

  function showTypingIndicator() {
    removeTypingIndicator();

    const scrollContainer = document.getElementById('chatMessagesScroll');
    if (!scrollContainer) return;

    const row = el('div', 'chat-message-row assistant-row typing-indicator-row', null, { id: 'chatTypingIndicator' });
    const avatar = el('div', 'msg-avatar', '🤖');
    const bubble = el('div', 'typing-bubble');

    bubble.appendChild(el('div', 'typing-dot'));
    bubble.appendChild(el('div', 'typing-dot'));
    bubble.appendChild(el('div', 'typing-dot'));

    row.appendChild(avatar);
    row.appendChild(bubble);

    scrollContainer.appendChild(row);
    scrollToBottom();
  }

  function removeTypingIndicator() {
    const existing = document.getElementById('chatTypingIndicator');
    if (existing) existing.remove();
  }

  function showError(message) {
    const toast = document.getElementById('chatErrorToast');
    const msgEl = document.getElementById('chatErrorMessage');
    if (toast && msgEl) {
      msgEl.textContent = message || 'Connection error. Please try again.';
      toast.style.display = 'flex';
    }
  }

  function hideError() {
    const toast = document.getElementById('chatErrorToast');
    if (toast) toast.style.display = 'none';
  }

  // ============================================================================
  // Conversations Sidebar Management
  // ============================================================================

  async function loadConversationsList() {
    const config = window.SchemeAIConfig || {};
    const backendUrl = config.BACKEND_API_URL || 'http://127.0.0.1:8000';
    const listContainer = document.getElementById('conversationsList');
    if (!listContainer) return;

    try {
      const res = await fetch(`${backendUrl}/api/chat/conversations`, {
        headers: {
          'Authorization': `Bearer ${currentToken}`
        }
      });

      if (res.ok) {
        const data = await res.json();
        const convs = data.conversations || [];
        renderConversationsSidebar(convs);
      }
    } catch (e) {
      console.warn('[SchemeAI Chat] Could not fetch conversations list:', e);
    }
  }

  function renderConversationsSidebar(conversations) {
    const listContainer = document.getElementById('conversationsList');
    if (!listContainer) return;

    listContainer.replaceChildren();

    if (!conversations || conversations.length === 0) {
      const emptyNote = el('div', null, 'No previous chats yet.', {
        style: 'font-size: 0.78rem; color: var(--slate-400); padding: 0.5rem 0.75rem;'
      });
      listContainer.appendChild(emptyNote);
      return;
    }

    conversations.forEach(c => {
      const item = el('div', `conversation-item ${c.id === currentConversationId ? 'active' : ''}`, null, {
        'data-conv-id': c.id
      });

      const title = el('div', 'conversation-item-title', c.title || 'Scheme Inquiry');
      const date = el('div', 'conversation-item-date', formatDate(c.updated_at || c.created_at));

      item.appendChild(title);
      item.appendChild(date);

      item.addEventListener('click', () => loadConversationThread(c.id, c.title));
      listContainer.appendChild(item);
    });
  }

  async function loadConversationThread(convId, title) {
    if (convId === currentConversationId && !document.getElementById('chatWelcomeBox')?.style.display) {
      return;
    }

    currentConversationId = convId;
    hideError();

    // Close mobile drawer if open
    document.getElementById('chatSidebar')?.classList.remove('open');

    // Update title
    const titleEl = document.getElementById('chatThreadTitle');
    if (titleEl) titleEl.textContent = title || 'AI Funding & Scheme Matcher Assistant';

    // Highlight active in sidebar
    document.querySelectorAll('.conversation-item').forEach(item => {
      item.classList.toggle('active', item.getAttribute('data-conv-id') === convId);
    });

    // Clear messages and hide welcome
    const scrollContainer = document.getElementById('chatMessagesScroll');
    if (scrollContainer) scrollContainer.replaceChildren();

    const welcomeBox = document.getElementById('chatWelcomeBox');
    if (welcomeBox) welcomeBox.style.display = 'none';

    showTypingIndicator();

    const config = window.SchemeAIConfig || {};
    const backendUrl = config.BACKEND_API_URL || 'http://127.0.0.1:8000';

    try {
      const res = await fetch(`${backendUrl}/api/chat/history?conversation_id=${convId}`, {
        headers: {
          'Authorization': `Bearer ${currentToken}`
        }
      });

      removeTypingIndicator();

      if (res.ok) {
        const data = await res.json();
        const messages = data.messages || [];
        messages.forEach(m => {
          if (m.role === 'user') {
            appendUserMessage(m.content, m.created_at);
          } else if (m.role === 'assistant') {
            const refs = (m.metadata && m.metadata.referenced_schemes) || [];
            appendAssistantMessage(m.content, refs, m.created_at);
          }
        });
      } else {
        showError('Could not load conversation history.');
      }
    } catch (e) {
      removeTypingIndicator();
      showError('Network error while retrieving conversation messages.');
    }
  }

  function startNewConversation() {
    currentConversationId = null;
    hideError();

    // Update title
    const titleEl = document.getElementById('chatThreadTitle');
    if (titleEl) titleEl.textContent = 'AI Funding & Scheme Matcher Assistant';

    // Deselect sidebar items
    document.querySelectorAll('.conversation-item').forEach(item => item.classList.remove('active'));

    // Clear messages and restore welcome box
    const scrollContainer = document.getElementById('chatMessagesScroll');
    if (scrollContainer) {
      scrollContainer.replaceChildren();
      const welcomeBox = document.getElementById('chatWelcomeBox');
      if (welcomeBox) {
        welcomeBox.style.display = 'block';
        scrollContainer.appendChild(welcomeBox);
      }
    }

    // Close mobile drawer
    document.getElementById('chatSidebar')?.classList.remove('open');

    // Focus input
    document.getElementById('chatInput')?.focus();
  }

  // ============================================================================
  // Sending Messages & Streaming/Response Handling
  // ============================================================================

  async function sendMessage(textToSend) {
    stopVoiceRecognition();
    const message = (textToSend || document.getElementById('chatInput')?.value || '').trim();
    if (!message || isSending) return;

    lastFailedMessage = message;
    hideError();

    const inputEl = document.getElementById('chatInput');
    const sendBtn = document.getElementById('btnSendChat');
    const langSelect = document.getElementById('selectLanguage');

    const languagePref = (window.SchemeAI_i18n ? window.SchemeAI_i18n.getLanguage() : null) || (langSelect ? langSelect.value : 'auto');

    // 1. Clear input & reset height
    if (inputEl) {
      inputEl.value = '';
      inputEl.style.height = 'auto';
      document.getElementById('charCounter').textContent = '0 / 2000';
    }

    // 2. Render user message in UI immediately
    appendUserMessage(message);

    // 3. Show typing indicator & disable send
    isSending = true;
    if (sendBtn) sendBtn.disabled = true;
    showTypingIndicator();

    const config = window.SchemeAIConfig || {};
    const backendUrl = config.BACKEND_API_URL || 'http://127.0.0.1:8000';

    try {
      const response = await fetch(`${backendUrl}/api/chat`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${currentToken}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          message: message,
          conversation_id: currentConversationId,
          language_preference: languagePref
        })
      });

      removeTypingIndicator();

      if (response.ok) {
        const data = await response.json();
        
        // Update active conversation ID
        if (data.conversation_id && !currentConversationId) {
          currentConversationId = data.conversation_id;
          // Refresh sidebar list to show new conversation
          loadConversationsList();
        }

        // Render assistant message
        appendAssistantMessage(data.response, data.referenced_schemes, new Date().toISOString());
        lastFailedMessage = null;

      } else {
        const errJson = await response.json().catch(() => ({}));
        const detail = errJson.detail || `Server responded with status ${response.status}`;
        showError(detail);
      }
    } catch (netErr) {
      removeTypingIndicator();
      console.warn('[SchemeAI Chat] Chat request failed:', netErr);
      showError('Unable to connect to the AI Funding & Scheme Matcher Assistant backend. Ensure the server is running on port 8000.');
    } finally {
      isSending = false;
      if (sendBtn) sendBtn.disabled = false;
    }
  }

  // ============================================================================
  // Voice Recognition Subsystem (Web Speech API)
  // ============================================================================

  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition || null;
  let recognitionInstance = null;
  let isListening = false;
  let speechDismissTimer = null;

  // Language Code Mapper: maps site language codes to BCP-47 speech recognition codes
  function getSpeechRecognitionLanguage() {
    const lang = (window.SchemeAI_i18n ? window.SchemeAI_i18n.getLanguage() : null) ||
                 document.getElementById('selectLanguage')?.value || 'en';
    switch (lang) {
      case 'ta':
        return { code: 'ta-IN', name: 'தமிழ் (Tamil)' };
      case 'hi':
        return { code: 'hi-IN', name: 'हिन्दी (Hindi)' };
      case 'te':
        return { code: 'te-IN', name: 'తెలుగు (Telugu)' };
      case 'ml':
        return { code: 'ml-IN', name: 'മലയാളம் (Malayalam)' };
      case 'kn':
        return { code: 'kn-IN', name: 'ಕನ್ನಡ (Kannada)' };
      case 'en':
      default:
        return { code: 'en-IN', name: 'English (India)' };
    }
  }

  // Set Voice Recognition UI State: 'ready' | 'listening' | 'processing' | 'success' | 'error'
  function setVoiceRecognitionState(state, message = '') {
    const micBtn = document.getElementById('btnMicVoiceInput');
    const micIcon = document.getElementById('micIcon');
    const statusBar = document.getElementById('voiceStatusBar');
    const statusText = document.getElementById('voiceStatusText');

    if (speechDismissTimer) {
      clearTimeout(speechDismissTimer);
      speechDismissTimer = null;
    }

    if (!micBtn || !statusBar || !statusText) return;

    // Reset base classes
    micBtn.classList.remove('listening');
    statusBar.className = 'voice-status-bar';

    switch (state) {
      case 'ready':
        isListening = false;
        if (micIcon) micIcon.textContent = '🎤';
        micBtn.title = 'Click to speak (English or தமிழ்)';
        statusBar.style.display = 'none';
        break;

      case 'listening':
        isListening = true;
        micBtn.classList.add('listening');
        if (micIcon) micIcon.textContent = '🔴';
        micBtn.title = 'Listening... Click to stop';
        statusBar.classList.add('listening');
        statusText.textContent = message || `Listening in ${getSpeechRecognitionLanguage().name}... Speak your query`;
        statusBar.style.display = 'flex';
        break;

      case 'processing':
        isListening = false;
        if (micIcon) micIcon.textContent = '⏳';
        micBtn.title = 'Processing recognized speech...';
        statusBar.classList.add('processing');
        statusText.textContent = message || 'Processing speech into text...';
        statusBar.style.display = 'flex';
        break;

      case 'success':
        isListening = false;
        if (micIcon) micIcon.textContent = '🎤';
        micBtn.title = 'Click to speak (English or தமிழ்)';
        statusBar.classList.add('success');
        statusText.textContent = message || 'Speech converted to text. You can review or edit before sending.';
        statusBar.style.display = 'flex';
        speechDismissTimer = setTimeout(() => {
          statusBar.style.display = 'none';
        }, 4000);
        break;

      case 'error':
        isListening = false;
        if (micIcon) micIcon.textContent = '🎤';
        micBtn.title = 'Click to speak (English or தமிழ்)';
        statusBar.classList.add('error');
        statusText.textContent = message || 'Voice recognition error. Please try again or type your query.';
        statusBar.style.display = 'flex';
        speechDismissTimer = setTimeout(() => {
          statusBar.style.display = 'none';
        }, 5500);
        break;
    }
  }

  // Stop active voice recognition safely
  function stopVoiceRecognition() {
    if (recognitionInstance && isListening) {
      try {
        recognitionInstance.stop();
      } catch (e) {
        console.warn('[SchemeAI Voice] Stop recognition error:', e);
      }
    }
    setVoiceRecognitionState('ready');
  }

  // Start or toggle voice recognition
  function toggleVoiceRecognition() {
    if (!SpeechRecognition) {
      setVoiceRecognitionState('error', 'Voice recognition is not supported in this browser. Please use Chrome, Edge, or Safari, or type your query.');
      return;
    }

    if (isListening) {
      stopVoiceRecognition();
      return;
    }

    const chatInput = document.getElementById('chatInput');
    const charCounter = document.getElementById('charCounter');
    const langInfo = getSpeechRecognitionLanguage();

    try {
      if (recognitionInstance) {
        try { recognitionInstance.abort(); } catch (e) {}
      }

      recognitionInstance = new SpeechRecognition();
      recognitionInstance.lang = langInfo.code;
      recognitionInstance.continuous = false;
      recognitionInstance.interimResults = true;
      recognitionInstance.maxAlternatives = 1;

      let finalTranscript = '';
      let interimTranscript = '';
      const initialInputVal = (chatInput?.value || '').trim();

      recognitionInstance.onstart = () => {
        setVoiceRecognitionState('listening', `Listening in ${langInfo.name}... Speak now`);
      };

      recognitionInstance.onaudiostart = () => {
        // Audio stream started
      };

      recognitionInstance.onspeechstart = () => {
        // Speech detected
      };

      recognitionInstance.onresult = (event) => {
        interimTranscript = '';
        for (let i = event.resultIndex; i < event.results.length; ++i) {
          const transcriptChunk = event.results[i][0].transcript;
          if (event.results[i].isFinal) {
            finalTranscript += transcriptChunk;
          } else {
            interimTranscript += transcriptChunk;
          }
        }

        // Live preview into input field so user sees words as they speak
        const currentSpoken = (finalTranscript + (interimTranscript ? ' ' + interimTranscript : '')).trim();
        if (chatInput && currentSpoken) {
          const combined = initialInputVal ? `${initialInputVal} ${currentSpoken}` : currentSpoken;
          chatInput.value = combined;
          chatInput.style.height = 'auto';
          chatInput.style.height = Math.min(chatInput.scrollHeight, 140) + 'px';
          if (charCounter) {
            charCounter.textContent = `${chatInput.value.length} / 2000`;
          }
        }
      };

      recognitionInstance.onspeechend = () => {
        setVoiceRecognitionState('processing', 'Speech completed. Processing text...');
      };

      recognitionInstance.onend = () => {
        const hasText = Boolean(finalTranscript.trim() || interimTranscript.trim());
        if (hasText) {
          setVoiceRecognitionState('success', 'Speech recognized! Review or edit your query, then press Send.');
          if (chatInput) {
            chatInput.focus();
            const len = chatInput.value.length;
            chatInput.setSelectionRange(len, len);
          }
        } else if (isListening) {
          setVoiceRecognitionState('ready');
        }
      };

      recognitionInstance.onerror = (event) => {
        console.warn('[SchemeAI Voice] Speech recognition error:', event.error);
        switch (event.error) {
          case 'not-allowed':
          case 'service-not-allowed':
            setVoiceRecognitionState('error', 'Microphone access denied. Please click the camera/mic icon in your browser address bar to allow microphone access.');
            break;
          case 'no-speech':
            setVoiceRecognitionState('error', 'No speech detected. Click the microphone and speak clearly.');
            break;
          case 'network':
            setVoiceRecognitionState('error', 'Network error during speech recognition. Please check your internet connection.');
            break;
          case 'language-not-supported':
            setVoiceRecognitionState('error', `Language ${langInfo.name} is not supported by your browser's speech engine.`);
            break;
          case 'aborted':
            setVoiceRecognitionState('ready');
            break;
          default:
            setVoiceRecognitionState('error', `Voice error (${event.error}). Please try again or type your query.`);
        }
      };

      recognitionInstance.start();

    } catch (err) {
      console.error('[SchemeAI Voice] Failed to start SpeechRecognition:', err);
      setVoiceRecognitionState('error', 'Could not start voice recognition. Please verify microphone permissions.');
    }
  }

  // ============================================================================
  // Initialization & Event Wiring
  // ============================================================================

  document.addEventListener('DOMContentLoaded', async () => {
    // 1. Enforce Authentication
    const session = await window.SchemeAIAuth.requireAuth('login.html');
    if (!session) return;

    currentToken = session.access_token;
    currentUser = session.user;

    // 2. Update Backend Status Badge
    const healthBadge = document.getElementById('backendStatusBadge');
    const config = window.SchemeAIConfig || {};
    const backendUrl = config.BACKEND_API_URL || 'http://127.0.0.1:8000';

    try {
      const healthRes = await fetch(`${backendUrl}/api/health`);
      if (healthRes.ok) {
        if (healthBadge) {
          healthBadge.textContent = '🟢 AI Assistant Ready (v1.0.0)';
          healthBadge.className = 'badge badge-success';
        }
      }
    } catch (e) {
      if (healthBadge) {
        healthBadge.textContent = '🟡 Offline Mode (Grounded Engine)';
        healthBadge.className = 'badge badge-gold';
      }
    }

    // 3. Load previous conversations list
    await loadConversationsList();

    // 4. Form Submit & Keydown Listeners
    const chatForm = document.getElementById('chatForm');
    const chatInput = document.getElementById('chatInput');
    const charCounter = document.getElementById('charCounter');

    if (chatForm) {
      chatForm.addEventListener('submit', (e) => {
        e.preventDefault();
        sendMessage();
      });
    }

    if (chatInput) {
      // Auto-expand and character counter
      chatInput.addEventListener('input', () => {
        chatInput.style.height = 'auto';
        chatInput.style.height = Math.min(chatInput.scrollHeight, 140) + 'px';
        if (charCounter) {
          charCounter.textContent = `${chatInput.value.length} / 2000`;
        }
      });

      // Submit on Enter (Shift+Enter for newline)
      chatInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
          e.preventDefault();
          sendMessage();
        }
      });
    }

    // 5. Suggested Prompts Click Listeners
    document.querySelectorAll('.suggested-prompt-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        const spanText = btn.querySelector('span[data-i18n]')?.textContent?.trim();
        const prompt = spanText || btn.getAttribute('data-prompt');
        if (prompt) {
          sendMessage(prompt);
        }
      });
    });

    // 6. Sidebar New Chat Button & Header Clear Chat Button
    document.getElementById('btnNewChat')?.addEventListener('click', startNewConversation);
    document.getElementById('btnClearChat')?.addEventListener('click', () => {
      startNewConversation();
    });

    // 7. Mobile Sidebar Drawer Toggle
    document.getElementById('btnToggleSidebar')?.addEventListener('click', () => {
      document.getElementById('chatSidebar')?.classList.toggle('open');
    });

    // 8. Retry Button
    document.getElementById('btnRetryChat')?.addEventListener('click', () => {
      if (lastFailedMessage) {
        sendMessage(lastFailedMessage);
      }
    });

    // 9. Signout Button
    document.getElementById('btnLogout')?.addEventListener('click', () => {
      window.SchemeAIAuth.signOut('login.html');
    });

    // 10. Multilingual Synchronization with SchemeAI_i18n
    const langSelect = document.getElementById('selectLanguage');
    if (langSelect && window.SchemeAI_i18n) {
      langSelect.value = window.SchemeAI_i18n.getLanguage();
      langSelect.addEventListener('change', () => {
        window.SchemeAI_i18n.setLanguage(langSelect.value);
      });
    }

    window.addEventListener('languageChanged', (e) => {
      const newLang = e.detail?.lang || (window.SchemeAI_i18n && window.SchemeAI_i18n.getLanguage());
      if (langSelect && newLang) {
        langSelect.value = newLang;
      }
    });

    // 11. Voice Recognition Microphone Button & Stop Button
    document.getElementById('btnMicVoiceInput')?.addEventListener('click', toggleVoiceRecognition);
    document.getElementById('btnStopVoice')?.addEventListener('click', stopVoiceRecognition);

    // 12. Auto-trigger query from URL parameter if provided (e.g. from scheme dossier)
    const urlParams = new URLSearchParams(window.location.search);
    const initialQuery = urlParams.get('query');
    if (initialQuery && initialQuery.trim()) {
      setTimeout(() => {
        sendMessage(initialQuery.trim());
      }, 300);
    }
  });

})();

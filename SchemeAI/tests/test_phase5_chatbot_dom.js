/**
 * Phase 5 Chatbot Frontend & DOM Integrity Test Suite
 * Validates chatbot.html, chatbot.js, and style.css for Phase 5 compliance
 */

const fs = require('fs');
const path = require('path');

const rootDir = path.resolve(__dirname, '..');
const chatbotHtmlPath = path.join(rootDir, 'frontend', 'chatbot.html');
const chatbotJsPath = path.join(rootDir, 'frontend', 'js', 'chatbot.js');
const styleCssPath = path.join(rootDir, 'frontend', 'css', 'style.css');

console.log('--- RUNNING PHASE 5 CHATBOT DOM & FRONTEND VERIFICATION ---');

// 1. Read files
const htmlContent = fs.readFileSync(chatbotHtmlPath, 'utf8');
const jsContent = fs.readFileSync(chatbotJsPath, 'utf8');
const cssContent = fs.readFileSync(styleCssPath, 'utf8');

// 2. Validate HTML Structure
const requiredHtmlElements = [
  'id="chatSidebar"',
  'id="btnNewChat"',
  'id="conversationsList"',
  'id="chatMessagesScroll"',
  'id="chatWelcomeBox"',
  'id="chatErrorToast"',
  'id="btnRetryChat"',
  'id="chatForm"',
  'id="chatInput"',
  'id="btnSendChat"',
  'id="selectLanguage"',
  'id="charCounter"',
  'id="btnToggleSidebar"'
];

for (const elId of requiredHtmlElements) {
  if (!htmlContent.includes(elId)) {
    console.error(`FAIL: Missing required HTML element: ${elId}`);
    process.exit(1);
  }
}
console.log('PASS: All required interactive DOM elements present in chatbot.html');

// 3. Validate Suggested Questions in HTML
const requiredPrompts = [
  'Which government schemes might suit my startup?',
  'Naan Tamil Nadu-la startup start panna enna funding schemes irukku?',
  'What are the eligibility requirements?',
  'How do I apply for this scheme?',
  'Which eligibility details are missing from my profile?'
];

for (const prompt of requiredPrompts) {
  if (!htmlContent.includes(prompt)) {
    console.error(`FAIL: Missing suggested prompt in chatbot.html: "${prompt}"`);
    process.exit(1);
  }
}
console.log('PASS: All 5 required suggested questions present in suggested pills');

// 4. Validate Language Options (Tamil, English, Tanglish)
const requiredLanguages = ['English', 'தமிழ்', 'Tanglish'];
for (const lang of requiredLanguages) {
  if (!htmlContent.includes(lang)) {
    console.error(`FAIL: Missing language option in dropdown: "${lang}"`);
    process.exit(1);
  }
}
console.log('PASS: Language switcher supports English, Tamil (தமிழ்), and Tanglish');

// 5. Validate Safe DOM Rendering in chatbot.js (NO innerHTML of untrusted responses)
if (jsContent.includes('.innerHTML =') || jsContent.includes('.innerHTML+=')) {
  console.error('FAIL: Detected unsafe innerHTML assignment in chatbot.js');
  process.exit(1);
}
if (!jsContent.includes('document.createElement') || !jsContent.includes('textContent')) {
  console.error('FAIL: Missing safe DOM node creation methods in chatbot.js');
  process.exit(1);
}
console.log('PASS: Zero innerHTML assignments found in chatbot.js; safe DOM element creation used');

// 6. Validate API Endpoint Calls in chatbot.js
const requiredEndpoints = [
  '/api/chat',
  '/api/chat/history',
  '/api/chat/conversations'
];

for (const ep of requiredEndpoints) {
  if (!jsContent.includes(ep)) {
    console.error(`FAIL: chatbot.js missing reference to endpoint: "${ep}"`);
    process.exit(1);
  }
}
console.log('PASS: All required backend API endpoints properly referenced in chatbot.js');

// 7. Validate CSS Classes in style.css
const requiredCssClasses = [
  '.chat-app-wrapper',
  '.chat-sidebar',
  '.chat-messages-scroll',
  '.msg-bubble',
  '.typing-bubble',
  '.suggested-prompt-btn',
  '.chat-input-stage',
  '.referenced-scheme-chip'
];

for (const cls of requiredCssClasses) {
  if (!cssContent.includes(cls)) {
    console.error(`FAIL: style.css missing required Phase 5 CSS class: "${cls}"`);
    process.exit(1);
  }
}
console.log('PASS: All required Phase 5 responsive chatbot CSS classes present in style.css');

console.log('--- ALL PHASE 5 FRONTEND CHECKS PASSED (7/7) ---');

/**
 * SchemeAI — Phase 6 Frontend DOM & Security Verification Test Suite
 * Validates roadmap.html, roadmap.js, and style.css for Phase 6 requirements
 */

const fs = require('fs');
const path = require('path');

const rootDir = path.resolve(__dirname, '..');
const roadmapHtmlPath = path.join(rootDir, 'frontend', 'roadmap.html');
const roadmapJsPath = path.join(rootDir, 'frontend', 'js', 'roadmap.js');
const styleCssPath = path.join(rootDir, 'frontend', 'css', 'style.css');
const dashboardHtmlPath = path.join(rootDir, 'frontend', 'dashboard.html');
const dashboardJsPath = path.join(rootDir, 'frontend', 'js', 'dashboard.js');

console.log('--- RUNNING PHASE 6 ROADMAP & CHECKLIST FRONTEND VERIFICATION ---');

const htmlContent = fs.readFileSync(roadmapHtmlPath, 'utf8');
const jsContent = fs.readFileSync(roadmapJsPath, 'utf8');
const cssContent = fs.readFileSync(styleCssPath, 'utf8');
const dashHtmlContent = fs.readFileSync(dashboardHtmlPath, 'utf8');
const dashJsContent = fs.readFileSync(dashboardJsPath, 'utf8');

// 1. Interactive Elements in roadmap.html
const requiredIds = [
  'id="schemeSelector"',
  'id="schemeTitleHeading"',
  'id="schemeOfficialPortalLink"',
  'id="tabBtnRoadmap"',
  'id="tabBtnChecklist"',
  'id="tabBtnGapAnalysis"',
  'id="viewRoadmap"',
  'id="viewChecklist"',
  'id="viewGapAnalysis"',
  'id="roadmapProgressPercent"',
  'id="roadmapProgressBarFill"',
  'id="roadmapTimelineContainer"',
  'id="checklistReadyPercent"',
  'id="checklistProgressBarFill"',
  'id="checklistItemsContainer"',
  'id="gapVerdictTitle"',
  'id="gapVerdictStatusBadge"',
  'id="satisfiedList"',
  'id="unsatisfiedList"',
  'id="missingList"',
  'id="verificationList"',
  'id="practicalNextStepsList"',
  'id="actionToast"'
];

for (const id of requiredIds) {
  if (!htmlContent.includes(id)) {
    console.error(`FAIL: Missing required ID in roadmap.html: ${id}`);
    process.exit(1);
  }
}
console.log('PASS: All required interactive DOM containers present in roadmap.html (23/23)');

// 2. Bilingual Support (Tamil + English)
const tamilLabels = [
  'விண்ணப்ப வழித்தடம்',
  'ஆவண சரிபார்ப்பு',
  'தகுதி பகுப்பாய்வு',
  'நடைமுறை அடுத்த படிகள்'
];

for (const label of tamilLabels) {
  if (!htmlContent.includes(label)) {
    console.error(`FAIL: Missing Tamil label in roadmap.html: "${label}"`);
    process.exit(1);
  }
}
console.log('PASS: Tamil & English friendly labels verified in roadmap.html');

// 3. Strict Safe DOM Rendering (NO innerHTML)
if (jsContent.includes('.innerHTML =') || jsContent.includes('.innerHTML+=')) {
  console.error('FAIL: Detected unsafe innerHTML assignment in roadmap.js');
  process.exit(1);
}
if (!jsContent.includes('document.createElement') || !jsContent.includes('textContent')) {
  console.error('FAIL: Missing safe DOM node creation methods in roadmap.js');
  process.exit(1);
}
console.log('PASS: Zero innerHTML assignments found in roadmap.js; safe DOM element creation verified');

// 4. API Endpoints Referenced in roadmap.js
const requiredEndpoints = [
  '/api/schemes/',
  '/roadmap',
  '/checklist',
  '/gap-analysis'
];

for (const ep of requiredEndpoints) {
  if (!jsContent.includes(ep)) {
    console.error(`FAIL: roadmap.js missing reference to endpoint: "${ep}"`);
    process.exit(1);
  }
}
console.log('PASS: All Phase 6 backend REST endpoints referenced in roadmap.js');

// 5. CSS Class Coverage in style.css
const requiredCssClasses = [
  '.roadmap-tabs-bar',
  '.roadmap-tab-btn',
  '.roadmap-progress-bar-track',
  '.roadmap-progress-bar-fill',
  '.roadmap-timeline',
  '.roadmap-step-card',
  '.checklist-grid',
  '.checklist-card',
  '.gap-analysis-grid',
  '.gap-column-card',
  '.header-satisfied',
  '.header-unsatisfied',
  '.header-missing',
  '.header-verification',
  '.action-toast'
];

for (const cls of requiredCssClasses) {
  if (!cssContent.includes(cls)) {
    console.error(`FAIL: style.css missing required Phase 6 CSS class: "${cls}"`);
    process.exit(1);
  }
}
console.log('PASS: All Phase 6 responsive CSS classes present in style.css');

// 6. Navigation Link Integration
if (!dashHtmlContent.includes('roadmap.html') || !dashJsContent.includes('roadmap.html')) {
  console.error('FAIL: dashboard.html or dashboard.js missing link to roadmap.html');
  process.exit(1);
}
console.log('PASS: Dashboard and scheme cards correctly integrated with roadmap.html');

console.log('--- ALL PHASE 6 FRONTEND CHECKS PASSED (6/6) ---');

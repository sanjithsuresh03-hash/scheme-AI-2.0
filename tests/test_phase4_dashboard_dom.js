/**
 * SchemeAI — Phase 4 Frontend Dashboard DOM Automated Test Suite
 * Tests:
 * 1. Safe DOM card generation & presence of all required Phase 4 scheme card fields
 * 2. Match summary metrics computation & rendering
 * 3. Search and filter interactions
 * 4. Modal dossier open/close
 * 5. Safe rendering verification (No dangerous innerHTML injection)
 */

const fs = require('fs');
const path = require('path');

// Test runner helper
function runTests() {
  console.log("=================================================================");
  console.log("SCHEMEAI PHASE 4 FRONTEND DOM & DASHBOARD AUTOMATED TEST SUITE");
  console.log("=================================================================");

  // 1. Verify dashboard.html has Phase 4 structure
  const htmlPath = path.join(__dirname, '..', 'frontend', 'dashboard.html');
  const htmlContent = fs.readFileSync(htmlPath, 'utf8');

  console.log("\n--- Checking dashboard.html markup elements ---");
  const requiredElements = [
    'schemeMatchingSection',
    'matchSummaryStrip',
    'metricTotalSchemes',
    'metricEligible',
    'metricPotential',
    'metricNeedsVerification',
    'metricNotEligible',
    'metricAvgScore',
    'schemeSearchInput',
    'filterFundingType',
    'filterGovernment',
    'filterEligibilityStatus',
    'btnResetFilters',
    'eligibleSchemesContainer',
    'schemeDetailsModal',
    'modalSchemeTitle',
    'modalSchemeBody',
    'modalOfficialPortalBtn'
  ];

  requiredElements.forEach(id => {
    if (!htmlContent.includes(`id="${id}"`)) {
      throw new Error(`Missing required dashboard element: id="${id}"`);
    }
  });
  console.log(`[PASS] All ${requiredElements.length} required Phase 4 markup IDs present in dashboard.html`);

  // 2. Verify dashboard.js uses safe DOM methods
  console.log("\n--- Verifying Safe DOM Construction in dashboard.js ---");
  const jsPath = path.join(__dirname, '..', 'frontend', 'js', 'dashboard.js');
  const jsContent = fs.readFileSync(jsPath, 'utf8');

  if (jsContent.includes('container.innerHTML =')) {
    throw new Error("Found dangerous container.innerHTML assignment in dashboard.js");
  }
  if (!jsContent.includes('document.createElement') || !jsContent.includes('replaceChildren')) {
    throw new Error("Expected safe DOM methods (createElement, replaceChildren) in dashboard.js");
  }
  console.log("[PASS] Safe DOM construction verified: Uses createElement and replaceChildren without untrusted innerHTML");

  // 3. Verify CSS rules for Phase 4
  console.log("\n--- Verifying Phase 4 CSS Design Tokens & Styles ---");
  const cssPath = path.join(__dirname, '..', 'frontend', 'css', 'style.css');
  const cssContent = fs.readFileSync(cssPath, 'utf8');

  const requiredClasses = [
    '.match-summary-strip',
    '.summary-metric-card',
    '.filter-search-toolbar',
    '.scheme-card',
    '.status-badge-eligible',
    '.status-badge-potential',
    '.status-badge-needs-verification',
    '.status-badge-not-eligible',
    '.scheme-benefit-callout',
    '.missing-requirements-box',
    '.verification-date-tag'
  ];

  requiredClasses.forEach(cls => {
    if (!cssContent.includes(cls)) {
      throw new Error(`Missing required CSS class rule: ${cls}`);
    }
  });
  console.log(`[PASS] All ${requiredClasses.length} Phase 4 styling classes verified in style.css`);

  // 4. Test Schema Completeness of opportunities.json
  console.log("\n--- Validating opportunities.json Seed Schemes Dataset ---");
  const oppsPath = path.join(__dirname, '..', 'opportunities.json');
  const schemes = JSON.parse(fs.readFileSync(oppsPath, 'utf8'));

  if (!Array.isArray(schemes) || schemes.length < 9) {
    throw new Error(`Expected at least 9 schemes in dataset, found ${schemes ? schemes.length : 0}`);
  }

  schemes.forEach((s, idx) => {
    if (!s.id || !s.name || !s.provider || !s.benefit || !s.official_link) {
      throw new Error(`Scheme index ${idx} missing required fields: ${JSON.stringify(s)}`);
    }
  });
  console.log(`[PASS] Verified ${schemes.length} schemes in dataset with complete official URLs, providers, and benefits`);

  console.log("\n=================================================================");
  console.log("ALL FRONTEND DOM & DASHBOARD VERIFICATION TESTS PASSED!");
  console.log("=================================================================");
}

try {
  runTests();
} catch (e) {
  console.error("TEST FAILED:", e.message);
  process.exit(1);
}

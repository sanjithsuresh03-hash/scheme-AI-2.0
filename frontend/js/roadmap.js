/**
 * SchemeAI — Application Roadmap, Document Checklist, and Gap Analysis Controller (Phase 6)
 * Smart India Hackathon: AI-Driven Funding & Scheme Matching for Marginalized Entrepreneurs
 * 
 * STRICT PRINCIPLES:
 * 1. Safe DOM Rendering: Absolutely zero untrusted innerHTML injection.
 * 2. Grounded Data: All steps, documents, and criteria come directly from verified backend endpoints.
 * 3. Privacy Preservation: No document upload, no Aadhaar or bank credentials stored.
 * 4. User Ownership: All progress updates are tied to authenticated user session.
 */

(function () {
  'use strict';

  let currentSchemeId = 'sisfs';
  let currentUser = null;
  let currentToken = null;
  let activeTab = 'roadmap';

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

  // Toast Notification
  function showToast(message, isError = false) {
    const toast = document.getElementById('actionToast');
    const msgEl = document.getElementById('actionToastMessage');
    if (!toast || !msgEl) return;

    msgEl.textContent = message;
    toast.style.background = isError ? 'rgba(239, 68, 68, 0.95)' : 'rgba(15, 118, 110, 0.95)';
    toast.style.display = 'block';

    setTimeout(() => {
      toast.style.display = 'none';
    }, 3200);
  }

  // Get Backend URL
  function getBackendUrl() {
    const config = window.SchemeAIConfig || {};
    return config.BACKEND_API_URL || 'http://127.0.0.1:8000';
  }

  // Format Timestamps
  function formatTimestamp(isoStr) {
    if (!isoStr) return 'Just now';
    try {
      const d = new Date(isoStr);
      return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) + ', ' +
             d.toLocaleDateString([], { month: 'short', day: 'numeric' });
    } catch (e) {
      return 'Recently';
    }
  }

  // ============================================================================
  // TAB NAVIGATION
  // ============================================================================

  function setupTabNavigation() {
    const tabRoadmap = document.getElementById('tabBtnRoadmap');
    const tabChecklist = document.getElementById('tabBtnChecklist');
    const tabGap = document.getElementById('tabBtnGapAnalysis');

    const viewRoadmap = document.getElementById('viewRoadmap');
    const viewChecklist = document.getElementById('viewChecklist');
    const viewGap = document.getElementById('viewGapAnalysis');

    function switchTab(target) {
      activeTab = target;
      [tabRoadmap, tabChecklist, tabGap].forEach(btn => btn?.classList.remove('active'));
      [viewRoadmap, viewChecklist, viewGap].forEach(panel => {
        if (panel) panel.style.display = 'none';
      });

      if (target === 'roadmap') {
        tabRoadmap?.classList.add('active');
        if (viewRoadmap) viewRoadmap.style.display = 'block';
      } else if (target === 'checklist') {
        tabChecklist?.classList.add('active');
        if (viewChecklist) viewChecklist.style.display = 'block';
      } else if (target === 'gap') {
        tabGap?.classList.add('active');
        if (viewGap) viewGap.style.display = 'block';
      }
    }

    tabRoadmap?.addEventListener('click', () => switchTab('roadmap'));
    tabChecklist?.addEventListener('click', () => switchTab('checklist'));
    tabGap?.addEventListener('click', () => switchTab('gap'));
  }

  // ============================================================================
  // LOAD ALL SCHEME DATA
  // ============================================================================

  async function loadAllSchemeData(schemeId) {
    currentSchemeId = schemeId;
    await Promise.all([
      loadSchemeRoadmap(schemeId),
      loadSchemeChecklist(schemeId),
      loadSchemeGapAnalysis(schemeId)
    ]);
  }

  // ============================================================================
  // 1. APPLICATION ROADMAP (Safe DOM)
  // ============================================================================

  async function loadSchemeRoadmap(schemeId) {
    const backendUrl = getBackendUrl();
    const container = document.getElementById('roadmapTimelineContainer');
    if (!container) return;

    try {
      const res = await fetch(`${backendUrl}/api/schemes/${encodeURIComponent(schemeId)}/roadmap`, {
        headers: { 'Authorization': `Bearer ${currentToken}` }
      });

      if (!res.ok) {
        throw new Error(`Failed to load roadmap: HTTP ${res.status}`);
      }

      const json = await res.json();
      const roadmap = json.roadmap || {};
      renderRoadmapHeader(roadmap);
      renderRoadmapTimeline(roadmap);
    } catch (err) {
      console.error('[SchemeAI Roadmap Error]:', err);
      container.replaceChildren();
      const errBox = el('div', 'alert-banner alert-warning', 'Failed to load application roadmap. Please check backend service.');
      container.appendChild(errBox);
    }
  }

  function renderRoadmapHeader(roadmap) {
    const heading = document.getElementById('schemeTitleHeading');
    const providerBadge = document.getElementById('schemeProviderBadge');
    const portalLink = document.getElementById('schemeOfficialPortalLink');
    const linkText = document.getElementById('officialLinkText');
    const benefitDesc = document.getElementById('schemeBenefitDesc');
    const percentEl = document.getElementById('roadmapProgressPercent');
    const barFill = document.getElementById('roadmapProgressBarFill');
    const stepsCounter = document.getElementById('roadmapStepsCounter');
    const statusBadge = document.getElementById('roadmapStatusBadge');
    const lastUpdated = document.getElementById('roadmapLastUpdated');
    const chatBtn = document.getElementById('btnAskAssistantForScheme');

    if (heading) heading.textContent = roadmap.scheme_name || 'Government Scheme';
    if (providerBadge) providerBadge.textContent = roadmap.provider || 'Government Agency';
    if (benefitDesc) benefitDesc.textContent = `Official Guidelines • ${roadmap.total_steps || 0} Verified Steps`;

    const pct = roadmap.progress_percentage || 0;
    if (percentEl) percentEl.textContent = `${pct}%`;
    if (barFill) barFill.style.width = `${pct}%`;
    if (stepsCounter) stepsCounter.textContent = `${roadmap.completed_steps || 0} of ${roadmap.total_steps || 0} Steps Completed`;
    if (lastUpdated) lastUpdated.textContent = `Last updated: ${formatTimestamp(roadmap.last_updated)}`;

    if (statusBadge) {
      statusBadge.textContent = roadmap.overall_status || 'Not started';
      statusBadge.className = `badge ${roadmap.overall_status === 'Completed' ? 'badge-success' : (roadmap.overall_status === 'In progress' ? 'badge-teal' : 'badge-navy')}`;
    }

    if (portalLink && linkText) {
      if (roadmap.is_link_verified && roadmap.official_link) {
        portalLink.href = roadmap.official_link;
        portalLink.className = 'badge badge-success';
        portalLink.style.display = 'inline-flex';
        linkText.textContent = roadmap.official_link;
      } else {
        portalLink.href = '#';
        portalLink.className = 'badge badge-gold';
        linkText.textContent = 'Not verified, check official site';
      }
    }

    if (chatBtn) {
      chatBtn.href = `chatbot.html?query=${encodeURIComponent('Tell me about application steps and requirements for ' + (roadmap.scheme_name || currentSchemeId))}`;
    }
  }

  function renderRoadmapTimeline(roadmap) {
    const container = document.getElementById('roadmapTimelineContainer');
    if (!container) return;

    container.replaceChildren();
    const steps = roadmap.steps || [];

    if (steps.length === 0) {
      const emptyCard = el('div', 'card', 'No application steps recorded for this scheme.');
      container.appendChild(emptyCard);
      return;
    }

    steps.forEach((step, idx) => {
      const card = el('article', 'roadmap-step-card', null, { 'data-step-id': step.step_id });

      // Step Header
      const header = el('div', 'step-card-header');

      const indexPill = el('div', 'step-index-pill', String(step.step_index || (idx + 1)));
      const infoWrap = el('div', 'step-info-wrap');

      const title = el('h4', 'step-title', step.title);
      const meta = el('span', 'step-meta', `Verified application procedure • Step ${step.step_index}`);

      infoWrap.appendChild(title);
      infoWrap.appendChild(meta);
      header.appendChild(indexPill);
      header.appendChild(infoWrap);

      // Status selector controls
      const controlsWrap = el('div', 'step-controls-wrap');
      const statuses = ['Not started', 'In progress', 'Completed'];

      statuses.forEach(st => {
        const isCurrent = (step.status === st);
        const btn = el('button', `btn btn-sm ${isCurrent ? 'btn-primary' : 'btn-outline'}`, st, {
          type: 'button',
          'data-status': st
        });

        if (isCurrent) {
          btn.style.fontWeight = '700';
        }

        btn.addEventListener('click', async () => {
          await updateStepStatus(roadmap.scheme_id, step.step_id, st);
        });

        controlsWrap.appendChild(btn);
      });

      card.appendChild(header);
      card.appendChild(controlsWrap);

      // Timestamp footer
      if (step.last_updated) {
        const footer = el('div', 'step-footer', `Updated: ${formatTimestamp(step.last_updated)}`);
        card.appendChild(footer);
      }

      container.appendChild(card);
    });
  }

  async function updateStepStatus(schemeId, stepId, newStatus) {
    const backendUrl = getBackendUrl();
    try {
      const res = await fetch(`${backendUrl}/api/schemes/${encodeURIComponent(schemeId)}/roadmap/progress`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${currentToken}`
        },
        body: JSON.stringify({ step_id: stepId, status: newStatus })
      });

      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      if (data.roadmap) {
        renderRoadmapHeader(data.roadmap);
        renderRoadmapTimeline(data.roadmap);
      }
      showToast(`Step updated to '${newStatus}'`);
    } catch (err) {
      console.error('[Update Step Error]:', err);
      showToast('Could not save step progress. Please retry.', true);
    }
  }

  // ============================================================================
  // 2. DOCUMENT CHECKLIST (Safe DOM)
  // ============================================================================

  async function loadSchemeChecklist(schemeId) {
    const backendUrl = getBackendUrl();
    const container = document.getElementById('checklistItemsContainer');
    if (!container) return;

    try {
      const res = await fetch(`${backendUrl}/api/schemes/${encodeURIComponent(schemeId)}/checklist`, {
        headers: { 'Authorization': `Bearer ${currentToken}` }
      });

      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const json = await res.json();
      const checklist = json.checklist || {};
      renderChecklistSummary(checklist);
      renderChecklistItems(checklist);
    } catch (err) {
      console.error('[Checklist Error]:', err);
      container.replaceChildren();
      const errBox = el('div', 'alert-banner alert-warning', 'Failed to load document checklist.');
      container.appendChild(errBox);
    }
  }

  function renderChecklistSummary(cl) {
    const percentEl = document.getElementById('checklistReadyPercent');
    const barFill = document.getElementById('checklistProgressBarFill');
    const bReady = document.getElementById('badgeReadyCount');
    const bAttn = document.getElementById('badgeAttentionCount');
    const bVerif = document.getElementById('badgeVerificationCount');
    const bNot = document.getElementById('badgeNotCheckedCount');

    const pct = cl.readiness_percentage || 0;
    if (percentEl) percentEl.textContent = `${pct}%`;
    if (barFill) barFill.style.width = `${pct}%`;

    if (bReady) bReady.textContent = `${cl.ready_count || 0} Ready`;
    if (bAttn) bAttn.textContent = `${cl.needs_attention_count || 0} Needs Attention`;
    if (bVerif) bVerif.textContent = `${cl.needs_verification_count || 0} Needs Verification`;
    if (bNot) bNot.textContent = `${cl.not_checked_count || 0} Not Checked`;
  }

  function renderChecklistItems(cl) {
    const container = document.getElementById('checklistItemsContainer');
    if (!container) return;

    container.replaceChildren();
    const items = cl.items || [];

    if (items.length === 0) {
      const empty = el('div', 'card', 'No document checklist recorded for this scheme.');
      container.appendChild(empty);
      return;
    }

    items.forEach((item, idx) => {
      const card = el('article', 'checklist-card', null, { 'data-item-id': item.item_id });

      const topRow = el('div', 'checklist-card-top');
      const titleWrap = el('div', 'checklist-title-wrap');
      const title = el('h4', 'checklist-item-title', item.name);
      const sourceTag = el('span', 'checklist-source-badge', `Source: ${item.source || 'Official Guidelines'}`);

      titleWrap.appendChild(title);
      titleWrap.appendChild(sourceTag);

      // Current Status Pill
      const statusPill = el('span', `badge ${getChecklistBadgeClass(item.status)}`, item.status);
      topRow.appendChild(titleWrap);
      topRow.appendChild(statusPill);
      card.appendChild(topRow);

      // Explanation
      if (item.explanation) {
        const desc = el('p', 'checklist-explanation', item.explanation);
        card.appendChild(desc);
      }

      // Status selector buttons
      const controls = el('div', 'checklist-controls');
      const validStatuses = ['Ready', 'Needs attention', 'Needs verification', 'Not checked'];

      validStatuses.forEach(st => {
        const isCurrent = (item.status === st);
        const btn = el('button', `btn btn-sm ${isCurrent ? getChecklistBtnClass(st) : 'btn-outline'}`, st, {
          type: 'button'
        });

        btn.addEventListener('click', async () => {
          await updateChecklistItemStatus(cl.scheme_id, item.item_id, st);
        });

        controls.appendChild(btn);
      });

      card.appendChild(controls);
      container.appendChild(card);
    });
  }

  function getChecklistBadgeClass(st) {
    switch (st) {
      case 'Ready': return 'badge-success';
      case 'Needs attention': return 'badge-gold';
      case 'Needs verification': return 'badge-teal';
      default: return 'badge-navy';
    }
  }

  function getChecklistBtnClass(st) {
    switch (st) {
      case 'Ready': return 'btn-primary';
      default: return 'btn-secondary';
    }
  }

  async function updateChecklistItemStatus(schemeId, itemId, newStatus) {
    const backendUrl = getBackendUrl();
    try {
      const res = await fetch(`${backendUrl}/api/schemes/${encodeURIComponent(schemeId)}/checklist/progress`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${currentToken}`
        },
        body: JSON.stringify({ item_id: itemId, status: newStatus })
      });

      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      if (data.checklist) {
        renderChecklistSummary(data.checklist);
        renderChecklistItems(data.checklist);
      }
      showToast(`Document marked as '${newStatus}'`);
    } catch (err) {
      console.error('[Checklist Update Error]:', err);
      showToast('Could not save checklist item. Please retry.', true);
    }
  }

  // ============================================================================
  // 3. ELIGIBILITY GAP ANALYSIS (Safe DOM)
  // ============================================================================

  async function loadSchemeGapAnalysis(schemeId) {
    const backendUrl = getBackendUrl();
    try {
      const res = await fetch(`${backendUrl}/api/schemes/${encodeURIComponent(schemeId)}/gap-analysis`, {
        headers: { 'Authorization': `Bearer ${currentToken}` }
      });

      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const json = await res.json();
      const gap = json.gap_analysis || {};
      renderGapAnalysis(gap);
    } catch (err) {
      console.error('[Gap Analysis Error]:', err);
      renderGapError();
    }
  }

  function renderGapAnalysis(gap) {
    // Verdict Banner
    const verdictTitle = document.getElementById('gapVerdictTitle');
    const verdictBadge = document.getElementById('gapVerdictStatusBadge');
    const verdictDesc = document.getElementById('gapVerdictDesc');
    const verdictCard = document.getElementById('gapVerdictCard');

    if (verdictTitle) verdictTitle.textContent = gap.verdict || 'Eligibility Evaluation Complete';
    if (verdictBadge) {
      verdictBadge.textContent = gap.verdict_status || 'Analyzed';
      verdictBadge.className = `badge ${gap.verdict_status === 'Satisfied' ? 'badge-success' : (gap.verdict_status === 'Unsatisfied' ? 'badge-danger' : 'badge-gold')}`;
    }
    if (verdictDesc) {
      verdictDesc.textContent = `Profile evaluated against ${gap.scheme_name || 'scheme'} rules. Results are deterministic reflections of verified records.`;
    }
    if (verdictCard) {
      verdictCard.style.borderLeftColor = gap.verdict_status === 'Satisfied' ? 'var(--emerald-400)' : (gap.verdict_status === 'Unsatisfied' ? 'var(--rose-500)' : 'var(--amber-400)');
    }

    // 1. Satisfied Requirements
    renderGapList('satisfiedList', gap.satisfied_requirements || [], (item) => {
      const wrap = el('div', 'gap-item-entry item-satisfied');
      const title = el('strong', null, item.criterion || 'Criterion');
      const rationale = el('p', null, `${item.rationale || item.rule} (Profile: ${item.user_value || 'Verified'})`);
      wrap.appendChild(title);
      wrap.appendChild(rationale);
      return wrap;
    }, 'No verified satisfied requirements yet.');

    // 2. Unsatisfied Requirements
    renderGapList('unsatisfiedList', gap.unsatisfied_requirements || [], (item) => {
      const wrap = el('div', 'gap-item-entry item-unsatisfied');
      const title = el('strong', null, item.criterion || 'Gap');
      const reason = el('p', null, `${item.reason || item.rule} (Current: ${item.user_value || 'Unmet'})`);
      wrap.appendChild(title);
      wrap.appendChild(reason);
      return wrap;
    }, 'No confirmed eligibility disqualifications found.');

    // 3. Missing Information
    renderGapList('missingList', gap.missing_information || [], (item) => {
      const wrap = el('div', 'gap-item-entry item-missing');
      const title = el('strong', null, item.criterion || 'Missing Field');
      const impact = el('p', null, `${item.impact || 'Required for evaluation.'} → ${item.how_to_provide || 'Update profile'}`);
      wrap.appendChild(title);
      wrap.appendChild(impact);
      return wrap;
    }, 'No required profile information missing.');

    // 4. Requirements Requiring Official Verification
    renderGapList('verificationList', gap.needs_official_verification || [], (item) => {
      const wrap = el('div', 'gap-item-entry item-verification');
      const title = el('strong', null, item.criterion || 'Verification');
      const note = el('p', null, `${item.note || ''} (Reviewing Body: ${item.verification_body || 'Official Board'})`);
      wrap.appendChild(title);
      wrap.appendChild(note);
      return wrap;
    }, 'No special institutional interviews or jury evaluations flagged.');

    // Practical Next Steps List
    const stepsList = document.getElementById('practicalNextStepsList');
    if (stepsList) {
      stepsList.replaceChildren();
      const steps = gap.practical_next_steps || [];
      if (steps.length === 0) {
        stepsList.appendChild(el('li', null, 'Review the verified document checklist above and prepare required items.'));
      } else {
        steps.forEach(stepText => {
          stepsList.appendChild(el('li', null, stepText));
        });
      }
    }
  }

  function renderGapList(containerId, items, renderFn, emptyText) {
    const container = document.getElementById(containerId);
    if (!container) return;

    container.replaceChildren();
    if (items.length === 0) {
      container.appendChild(el('div', 'gap-empty-text', emptyText));
      return;
    }

    items.forEach(item => {
      container.appendChild(renderFn(item));
    });
  }

  function renderGapError() {
    const verdictTitle = document.getElementById('gapVerdictTitle');
    const verdictDesc = document.getElementById('gapVerdictDesc');
    if (verdictTitle) verdictTitle.textContent = 'Gap Analysis Unavailable';
    if (verdictDesc) verdictDesc.textContent = 'Please make sure your profile registration is complete.';
  }

  // ============================================================================
  // INITIALIZATION
  // ============================================================================

  document.addEventListener('DOMContentLoaded', async () => {
    // 1. Session verification
    if (window.SchemeAIAuth) {
      const session = await window.SchemeAIAuth.requireAuth('login.html');
      if (session && session.user) {
        currentUser = session.user;
        currentToken = session.access_token || `mock-demo-token-${session.user.id}`;
      }
    }

    if (!currentToken) {
      currentToken = 'mock-demo-token-demo-entrepreneur-001';
    }

    // 2. Setup Tabs
    setupTabNavigation();

    // 3. Scheme Selector change handler
    const selector = document.getElementById('schemeSelector');
    if (selector) {
      // Check URL query parameters for ?scheme_id=...
      const urlParams = new URLSearchParams(window.location.search);
      const urlScheme = urlParams.get('scheme_id');
      if (urlScheme) {
        selector.value = urlScheme;
        currentSchemeId = urlScheme;
      } else {
        currentSchemeId = selector.value || 'sisfs';
      }

      selector.addEventListener('change', (e) => {
        loadAllSchemeData(e.target.value);
      });
    }

    // 4. Initial Load
    await loadAllSchemeData(currentSchemeId);

    // 5. Signout listener
    document.getElementById('btnLogout')?.addEventListener('click', () => {
      window.SchemeAIAuth?.signOut('login.html');
    });

    // 6. Language change listener
    window.addEventListener('languageChanged', () => {
      loadAllSchemeData(currentSchemeId);
    });
  });

})();

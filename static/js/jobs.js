/**
 * HRMS Candidate Portal - Jobs & Applications JS
 * Handles live job searching, filtering, and job application submission flow.
 */

document.addEventListener('DOMContentLoaded', () => {
  initJobFilters();
  initApplyModal();
});

function initJobFilters() {
  const searchInput = document.getElementById('jobSearchInput');
  const deptFilter = document.getElementById('deptFilter');
  const expFilter = document.getElementById('expFilter');
  const typeFilter = document.getElementById('typeFilter');
  const jobCards = document.querySelectorAll('.job-card-item');
  const countBadge = document.getElementById('availableJobsCount');

  if (!searchInput && !deptFilter && !expFilter && !typeFilter) return;

  function filterJobs() {
    const query = searchInput ? searchInput.value.toLowerCase().trim() : '';
    const dept = deptFilter ? deptFilter.value.toLowerCase() : '';
    const exp = expFilter ? expFilter.value.toLowerCase() : '';
    const type = typeFilter ? typeFilter.value.toLowerCase() : '';

    let visibleCount = 0;

    jobCards.forEach(card => {
      const title = card.getAttribute('data-title') || '';
      const cardDept = card.getAttribute('data-dept') || '';
      const cardExp = card.getAttribute('data-exp') || '';
      const cardType = card.getAttribute('data-type') || '';
      const tags = card.getAttribute('data-tags') || '';

      const matchesQuery = !query || title.includes(query) || tags.includes(query);
      const matchesDept = !dept || cardDept === dept;
      const matchesExp = !exp || cardExp === exp;
      const matchesType = !type || cardType === type;

      if (matchesQuery && matchesDept && matchesExp && matchesType) {
        card.style.display = 'flex';
        visibleCount++;
      } else {
        card.style.display = 'none';
      }
    });

    if (countBadge) {
      countBadge.textContent = `${visibleCount} Available Jobs`;
    }

    const emptyContainer = document.getElementById('jobsEmptyState');
    if (emptyContainer) {
      emptyContainer.style.display = visibleCount === 0 ? 'block' : 'none';
    }
  }

  if (searchInput) searchInput.addEventListener('input', filterJobs);
  if (deptFilter) deptFilter.addEventListener('change', filterJobs);
  if (expFilter) expFilter.addEventListener('change', filterJobs);
  if (typeFilter) typeFilter.addEventListener('change', filterJobs);
}

function initApplyModal() {
  const applyButtons = document.querySelectorAll('.btn-apply-job');
  const modal = document.getElementById('applyJobModal');
  const titleSpan = document.getElementById('modalJobTitle');
  const deptSpan = document.getElementById('modalJobDept');
  const applyForm = document.getElementById('quickApplyForm');

  applyButtons.forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.preventDefault();
      const jobTitle = btn.getAttribute('data-job-title') || 'Python Developer';
      const jobDept = btn.getAttribute('data-job-dept') || 'Engineering';

      if (titleSpan) titleSpan.textContent = jobTitle;
      if (deptSpan) deptSpan.textContent = jobDept;

      if (modal) modal.classList.add('show');
    });
  });

  if (applyForm) {
    applyForm.addEventListener('submit', (e) => {
      e.preventDefault();
      
      // Close apply modal
      if (modal) modal.classList.remove('show');

      // Open Success Modal
      const successModal = document.getElementById('applySuccessModal');
      if (successModal) {
        const appNum = 'APP-' + Math.floor(100000 + Math.random() * 900000);
        const appIdEl = document.getElementById('successApplicationId');
        if (appIdEl) appIdEl.textContent = appNum;
        successModal.classList.add('show');
      } else if (window.showToast) {
        window.showToast('Application Submitted!', 'Your application has been received successfully.', 'success');
      }
    });
  }
}

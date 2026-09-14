/**
 * HRMS Candidate Portal - Aptitude Test JS
 * Handles countdown timer, question switching, question palette states, and secure server-side submission.
 * Correct answers are strictly NEVER stored or calculated on the client.
 */

(function () {
  'use strict';

  let questionsData = [];
  let currentIndex = 0;
  const userAnswers = {}; // { [questionId]: optionIndex (0, 1, 2, 3) }
  let timeLeftSeconds = 30 * 60;
  let timerInterval = null;

  document.addEventListener('DOMContentLoaded', () => {
    if (document.getElementById('aptitudeTestArea')) {
      initTestRunner();
    }
  });

  function initTestRunner() {
    // 1. Load questions from window.testConfig or fallback
    if (window.testConfig && Array.isArray(window.testConfig.questions)) {
      questionsData = window.testConfig.questions;
      if (window.testConfig.durationMinutes) {
        timeLeftSeconds = window.testConfig.durationMinutes * 60;
      }
    }

    if (!questionsData || questionsData.length === 0) {
      const qText = document.getElementById('currentQuestionText');
      if (qText) qText.textContent = 'No questions available for this assessment.';
      return;
    }

    // 2. Initial rendering
    renderQuestion(currentIndex);
    renderNavigator();
    startTimer();

    // 3. Setup Navigation buttons
    const prevBtn = document.getElementById('prevQuestionBtn');
    const nextBtn = document.getElementById('nextQuestionBtn');
    const submitBtn = document.getElementById('submitTestBtn');
    const confirmModal = document.getElementById('submitConfirmModal');

    if (prevBtn) {
      prevBtn.addEventListener('click', () => {
        if (currentIndex > 0) {
          currentIndex--;
          renderQuestion(currentIndex);
          updateNavigator();
        }
      });
    }

    if (nextBtn) {
      nextBtn.addEventListener('click', () => {
        if (currentIndex < questionsData.length - 1) {
          currentIndex++;
          renderQuestion(currentIndex);
          updateNavigator();
        }
      });
    }

    if (submitBtn) {
      submitBtn.addEventListener('click', () => {
        if (confirmModal) {
          const answeredCount = Object.keys(userAnswers).length;
          const total = questionsData.length;
          const summaryText = document.getElementById('submitSummaryText');
          if (summaryText) {
            summaryText.textContent = `You have answered ${answeredCount} of ${total} questions. Once submitted, you cannot change your answers.`;
          }
          confirmModal.classList.add('show');
        }
      });
    }

    // Modal Close
    document.querySelectorAll('[data-modal-close]').forEach((btn) => {
      btn.addEventListener('click', () => {
        if (confirmModal) confirmModal.classList.remove('show');
      });
    });

    // 4. Final Submission: Submit hidden Django POST form with answers
    const confirmFinalSubmit = document.getElementById('confirmFinalSubmitBtn');
    if (confirmFinalSubmit) {
      confirmFinalSubmit.addEventListener('click', () => {
        submitTestAnswers();
      });
    }
  }

  function submitTestAnswers() {
    if (timerInterval) {
      clearInterval(timerInterval);
    }
    const answersInput = document.getElementById('answersJsonInput');
    const form = document.getElementById('aptitudeSubmitForm');

    if (answersInput && form) {
      answersInput.value = JSON.stringify(userAnswers);
      const confirmSubmitBtn = document.getElementById('confirmFinalSubmitBtn');
      if (confirmSubmitBtn) {
        confirmSubmitBtn.disabled = true;
        confirmSubmitBtn.textContent = 'Submitting & Grading...';
      }
      form.submit();
    } else {
      // Fallback redirect if form not found
      window.location.href = '../aptitude/';
    }
  }

  function startTimer() {
    const timerEl = document.getElementById('timeRemaining');
    if (!timerEl) return;

    updateTimerDisplay(timerEl);

    timerInterval = setInterval(() => {
      if (timeLeftSeconds <= 0) {
        clearInterval(timerInterval);
        alert('Time is up! Submitting your assessment automatically.');
        submitTestAnswers();
        return;
      }
      timeLeftSeconds--;
      updateTimerDisplay(timerEl);
    }, 1000);
  }

  function updateTimerDisplay(timerEl) {
    const mins = Math.floor(timeLeftSeconds / 60);
    const secs = timeLeftSeconds % 60;
    timerEl.textContent = `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    if (timeLeftSeconds < 300) {
      // Last 5 minutes warning
      timerEl.style.color = 'var(--danger)';
      timerEl.style.fontWeight = '700';
    }
  }

  function renderQuestion(index) {
    const q = questionsData[index];
    if (!q) return;

    const qNumEl = document.getElementById('currentQuestionNumber');
    const qTextEl = document.getElementById('currentQuestionText');
    const optionsListEl = document.getElementById('questionOptionsList');

    if (qNumEl) qNumEl.textContent = `Question ${index + 1} of ${questionsData.length}`;
    if (qTextEl) qTextEl.textContent = q.question;

    if (optionsListEl) {
      optionsListEl.innerHTML = '';
      const optionLabels = ['A', 'B', 'C', 'D'];

      q.options.forEach((opt, optIndex) => {
        const isSelected = userAnswers[q.id] === optIndex;
        const optionCard = document.createElement('div');
        optionCard.className = `question-option ${isSelected ? 'selected' : ''}`;
        optionCard.style.cursor = 'pointer';
        optionCard.innerHTML = `
          <div style="width: 22px; height: 22px; border-radius: 50%; border: 2px solid ${
            isSelected ? '#1976F3' : '#CBD5E1'
          }; display: flex; align-items: center; justify-content: center; background: ${
          isSelected ? '#1976F3' : '#FFF'
        }; flex-shrink: 0;">
            ${isSelected ? '<div style="width: 8px; height: 8px; border-radius: 50%; background: #FFF;"></div>' : ''}
          </div>
          <span style="font-weight: 600; color: var(--secondary-text); margin-right: 4px;">${optionLabels[optIndex] || ''}.</span>
          <span style="font-size: 0.938rem; color: #172033;">${escapeHtml(opt)}</span>
        `;

        optionCard.addEventListener('click', () => {
          userAnswers[q.id] = optIndex;
          renderQuestion(currentIndex);
          updateNavigator();
        });

        optionsListEl.appendChild(optionCard);
      });
    }

    // Navigation button states
    const prevBtn = document.getElementById('prevQuestionBtn');
    const nextBtn = document.getElementById('nextQuestionBtn');
    if (prevBtn) prevBtn.disabled = index === 0;
    if (nextBtn) {
      if (index === questionsData.length - 1) {
        nextBtn.style.display = 'none';
      } else {
        nextBtn.style.display = 'inline-flex';
      }
    }
  }

  function renderNavigator() {
    const navGrid = document.getElementById('questionNavGrid');
    if (!navGrid) return;
    navGrid.innerHTML = '';

    questionsData.forEach((q, idx) => {
      const btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'q-nav-btn';
      btn.textContent = idx + 1;
      btn.id = `q-nav-btn-${idx}`;

      btn.addEventListener('click', () => {
        currentIndex = idx;
        renderQuestion(currentIndex);
        updateNavigator();
      });

      navGrid.appendChild(btn);
    });

    updateNavigator();
  }

  function updateNavigator() {
    questionsData.forEach((q, idx) => {
      const btn = document.getElementById(`q-nav-btn-${idx}`);
      if (!btn) return;

      btn.classList.remove('answered', 'current');
      if (userAnswers[q.id] !== undefined) {
        btn.classList.add('answered');
      }
      if (idx === currentIndex) {
        btn.classList.add('current');
      }
    });

    // Update answered count label
    const answeredCountEl = document.getElementById('answeredQuestionsCount');
    if (answeredCountEl) {
      answeredCountEl.textContent = Object.keys(userAnswers).length;
    }
  }

  function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }
})();

/**
 * SecurePass - Shared client-side logic for password strength, generator, and feedback.
 */

function safeQuery(selector) {
  return document.querySelector(selector);
}

function setActiveNav() {
  const links = document.querySelectorAll('.site-nav .nav-link');
  const current = window.location.pathname.split('/').pop();
  links.forEach((link) => {
    const href = link.getAttribute('href');
    if (href === current || (href === 'index.html' && current === '')) {
      link.classList.add('active');
      link.setAttribute('aria-current', 'page');
    }
  });
}

function updateStrengthMeter(password) {
  const bar = safeQuery('#strength-bar');
  const msg = safeQuery('#msg');

  if (!bar || !msg) return;

  // FIX: Handle very short passwords
  if (password.length < 6) {
    bar.style.width = '10%';
    bar.style.backgroundColor = '#ff4d4d';
    msg.textContent = 'Too short';
    msg.style.color = '#ff4d4d';
    return;
  }

  const checks = [
    password.length >= 12,
    /[a-z]/.test(password),
    /[A-Z]/.test(password),
    /\d/.test(password),
    /[^A-Za-z0-9]/.test(password),
  ];

  const score = checks.filter(Boolean).length;

  const colorMap = {
    1: { text: 'Very weak', color: '#ff4d4d' },
    2: { text: 'Weak', color: '#ff9900' },
    3: { text: 'Fair', color: '#f59e0b' },
    4: { text: 'Good', color: '#22c55e' },
    5: { text: 'Strong', color: '#22c55e' },
  };

  const { text, color } = colorMap[score] || colorMap[1];
  const width = (score / 5) * 100;

  bar.style.width = `${width}%`;
  bar.style.backgroundColor = color;

  msg.textContent = `Strength: ${text}`;
  msg.style.color = color;
}

function initStrengthChecker() {
  const passwordInput = safeQuery('#password');
  if (!passwordInput) return;

  passwordInput.addEventListener('input', (event) => {
    updateStrengthMeter(event.target.value.trim());
  });
}

function generatePass(length = 16) {
  const output = safeQuery('#generated-output');
  if (!output) return;

  const chars =
    'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*_-+=';
  const array = new Uint32Array(length);
  crypto.getRandomValues(array);

  const password = Array.from(array)
    .map((value) => chars[value % chars.length])
    .join('');

  output.textContent = password;
  return password;
}

function copyPassword() {
  const output = safeQuery('#generated-output');
  if (!output) return;

  const text = output.textContent.trim();
  if (!text || text === 'Generate') return;

  navigator.clipboard
    .writeText(text)
    .then(() => {
      showToast('Password copied!');
    })
    .catch(() => {
      alert('Copy manually: ' + text);
    });
}

function showToast(message) {
  // FIX: prevent multiple toasts
  const existing = document.querySelector('.toast');
  if (existing) existing.remove();

  const toast = document.createElement('div');
  toast.className = 'toast';
  toast.textContent = message;

  document.body.appendChild(toast);

  setTimeout(() => {
    toast.classList.add('visible');
  }, 10);

  setTimeout(() => {
    toast.classList.remove('visible');
    setTimeout(() => toast.remove(), 300);
  }, 2800);
}

function initGenerateButtons() {
  const genBtn = safeQuery('#gen-btn');
  const copyBtn = safeQuery('#copy-btn');

  if (genBtn) {
    genBtn.addEventListener('click', () => {
      generatePass();
    });
  }

  if (copyBtn) {
    copyBtn.addEventListener('click', copyPassword);
  }
}

function checkLeak() {
  const input = safeQuery('#leaked-password');
  const output = safeQuery('#leak-result');
  if (!input || !output) return;

  const value = input.value.trim();

  const leaked = {
    '123456': true,
    'password': true,
    '12345678': true,
    'qwerty': true,
    '111111': true,
    'abc123': true,
    'letmein': true,
  };

  if (!value) {
    output.textContent = 'Enter a password to check.';
    output.style.color = 'var(--muted)';
    return;
  }

  if (leaked[value]) {
    output.textContent = 'This password is commonly leaked. Please change it.';
    output.style.color = 'var(--danger)';
  } else {
    output.textContent = 'Not found in demo leak list.';
    output.style.color = 'var(--success)';
  }
}

function sendReport(event) {
  if (event) event.preventDefault();

  const email = safeQuery('#report-email');
  const message = safeQuery('#report-message');
  const response = safeQuery('#report-response');

  if (!message || !response) return false;

  const content = message.value.trim();
  if (!content) {
    response.textContent = 'Please enter a message.';
    response.style.color = 'var(--warning)';
    return false;
  }

  const payload = {
    email: email ? email.value.trim() : '',
    message: content,
  };

  fetch('/api/report', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
  })
    .then((res) => res.json())
    .then((data) => {
      if (data.success) {
        response.textContent = 'Feedback sent!';
        response.style.color = 'var(--success)';
        message.value = '';
        if (email) email.value = '';
      } else {
        response.textContent = data.error || 'Failed to send.';
        response.style.color = 'var(--danger)';
      }
    })
    .catch(() => {
      response.textContent = 'Backend not connected yet.';
      response.style.color = 'var(--danger)';
    });

  return false;
}

function initLeakCheck() {
  const button = safeQuery('#leak-check-btn');
  if (button) {
    button.addEventListener('click', checkLeak);
  }
}

function initReportForm() {
  const form = safeQuery('#report-form');
  if (form) {
    form.addEventListener('submit', sendReport);
  }
}

function init() {
  setActiveNav();
  initStrengthChecker();
  initGenerateButtons();
  initLeakCheck();
  initReportForm();
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', init);
} else {
  init();
}
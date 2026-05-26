// Global variables
let videoFeed = null;
let captureCanvas = null;
let autoRecognitionActive = false;

document.addEventListener('DOMContentLoaded', function () {
    videoFeed = document.getElementById('videoFeed');
    captureCanvas = document.getElementById('captureCanvas');

    initializeCamera();
    loadStats();
    refreshLogs();
    setupAutoRecognition();
});

// ── Camera ──────────────────────────────────────────────────────

function initializeCamera() {
    videoFeed.src = '/video_feed';

    fetch('/camera/status')
        .then(r => r.json())
        .then(data => {
            const el = document.getElementById('cameraStatus');
            if (data.available) {
                el.textContent = 'Active';
                el.classList.add('active');
            } else {
                fetch('/camera/initialize')
                    .then(r => r.json())
                    .then(result => {
                        if (result.success) {
                            el.textContent = 'Active';
                            el.classList.add('active');
                        } else {
                            el.textContent = 'Error';
                            showToast(result.message, 'error');
                        }
                    });
            }
        })
        .catch(() => showToast('Camera initialization failed', 'error'));
}

function captureFrame() {
    captureCanvas.width  = 640;
    captureCanvas.height = 480;
    const ctx = captureCanvas.getContext('2d');
    ctx.drawImage(videoFeed, 0, 0, captureCanvas.width, captureCanvas.height);
    return captureCanvas.toDataURL('image/jpeg', 0.95);
}

// ── Registration ─────────────────────────────────────────────────

async function captureAndRegister() {
    const name    = document.getElementById('studentName').value.trim();
    const course  = document.getElementById('studentCourse').value.trim();
    const section = document.getElementById('studentSection').value.trim();

    if (!name || !course || !section) {
        showToast('Please fill in all fields', 'error');
        return;
    }

    showToast('Capturing image…', 'info');
    const imageData = captureFrame();
    showToast('Processing…', 'info');

    try {
        const response = await fetch('/register_student', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, course, section, image: imageData })
        });
        const data = await response.json();

        if (data.success) {
            showToast('✓ ' + data.message, 'success');
            document.getElementById('registerForm').reset();
            loadStats();
        } else {
            showToast('✕ ' + data.message, 'error');
        }
    } catch (e) {
        showToast('Registration failed. Please try again.', 'error');
    }
}

// ── Attendance ───────────────────────────────────────────────────

async function captureAndMarkAttendance() {
    showToast('Scanning faces…', 'info');
    const imageData = captureFrame();
    showToast('Processing…', 'info');

    try {
        const response = await fetch('/mark_attendance', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ image: imageData })
        });
        const data = await response.json();

        if (data.success) {
            showToast('👋 ' + data.message, 'success');
            if (document.getElementById('logs').classList.contains('active')) refreshLogs();
        } else {
            showToast('✕ ' + data.message, 'error');
        }
    } catch (e) {
        showToast('Attendance marking failed. Please try again.', 'error');
    }
}

// ── Auto Recognition ─────────────────────────────────────────────

function setupAutoRecognition() {
    const toggle = document.getElementById('autoRecognitionToggle');
    toggle.addEventListener('change', async function () {
        autoRecognitionActive = this.checked;
        try {
            const response = await fetch('/toggle_auto_recognition', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ active: autoRecognitionActive })
            });
            const data = await response.json();
            if (data.success) {
                showToast(autoRecognitionActive ? '🤖 Auto recognition enabled' : '🤖 Auto recognition disabled', 'info');
            }
        } catch (e) {
            this.checked = !this.checked;
            showToast('Failed to toggle auto recognition', 'error');
        }
    });
}

// ── Logs ─────────────────────────────────────────────────────────

async function refreshLogs() {
    try {
        const response = await fetch('/get_logs');
        const data = await response.json();
        if (data.success) displayLogs(data.logs);
        else showToast('Failed to load logs', 'error');
    } catch (e) {
        showToast('Failed to load logs', 'error');
    }
}

function displayLogs(logs) {
    const tbody = document.getElementById('logsTableBody');

    if (!logs.length) {
        tbody.innerHTML = '<tr><td colspan="7" class="empty-row">No attendance records found</td></tr>';
        return;
    }

    tbody.innerHTML = logs.map(log => {
        let badgeClass = 'badge-progress';
        if (log.status === 'Present')        badgeClass = 'badge-present';
        else if (log.status === 'Early Dismissal') badgeClass = 'badge-early';
        else if (log.status === 'Completed') badgeClass = 'badge-completed';

        return `
        <tr>
            <td><strong>${log.student_name}</strong></td>
            <td>${log.course}</td>
            <td>${log.section}</td>
            <td>${log.date}</td>
            <td>${log.time_in}</td>
            <td>${log.time_out}</td>
            <td><span class="badge ${badgeClass}">${log.status}</span></td>
        </tr>`;
    }).join('');
}

// ── Stats ────────────────────────────────────────────────────────

async function loadStats() {
    try {
        const response = await fetch('/get_stats');
        const data = await response.json();
        if (data.success) {
            document.getElementById('totalStudents').textContent = data.stats.total_students;
        }
    } catch (e) { /* silent */ }
}

// ── Toast System ─────────────────────────────────────────────────

function showToast(message, type = 'info') {
    const container = document.getElementById('messageContainer');

    const icons = { success: '✓', error: '✕', info: 'ℹ' };

    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerHTML = `<span class="toast-icon">${icons[type]}</span><span>${message}</span>`;

    container.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = '0';
        setTimeout(() => toast.remove(), 320);
    }, 4500);
}

function logout() {
    if (confirm('Sign out of AttendAI?')) window.location.href = '/logout';
}

window.addEventListener('error', e => console.error('Global error:', e));
document.addEventListener('DOMContentLoaded', () => {
    const analyzeBtn = document.getElementById('analyze-btn');
    const resetBtn = document.getElementById('reset-btn');
    const textarea = document.getElementById('message-input');
    
    const heroSection = document.getElementById('hero-section');
    const loadingSkeleton = document.getElementById('loading-skeleton');
    const resultsDashboard = document.getElementById('results-dashboard');
    const errorToast = document.getElementById('error-message');
    
    const riskScore = document.getElementById('risk-score');
    const riskBadge = document.getElementById('risk-badge');
    const scoreBanner = document.getElementById('score-banner');
    
    const explanationBody = document.getElementById('explanation-body');
    const indicatorsBody = document.getElementById('indicators-body');
    const safetyBody = document.getElementById('safety-body');

    const colors = {
        'safe': '#10b981',
        'low': '#38bdf8',
        'moderate': '#f59e0b',
        'high': '#f97316',
        'critical': '#ef4444'
    };

    analyzeBtn.addEventListener('click', async () => {
        const text = textarea.value.trim();
        if (!text) {
            textarea.focus();
            return;
        }

        errorToast.classList.add('hidden');
        analyzeBtn.disabled = true;
        document.querySelector('.btn-text').textContent = 'Analyzing...';
        document.getElementById('btn-loader').classList.remove('hidden');
        
        heroSection.classList.add('shrink');
        resultsDashboard.classList.add('hidden');
        loadingSkeleton.classList.remove('hidden');

        try {
            const response = await fetch('/api/analyze', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ text })
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || 'Failed to analyze message');
            }

            riskScore.textContent = data.score;
            riskBadge.textContent = data.level_label;
            
            const color = colors[data.level_class] || colors.safe;
            riskScore.style.color = color;
            riskScore.style.textShadow = `0 0 20px ${color}40`; // Add a subtle glow
            riskBadge.style.color = color;
            riskBadge.style.borderColor = color;
            scoreBanner.style.setProperty('--accent', color);

            // Animate Ring
            const circle = document.getElementById('progress-ring-circle');
            circle.style.stroke = color;
            const radius = circle.r.baseVal.value;
            const circumference = radius * 2 * Math.PI;
            circle.style.strokeDasharray = `${circumference} ${circumference}`;
            const offset = circumference - (data.score / 100) * circumference;
            setTimeout(() => {
                circle.style.strokeDashoffset = offset;
            }, 100);

            explanationBody.innerHTML = formatMarkdown(data.explanation);
            indicatorsBody.innerHTML = formatMarkdown(data.indicators);
            safetyBody.innerHTML = formatMarkdown(data.safety);

            loadingSkeleton.classList.add('hidden');
            resultsDashboard.classList.remove('hidden');

        } catch (error) {
            errorToast.textContent = error.message;
            errorToast.classList.remove('hidden');
            heroSection.classList.remove('shrink');
            loadingSkeleton.classList.add('hidden');
        } finally {
            analyzeBtn.disabled = false;
            document.querySelector('.btn-text').textContent = 'Run Threat Analysis';
            document.getElementById('btn-loader').classList.add('hidden');
        }
    });

    resetBtn.addEventListener('click', () => {
        textarea.value = '';
        resultsDashboard.classList.add('hidden');
        heroSection.classList.remove('shrink');
        textarea.focus();
        window.scrollTo({ top: 0, behavior: 'smooth' });
    });

    function formatMarkdown(text) {
        if (!text) return '<p>No details provided.</p>';
        let html = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
        
        if (html.includes('- ') || html.includes('* ')) {
            const items = html.split('\n')
                .filter(line => line.trim().match(/^[-*]/))
                .map(line => `<li>${line.replace(/^[-*]\s*/, '')}</li>`)
                .join('');
            return `<ul>${items}</ul>`;
        }
        return `<p>${html.replace(/\n/g, '<br>')}</p>`;
    }
});

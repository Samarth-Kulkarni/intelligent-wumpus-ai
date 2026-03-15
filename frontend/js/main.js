document.addEventListener('DOMContentLoaded', async () => {
    const renderer = new WumpusRenderer('wumpus-canvas');
    const logArea = document.getElementById('log-content');
    const scoreVal = document.getElementById('score-val');
    const movesVal = document.getElementById('moves-val');
    
    // UI Elements
    const stepBtn = document.getElementById('step-btn');
    const resetBtn = document.getElementById('reset-btn');
    const aiToggle = document.getElementById('ai-mode-toggle');

    function updateUI(state) {
        renderer.draw(state);
        scoreVal.textContent = state.score;
        movesVal.textContent = state.moves;
        
        // Update KB count and thoughts
        document.getElementById('kb-count').textContent = state.kb_count || 0;
        const thoughtsEl = document.getElementById('ai-thoughts');
        if (state.ai_thoughts && state.ai_thoughts.length > 0) {
            thoughtsEl.innerHTML = state.ai_thoughts.map(t => `<p>• ${t}</p>`).join('');
        } else {
            thoughtsEl.innerHTML = "Gathering data...";
        }

        // Update percept indicators
        Object.entries(state.percepts).forEach(([type, active]) => {
            const el = document.querySelector(`.indicator[data-type="${type}"]`);
            if (el) {
                if (active) el.classList.add('active');
                else el.classList.remove('active');
            }
        });

        if (state.is_over) {
            addLog("Game Over! Final Score: " + state.score);
        }
    }

    function addLog(msg) {
        const p = document.createElement('p');
        p.textContent = `> ${msg}`;
        logArea.prepend(p);
    }

    let autoInterval = null;

    async function autoStep() {
        if (!aiToggle.checked) return;
        
        try {
            const currentState = await wumpusApi.getState();
            if (currentState.is_over) {
                aiToggle.checked = false;
                clearInterval(autoInterval);
                return;
            }

            const action = currentState.best_action;
            if (action) {
                const state = await wumpusApi.step(action);
                updateUI(state);
                addLog(`Auto-Action: ${action}`);
            }
        } catch (e) {
            console.error("Auto-step failed", e);
        }
    }

    aiToggle.addEventListener('change', () => {
        if (aiToggle.checked) {
            addLog("Auto-Play Enabled.");
            autoInterval = setInterval(autoStep, 1000);
        } else {
            addLog("Auto-Play Disabled.");
            if (autoInterval) clearInterval(autoInterval);
        }
    });

    stepBtn.addEventListener('click', async () => {
        try {
            const currentState = await wumpusApi.getState();
            if (currentState.is_over) return;

            const action = currentState.best_action;
            if (action) {
                const state = await wumpusApi.step(action);
                updateUI(state);
                addLog(`Action: ${action}`);
            }
        } catch (e) {
            console.error("Step failed", e);
        }
    });

    resetBtn.addEventListener('click', async () => {
        const state = await wumpusApi.init(4);
        updateUI(state);
        logArea.innerHTML = "<p>Game Reset.</p>";
    });

    // Helper for keyboard controls
    window.addEventListener('keydown', async (e) => {
        let action = null;
        if (e.key === 'ArrowUp') action = 'FORWARD';
        if (e.key === 'ArrowLeft') action = 'TURNLEFT';
        if (e.key === 'ArrowRight') action = 'TURNRIGHT';
        if (e.key === 'g') action = 'GRAB';
        if (e.key === 's') action = 'SHOOT';
        if (e.key === 'c') action = 'CLIMB';

        if (action) {
            const state = await wumpusApi.step(action);
            updateUI(state);
            addLog(`Action: ${action}`);
        }
    });

    // Initial state
    try {
        const state = await wumpusApi.getState();
        updateUI(state);
    } catch (e) {
        console.error("Failed to connect to backend", e);
        addLog("Error: Could not connect to Flask backend.");
    }
});

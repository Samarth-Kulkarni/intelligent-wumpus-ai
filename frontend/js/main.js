document.addEventListener('DOMContentLoaded', async () => {
    const renderer = new WumpusRenderer('wumpus-canvas');
    const logArea = document.getElementById('log-content');
    const scoreVal = document.getElementById('score-val');
    const movesVal = document.getElementById('moves-val');
    const stepBtn = document.getElementById('step-btn');
    const resetBtn = document.getElementById('reset-btn');
    const aiToggle = document.getElementById('ai-mode-toggle');

    // Modal elements
    const modal = document.getElementById('game-over-modal');
    const modalTitle = document.getElementById('modal-title');
    const modalScore = document.getElementById('modal-score');
    const modalMoves = document.getElementById('modal-moves');
    const modalGold = document.getElementById('modal-gold');
    const modalWumpus = document.getElementById('modal-wumpus');
    const modalCloseBtn = document.getElementById('modal-close-btn');

    let gameOverShown = false;

    function updateUI(state) {
        renderer.draw(state);
        scoreVal.textContent = state.score;
        movesVal.textContent = state.moves;

        document.getElementById('kb-count').textContent = state.kb_count || 0;
        const thoughtsEl = document.getElementById('ai-thoughts');
        if (state.ai_thoughts && state.ai_thoughts.length > 0) {
            thoughtsEl.innerHTML = state.ai_thoughts.map(t => `<p>• ${t}</p>`).join('');
        } else {
            thoughtsEl.innerHTML = "Gathering data...";
        }

        // Percept indicators
        Object.entries(state.percepts).forEach(([type, active]) => {
            const el = document.querySelector(`.indicator[data-type="${type}"]`);
            if (el) {
                if (active) el.classList.add('active');
                else el.classList.remove('active');
            }
        });

        // Game over modal
        if (state.is_over && !gameOverShown) {
            gameOverShown = true;
            if (aiToggle.checked) {
                aiToggle.checked = false;
                if (autoInterval) clearInterval(autoInterval);
            }

            if (!state.agent_alive) {
                modalTitle.textContent = '☠️ You Died!';
            } else {
                modalTitle.textContent = '🏆 Maze Escaped!';
            }
            modalScore.textContent = state.score;
            modalMoves.textContent = state.moves;
            modalGold.textContent = state.agent_has_gold ? '✅ Yes' : '❌ No';
            modalGold.style.color = state.agent_has_gold ? '#10b981' : '#ef4444';
            modalWumpus.textContent = state.wumpus_alive ? '❌ No' : '✅ Yes';
            modalWumpus.style.color = state.wumpus_alive ? '#ef4444' : '#10b981';
            modal.style.display = 'flex';
        }
    }

    function addLog(msg) {
        const p = document.createElement('p');
        p.textContent = msg;
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
                updateUI(currentState);
                return;
            }
            const action = currentState.best_action;
            if (action) {
                const state = await wumpusApi.step(action);
                updateUI(state);
                addLog(`AI: ${action}`);
            }
        } catch (e) {
            console.error("Auto-step failed", e);
        }
    }

    aiToggle.addEventListener('change', () => {
        if (aiToggle.checked) {
            addLog("Auto-Play ON");
            autoInterval = setInterval(autoStep, 600);
        } else {
            addLog("Auto-Play OFF");
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
                addLog(`Step: ${action}`);
            }
        } catch (e) { console.error("Step failed", e); }
    });

    resetBtn.addEventListener('click', async () => {
        gameOverShown = false;
        modal.style.display = 'none';
        const state = await wumpusApi.init(8);
        updateUI(state);
        logArea.innerHTML = "<p>Game Reset.</p>";
    });

    modalCloseBtn.addEventListener('click', async () => {
        gameOverShown = false;
        modal.style.display = 'none';
        const state = await wumpusApi.init(8);
        updateUI(state);
        logArea.innerHTML = "<p>New game started.</p>";
    });

    // Keyboard controls
    window.addEventListener('keydown', async (e) => {
        let action = null;
        if (e.key === 'ArrowUp' || e.key === 'w') action = 'FORWARD';
        if (e.key === 'ArrowLeft' || e.key === 'a') action = 'TURNLEFT';
        if (e.key === 'ArrowRight' || e.key === 'd') action = 'TURNRIGHT';
        if (e.key === 'g') action = 'GRAB';
        if (e.key === 's') action = 'SHOOT';
        if (e.key === 'c') action = 'CLIMB';

        if (action) {
            if (aiToggle.checked) {
                aiToggle.checked = false;
                addLog("Manual override — Auto-Play OFF");
                if (autoInterval) clearInterval(autoInterval);
            }
            const state = await wumpusApi.step(action);
            document.querySelector('.canvas-wrapper').classList.add('action-flash');
            setTimeout(() => document.querySelector('.canvas-wrapper').classList.remove('action-flash'), 150);
            updateUI(state);
            addLog(`Manual: ${action}`);
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

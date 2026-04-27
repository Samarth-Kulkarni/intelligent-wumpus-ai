document.addEventListener('DOMContentLoaded', async () => {
    const renderer = new WumpusRenderer('wumpus-canvas');
    const logArea = document.getElementById('log-content');
    const scoreVal = document.getElementById('score-val');
    const movesVal = document.getElementById('moves-val');
    const stepBtn = document.getElementById('step-btn');
    const resetBtn = document.getElementById('reset-btn');
    const aiToggle = document.getElementById('ai-mode-toggle');
    const revealToggle = document.getElementById('reveal-mode-toggle');
    const algoSelect = document.getElementById('algo-select');

    // Modal elements
    const gameOverMessage = document.getElementById('game-over-message');

    // Batch Modal elements
    const batchBtn = document.getElementById('batch-btn');
    const batchModal = document.getElementById('batch-modal');
    const batchStats = document.getElementById('batch-stats');
    const batchCloseBtn = document.getElementById('batch-close-btn');
    const modal = document.getElementById('game-over-modal');
    const modalTitle = document.getElementById('modal-title');
    const modalScore = document.getElementById('modal-score');
    const modalMoves = document.getElementById('modal-moves');
    const modalGold = document.getElementById('modal-gold');
    const modalWumpus = document.getElementById('modal-wumpus');
    const modalCloseBtn = document.getElementById('modal-close-btn');

    let gameOverShown = false;
    let usedAuto = false;

    let playerScore = null;
    let agentScore = null;

    function updateScoreBoard() {
        document.getElementById('player-score-val').textContent = playerScore !== null ? playerScore : '—';
        document.getElementById('agent-score-val').textContent = agentScore !== null ? agentScore : '—';
    }
    updateScoreBoard();

    function updateUI(state) {
        const hideMaze = !aiToggle.checked && !revealToggle.checked;
        renderer.draw(state, hideMaze);
        scoreVal.textContent = state.score;
        movesVal.textContent = state.moves;

        if (state.nodes_expanded !== undefined) {
            document.getElementById('nodes-expanded-val').textContent = state.nodes_expanded;
        }

        document.getElementById('kb-count').textContent = state.kb_count || 0;
        
        const factsEl = document.getElementById('kb-facts');
        if (state.kb_facts && state.kb_facts.length > 0) {
            factsEl.innerHTML = state.kb_facts.slice(-20).reverse().map(f => `<div>${f}</div>`).join('');
        } else {
            factsEl.innerHTML = "Initializing FOL...";
        }

        const thoughtsEl = document.getElementById('ai-thoughts');
        if (state.ai_thoughts && state.ai_thoughts.length > 0) {
            thoughtsEl.innerHTML = state.ai_thoughts.map(t => `<p>• ${t}</p>`).join('');
        } else {
            thoughtsEl.innerHTML = "Gathering data...";
        }

        // Percept indicators
        Object.entries(state.percepts).forEach(([type, active]) => {
            if (type === 'stench_intensity' || type === 'breeze_intensity' || type === 'glitter_intensity') return;
            const el = document.querySelector(`.indicator[data-type="${type}"]`);
            if (el) {
                el.classList.remove('active', 'intensity-high', 'intensity-low', 'intensity-max');
                if (active) {
                    el.classList.add('active');
                    if (type === 'stench' && state.percepts.stench_intensity && state.percepts.stench_intensity !== 'none') {
                        el.classList.add(`intensity-${state.percepts.stench_intensity}`);
                        el.textContent = `Stench (${state.percepts.stench_intensity === 'high' ? 'Strong' : 'Faint'})`;
                    } else if (type === 'stench') {
                        el.textContent = 'Stench';
                    }
                    if (type === 'breeze' && state.percepts.breeze_intensity && state.percepts.breeze_intensity !== 'none') {
                        el.classList.add(`intensity-${state.percepts.breeze_intensity}`);
                        el.textContent = `Breeze (${state.percepts.breeze_intensity === 'high' ? 'Strong' : 'Faint'})`;
                    } else if (type === 'breeze') {
                        el.textContent = 'Breeze';
                    }
                    if (type === 'glitter' && state.percepts.glitter_intensity && state.percepts.glitter_intensity !== 'none') {
                        el.classList.add(`intensity-${state.percepts.glitter_intensity}`);
                        if (state.percepts.glitter_intensity === 'max') {
                            el.textContent = 'Glitter (Max)';
                        } else {
                            el.textContent = `Glitter (${state.percepts.glitter_intensity === 'high' ? 'Strong' : 'Faint'})`;
                        }
                    } else if (type === 'glitter') {
                        el.textContent = 'Glitter';
                    }
                } else {
                    if (type === 'stench') el.textContent = 'Stench';
                    if (type === 'breeze') el.textContent = 'Breeze';
                    if (type === 'glitter') el.textContent = 'Glitter';
                }
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
            // Score tracking for this maze
            if (usedAuto) {
                agentScore = state.score;
            } else {
                playerScore = state.score;
            }
            updateScoreBoard();
            
            // Winner declaration
            const winnerEl = document.getElementById('modal-winner');
            if (playerScore !== null && agentScore !== null) {
                if (playerScore > agentScore) {
                    winnerEl.textContent = `Player wins by ${playerScore - agentScore} points!`;
                    winnerEl.style.color = '#10b981';
                } else if (agentScore > playerScore) {
                    winnerEl.textContent = `Agent wins by ${agentScore - playerScore} points!`;
                    winnerEl.style.color = '#ef4444';
                } else {
                    winnerEl.textContent = "It's a Tie!";
                    winnerEl.style.color = '#38bdf8';
                }
            } else {
                winnerEl.textContent = "Try the other mode to compare scores!";
                winnerEl.style.color = '#94a3b8';
            }
            
            modal.style.display = 'flex';
        }
    }

    function addLog(msg) {
        const p = document.createElement('p');
        p.textContent = msg;
        logArea.prepend(p);
    }

    let autoInterval = null;
    let autoTimeout = null;

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

    aiToggle.addEventListener('change', async () => {
        if (aiToggle.checked) {
            usedAuto = true;
            addLog("Auto-Play ON. Agent will start in 2 seconds...");
            
            try {
                // Trigger transition immediately
                const state = await wumpusApi.getState();
                updateUI(state);
            } catch(e) {}
            
            autoTimeout = setTimeout(() => {
                if (aiToggle.checked) {
                    addLog("Agent starting...");
                    autoInterval = setInterval(autoStep, 600);
                }
            }, 2000);
        } else {
            addLog("Auto-Play OFF");
            if (autoTimeout) clearTimeout(autoTimeout);
            if (autoInterval) clearInterval(autoInterval);
            
            try {
                // Revert visual state immediately
                const state = await wumpusApi.getState();
                updateUI(state);
            } catch(e) {}
        }
    });

    revealToggle.addEventListener('change', async () => {
        try {
            const state = await wumpusApi.getState();
            updateUI(state);
        } catch(e) {}
    });

    batchBtn.addEventListener('click', async () => {
        batchBtn.textContent = "Running...";
        batchBtn.disabled = true;
        try {
            const stats = await wumpusApi.runBatch(100, algoSelect.value);
            batchStats.innerHTML = `
                <p><strong>Iterations:</strong> ${stats.iterations}</p>
                <p><strong>Win Rate:</strong> <span style="color:#10b981;">${stats.win_rate.toFixed(1)}%</span></p>
                <p><strong>Wins:</strong> ${stats.wins}</p>
                <p><strong>Deaths (Pit):</strong> <span style="color:#ef4444;">${stats.deaths_pit}</span></p>
                <p><strong>Deaths (Wumpus):</strong> <span style="color:#ef4444;">${stats.deaths_wumpus}</span></p>
                <p><strong>Avg Moves:</strong> ${stats.avg_moves}</p>
                <p><strong>Avg Score:</strong> ${stats.avg_score}</p>
                <p><strong>Probabilistic Gambles:</strong> <span style="color:#f59e0b;">${stats.total_gambles}</span></p>
            `;
            batchModal.style.display = 'flex';
        } catch (e) {
            console.error(e);
            alert("Error running batch simulation.");
        } finally {
            batchBtn.textContent = "Run Batch (100)";
            batchBtn.disabled = false;
        }
    });

    batchCloseBtn.addEventListener('click', () => {
        batchModal.style.display = 'none';
    });

    algoSelect.addEventListener('change', async () => {
        try {
            const state = await wumpusApi.setAlgo(algoSelect.value);
            updateUI(state);
            addLog(`Pathfinding changed to ${algoSelect.value}`);
        } catch(e) {}
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
        try {
            gameOverShown = false;
            usedAuto = false;
            modal.style.display = 'none';
            
            aiToggle.checked = false;
            revealToggle.checked = false;
            if (autoTimeout) clearTimeout(autoTimeout);
            if (autoInterval) clearInterval(autoInterval);

            playerScore = null;
            agentScore = null;
            updateScoreBoard();

            const state = await wumpusApi.init(8);
            updateUI(state);
            logArea.innerHTML = "<p>New Maze Generated.</p>";
        } catch (e) {
            console.error("Error in resetBtn:", e);
            alert("Error generating new maze: " + e.message);
        }
    });

    document.getElementById('retry-btn').addEventListener('click', async () => {
        try {
            gameOverShown = false;
            usedAuto = false;
            modal.style.display = 'none';
            
            aiToggle.checked = false;
            revealToggle.checked = false;
            if (autoTimeout) clearTimeout(autoTimeout);
            if (autoInterval) clearInterval(autoInterval);

            const state = await wumpusApi.retry();
            updateUI(state);
            logArea.innerHTML = "<p>Maze Reset. Try again!</p>";
        } catch (e) {
            console.error("Error in retryBtn:", e);
            alert("Error retrying maze: " + e.message);
        }
    });

    document.getElementById('modal-retry-btn').addEventListener('click', async () => {
        try {
            gameOverShown = false;
            usedAuto = false;
            modal.style.display = 'none';

            aiToggle.checked = false;
            revealToggle.checked = false;
            if (autoTimeout) clearTimeout(autoTimeout);
            if (autoInterval) clearInterval(autoInterval);

            const state = await wumpusApi.retry();
            updateUI(state);
            logArea.innerHTML = "<p>Maze Reset. Try again!</p>";
        } catch (e) {
            console.error("Error in modal-retry-btn:", e);
            alert("Error retrying maze: " + e.message);
        }
    });

    modalCloseBtn.addEventListener('click', async () => {
        try {
            gameOverShown = false;
            usedAuto = false;
            modal.style.display = 'none';

            aiToggle.checked = false;
            revealToggle.checked = false;
            if (autoTimeout) clearTimeout(autoTimeout);
            if (autoInterval) clearInterval(autoInterval);

            playerScore = null;
            agentScore = null;
            updateScoreBoard();

            const state = await wumpusApi.init(8);
            updateUI(state);
            logArea.innerHTML = "<p>New Maze Generated.</p>";
        } catch (e) {
            console.error("Error in modalCloseBtn:", e);
            alert("Error generating new maze: " + e.message);
        }
    });

    document.getElementById('modal-dismiss-btn').addEventListener('click', () => {
        modal.style.display = 'none';
        addLog("Game Over screen dismissed. You may review the dashboard.");
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

    // Initial state (force reset on reload)
    try {
        aiToggle.checked = false;
        revealToggle.checked = false;
        playerScore = null;
        agentScore = null;
        updateScoreBoard();
        const state = await wumpusApi.init(8);
        updateUI(state);
    } catch (e) {
        console.error("Failed to connect to backend", e);
        addLog("Error: Could not connect to Flask backend.");
    }
});

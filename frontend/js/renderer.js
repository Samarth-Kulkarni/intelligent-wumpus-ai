class WumpusRenderer {
    constructor(canvasId) {
        this.canvas = document.getElementById(canvasId);
        this.ctx = this.canvas.getContext('2d');
        this.resize();
        window.addEventListener('resize', () => this.resize());
        
        this.animAgentPos = null;
        this.animAgentDir = null;
        this.targetState = null;
        this.isManual = false;
        
        const loop = () => {
            if (this.targetState) {
                this.updateAnim();
                this._render(this.targetState);
            }
            requestAnimationFrame(loop);
        };
        requestAnimationFrame(loop);
    }

    resize() {
        const parent = this.canvas.parentElement;
        this.canvas.width = parent.clientWidth;
        this.canvas.height = parent.clientHeight;
    }

    _dirToAngle(dir) {
        const rot = { RIGHT: 0, UP: -Math.PI / 2, LEFT: Math.PI, DOWN: Math.PI / 2 };
        return rot[dir] || 0;
    }

    updateAnim() {
        const tx = this.targetState.agent_pos[0];
        const ty = this.targetState.agent_pos[1];
        const spd = 0.2;
        this.animAgentPos[0] += (tx - this.animAgentPos[0]) * spd;
        this.animAgentPos[1] += (ty - this.animAgentPos[1]) * spd;

        let targetAngle = this._dirToAngle(this.targetState.agent_dir);
        let diff = targetAngle - this.animAgentDir;
        while (diff < -Math.PI) diff += Math.PI * 2;
        while (diff > Math.PI) diff -= Math.PI * 2;
        this.animAgentDir += diff * spd;
        
        if (this.revealAnim !== undefined) {
            if (this.animDirection === 1 && this.revealAnim < 1) {
                this.revealAnim += 0.02; // expanding
                if (this.revealAnim > 1) this.revealAnim = 1;
            } else if (this.animDirection === -1 && this.revealAnim > 0) {
                this.revealAnim -= 0.02; // collapsing
                if (this.revealAnim < 0) this.revealAnim = 0;
            }
        }
    }

    draw(gameState, isManual = false) {
        if (this.isManual && !isManual) {
            // Trigger transition from manual to auto (Reveal)
            this.revealAnim = this.revealAnim !== undefined ? this.revealAnim : 0;
            this.animDirection = 1;
            this.revealStartPos = [...gameState.agent_pos];
        } else if (!this.isManual && isManual) {
            // Trigger transition from auto to manual (Hide)
            this.revealAnim = this.revealAnim !== undefined ? this.revealAnim : 1;
            this.animDirection = -1;
            this.revealStartPos = [...gameState.agent_pos];
        }
        
        this.targetState = gameState;
        this.isManual = isManual;
        
        // If it's a reset or first draw, snap to position immediately
        if (!this.animAgentPos || gameState.moves === 0) {
            this.animAgentPos = [...gameState.agent_pos];
            this.animAgentDir = this._dirToAngle(gameState.agent_dir);
        }
    }

    _render(gameState) {
        const { size, pits, walls, gold_pos, exit_pos,
                wumpus_pos, wumpus_alive, agent_has_gold, visited_cells } = gameState;
        const ctx = this.ctx;
        const w = this.canvas.width;
        const h = this.canvas.height;
        const cs = Math.min(w, h) / size;

        const cellX  = (x) => x * cs;
        const cellY  = (y) => (size - 1 - y) * cs;
        const centerX = (x) => x * cs + cs / 2;
        const centerY = (y) => (size - 1 - y) * cs + cs / 2;

        // Background
        ctx.fillStyle = '#0f172a';
        ctx.fillRect(0, 0, w, h);

        // Fog of War helper with radial fade transition
        const getVisibility = (x, y) => {
            const visited = visited_cells && visited_cells.some(v => v[0] === x && v[1] === y);
            if (visited) return 1;

            if (this.isManual && (this.revealAnim === undefined || this.revealAnim <= 0)) {
                return 0; // Fully hidden
            } else if (!this.isManual && (this.revealAnim === undefined || this.revealAnim >= 1)) {
                return 1; // Fully revealed
            }
            
            const sx = this.revealStartPos ? this.revealStartPos[0] : 0;
            const sy = this.revealStartPos ? this.revealStartPos[1] : 0;
            const dist = Math.sqrt(Math.pow(x - sx, 2) + Math.pow(y - sy, 2));
            const maxDist = size * 1.5; 
            const threshold = this.revealAnim * maxDist;
            
            if (dist <= threshold) return 1;
            const fadeWidth = 2.5; // Smooth fade radius
            if (dist < threshold + fadeWidth) {
                return 1 - ((dist - threshold) / fadeWidth);
            }
            return 0;
        };

        // Checkerboard cells (drawn over pure dark fog)
        for (let x = 0; x < size; x++) {
            for (let y = 0; y < size; y++) {
                const vis = getVisibility(x, y);
                if (vis > 0) {
                    ctx.globalAlpha = vis;
                    ctx.fillStyle = (x + y) % 2 === 0 ? '#1e293b' : '#1a2332';
                    ctx.fillRect(cellX(x), cellY(y), cs, cs);
                    ctx.globalAlpha = 1.0;
                    
                    // Draw Probabilities only on visible frontier cells
                    if (gameState.probabilities) {
                        const prob = gameState.probabilities[`${x},${y}`];
                        if (prob !== undefined) {
                            ctx.fillStyle = `rgba(239, 68, 68, ${Math.max(0.3, prob)})`; // Red overlay based on risk
                            ctx.fillRect(cellX(x), cellY(y), cs, cs);
                            
                            ctx.fillStyle = '#ffffff'; // White text for high contrast against red background
                            ctx.font = `bold ${Math.max(10, cs * 0.2)}px Arial`;
                            ctx.textAlign = 'center';
                            ctx.textBaseline = 'middle';
                            ctx.fillText(`P=${(prob*100).toFixed(0)}%`, centerX(x), centerY(y));
                        }
                    }
                }
            }
        }

        // START marker at (0, 0)
        const startVis = getVisibility(0, 0);
        if (startVis > 0) {
            ctx.globalAlpha = startVis;
            ctx.fillStyle = 'rgba(14, 165, 233, 0.15)';
            ctx.fillRect(cellX(0), cellY(0), cs, cs);
            ctx.fillStyle = '#38bdf8';
            ctx.font = `bold ${Math.max(10, cs * 0.18)}px Arial`;
            ctx.textAlign = 'center';
            ctx.textBaseline = 'top';
            ctx.fillText('START', centerX(0), cellY(0) + 3);
            ctx.globalAlpha = 1.0;
        }

        // EXIT marker
        if (exit_pos) {
            const exitVis = getVisibility(exit_pos[0], exit_pos[1]);
            if (exitVis > 0) {
                ctx.globalAlpha = exitVis;
                ctx.fillStyle = 'rgba(16, 185, 129, 0.18)';
                ctx.fillRect(cellX(exit_pos[0]), cellY(exit_pos[1]), cs, cs);
                ctx.fillStyle = '#10b981';
                ctx.font = `bold ${Math.max(10, cs * 0.18)}px Arial`;
                ctx.textAlign = 'center';
                ctx.textBaseline = 'top';
                ctx.fillText('EXIT', centerX(exit_pos[0]), cellY(exit_pos[1]) + 3);
                ctx.globalAlpha = 1.0;
            }
        }

        // Pits
        pits.forEach(([px, py]) => {
            const vis = getVisibility(px, py);
            if (vis > 0) {
                ctx.globalAlpha = vis;
                this.drawPit(centerX(px), centerY(py), cs);
                ctx.globalAlpha = 1.0;
            }
        });

        // Gold
        if (!agent_has_gold) {
            const vis = getVisibility(gold_pos[0], gold_pos[1]);
            if (vis > 0) {
                ctx.globalAlpha = vis;
                this.drawGold(centerX(gold_pos[0]), centerY(gold_pos[1]), cs);
                ctx.globalAlpha = 1.0;
            }
        }

        // Wumpus
        if (wumpus_alive) {
            const vis = getVisibility(wumpus_pos[0], wumpus_pos[1]);
            if (vis > 0) {
                ctx.globalAlpha = vis;
                this.drawWumpus(centerX(wumpus_pos[0]), centerY(wumpus_pos[1]), cs);
                ctx.globalAlpha = 1.0;
            }
        }

        // Agent - using animated position
        this.drawAgent(centerX(this.animAgentPos[0]), centerY(this.animAgentPos[1]), cs * 0.5, this.animAgentDir);

        // ── Draw wall edges ──
        if (walls && walls.length) {
            ctx.strokeStyle = '#cbd5e1';
            ctx.lineWidth = Math.max(3, cs * 0.07);
            ctx.lineCap = 'round';
            walls.forEach(([c1, c2]) => {
                const [x1, y1] = c1;
                const [x2, y2] = c2;
                
                const vis1 = getVisibility(x1, y1);
                const vis2 = getVisibility(x2, y2);
                const vis = Math.max(vis1, vis2); // Wall is visible if either adjacent cell is visible

                if (vis > 0) {
                    ctx.globalAlpha = vis;
                    ctx.beginPath();
                    if (y1 === y2) {
                        const wx = Math.max(x1, x2) * cs;
                        const wy = (size - 1 - y1) * cs;
                        ctx.moveTo(wx, wy); ctx.lineTo(wx, wy + cs);
                    } else {
                        const wy = (size - Math.max(y1, y2)) * cs;
                        const wx = Math.min(x1, x2) * cs;
                        ctx.moveTo(wx, wy); ctx.lineTo(wx + cs, wy);
                    }
                    ctx.stroke();
                    ctx.globalAlpha = 1.0;
                }
            });
        }

        // Outer border
        ctx.strokeStyle = '#cbd5e1';
        ctx.lineWidth = Math.max(4, cs * 0.08);
        ctx.strokeRect(0, 0, size * cs, size * cs);
    }

    drawPit(x, y, cs) {
        const ctx = this.ctx;
        const r = cs * 0.28;
        const g = ctx.createRadialGradient(x, y, r * 0.1, x, y, r);
        g.addColorStop(0, '#000'); g.addColorStop(1, '#1e293b');
        ctx.fillStyle = g;
        ctx.beginPath(); ctx.arc(x, y, r, 0, Math.PI * 2); ctx.fill();
        ctx.strokeStyle = '#0f172a'; ctx.lineWidth = 2; ctx.stroke();
    }

    drawGold(x, y, cs) {
        const ctx = this.ctx;
        const r = cs * 0.18;
        ctx.fillStyle = '#fbbf24'; ctx.shadowColor = '#fbbf24'; ctx.shadowBlur = 12;
        ctx.beginPath();
        ctx.moveTo(x, y - r);
        ctx.lineTo(x + r * 0.3, y - r * 0.3);
        ctx.lineTo(x + r, y);
        ctx.lineTo(x + r * 0.3, y + r * 0.3);
        ctx.lineTo(x, y + r);
        ctx.lineTo(x - r * 0.3, y + r * 0.3);
        ctx.lineTo(x - r, y);
        ctx.lineTo(x - r * 0.3, y - r * 0.3);
        ctx.closePath(); ctx.fill();
        ctx.shadowBlur = 0;
    }

    drawWumpus(x, y, cs) {
        const ctx = this.ctx;
        const r = cs * 0.28;
        ctx.fillStyle = '#ef4444'; ctx.shadowColor = '#ef4444'; ctx.shadowBlur = 8;
        const spikes = 8;
        ctx.beginPath();
        for (let i = 0; i < spikes * 2; i++) {
            const rad = (i % 2 === 0) ? r : r * 0.5;
            const a = (i * Math.PI) / spikes;
            const px = x + Math.cos(a) * rad, py = y + Math.sin(a) * rad;
            i === 0 ? ctx.moveTo(px, py) : ctx.lineTo(px, py);
        }
        ctx.closePath(); ctx.fill();
        ctx.fillStyle = '#fee2e2';
        ctx.beginPath();
        ctx.arc(x - r * 0.25, y - r * 0.1, r * 0.12, 0, Math.PI * 2);
        ctx.arc(x + r * 0.25, y - r * 0.1, r * 0.12, 0, Math.PI * 2);
        ctx.fill();
        ctx.shadowBlur = 0;
    }

    drawAgent(x, y, sz, angle) {
        const ctx = this.ctx;
        ctx.save(); ctx.translate(x, y);
        ctx.rotate(angle);
        const g = ctx.createLinearGradient(-sz / 2, 0, sz / 2, 0);
        g.addColorStop(0, '#0284c7'); g.addColorStop(1, '#38bdf8');
        ctx.fillStyle = g;
        ctx.beginPath();
        ctx.moveTo(sz / 2, 0);
        ctx.lineTo(-sz / 2, -sz / 2.5);
        ctx.lineTo(-sz / 3, 0);
        ctx.lineTo(-sz / 2, sz / 2.5);
        ctx.closePath(); ctx.fill();
        ctx.shadowBlur = 10; ctx.shadowColor = '#0ea5e9';
        ctx.strokeStyle = '#e0f2fe'; ctx.lineWidth = 1.5; ctx.stroke();
        ctx.restore();
    }
}

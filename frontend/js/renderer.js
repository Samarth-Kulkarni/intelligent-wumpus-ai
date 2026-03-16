class WumpusRenderer {
    constructor(canvasId) {
        this.canvas = document.getElementById(canvasId);
        this.ctx = this.canvas.getContext('2d');
        this.resize();
        window.addEventListener('resize', () => this.resize());
    }

    resize() {
        const parent = this.canvas.parentElement;
        this.canvas.width = parent.clientWidth;
        this.canvas.height = parent.clientHeight;
    }

    draw(gameState) {
        const { size, agent_pos, agent_dir, pits, walls, gold_pos, exit_pos,
                wumpus_pos, wumpus_alive, agent_has_gold } = gameState;
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

        // Checkerboard cells
        for (let x = 0; x < size; x++) {
            for (let y = 0; y < size; y++) {
                ctx.fillStyle = (x + y) % 2 === 0 ? '#1e293b' : '#1a2332';
                ctx.fillRect(cellX(x), cellY(y), cs, cs);
            }
        }

        // START marker at (0, 0)
        ctx.fillStyle = 'rgba(14, 165, 233, 0.15)';
        ctx.fillRect(cellX(0), cellY(0), cs, cs);
        ctx.fillStyle = '#38bdf8';
        ctx.font = `bold ${Math.max(10, cs * 0.18)}px Arial`;
        ctx.textAlign = 'center';
        ctx.textBaseline = 'top';
        ctx.fillText('START', centerX(0), cellY(0) + 3);

        // EXIT marker
        if (exit_pos) {
            ctx.fillStyle = 'rgba(16, 185, 129, 0.18)';
            ctx.fillRect(cellX(exit_pos[0]), cellY(exit_pos[1]), cs, cs);
            ctx.fillStyle = '#10b981';
            ctx.font = `bold ${Math.max(10, cs * 0.18)}px Arial`;
            ctx.textAlign = 'center';
            ctx.textBaseline = 'top';
            ctx.fillText('EXIT', centerX(exit_pos[0]), cellY(exit_pos[1]) + 3);
        }

        // Pits
        pits.forEach(([px, py]) => this.drawPit(centerX(px), centerY(py), cs));

        // Gold
        if (!agent_has_gold) {
            this.drawGold(centerX(gold_pos[0]), centerY(gold_pos[1]), cs);
        }

        // Wumpus (only alive)
        if (wumpus_alive) {
            this.drawWumpus(centerX(wumpus_pos[0]), centerY(wumpus_pos[1]), cs);
        }

        // Agent
        this.drawAgent(centerX(agent_pos[0]), centerY(agent_pos[1]), cs * 0.5, agent_dir);

        // ── Draw wall edges ──
        if (walls && walls.length) {
            ctx.strokeStyle = '#cbd5e1';
            ctx.lineWidth = Math.max(3, cs * 0.07);
            ctx.lineCap = 'round';
            walls.forEach(([c1, c2]) => {
                const [x1, y1] = c1;
                const [x2, y2] = c2;
                if (y1 === y2) {
                    // Horizontal neighbours → vertical wall line
                    const wx = Math.max(x1, x2) * cs;
                    const wy = (size - 1 - y1) * cs;
                    ctx.beginPath(); ctx.moveTo(wx, wy); ctx.lineTo(wx, wy + cs); ctx.stroke();
                } else {
                    // Vertical neighbours → horizontal wall line
                    const wy = (size - Math.max(y1, y2)) * cs;
                    const wx = Math.min(x1, x2) * cs;
                    ctx.beginPath(); ctx.moveTo(wx, wy); ctx.lineTo(wx + cs, wy); ctx.stroke();
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

    drawAgent(x, y, sz, dir) {
        const ctx = this.ctx;
        ctx.save(); ctx.translate(x, y);
        const rot = { RIGHT: 0, UP: -Math.PI / 2, LEFT: Math.PI, DOWN: Math.PI / 2 };
        ctx.rotate(rot[dir] || 0);
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

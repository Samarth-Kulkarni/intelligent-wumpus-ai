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
        const { size, agent_pos, agent_dir, pits, gold_pos, wumpus_pos, wumpus_alive, agent_has_gold } = gameState;
        const ctx = this.ctx;
        const width = this.canvas.width;
        const height = this.canvas.height;
        const cellSize = width / size;

        ctx.clearRect(0, 0, width, height);

        // Draw Grid
        ctx.strokeStyle = '#334155';
        ctx.lineWidth = 1;
        for (let i = 0; i <= size; i++) {
            ctx.beginPath();
            ctx.moveTo(i * cellSize, 0);
            ctx.lineTo(i * cellSize, height);
            ctx.stroke();

            ctx.beginPath();
            ctx.moveTo(0, i * cellSize);
            ctx.lineTo(width, i * cellSize);
            ctx.stroke();
        }

        // Help visualize (Cheat mode/Debug)
        pits.forEach(p => this.drawEntity(p[0], p[1], size, cellSize, '#1e293b', 'P'));
        if (!agent_has_gold) this.drawEntity(gold_pos[0], gold_pos[1], size, cellSize, '#eab308', 'G');
        this.drawEntity(wumpus_pos[0], wumpus_pos[1], size, cellSize, wumpus_alive ? '#ef4444' : '#475569', wumpus_alive ? 'W' : 'X');

        // Draw Agent
        const [ax, ay] = agent_pos;
        const cx = ax * cellSize + cellSize / 2;
        const cy = (size - 1 - ay) * cellSize + cellSize / 2;

        this.drawAgent(cx, cy, cellSize * 0.6, agent_dir);
    }

    drawEntity(x, y, size, cellSize, color, label) {
        const ctx = this.ctx;
        const cx = x * cellSize + cellSize / 2;
        const cy = (size - 1 - y) * cellSize + cellSize / 2;

        ctx.fillStyle = color;
        ctx.beginPath();
        ctx.arc(cx, cy, cellSize * 0.3, 0, Math.PI * 2);
        ctx.fill();

        ctx.fillStyle = 'white';
        ctx.font = `${cellSize * 0.3}px Arial`;
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText(label, cx, cy);
    }

    drawAgent(x, y, size, direction) {
        const ctx = this.ctx;
        ctx.save();
        ctx.translate(x, y);

        // Rotate based on direction
        const rotations = { "RIGHT": 0, "UP": -Math.PI/2, "LEFT": Math.PI, "DOWN": Math.PI/2 };
        ctx.rotate(rotations[direction] || 0);

        // Simple Triangle Agent
        ctx.fillStyle = '#38bdf8';
        ctx.beginPath();
        ctx.moveTo(size/2, 0);
        ctx.lineTo(-size/2, -size/3);
        ctx.lineTo(-size/2, size/3);
        ctx.closePath();
        ctx.fill();

        // Glow
        ctx.shadowBlur = 15;
        ctx.shadowColor = '#38bdf8';
        ctx.stroke();

        ctx.restore();
    }
}

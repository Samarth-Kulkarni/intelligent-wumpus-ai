# 🏹 Intelligent Wumpus World Agent Simulator

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Flask](https://img.shields.io/badge/Flask-3.0+-green.svg)](https://flask.palletsprojects.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

An interactive AI simulation of the classic **Wumpus World problem** — an intelligent agent navigates an 8×8 maze using **First Order Logic** and **Probabilistic Reasoning** to avoid deadly hazards, hunt the Wumpus, collect gold, and escape alive.

> **Subject:** Mathematical Foundations of Artificial Intelligence (MFAI)

---

⚠️ This project is currently under development.

## 🌟 Project Overview

The **Wumpus World** is a benchmark problem in AI (Russell & Norvig, *AI: A Modern Approach*) used to demonstrate reasoning under uncertainty.

In this simulation:
- An agent explores an **8×8 maze** generated with DFS recursive backtracking
- The maze contains **pits**, a **Wumpus monster**, and **gold**
- The agent has **partial observability** — it cannot see the full maze
- It uses **logical inference** and **probability** to make safe decisions

### Percept System

| Percept | Meaning |
| :--- | :--- |
| **Stench** | The Wumpus is in an adjacent (reachable) cell |
| **Breeze** | A pit is in an adjacent (reachable) cell |
| **Glitter** | Gold is in the current cell |
| **Bump** | The agent walked into a wall |
| **Scream** | The Wumpus has been killed by the arrow |

---

## 🚀 Key Features

### 🧠 Intelligent AI Agent
- **First-Order Logic (FOL):** Custom mathematical Forward-Chaining deduction proves cell safety
- **Probabilistic Reasoning:** Fractional Bayesian risk estimation when logic is insufficient
- **Advanced Navigation:** A* (A-Star) Search and BFS path planning prevents the agent from getting stuck
- **Wumpus Hunting:** Agent detects directional high/low stench intensities and shoots arrow
- **Gold Collection & Homing:** Grabs gold on max glitter, then A* shortest path to EXIT

### 🗺️ Proper Maze Environment
- **DFS Recursive Backtracking** generates real corridors with wall edges
- **Wall-edge rendering** — walls are drawn as lines between cells, not blocks
- **START** (bottom-left) and **EXIT** (top-right) clearly labeled
- **Scoring System:** Base 500, −10/action, +500 kill Wumpus, +500 grab gold, +1000 exit with gold, −500 die

### 🎮 Operation Modes
- **Manual Mode:** Control with keyboard — `↑/W` move, `←/A` turn left, `→/D` turn right, `G` grab, `S` shoot, `C` climb
- **Auto Mode:** Watch the AI autonomously explore, reason, and solve the maze
- **Batch Simulator:** Instantly run 100 simulations in the background to calculate statistical win rates

### 💻 Interactive Dashboard
- **Real-time maze visualization** on HTML5 Canvas
- **Percept indicators** light up based on current cell signals
- **Action Log** tracks and traces every decision horizontally across the UI
- **AI Reasoning panel** shows live logical deductions and probabilistic analysis
- **Nodes Expanded counter** dynamically compares search algorithm efficiency
- **Knowledge Base counter** tracks proven-safe mathematical axioms
- **Game Over modal** displays final score, moves, gold status, and Wumpus kill status
----

## 🏗️ System Architecture

```
Frontend (Browser)
├── HTML5 Canvas — Maze renderer with wall edges
├── CSS3 — Dark glassmorphic UI theme
└── JavaScript — API client, controls, dashboard
        │
        │  REST API (JSON)
        ▼
Backend (Python Flask — app.py)
├── simulator/simulator.py
│   ├── DFS maze generation (wall edges between cells)
│   ├── Percept system (stench, breeze, glitter, bump, scream)
│   ├── Action execution (move, turn, grab, shoot, climb)
│   └── Scoring engine
└── ai/
    ├── agent.py — Decision engine, BFS pathfinding, committed plans
    ├── logic_engine.py — FOL clause database, entailment checking
    └── probability_engine.py — Bayesian risk scoring, frontier analysis
```

---

## 📂 Project Structure

```
intelligent_wumpus_agent_simulator/
├── backend/
│   ├── ai/
│   │   ├── agent.py               # Intelligent Agent — decision engine & BFS
│   │   ├── logic_engine.py        # FOL Knowledge Base & inference
│   │   └── probability_engine.py  # Probabilistic risk estimation
│   ├── simulator/
│   │   └── simulator.py           # Maze generation, percepts, scoring
│   ├── app.py                     # Flask API server
│   └── requirements.txt           # Python dependencies
├── frontend/
│   ├── css/
│   │   └── styles.css             # Dark-themed glassmorphic UI
│   ├── js/
│   │   ├── api.js                 # REST API client
│   │   ├── main.js                # Dashboard controller & game-over modal
│   │   └── renderer.js            # Canvas maze renderer (wall edges)
│   └── index.html                 # Main dashboard page
└── README.md
```

---

## 🔨 Technologies Used

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Backend | Python 3, Flask | Game logic, REST API |
| AI Logic | SymPy | First Order Logic & entailment |
| Frontend | HTML5 Canvas, CSS, JS | Maze rendering, dashboard |
| Maze | DFS Recursive Backtracking | Corridor-based maze with wall edges |
| Pathfinding | BFS | Navigation, backtracking, homing |
| API | REST (JSON) | Frontend ↔ Backend communication |

---

## ⚙️ How to Run

### 1. Clone the Repository
```bash
git clone https://github.com/krishna-marathe/intelligent_wumpus_agent_simulator.git
cd intelligent_wumpus_agent_simulator
```

### 2. Install Dependencies
```bash
pip install -r backend/requirements.txt
```

### 3. Start the Server
```bash
python backend/app.py
```

### 4. Open the Dashboard
Navigate to **http://localhost:5000** in your browser.

---

## 🎮 Controls

| Key | Action |
|-----|--------|
| `↑` / `W` | Move Forward |
| `←` / `A` | Turn Left |
| `→` / `D` | Turn Right |
| `G` | Grab Gold |
| `S` | Shoot Arrow |
| `C` | Climb Out (at EXIT) |

Toggle **Auto-Mode** to let the AI play autonomously.

---

## 🧠 AI Decision Algorithm

```
1. PERCEPT    → Receive stench, breeze, glitter, bump, scream
2. KB UPDATE  → Update Knowledge Base; apply FOL to deduce safe cells
3. PRIORITY   → Glitter? Grab. Stench + arrow? Shoot.
4. SAFE MOVE  → Go to proven-safe unvisited neighbor
5. BACKTRACK  → BFS through visited cells to nearest safe frontier
6. RISK MOVE  → Probabilistic ranking of frontier; pick lowest risk
7. HOMING     → After gold: BFS to EXIT → follow plan → Climb Out
```

---

## 🎓 MFAI Concepts Applied

| Concept | Application |
|---------|-------------|
| **First Order Logic** | ∀x: Breeze(x) → ∃y: Adjacent(x,y) ∧ Pit(y) |
| **Knowledge Representation** | KB stores safe cells, visited cells, percept observations |
| **Logical Inference** | No breeze → all neighbors safe (KB ⊨ Safe) |
| **Probabilistic Reasoning** | Bayesian risk estimation for frontier cells |
| **Intelligent Agents** | PEAS framework: Percept → Reason → Act loop |

---

## 📊 Scoring System

| Event | Points |
|-------|--------|
| Base Score | 1000 |
| Each Action | −1 |
| Kill Wumpus | +500 |
| Grab Gold | +1000 |
| Exit with Gold | +2000 |
| Die (pit/Wumpus) | −1000 |

---

## 👤 Author

**Krishna Marathe**
*Vishwakarma Institute of Technology, Pune*

---

## 📄 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

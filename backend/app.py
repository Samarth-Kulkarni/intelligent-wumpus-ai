from flask import Flask, jsonify, request
from flask_cors import CORS
import sys, os

sys.path.append(os.path.join(os.path.dirname(__file__), 'simulator'))
sys.path.append(os.path.dirname(__file__))

from simulator import WumpusWorld, Action
from ai.agent import IntelligentAgent

frontend_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'frontend')
app = Flask(__name__, static_folder=frontend_path, static_url_path='')
CORS(app)

@app.route('/')
def index():
    return app.send_static_file('index.html')

# Global instances
game_instance = WumpusWorld(size=8)
ai_agent = IntelligentAgent(size=8)

def get_combined_state():
    state = game_instance.get_state()
    x, y = state['agent_pos']
    ai_agent.update_knowledge(x, y, state['percepts'], state.get('walls', []))
    # Sync authoritative game state into AI agent
    ai_agent.has_gold = state['agent_has_gold']
    ai_agent.wumpus_alive = state['wumpus_alive']
    ai_agent.has_arrow = state.get('agent_has_arrow', True)
    ai_logic = ai_agent.get_recommendation(state['agent_dir'])
    state['ai_thoughts'] = ai_logic['thoughts']
    state['best_action'] = ai_logic['best_action']
    state['kb_count'] = ai_logic['kb_count']
    state['kb_facts'] = ai_logic.get('kb_facts', [])
    state['probabilities'] = ai_logic.get('probabilities', {})
    state['nodes_expanded'] = ai_logic.get('nodes_expanded', 0)
    return state

@app.route('/api/init', methods=['POST'])
def init_game():
    global game_instance, ai_agent
    data = request.json or {}
    size = data.get('size', 8)
    game_instance = WumpusWorld(size=size)
    ai_agent = IntelligentAgent(size=size)
    return jsonify(get_combined_state())

@app.route('/api/retry', methods=['POST'])
def retry_game():
    global game_instance, ai_agent
    if game_instance:
        game_instance.reset()
        ai_agent = IntelligentAgent(size=game_instance.size)
    return jsonify(get_combined_state())

@app.route('/api/state', methods=['GET'])
def get_state():
    return jsonify(get_combined_state())

@app.route('/api/batch', methods=['POST'])
def batch_simulate():
    data = request.json or {}
    iterations = data.get('iterations', 100)
    size = data.get('size', 8)
    algo = data.get('algo', 'ASTAR')

    wins = 0
    deaths_pit = 0
    deaths_wumpus = 0
    total_moves = 0
    total_gambles = 0
    total_score = 0

    for _ in range(iterations):
        game = WumpusWorld(size=size)
        agent = IntelligentAgent(size=size)
        agent.pathfinding_algo = algo

        while not game.is_game_over():
            state = game.get_state()
            x, y = state['agent_pos']
            agent.update_knowledge(x, y, state['percepts'], state.get('walls', []))
            agent.has_gold = state['agent_has_gold']
            agent.wumpus_alive = state['wumpus_alive']
            agent.has_arrow = state.get('agent_has_arrow', True)
            
            ai_logic = agent.get_recommendation(state['agent_dir'])
            action_str = ai_logic['best_action']
            
            if any("Probabilistic reasoning" in t for t in ai_logic['thoughts']):
                total_gambles += 1

            action_map = {
                "FORWARD": Action.GOFORWARD, "TURNLEFT": Action.TURNLEFT,
                "TURNRIGHT": Action.TURNRIGHT, "GRAB": Action.GRAB,
                "SHOOT": Action.SHOOT, "CLIMB": Action.CLIMB,
            }
            if action_str not in action_map:
                break
            
            game.execute_action(action_map[action_str])
            
            # Prevent infinite loops in simulation if the agent gets stuck
            if game.num_actions > 150:
                break
        
        final_state = game.get_state()
        total_score += final_state['score']
        total_moves += final_state['moves']
        if not final_state['agent_alive']:
            if final_state['agent_pos'] == final_state['wumpus_pos'] and final_state['wumpus_alive']:
                deaths_wumpus += 1
            else:
                deaths_pit += 1
        elif final_state['is_over'] and final_state['agent_alive']:
            wins += 1

    return jsonify({
        "iterations": iterations,
        "wins": wins,
        "win_rate": (wins / iterations) * 100,
        "deaths_pit": deaths_pit,
        "deaths_wumpus": deaths_wumpus,
        "avg_moves": round(total_moves / iterations, 1),
        "total_gambles": total_gambles,
        "avg_score": round(total_score / iterations, 1)
    })

@app.route('/api/algo', methods=['POST'])
def set_algo():
    data = request.json
    algo = data.get('algo')
    if algo in ['BFS', 'ASTAR']:
        ai_agent.pathfinding_algo = algo
    return jsonify(get_combined_state())

@app.route('/api/step', methods=['POST'])
def step():
    if game_instance.is_game_over():
        return jsonify({"error": "Game is over", "state": get_combined_state()}), 400
    data = request.json
    action_str = data.get('action')
    action_map = {
        "FORWARD": Action.GOFORWARD, "TURNLEFT": Action.TURNLEFT,
        "TURNRIGHT": Action.TURNRIGHT, "GRAB": Action.GRAB,
        "SHOOT": Action.SHOOT, "CLIMB": Action.CLIMB,
    }
    if action_str not in action_map:
        return jsonify({"error": "Invalid action"}), 400
    game_instance.execute_action(action_map[action_str])
    return jsonify(get_combined_state())

if __name__ == '__main__':
    app.run(debug=True, port=5000)

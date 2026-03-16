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
    return state

@app.route('/api/init', methods=['POST'])
def init_game():
    global game_instance, ai_agent
    data = request.json or {}
    size = data.get('size', 8)
    game_instance = WumpusWorld(size=size)
    ai_agent = IntelligentAgent(size=size)
    return jsonify(get_combined_state())

@app.route('/api/state', methods=['GET'])
def get_state():
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

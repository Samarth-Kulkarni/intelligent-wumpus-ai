import sys
import os
sys.path.append(os.path.join(os.getcwd(), 'backend'))
try:
    from backend.ai.agent import IntelligentAgent
    print("Import successful")
except Exception as e:
    print(f"Import failed: {e}")
    import traceback
    traceback.print_exc()

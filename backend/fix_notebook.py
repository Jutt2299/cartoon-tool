import json
import os

nb_path = 'c:/Users/alone/Desktop/cartoon-tool/kaggle_notebook/notebook.ipynb'
with open(nb_path, 'r', encoding='utf-8') as f:
    nb = json.load(f)

for cell in nb.get('cells', []):
    if cell.get('cell_type') == 'code':
        source_lines = cell.get('source', [])
        source = ''.join(source_lines)
        
        if 'def idle_checker():' in source:
            idx = source.find('def idle_checker():')
            new_source = source[:idx] + 'def run_server():\n    uvicorn.run(app, host="0.0.0.0", port=8000)\n\nserver_thread = threading.Thread(target=run_server, daemon=True)\nserver_thread.start()\nprint("FastAPI server started on port 8000 with Wan2.1 model!")'
            # Convert back to list of lines
            lines = new_source.split('\n')
            cell['source'] = [line + '\n' for line in lines[:-1]] + [lines[-1]] if lines[-1] else [line + '\n' for line in lines]
            
        elif 'CELL 6' in source:
            new_source = '''# CELL 6 - Keep alive and idle checker
import time
print("Ready! Will auto-shutdown after 5 minutes of idle.")
while True:
    time.sleep(30)
    idle_secs = time.time() - last_activity
    print(f"Idle for {int(idle_secs)}s / {IDLE_TIMEOUT}s")
    if idle_secs > IDLE_TIMEOUT:
        print("Idle timeout reached. Cleanly exiting to stop Kaggle session.")
        break
'''
            lines = new_source.split('\n')
            cell['source'] = [line + '\n' for line in lines[:-1]] + [lines[-1]] if lines[-1] else [line + '\n' for line in lines]

with open(nb_path, 'w', encoding='utf-8') as f:
    json.dump(nb, f, indent=1)

print("Updated notebook.ipynb successfully.")

import os
import subprocess
import sys
import tempfile
import json

env = os.environ.copy()
env['KAGGLE_USERNAME'] = 'alonevideogentool'
env['KAGGLE_KEY'] = 'KGAT_96fb3c35d249d9c146ebc656313e60ef'
kaggle_cmd = [os.path.join(os.path.dirname(sys.executable), 'Scripts', 'kaggle.exe')]

try:
    with tempfile.TemporaryDirectory() as tmpdir:
        metadata = {
            'id': 'alonevideogentool/cartoon-video-generator',
            'title': 'cartoon-video-generator',
            'code_file': 'test.py',
            'language': 'python',
            'kernel_type': 'script',
            'is_private': True
        }
        with open(os.path.join(tmpdir, 'kernel-metadata.json'), 'w') as f:
            json.dump(metadata, f)
        with open(os.path.join(tmpdir, 'test.py'), 'w') as f:
            f.write('print(\"hello\")')
            
        print('Pushing script with matching slug...')
        result = subprocess.run(
            kaggle_cmd + ['kernels', 'push', '-p', tmpdir],
            capture_output=True, text=True, check=False, env=env, encoding='utf-8', errors='replace'
        )
        print('Return code:', result.returncode)
        print('Stdout:', result.stdout.strip())
        print('Stderr:', result.stderr.strip())
except Exception as e:
    print('Exception:', e)

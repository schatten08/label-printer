import subprocess
result = subprocess.run(['lpstat', '-v'], capture_output=True, text=True)
print('lpstat -v output:')
print(result.stdout)

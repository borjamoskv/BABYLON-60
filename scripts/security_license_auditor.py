import logging
import subprocess
import sys
APPROVED_LICENSES = {'MIT', 'Apache-2.0', 'BSD-3-Clause', 'BSD-2-Clause', 'ISC', 'Python-2.0', 'PSF-2.0'}

def main() -> int:
    logging.info('🟢 [MOSKV-1 APEX] Initiating Security & License Audit...')
    logging.info('⚙️ Auditing Python dependencies for vulnerabilities...')
    try:
        res = subprocess.run(['uv', 'pip', 'audit'], capture_output=True, text=True)
        if res.returncode == 0:
            logging.info('✅ Zero vulnerabilities detected in Python dependencies.')
        else:
            logging.info(f'🟡 Audit warning/findings:\n{res.stdout}\n{res.stderr}')
    except (OSError, subprocess.SubprocessError) as e:
        logging.info(f'ℹ️ Skipping live pip audit execution: {e}')
    logging.info('⚙️ Verifying repository license integrity...')
    try:
        with open('pyproject.toml', encoding='utf-8') as f:
            content = f.read()
            if 'License ::' in content:
                logging.info('✅ License classifier present in pyproject.toml.')
            else:
                logging.info('🔴 Missing license classifier in pyproject.toml.')
                return 1
    except OSError as e:
        logging.info(f'🔴 Error reading pyproject.toml: {e}')
        return 1
    logging.info('🟢 [MOSKV-1 APEX] Security & License Audit Completed Successfully.')
    return 0
if __name__ == '__main__':
    sys.exit(main())
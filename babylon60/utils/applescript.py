import asyncio
import logging
logger = logging.getLogger(__name__)

async def run_applescript(script: str, timeout_seconds: int=30) -> tuple[bool, str, str]:
    logger.debug('Executing AppleScript (timeout=%ss)', timeout_seconds)
    try:
        process = await asyncio.create_subprocess_exec('osascript', '-e', script, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        try:
            stdout_bytes, stderr_bytes = await asyncio.wait_for(process.communicate(), timeout=timeout_seconds)
            success = process.returncode == 0
            stdout = stdout_bytes.decode('utf-8', errors='replace').strip()
            stderr = stderr_bytes.decode('utf-8', errors='replace').strip()
            if not success:
                logger.warning('AppleScript execution failed: %s', stderr)
            return (success, stdout, stderr)
        except asyncio.TimeoutError:
            logger.error('AppleScript execution timed out.')
            process.kill()
            await process.communicate()
            return (False, '', 'TimeoutError: AppleScript execution exceeded time limit.')
    except OSError as e:
        logger.error('OSError executing osascript: %s', e)
        return (False, '', f'OSError: {e!s}')
    except ValueError as e:
        logger.error('ValueError executing osascript: %s', e)
        return (False, '', f'ValueError: {e!s}')
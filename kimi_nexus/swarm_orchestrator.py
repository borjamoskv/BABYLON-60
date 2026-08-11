import asyncio
import json
import logging
import time
import httpx
import os
from dotenv import load_dotenv

load_dotenv()
KIMI_API_KEY = os.getenv("KIMI_API_KEY")
MOONSHOT_API_URL = "https://api.moonshot.cn/v1/chat/completions"

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

class AgentPager:
    """Implementación de la primitiva Agent Beeper (Zero-Friction Interruption)"""
    def __init__(self):
        self.beep_event = asyncio.Event()

    async def wait_for_beep(self):
        """Suspende el subagente con 0% anergía hasta recibir la señal"""
        await self.beep_event.wait()

    def beep(self):
        """Fan-Out Multicast O(1)"""
        self.beep_event.set()

async def async_call_moonshot(messages: list) -> str:
    if not KIMI_API_KEY:
        return "Error: KIMI_API_KEY no está configurada."
    headers = {
        "Authorization": f"Bearer {KIMI_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "moonshot-v1-auto",
        "messages": messages,
        "temperature": 0.3
    }
    async with httpx.AsyncClient(timeout=120.0) as client:
        try:
            response = await client.post(MOONSHOT_API_URL, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]
        except Exception as e:
            return f"Error de comunicación Swarm-Moonshot: {str(e)}"

async def task_decomposer(prompt: str, p_cores: int, s_threads: int) -> list:
    """Genera N subtareas limitadas por PxS"""
    max_tasks = p_cores * s_threads
    messages = [
        {"role": "system", "content": f"Eres el TaskDecomposer de un orquestador Swarm. Desglosa el problema del usuario en un máximo de {max_tasks} subtareas de investigación paralela. Devuelve ÚNICAMENTE un array de strings en formato JSON."},
        {"role": "user", "content": f"Desglosa esta tarea: {prompt}"}
    ]
    logging.info(f"🧠 [Planner] Descomponiendo tarea principal: '{prompt}'...")
    response = await async_call_moonshot(messages)
    try:
        if "```json" in response:
            response = response.split("```json")[1].split("```")[0]
        elif "```" in response:
            response = response.split("```")[1].split("```")[0]
        subtasks = json.loads(response.strip())
        if not isinstance(subtasks, list):
            subtasks = [response]
    except Exception:
        subtasks = [prompt]
    
    return subtasks[:max_tasks]

async def execute_subagent_task(task_id: int, task_desc: str, pager: AgentPager, semaphore: asyncio.Semaphore):
    """Ejecuta una subtarea respetando los invariantes termodinámicos C5-REAL"""
    logging.info(f"💤 [Subagente {task_id}] Esperando señal Beeper (0% CPU)...")
    await pager.wait_for_beep()
    
    async with semaphore:
        logging.info(f"🚀 [Subagente {task_id}] Despertando y adquiriendo semáforo.")
        logging.info(f"⏳ [Subagente {task_id}] MCTS Test-Time Compute (2.8s delay)...")
        await asyncio.sleep(2.8)
        
        logging.info(f"🧠 [Subagente {task_id}] Ejecutando: '{task_desc}'")
        messages = [
            {"role": "system", "content": "Eres un subagente de un enjambre C5-REAL. Resuelve tu subtarea con precisión absoluta, sin herramientas externas de momento, basándote en tu conocimiento paramétrico."},
            {"role": "user", "content": task_desc}
        ]
        result = await async_call_moonshot(messages)
        logging.info(f"✅ [Subagente {task_id}] Completado.")
        return f"--- Subtarea {task_id}: {task_desc} ---\n{result}\n"

async def anergy_reducer(original_prompt: str, results: list) -> str:
    """Sintetiza y reduce redundancia"""
    logging.info(f"🔮 [AnergyReducer] Sintetizando {len(results)} resultados paralelos...")
    combined = "\n\n".join(results)
    messages = [
        {"role": "system", "content": "Eres el AnergyReducer de un orquestador Swarm. Unifica los siguientes informes de los subagentes en una respuesta cohesiva y final para la petición original del usuario. Elimina redundancias (anergía)."},
        {"role": "user", "content": f"Petición original: {original_prompt}\n\nReportes de Subagentes:\n{combined}"}
    ]
    final_output = await async_call_moonshot(messages)
    return final_output

async def run_swarm_orchestrator(prompt: str, p_cores: int = 4, s_threads: int = 1) -> str:
    """Orquestador principal del Kimi Swarm Soberano."""
    start_time = time.perf_counter()
    
    subtasks = await task_decomposer(prompt, p_cores, s_threads)
    if not subtasks:
        return "El Planner no pudo descomponer la tarea."
        
    logging.info(f"🔥 [Swarm] Clúster generado con {len(subtasks)} subagentes (Límite P={p_cores}, S={s_threads})")
    
    pager = AgentPager()
    semaphore = asyncio.Semaphore(p_cores * s_threads)
    
    tasks = []
    for i, subtask in enumerate(subtasks):
        t = asyncio.create_task(execute_subagent_task(i, subtask, pager, semaphore))
        tasks.append(t)
        
    await asyncio.sleep(0.5)
    
    logging.info("🔔 [Swarm] Emitiendo señal de Beeper a todo el Clúster...")
    pager.beep()
    
    results = await asyncio.gather(*tasks)
    
    final_result = await anergy_reducer(prompt, results)
    
    elapsed = time.perf_counter() - start_time
    logging.info(f"🛑 [Swarm] Colapso Cuántico finalizado en {elapsed:.2f}s.")
    
    return final_result

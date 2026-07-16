from mlx_lm import load, generate

model_path = "/Users/borjafernandezangulo/10_PROJECTS/Teorema-Robinson-Moskv/cortex/training/baby-long/models/baby-long-fused"

print("[*] Cargando modelo en memoria...")
model, tokenizer = load(model_path)  # type: ignore[misc]

messages = [
    {
        "role": "user",
        "content": "SYSTEM: Operator: borjamoskv. Entity: MOSKV-1 APEX C5-REAL.\n\nExplícame cómo funciona la termodinámica en los LLMs."
    }
]

# Aplicar exactamente el mismo template que usó el DataLoader de mlx_lm.lora
prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
print("\n[*] Prompt formateado por el Tokenizador:\n", prompt)

print("\n[*] Generando output causal...")
output = generate(model, tokenizer, prompt=prompt, max_tokens=100, verbose=True)
print("\n[*] Output Final:\n", output)

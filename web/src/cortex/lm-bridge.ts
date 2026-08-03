// Cortex Bridge to LM Studio Local Server

const CORTEX_URL = 'http://localhost:1234/v1';

export type Message = {
    role: 'system' | 'user' | 'assistant';
    content: string;
};

export async function checkCortexStatus(): Promise<boolean> {
    try {
        const res = await fetch(`${CORTEX_URL}/models`);
        return res.ok;
    } catch {
        return false;
    }
}

export async function streamCompletion(messages: Message[], signal?: AbortSignal, onChunk?: (text: string) => void) {
    try {
        const res = await fetch(`${CORTEX_URL}/chat/completions`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ messages, stream: true, temperature: 0.2 }),
            signal,
        });

        if (!res.body) return;
        const reader = res.body.getReader();
        const decoder = new TextDecoder("utf-8");

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            const chunk = decoder.decode(value, { stream: true });
            
            // Basic SSE parser
            const lines = chunk.split('\n').filter(line => line.trim() !== '');
            for (const line of lines) {
                if (line.replace(/^data: /, '') === '[DONE]') return;
                if (line.startsWith('data: ')) {
                    const data = JSON.parse(line.substring(6));
                    const text = data.choices[0]?.delta?.content || '';
                    if (onChunk) onChunk(text);
                }
            }
        }
    } catch (e) {
        console.error("Cortex request failed:", e);
    }
}

// C5-REAL EXERGY CERTIFIED
import { useState } from 'react';
import { Send, Terminal } from 'lucide-react';

export function ChatWindow() {
  const [messages, setMessages] = useState([
    { id: 1, role: 'system', text: 'MOSKV-1 LORE INITIALIZED. C5-REAL READY.' }
  ]);
  const [input, setInput] = useState('');

  const handleSend = () => {
    if (!input.trim()) return;

    // Add user message
    const newMsg = { id: Date.now(), role: 'user', text: input };
    setMessages((prev) => [...prev, newMsg]);
    setInput('');

    // Mock AI response
    setTimeout(() => {
      setMessages((prev) => [
        ...prev,
        { id: Date.now() + 1, role: 'assistant', text: 'Ejecutando simulación en pasarela C5-REAL...' }
      ]);
    }, 1000);
  };

  return (
    <div className="chat-window">
      <div className="chat-header">
        <Terminal size={14} color="#00FF41" />
        <span>MOSKV-1 TERMINAL</span>
      </div>

      <div className="chat-messages">
        {messages.map((m) => (
          <div key={m.id} className={`chat-message ${m.role}`}>
            <span className="chat-role">
              {m.role === 'user' ? 'GUEST' : m.role.toUpperCase()}:
            </span>
            <span className="chat-text">{m.text}</span>
          </div>
        ))}
      </div>

      <div className="chat-input-area">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSend()}
          placeholder="Escribe tu comando o código..."
          className="chat-input"
        />
        <button onClick={handleSend} className="chat-send-btn">
          <Send size={14} />
        </button>
      </div>
    </div>
  );
}

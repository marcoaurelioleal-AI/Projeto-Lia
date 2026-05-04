import { useMutation, useQuery } from '@tanstack/react-query';
import { Bot, KeyRound, Send, ShieldCheck, UserRound } from 'lucide-react';
import { FormEvent, useState } from 'react';
import { api } from '../api/client';
import { PageHeader } from '../components/PageHeader';
import { useAuth } from '../contexts/useAuth';
import type { ChatMessage } from '../types';

export function AssistantPage() {
  const { user } = useAuth();
  const isAdmin = user?.role === 'admin';
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      role: 'assistant',
      content: 'Olá. Sou o Assistente LIA. Posso ajudar com preparo, atendimento, fechamento, estoque e padronização.'
    }
  ]);
  const [input, setInput] = useState('');

  const statusQuery = useQuery({
    queryKey: ['ai-status'],
    queryFn: api.aiStatus,
    enabled: isAdmin,
    staleTime: 30_000
  });

  const mutation = useMutation({
    mutationFn: (history: ChatMessage[]) => api.chat(history),
    onSuccess: (response) => {
      setMessages((current) => [...current, { role: 'assistant', content: response.reply }]);
    },
    onError: (error) => {
      setMessages((current) => [
        ...current,
        { role: 'assistant', content: error instanceof Error ? error.message : 'Não consegui responder agora.' }
      ]);
    }
  });

  function handleSubmit(event: FormEvent) {
    event.preventDefault();
    const content = input.trim();
    if (!content || mutation.isPending) return;
    const userMessage: ChatMessage = { role: 'user', content };
    const nextMessages: ChatMessage[] = [...messages, userMessage].slice(-10);
    setMessages(nextMessages);
    setInput('');
    mutation.mutate(nextMessages);
  }

  return (
    <>
      <PageHeader
        eyebrow="Consultoria IA"
        title="Assistente operacional"
        description="Pergunte sobre preparo, processos, atendimento e padrões. A chave Gemini fica protegida no backend."
      />

      {isAdmin ? (
        <section className="mb-4 grid gap-3 rounded-lg border border-lia-red/10 bg-white p-4 shadow-sm md:grid-cols-4">
          <div className="flex items-center gap-3 md:col-span-1">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-lia-red text-white">
              <ShieldCheck size={18} />
            </div>
            <div>
              <p className="text-xs font-bold uppercase tracking-[0.2em] text-lia-red">Diagnostico IA</p>
              <p className="font-extrabold text-lia-burgundy">
                {statusQuery.data?.configured ? 'Gemini configurado' : 'Gemini sem chave'}
              </p>
            </div>
          </div>
          <div className="rounded-lg bg-lia-cream px-3 py-2">
            <p className="text-xs font-bold uppercase text-lia-muted">Modelo</p>
            <p className="truncate font-semibold text-lia-ink">{statusQuery.data?.model ?? 'Carregando...'}</p>
          </div>
          <div className="rounded-lg bg-lia-cream px-3 py-2">
            <p className="text-xs font-bold uppercase text-lia-muted">Tamanho da chave</p>
            <p className="font-semibold text-lia-ink">{statusQuery.data?.key_length ?? '--'} caracteres</p>
          </div>
          <div className="rounded-lg bg-lia-cream px-3 py-2">
            <p className="flex items-center gap-1 text-xs font-bold uppercase text-lia-muted">
              <KeyRound size={13} /> Fingerprint
            </p>
            <p className="font-mono text-sm font-semibold text-lia-ink">
              {statusQuery.data?.key_fingerprint ?? 'indisponivel'}
            </p>
          </div>
          {statusQuery.isError ? (
            <p className="text-sm font-semibold text-lia-red md:col-span-4">
              Nao consegui carregar o diagnostico da IA. Entre novamente e tente de novo.
            </p>
          ) : null}
        </section>
      ) : null}

      <section className="surface flex min-h-[65vh] flex-col rounded-lg">
        <div className="flex-1 space-y-3 overflow-y-auto p-4">
          {messages.map((message, index) => (
            <div
              key={`${message.role}-${index}`}
              className={`flex gap-3 ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              {message.role === 'assistant' ? (
                <div className="mt-1 flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-lia-red text-white">
                  <Bot size={18} />
                </div>
              ) : null}
              <div
                className={[
                  'max-w-[88%] rounded-lg px-4 py-3 text-sm leading-6 md:max-w-[70%]',
                  message.role === 'user' ? 'bg-lia-burgundy text-white' : 'bg-white text-lia-ink'
                ].join(' ')}
              >
                {message.content}
              </div>
              {message.role === 'user' ? (
                <div className="mt-1 flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-lia-burgundy text-white">
                  <UserRound size={18} />
                </div>
              ) : null}
            </div>
          ))}
          {mutation.isPending ? <p className="text-sm font-semibold text-lia-muted">Consultando assistente...</p> : null}
        </div>

        <form onSubmit={handleSubmit} className="border-t border-lia-red/10 p-3">
          <div className="flex gap-2">
            <input
              value={input}
              onChange={(event) => setInput(event.target.value)}
              placeholder="Digite uma dúvida operacional..."
              className="focus-ring min-w-0 flex-1 rounded-lg border border-lia-red/15 bg-white px-3 py-3"
            />
            <button
              disabled={mutation.isPending}
              className="focus-ring flex items-center justify-center rounded-lg bg-lia-red px-4 font-bold text-white disabled:opacity-70"
            >
              <Send size={18} />
            </button>
          </div>
        </form>
      </section>
    </>
  );
}

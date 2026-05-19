import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  AlertTriangle,
  Bot,
  Clock3,
  KeyRound,
  Send,
  ShieldCheck,
  Sparkles,
  ThumbsDown,
  ThumbsUp,
  UserRound
} from 'lucide-react';
import { FormEvent, useMemo, useState } from 'react';
import { api } from '../api/client';
import { PageHeader } from '../components/PageHeader';
import { useAuth } from '../contexts/useAuth';
import type { AiFeedbackRating, AiResponseMode, ChatMessage, ChatSource } from '../types';

type UiMessage = ChatMessage & {
  mode?: 'offline' | 'gemini' | 'error';
  interactionId?: number;
  sources?: ChatSource[];
  needsManagerConfirmation?: boolean;
  feedbackRating?: AiFeedbackRating | null;
};

const STORE = 'Grupo Lia';

export function AssistantPage() {
  const queryClient = useQueryClient();
  const { user } = useAuth();
  const isAdmin = user?.role === 'admin';
  const [unit, setUnit] = useState('');
  const [responseMode, setResponseMode] = useState<AiResponseMode>('rapido');
  const [sessionId, setSessionId] = useState<number | null>(null);
  const [messages, setMessages] = useState<UiMessage[]>([
    {
      role: 'assistant',
      content:
        'Ola, eu sou a Lia. Posso ajudar com preparo, padronizacao, validade, limpeza, atendimento e fechamento usando os manuais internos da Central LIA.'
    }
  ]);
  const [input, setInput] = useState('');

  const feedbackMutation = useMutation({
    mutationFn: ({ interactionId, rating }: { interactionId: number; rating: AiFeedbackRating }) =>
      api.submitAiFeedback(interactionId, rating),
    onSuccess: (interaction) => {
      setMessages((current) =>
        current.map((message) =>
          message.interactionId === interaction.id
            ? { ...message, feedbackRating: interaction.feedback_rating }
            : message
        )
      );
      queryClient.invalidateQueries({ queryKey: ['ai-history'] });
    }
  });

  const { data: manuals = [] } = useQuery({ queryKey: ['manuals'], queryFn: api.manuals });
  const { data: history = [] } = useQuery({ queryKey: ['ai-history'], queryFn: api.aiHistory });

  const units = useMemo(() => Array.from(new Set(manuals.map((manual) => manual.unit))), [manuals]);

  const statusQuery = useQuery({
    queryKey: ['ai-status'],
    queryFn: api.aiStatus,
    enabled: isAdmin,
    staleTime: 30_000
  });

  const mutation = useMutation({
    mutationFn: (historyMessages: ChatMessage[]) =>
      api.chat(historyMessages, {
        store: STORE,
        unit,
        sessionId,
        responseMode
      }),
    onSuccess: (response) => {
      setSessionId(response.session_id);
      setMessages((current) => [
        ...current,
        {
          role: 'assistant',
          content: response.reply,
          mode: response.mode,
          interactionId: response.interaction_id,
          sources: response.sources,
          needsManagerConfirmation: response.needs_manager_confirmation
        }
      ]);
      queryClient.invalidateQueries({ queryKey: ['ai-history'] });
    },
    onError: (error) => {
      setMessages((current) => [
        ...current,
        {
          role: 'assistant',
          content: error instanceof Error ? error.message : 'Nao consegui responder agora.',
          mode: 'error',
          needsManagerConfirmation: true
        }
      ]);
    }
  });

  function handleSubmit(event: FormEvent) {
    event.preventDefault();
    const content = input.trim();
    if (!content || mutation.isPending) return;
    const userMessage: UiMessage = { role: 'user', content };
    const nextMessages = [...messages, userMessage].slice(-10);
    setMessages(nextMessages);
    setInput('');
    mutation.mutate(nextMessages.map(({ role, content }) => ({ role, content })));
  }

  function startNewSession() {
    setSessionId(null);
    setMessages([
      {
        role: 'assistant',
        content:
          'Nova conversa iniciada. Escolha a unidade, se quiser filtrar, e me diga qual duvida operacional precisa resolver.'
      }
    ]);
  }

  return (
    <>
      <PageHeader
        eyebrow="Lia"
        title="Chatbot operacional"
        description="Converse com a Lia sobre preparo, validade, limpeza, atendimento e fechamento com base nos manuais internos."
      />

      <section className="mb-4 grid gap-3 lg:grid-cols-[1fr_320px]">
        <div className="surface rounded-lg p-4">
          <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
            <div className="flex items-center gap-3">
              <div className="flex h-11 w-11 items-center justify-center rounded-lg bg-lia-red text-white">
                <Sparkles size={20} />
              </div>
              <div>
                <p className="text-xs font-bold uppercase tracking-[0.2em] text-lia-red">Central LIA</p>
                <h2 className="text-xl font-black text-lia-burgundy">Lia pronta para orientar o turno</h2>
              </div>
            </div>
            <button
              onClick={startNewSession}
              className="focus-ring rounded-lg border border-lia-red/20 px-3 py-2 text-sm font-bold text-lia-burgundy hover:bg-lia-red/10"
            >
              Nova conversa
            </button>
          </div>

          <div className="mt-4 grid gap-3 md:grid-cols-[220px_220px_1fr]">
            <label className="grid gap-1 text-sm font-bold text-lia-burgundy">
              Unidade
              <select
                value={unit}
                onChange={(event) => setUnit(event.target.value)}
                className="focus-ring rounded-lg border border-lia-red/15 bg-white px-3 py-3 font-semibold"
              >
                <option value="">Todas as lojas</option>
                {units.map((unitName) => (
                  <option key={unitName} value={unitName}>
                    {unitName}
                  </option>
                ))}
              </select>
            </label>
            <label className="grid gap-1 text-sm font-bold text-lia-burgundy">
              Modo
              <select
                value={responseMode}
                onChange={(event) => setResponseMode(event.target.value as AiResponseMode)}
                className="focus-ring rounded-lg border border-lia-red/15 bg-white px-3 py-3 font-semibold"
              >
                <option value="rapido">Rapido</option>
                <option value="detalhado">Detalhado</option>
                <option value="treinamento">Treinamento</option>
              </select>
            </label>
            <div className="rounded-lg bg-white px-3 py-3 text-sm leading-6 text-lia-muted">
              A Lia responde com base nos manuais internos. Quando a base nao for suficiente, ela orienta confirmar com
              a gestao.
            </div>
          </div>
        </div>

        <HistoryPanel history={history} />
      </section>

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
        </section>
      ) : null}

      <section className="surface flex min-h-[62vh] flex-col rounded-lg">
        <div className="flex-1 space-y-3 overflow-y-auto p-4">
          {messages.map((message, index) => (
            <ChatBubble
              key={`${message.role}-${index}`}
              message={message}
              feedbackPending={feedbackMutation.isPending}
              onFeedback={(interactionId, rating) => feedbackMutation.mutate({ interactionId, rating })}
            />
          ))}
          {mutation.isPending ? <p className="text-sm font-semibold text-lia-muted">Lia consultando os manuais...</p> : null}
        </div>

        <form onSubmit={handleSubmit} className="border-t border-lia-red/10 p-3">
          <div className="flex gap-2">
            <input
              value={input}
              onChange={(event) => setInput(event.target.value)}
              placeholder="Digite uma duvida operacional..."
              className="focus-ring min-w-0 flex-1 rounded-lg border border-lia-red/15 bg-white px-3 py-3"
            />
            <button
              disabled={mutation.isPending}
              aria-label="Enviar pergunta para a Lia"
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

function ChatBubble({
  message,
  feedbackPending,
  onFeedback
}: {
  message: UiMessage;
  feedbackPending: boolean;
  onFeedback: (interactionId: number, rating: AiFeedbackRating) => void;
}) {
  const isUser = message.role === 'user';

  return (
    <div className={`flex gap-3 ${isUser ? 'justify-end' : 'justify-start'}`}>
      {!isUser ? (
        <div className="mt-1 flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-lia-red text-white">
          <Bot size={18} />
        </div>
      ) : null}
      <div className="max-w-[88%] space-y-2 md:max-w-[72%]">
        <div
          className={[
            'rounded-lg px-4 py-3 text-sm leading-6',
            isUser ? 'bg-lia-burgundy text-white' : 'bg-white text-lia-ink'
          ].join(' ')}
        >
          {message.content}
        </div>
        {!isUser && message.needsManagerConfirmation ? (
          <p className="flex items-center gap-2 rounded-lg bg-lia-red/10 px-3 py-2 text-xs font-bold text-lia-red">
            <AlertTriangle size={14} /> Confirme com a gestao antes de aplicar esta orientacao.
          </p>
        ) : null}
        {!isUser && message.interactionId ? (
          <div className="flex flex-wrap items-center gap-2 text-xs font-bold text-lia-muted">
            {message.feedbackRating ? (
              <span className="rounded-lg bg-lia-green/10 px-3 py-2 text-lia-green">Feedback registrado</span>
            ) : (
              <>
                <button
                  type="button"
                  title="Marcar resposta como util"
                  disabled={feedbackPending}
                  onClick={() => onFeedback(message.interactionId!, 'ajudou')}
                  className="focus-ring flex items-center gap-1 rounded-lg border border-lia-red/15 bg-white px-3 py-2 text-lia-burgundy disabled:opacity-60"
                >
                  <ThumbsUp size={14} /> Ajudou
                </button>
                <button
                  type="button"
                  title="Marcar resposta como insuficiente"
                  disabled={feedbackPending}
                  onClick={() => onFeedback(message.interactionId!, 'nao_ajudou')}
                  className="focus-ring flex items-center gap-1 rounded-lg border border-lia-red/15 bg-white px-3 py-2 text-lia-burgundy disabled:opacity-60"
                >
                  <ThumbsDown size={14} /> Nao ajudou
                </button>
              </>
            )}
          </div>
        ) : null}
        {!isUser && message.sources?.length ? <Sources sources={message.sources} /> : null}
      </div>
      {isUser ? (
        <div className="mt-1 flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-lia-burgundy text-white">
          <UserRound size={18} />
        </div>
      ) : null}
    </div>
  );
}

function Sources({ sources }: { sources: ChatSource[] }) {
  return (
    <div className="space-y-2">
      <p className="text-xs font-bold uppercase tracking-[0.16em] text-lia-muted">Fontes consultadas</p>
      <div className="grid gap-2">
        {sources.map((source, index) => (
          <div key={`${source.manual_id}-${source.section_title}-${index}`} className="rounded-lg bg-lia-cream px-3 py-2">
            <p className="text-sm font-black text-lia-burgundy">
              {source.unit} - {source.title ?? source.manual_title}
            </p>
            {source.section_title ? <p className="text-xs font-bold text-lia-red">{source.section_title}</p> : null}
            <p className="mt-1 line-clamp-2 text-xs leading-5 text-lia-muted">{source.excerpt}</p>
          </div>
        ))}
      </div>
    </div>
  );
}

function HistoryPanel({
  history
}: {
  history: Array<{
    id: number;
    store: string;
    unit: string | null;
    question: string;
    created_at: string;
  }>;
}) {
  return (
    <aside className="surface rounded-lg p-4">
      <div className="mb-3 flex items-center gap-2">
        <Clock3 size={18} className="text-lia-red" />
        <h3 className="font-black text-lia-burgundy">Historico recente</h3>
      </div>
      {history.length ? (
        <div className="space-y-2">
          {history.slice(0, 5).map((item) => (
            <div key={item.id} className="rounded-lg bg-white px-3 py-2">
              <p className="line-clamp-2 text-sm font-semibold text-lia-ink">{item.question}</p>
              <p className="mt-1 text-xs text-lia-muted">
                {item.unit || item.store} - {new Date(item.created_at).toLocaleDateString('pt-BR')}
              </p>
            </div>
          ))}
        </div>
      ) : (
        <p className="text-sm leading-6 text-lia-muted">As conversas resumidas da Lia aparecerao aqui.</p>
      )}
    </aside>
  );
}

import { useEffect, useMemo, useState } from "react";
import {
  ChatResponse,
  Citation,
  DocumentItem,
  deleteDocument,
  fetchDocuments,
  sendChat,
  uploadNote,
  uploadPdf
} from "./lib/api";

const modes = [
  { value: "qa", label: "Q&A" },
  { value: "summarize_doc", label: "Summarize doc" },
  { value: "summarize_multi", label: "Summarize multi" },
  { value: "key_takeaways", label: "Key takeaways" },
  { value: "flashcards", label: "Flashcards" }
];

type Message = {
  id: string;
  role: "user" | "assistant";
  content: string;
  citations?: Citation[];
  retrieved?: number;
};

const apiModels = (import.meta.env.VITE_MODEL_OPTIONS as string | undefined) || "gpt-4o-mini";
const modelOptions = apiModels.split(",").map((item) => item.trim()).filter(Boolean);

export default function App() {
  const [docs, setDocs] = useState<DocumentItem[]>([]);
  const [selectedDocs, setSelectedDocs] = useState<Set<string>>(new Set());
  const [messages, setMessages] = useState<Message[]>([]);
  const [question, setQuestion] = useState("");
  const [noteText, setNoteText] = useState("");
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [chatLoading, setChatLoading] = useState(false);
  const [mode, setMode] = useState("qa");
  const [topK, setTopK] = useState(5);
  const [temperature, setTemperature] = useState(0.2);
  const [model, setModel] = useState(modelOptions[0] || "gpt-4o-mini");
  const [toast, setToast] = useState<string | null>(null);

  const selectedDocIds = useMemo(() => Array.from(selectedDocs), [selectedDocs]);

  useEffect(() => {
    void loadDocs();
  }, []);

  async function loadDocs() {
    try {
      const list = await fetchDocuments();
      setDocs(list);
    } catch (error) {
      showToast("Failed to load documents");
    }
  }

  function toggleDoc(id: string) {
    setSelectedDocs((prev) => {
      const copy = new Set(prev);
      if (copy.has(id)) {
        copy.delete(id);
      } else {
        copy.add(id);
      }
      return copy;
    });
  }

  async function handleUpload(file: File) {
    setUploading(true);
    setUploadProgress(0);
    try {
      await uploadPdf(file, (pct) => setUploadProgress(pct));
      await loadDocs();
    } catch (error) {
      showToast("Upload failed");
    } finally {
      setUploading(false);
      setUploadProgress(0);
    }
  }

  async function handleNoteUpload() {
    if (!noteText.trim()) {
      showToast("Add some notes first");
      return;
    }
    setUploading(true);
    try {
      await uploadNote(noteText.trim());
      setNoteText("");
      await loadDocs();
    } catch (error) {
      showToast("Note upload failed");
    } finally {
      setUploading(false);
    }
  }

  async function handleDelete(docId: string) {
    try {
      await deleteDocument(docId);
      setSelectedDocs((prev) => {
        const copy = new Set(prev);
        copy.delete(docId);
        return copy;
      });
      await loadDocs();
    } catch (error) {
      showToast("Delete failed");
    }
  }

  async function handleSend() {
    if (!question.trim()) {
      return;
    }
    const userMessage: Message = {
      id: crypto.randomUUID(),
      role: "user",
      content: question.trim()
    };
    setMessages((prev) => [...prev, userMessage]);
    setQuestion("");
    setChatLoading(true);

    try {
      const payload = {
        question: userMessage.content,
        doc_ids: selectedDocIds.length > 0 ? selectedDocIds : undefined,
        mode,
        top_k: topK,
        temperature,
        model
      };
      const response: ChatResponse = await sendChat(payload);
      const assistantMessage: Message = {
        id: crypto.randomUUID(),
        role: "assistant",
        content: response.answer,
        citations: response.citations,
        retrieved: response.retrieved_chunks_count
      };
      setMessages((prev) => [...prev, assistantMessage]);
    } catch (error) {
      showToast("Chat request failed");
    } finally {
      setChatLoading(false);
    }
  }

  function showToast(message: string) {
    setToast(message);
    setTimeout(() => setToast(null), 3000);
  }

  return (
    <div className="min-h-screen flex flex-col">
      <header className="px-6 py-5 flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
        <div>
          <p className="text-xs uppercase tracking-[0.3em] text-ocean font-semibold">LLM Research Assistant</p>
          <h1 className="text-3xl md:text-4xl font-display text-ink">Study, search, and synthesize across your PDFs</h1>
        </div>
        <div className="bg-white/70 border border-white rounded-full px-4 py-2 shadow-soft text-sm">
          Ready for indexed answers with citations.
        </div>
      </header>

      <main className="flex-1 px-6 pb-8">
        <div className="grid grid-cols-1 lg:grid-cols-[280px_1fr_280px] gap-6">
          <aside className="flex flex-col gap-4">
            <div className="bg-white/80 rounded-2xl p-4 shadow-soft border border-white">
              <h2 className="text-lg font-display mb-2">Upload</h2>
              <label className="flex flex-col gap-2 text-sm">
                <span className="font-medium">PDF file</span>
                <input
                  type="file"
                  accept="application/pdf"
                  className="block w-full text-sm file:mr-4 file:rounded-full file:border-0 file:bg-ocean file:px-4 file:py-2 file:text-white file:shadow-soft"
                  onChange={(event) => {
                    const file = event.target.files?.[0];
                    if (file) {
                      void handleUpload(file);
                      event.target.value = "";
                    }
                  }}
                  disabled={uploading}
                />
              </label>
              {uploading && (
                <div className="mt-3">
                  <div className="h-2 w-full rounded-full bg-slate-100 overflow-hidden">
                    <div
                      className="h-full bg-sunrise transition-all"
                      style={{ width: `${uploadProgress || 20}%` }}
                    />
                  </div>
                  <p className="text-xs mt-1 text-slate-500">Uploading & indexing...</p>
                </div>
              )}
              <div className="mt-4">
                <label className="text-sm font-medium">Quick note</label>
                <textarea
                  value={noteText}
                  onChange={(event) => setNoteText(event.target.value)}
                  placeholder="Paste study notes here..."
                  className="mt-2 w-full rounded-xl border border-slate-200 bg-white/80 p-2 text-sm focus:outline-none focus:ring-2 focus:ring-ocean"
                  rows={4}
                />
                <button
                  className="mt-2 w-full rounded-xl bg-ink text-white py-2 text-sm shadow-soft"
                  onClick={() => void handleNoteUpload()}
                  disabled={uploading}
                >
                  Save note
                </button>
              </div>
            </div>

            <div className="bg-white/80 rounded-2xl p-4 shadow-soft border border-white">
              <div className="flex items-center justify-between mb-2">
                <h2 className="text-lg font-display">Documents</h2>
                <button
                  className="text-xs text-ocean"
                  onClick={() => void loadDocs()}
                >
                  Refresh
                </button>
              </div>
              <div className="space-y-3 max-h-[360px] overflow-auto pr-1">
                {docs.length === 0 && (
                  <p className="text-sm text-slate-500">No documents yet. Upload a PDF or add notes.</p>
                )}
                {docs.map((doc) => (
                  <div key={doc.id} className="border border-slate-200 rounded-xl p-2 bg-white/70">
                    <label className="flex items-start gap-2 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={selectedDocs.has(doc.id)}
                        onChange={() => toggleDoc(doc.id)}
                        className="mt-1"
                      />
                      <div className="flex-1">
                        <p className="text-sm font-medium text-ink">{doc.title}</p>
                        <p className="text-xs text-slate-500">{doc.num_pages} pages - {new Date(doc.created_at).toLocaleDateString()}</p>
                        <span className={`inline-block mt-1 text-[10px] px-2 py-0.5 rounded-full ${doc.status === "indexed" ? "bg-green-100 text-green-700" : "bg-yellow-100 text-yellow-700"}`}>
                          {doc.status}
                        </span>
                      </div>
                      <button
                        className="text-xs text-red-500"
                        onClick={(event) => {
                          event.preventDefault();
                          event.stopPropagation();
                          void handleDelete(doc.id);
                        }}
                      >
                        Delete
                      </button>
                    </label>
                  </div>
                ))}
              </div>
            </div>
          </aside>

          <section className="flex flex-col gap-4">
            <div className="bg-white/80 rounded-2xl p-4 shadow-soft border border-white flex-1 flex flex-col">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h2 className="text-lg font-display">Chat</h2>
                  <p className="text-xs text-slate-500">Ask questions, summarize, or generate study assets.</p>
                </div>
                <select
                  className="rounded-full border border-slate-200 bg-white/80 px-3 py-1 text-sm"
                  value={mode}
                  onChange={(event) => setMode(event.target.value)}
                >
                  {modes.map((item) => (
                    <option key={item.value} value={item.value}>{item.label}</option>
                  ))}
                </select>
              </div>
              <div className="flex-1 overflow-auto space-y-4 pr-2">
                {messages.length === 0 && (
                  <div className="border border-dashed border-slate-200 rounded-2xl p-6 text-center text-slate-500">
                    <p className="font-medium">No messages yet.</p>
                    <p className="text-sm">Select documents, then ask your first question.</p>
                  </div>
                )}
                {messages.map((message) => (
                  <div
                    key={message.id}
                    className={`rounded-2xl p-4 ${message.role === "user" ? "bg-ocean text-white ml-auto" : "bg-white border border-slate-200"} max-w-2xl`}
                  >
                    <p className="text-sm whitespace-pre-wrap">{message.content}</p>
                    {message.role === "assistant" && (
                      <div className="mt-3 text-xs text-slate-500">
                        <p>Retrieved chunks: {message.retrieved ?? 0}</p>
                        {message.citations && message.citations.length > 0 && (
                          <details className="mt-2">
                            <summary className="cursor-pointer text-ocean">Citations ({message.citations.length})</summary>
                            <div className="mt-2 space-y-2">
                              {message.citations.map((citation) => (
                                <div key={citation.ref} className="rounded-xl border border-slate-200 bg-slate-50 p-2">
                                  <p className="text-[11px] font-semibold">[{citation.ref}] {citation.doc_title} (page {citation.page})</p>
                                  <p className="text-[11px] italic">"{citation.snippet}"</p>
                                  <p className="text-[10px] text-slate-400">chunk {citation.chunk_id} - score {citation.score.toFixed(3)}</p>
                                </div>
                              ))}
                            </div>
                          </details>
                        )}
                      </div>
                    )}
                  </div>
                ))}
                {chatLoading && (
                  <div className="rounded-2xl p-4 bg-white border border-slate-200 max-w-sm">
                    <p className="text-sm text-slate-500">Thinking...</p>
                  </div>
                )}
              </div>
              <div className="mt-4 flex items-center gap-2">
                <input
                  value={question}
                  onChange={(event) => setQuestion(event.target.value)}
                  placeholder="Ask a question or request a summary..."
                  className="flex-1 rounded-full border border-slate-200 bg-white/90 px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ocean"
                />
                <button
                  className="rounded-full bg-sunrise px-5 py-2 text-sm font-medium text-white shadow-soft"
                  onClick={() => void handleSend()}
                  disabled={chatLoading}
                >
                  Send
                </button>
              </div>
            </div>
          </section>

          <aside className="flex flex-col gap-4">
            <div className="bg-white/80 rounded-2xl p-4 shadow-soft border border-white">
              <h2 className="text-lg font-display mb-3">Settings</h2>
              <label className="text-sm font-medium">Model</label>
              <select
                className="mt-2 w-full rounded-xl border border-slate-200 bg-white/80 px-3 py-2 text-sm"
                value={model}
                onChange={(event) => setModel(event.target.value)}
              >
                {modelOptions.map((option) => (
                  <option key={option} value={option}>{option}</option>
                ))}
              </select>

              <label className="mt-4 text-sm font-medium block">Temperature</label>
              <input
                type="range"
                min={0}
                max={1}
                step={0.05}
                value={temperature}
                onChange={(event) => setTemperature(Number(event.target.value))}
                className="w-full"
              />
              <p className="text-xs text-slate-500">{temperature.toFixed(2)}</p>

              <label className="mt-4 text-sm font-medium block">Top K</label>
              <input
                type="number"
                min={1}
                max={20}
                value={topK}
                onChange={(event) => setTopK(Number(event.target.value))}
                className="mt-2 w-full rounded-xl border border-slate-200 bg-white/80 px-3 py-2 text-sm"
              />
              <p className="text-xs text-slate-500">Number of chunks retrieved per request.</p>
            </div>

            <div className="bg-white/80 rounded-2xl p-4 shadow-soft border border-white">
              <h2 className="text-lg font-display mb-2">Selection</h2>
              <p className="text-sm text-slate-500">Selected documents: {selectedDocIds.length}</p>
              <p className="text-xs text-slate-400 mt-1">If none are selected, all documents are searched.</p>
            </div>
          </aside>
        </div>
      </main>

      {toast && (
        <div className="fixed bottom-6 right-6 rounded-full bg-ink text-white px-4 py-2 shadow-soft text-sm">
          {toast}
        </div>
      )}
    </div>
  );
}

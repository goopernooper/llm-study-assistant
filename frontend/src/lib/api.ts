export type DocumentItem = {
  id: string;
  title: string;
  num_pages: number;
  created_at: string;
  status: string;
};

export type Citation = {
  ref: number;
  doc_id: string;
  doc_title: string;
  page: number;
  chunk_id: string;
  snippet: string;
  score: number;
};

export type ChatResponse = {
  answer: string;
  citations: Citation[];
  retrieved_chunks_count: number;
};

const API_BASE = (import.meta.env.VITE_API_URL as string) || "http://localhost:8000/api";

export async function fetchDocuments(): Promise<DocumentItem[]> {
  const res = await fetch(`${API_BASE}/docs`);
  if (!res.ok) {
    throw new Error("Failed to load documents");
  }
  return res.json();
}

export async function deleteDocument(docId: string): Promise<void> {
  const res = await fetch(`${API_BASE}/docs/${docId}`, { method: "DELETE" });
  if (!res.ok) {
    throw new Error("Failed to delete document");
  }
}

export function uploadPdf(file: File, onProgress: (pct: number) => void): Promise<void> {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    xhr.open("POST", `${API_BASE}/docs/upload`);
    xhr.onload = () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        resolve();
      } else {
        reject(new Error("Upload failed"));
      }
    };
    xhr.onerror = () => reject(new Error("Upload failed"));
    xhr.upload.onprogress = (event) => {
      if (event.lengthComputable) {
        const pct = Math.round((event.loaded / event.total) * 100);
        onProgress(pct);
      }
    };
    const form = new FormData();
    form.append("file", file);
    xhr.send(form);
  });
}

export async function uploadNote(text: string): Promise<void> {
  const form = new FormData();
  form.append("text", text);
  const res = await fetch(`${API_BASE}/docs/upload`, { method: "POST", body: form });
  if (!res.ok) {
    throw new Error("Failed to upload note");
  }
}

export async function sendChat(payload: {
  question: string;
  doc_ids?: string[];
  mode: string;
  top_k: number;
  temperature: number;
  model: string;
}): Promise<ChatResponse> {
  const res = await fetch(`${API_BASE}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });
  if (!res.ok) {
    const detail = await res.text();
    throw new Error(detail || "Chat request failed");
  }
  return res.json();
}

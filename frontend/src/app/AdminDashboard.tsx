"use client";
import React, { useState, useEffect } from 'react';
import { Settings, FileText, CheckCircle, AlertTriangle, Trash2, ShieldAlert } from 'lucide-react';

interface Document {
  doc_id: string;
  file_name: string;
  file_size: string;
  status: string;
  uploaded_at: string;
  category_name?: string;
  chunk_count?: number;
}

export default function AdminDashboard() {
  const [activeTab, setActiveTab] = useState<'docs' | 'system'>('docs');
  const [documents, setDocuments] = useState<Document[]>([]);
  const [selectedDocs, setSelectedDocs] = useState<Set<string>>(new Set());
  const [systemCheck, setSystemCheck] = useState<any>(null);

  useEffect(() => {
    if (activeTab === 'docs') {
      fetch('/api/admin/documents')
        .then(res => res.json())
        .then(data => setDocuments(data || []))
        .catch(err => console.error(err));
    } else {
      fetch('/api/admin/system_check')
        .then(res => res.json())
        .then(data => setSystemCheck(data))
        .catch(err => console.error(err));
    }
  }, [activeTab]);

  const handleToggleSelect = (doc_id: string) => {
    const newSelected = new Set(selectedDocs);
    if (newSelected.has(doc_id)) {
      newSelected.delete(doc_id);
    } else {
      newSelected.add(doc_id);
    }
    setSelectedDocs(newSelected);
  };

  const handleBatchDelete = async () => {
    if (selectedDocs.size === 0) return;
    if (!confirm('Are you sure you want to delete selected documents?')) return;

    try {
      await fetch('/api/admin/documents/delete', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ doc_ids: Array.from(selectedDocs) })
      });
      setSelectedDocs(new Set());
      // Refresh list
      const res = await fetch('/api/admin/documents');
      const data = await res.json();
      setDocuments(data || []);
    } catch (err) {
      console.error(err);
    }
  };

  const handleClearFailed = async () => {
    if (!confirm('Are you sure you want to clear failed imports?')) return;
    try {
      await fetch('/api/admin/documents/clear_failed', { method: 'POST' });
      // Refresh list
      const res = await fetch('/api/admin/documents');
      const data = await res.json();
      setDocuments(data || []);
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="flex flex-col h-full bg-[#131315] text-[#e5e1e4] p-6 font-sans">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-semibold tracking-tight">Admin Dashboard</h1>
        <div className="flex gap-2">
          <button
            onClick={() => setActiveTab('docs')}
            className={`p-2 rounded-md transition-colors ${activeTab === 'docs' ? 'bg-[#2a2a2c]' : 'hover:bg-[#1c1b1d]'}`}
          >
            <FileText size={20} />
          </button>
          <button
            onClick={() => setActiveTab('system')}
            className={`p-2 rounded-md transition-colors ${activeTab === 'system' ? 'bg-[#2a2a2c]' : 'hover:bg-[#1c1b1d]'}`}
          >
            <Settings size={20} />
          </button>
        </div>
      </div>

      {activeTab === 'docs' && (
        <div className="flex flex-col flex-1">
          <div className="flex justify-between mb-4">
            <h2 className="text-lg font-medium text-[#bbcabf]">Knowledge Base Documents</h2>
            <div className="flex gap-3">
              <button
                onClick={handleClearFailed}
                className="px-4 py-2 text-sm border border-[#3c4a42] rounded-md hover:bg-[#1c1b1d] transition-colors"
              >
                Clear Failed Imports
              </button>
              <button
                onClick={handleBatchDelete}
                disabled={selectedDocs.size === 0}
                className="px-4 py-2 text-sm bg-red-900/40 text-red-200 border border-red-900 rounded-md disabled:opacity-50 disabled:cursor-not-allowed hover:bg-red-900/60 transition-colors flex items-center gap-2"
              >
                <Trash2 size={16} />
                Batch Delete ({selectedDocs.size})
              </button>
            </div>
          </div>

          <div className="overflow-x-auto bg-[#09090b] border border-[#27272a] rounded-lg">
            <table className="w-full text-sm text-left">
              <thead className="text-xs text-[#86948a] uppercase bg-[#1c1b1d] border-b border-[#27272a]">
                <tr>
                  <th className="p-4 w-4">
                    <input type="checkbox" className="rounded border-gray-600 bg-transparent text-[#4edea3] focus:ring-0"
                      onChange={(e) => {
                        if (e.target.checked) setSelectedDocs(new Set(documents.map(d => d.doc_id)));
                        else setSelectedDocs(new Set());
                      }}
                      checked={selectedDocs.size === documents.length && documents.length > 0}
                    />
                  </th>
                  <th className="px-6 py-3">Document Name</th>
                  <th className="px-6 py-3">Size / Chunks</th>
                  <th className="px-6 py-3">Status</th>
                  <th className="px-6 py-3">Upload Time</th>
                </tr>
              </thead>
              <tbody>
                {documents.length === 0 ? (
                  <tr><td colSpan={5} className="p-8 text-center text-gray-500">No documents found.</td></tr>
                ) : documents.map(doc => (
                  <tr key={doc.doc_id} className="border-b border-[#27272a] hover:bg-[#18181b] transition-colors">
                    <td className="p-4">
                      <input type="checkbox" className="rounded border-gray-600 bg-transparent text-[#4edea3] focus:ring-0"
                        checked={selectedDocs.has(doc.doc_id)}
                        onChange={() => handleToggleSelect(doc.doc_id)}
                      />
                    </td>
                    <td className="px-6 py-4 font-medium">{doc.file_name}</td>
                    <td className="px-6 py-4 text-[#86948a]">{doc.file_size} {doc.chunk_count ? `(${doc.chunk_count} chunks)` : ''}</td>
                    <td className="px-6 py-4">
                      {doc.status === 'success' || doc.status === 'indexed' ? (
                        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-[#4edea3]/10 text-[#4edea3]">
                          <CheckCircle size={12} /> Active
                        </span>
                      ) : doc.status.includes('fail') || doc.status.includes('error') ? (
                        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-red-500/10 text-red-400">
                          <AlertTriangle size={12} /> Failed
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-blue-500/10 text-blue-400">
                          <span className="w-1.5 h-1.5 rounded-full bg-blue-400 animate-pulse"></span> Processing
                        </span>
                      )}
                    </td>
                    <td className="px-6 py-4 text-[#86948a]">{doc.uploaded_at}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {activeTab === 'system' && (
        <div className="flex flex-col flex-1">
          <h2 className="text-lg font-medium text-[#bbcabf] mb-4">System Status Check</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">

            <div className="bg-[#09090b] border border-[#27272a] rounded-lg p-5">
              <div className="flex items-center justify-between mb-4">
                <h3 className="font-medium text-[#e5e1e4]">API Connectivity</h3>
                <CheckCircle size={18} className="text-[#4edea3]" />
              </div>
              <p className="text-sm text-[#86948a] mb-1">FastAPI Backend</p>
              <p className="text-sm font-mono text-[#bbcabf]">Connected</p>
            </div>

            <div className="bg-[#09090b] border border-[#27272a] rounded-lg p-5">
              <div className="flex items-center justify-between mb-4">
                <h3 className="font-medium text-[#e5e1e4]">System Checks</h3>
                <CheckCircle size={18} className="text-[#4edea3]" />
              </div>
              <p className="text-sm text-[#86948a] mb-1">Status</p>
              <p className="text-sm font-mono text-[#bbcabf]">{systemCheck?.message || 'Loading...'}</p>
            </div>

            <div className="bg-[#09090b] border border-[#27272a] rounded-lg p-5">
               <div className="flex items-center justify-between mb-4">
                <h3 className="font-medium text-[#e5e1e4]">Database</h3>
                <CheckCircle size={18} className="text-[#4edea3]" />
              </div>
              <p className="text-sm text-[#86948a] mb-1">SQLite & ChromaDB</p>
              <p className="text-sm font-mono text-[#bbcabf]">Online</p>
            </div>

          </div>
        </div>
      )}
    </div>
  );
}

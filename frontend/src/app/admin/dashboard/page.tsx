"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";

export default function AdminDashboard() {
  const [status, setStatus] = useState<any>(null);
  const [error, setError] = useState("");
  const router = useRouter();

  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const res = await fetch("/api/admin/status");
        if (res.ok) {
          const data = await res.json();
          setStatus(data);
        } else {
          setError("Failed to fetch system status");
        }
      } catch (err) {
        setError("Error connecting to server");
      }
    };
    fetchStatus();
  }, []);

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-[#0a0a0a] p-8">
      <div className="max-w-6xl mx-auto">
        <header className="mb-8 flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 dark:text-white">System Dashboard</h1>
            <p className="text-gray-500 dark:text-gray-400 mt-1">AIZS Campus Assistant Administration</p>
          </div>
          <button
            onClick={() => router.push("/admin")}
            className="px-4 py-2 border border-gray-300 dark:border-gray-700 rounded-lg text-sm font-medium hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
          >
            Logout
          </button>
        </header>

        {error && (
          <div className="mb-6 p-4 rounded-lg bg-red-50 text-red-600 border border-red-100">
            {error}
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-white dark:bg-gray-900 p-6 rounded-xl border border-gray-200 dark:border-gray-800 shadow-sm relative overflow-hidden">
             <div className="absolute top-0 right-0 p-4 opacity-10">
                <svg className="w-16 h-16 text-[#0169a3]" fill="currentColor" viewBox="0 0 20 20"><path d="M13 6a3 3 0 11-6 0 3 3 0 016 0zM18 8a2 2 0 11-4 0 2 2 0 014 0zM14 15a4 4 0 00-8 0v3h8v-3zM6 8a2 2 0 11-4 0 2 2 0 014 0zM16 18v-3a5.972 5.972 0 00-.75-2.906A3.005 3.005 0 0119 15v3h-3zM4.75 12.094A5.973 5.973 0 004 15v3H1v-3a3 3 0 013.75-2.906z"></path></svg>
             </div>
            <h2 className="text-sm font-medium text-gray-500 dark:text-gray-400">Total Sessions</h2>
            <div className="mt-2 flex items-baseline gap-2">
              <span className="text-4xl font-bold text-gray-900 dark:text-white">
                {status ? status.total_sessions : "-"}
              </span>
            </div>
          </div>

          <div className="bg-white dark:bg-gray-900 p-6 rounded-xl border border-gray-200 dark:border-gray-800 shadow-sm relative overflow-hidden">
            <div className="absolute top-0 right-0 p-4 opacity-10">
                <svg className="w-16 h-16 text-[#22887d]" fill="currentColor" viewBox="0 0 20 20"><path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM9.555 7.168A1 1 0 008 8v4a1 1 0 001.555.832l3-2a1 1 0 000-1.664l-3-2z" clipRule="evenodd"></path></svg>
             </div>
            <h2 className="text-sm font-medium text-gray-500 dark:text-gray-400">System Status</h2>
            <div className="mt-2 flex items-center gap-2">
               <div className={`w-3 h-3 rounded-full ${status?.status === 'online' ? 'bg-green-500' : 'bg-gray-300'}`}></div>
              <span className="text-2xl font-semibold capitalize text-gray-900 dark:text-white">
                {status ? status.status : "Checking..."}
              </span>
            </div>
          </div>

          <div className="bg-white dark:bg-gray-900 p-6 rounded-xl border border-gray-200 dark:border-gray-800 shadow-sm relative overflow-hidden">
             <div className="absolute top-0 right-0 p-4 opacity-10">
                <svg className="w-16 h-16 text-indigo-500" fill="currentColor" viewBox="0 0 20 20"><path d="M3 12v3c0 1.657 3.134 3 7 3s7-1.343 7-3v-3c0 1.657-3.134 3-7 3s-7-1.343-7-3z"></path><path d="M3 7v3c0 1.657 3.134 3 7 3s7-1.343 7-3V7c0 1.657-3.134 3-7 3S3 8.657 3 7z"></path><path d="M17 5c0 1.657-3.134 3-7 3S3 6.657 3 5s3.134-3 7-3 7 1.343 7 3z"></path></svg>
             </div>
            <h2 className="text-sm font-medium text-gray-500 dark:text-gray-400">Database</h2>
            <div className="mt-2 flex items-center gap-2">
              <span className="text-2xl font-semibold capitalize text-gray-900 dark:text-white">
                {status ? status.database : "Checking..."}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

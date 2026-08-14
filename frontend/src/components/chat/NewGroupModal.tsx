import React, { useState } from "react";
import { User } from "@/types";

interface NewGroupModalProps {
  onClose: () => void;
  onCreate: (name: string, pids: string[]) => void;
  users: User[]; 
}

export function NewGroupModal({ onClose, onCreate, users }: NewGroupModalProps) {
  const [name, setName] = useState("");
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());

  const toggle = (id: string) => {
    const next = new Set(selectedIds);
    if (next.has(id)) next.delete(id);
    else next.add(id);
    setSelectedIds(next);
  };

  return (
    <div className="absolute inset-0 z-50 flex items-center justify-center bg-black/60 p-4 animate-fade-in backdrop-blur-sm">
       <div className="rounded-xl p-6 w-full max-w-sm shadow-xl" style={{ backgroundColor: 'var(--bg-secondary)', border: '1px solid var(--border-color)' }}>
          <h3 className="text-xl font-bold mb-4">New Group</h3>
          <input 
             className="w-full p-2.5 rounded-lg mb-5 outline-none transition-all focus:ring-2"
             style={{ backgroundColor: 'var(--bg-input)', border: '1px solid var(--border-color)' }}
             placeholder="Group Subject"
             value={name} onChange={e => setName(e.target.value)}
          />
          <h4 className="text-sm font-semibold mb-2 text-primary">Select Users</h4>
          <div className="max-h-56 overflow-y-auto mb-6 p-1 rounded-lg" style={{ backgroundColor: 'var(--bg-primary)' }}>
             {users.length === 0 ? (
               <div className="text-sm text-muted p-4 text-center">No users available.</div>
             ) : users.map(u => (
                 <label key={u.id} className="flex items-center gap-3 mb-1 p-2 hover:bg-white/5 rounded-lg cursor-pointer transition-colors">
                    <input 
                      type="checkbox" 
                      className="w-4 h-4 accent-[var(--accent)]"
                      checked={selectedIds.has(u.id)} 
                      onChange={() => toggle(u.id)} 
                    />
                    <div className="flex flex-col">
                      <span className="text-sm text-primary font-medium">{u.display_name}</span>
                      {u.phone && <span className="text-xs text-muted">{u.phone}</span>}
                    </div>
                 </label>
             ))}
          </div>
          <div className="flex gap-3 justify-end">
             <button onClick={onClose} className="px-4 py-2 bg-transparent border rounded-lg hover:bg-white/5 font-semibold text-sm transition-colors" style={{ borderColor: 'var(--border-color)' }}>
               Cancel
             </button>
             <button 
                 onClick={() => { if (name && selectedIds.size > 0) onCreate(name, Array.from(selectedIds)); }}
                 className="px-4 py-2 rounded-lg font-semibold text-sm text-white transition-all hover:brightness-110 disabled:opacity-50 disabled:cursor-not-allowed"
                 style={{ backgroundColor: 'var(--accent)' }}
                 disabled={!name || selectedIds.size === 0}
              >
                 Create Group
             </button>
          </div>
       </div>
    </div>
  );
}

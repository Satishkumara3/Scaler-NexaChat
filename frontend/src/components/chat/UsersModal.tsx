import React, { useEffect, useState } from "react";
import Avatar from "@/components/common/Avatar";
import { User } from "@/types";
import api from "@/lib/api";

interface UsersModalProps {
  onClose: () => void;
  onSelectUser: (userId: string) => void;
  currentUserId: string;
}

export function UsersModal({ onClose, onSelectUser, currentUserId }: UsersModalProps) {
  const [users, setUsers] = useState<User[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchUsers = async () => {
      try {
        const res = await api.get("/api/users");
        setUsers(res.data.users.filter((u: User) => u.id !== currentUserId));
      } catch (e) {
        console.error("Failed to load users", e);
      } finally {
        setIsLoading(false);
      }
    };
    fetchUsers();
  }, [currentUserId]);

  return (
    <div className="absolute inset-0 z-50 flex items-center justify-center bg-black/60 p-4 animate-fade-in backdrop-blur-sm">
      <div 
        className="rounded-xl flex flex-col w-full max-w-sm shadow-xl overflow-hidden" 
        style={{ 
          backgroundColor: 'var(--bg-secondary)', 
          border: '1px solid var(--border-color)',
          maxHeight: '80vh'
        }}
      >
        <div className="p-4 border-b flex justify-between items-center bg-black/20" style={{ borderColor: 'var(--border-color)' }}>
          <h3 className="text-xl font-bold text-primary">Start New Chat</h3>
          <button 
            onClick={onClose}
            className="p-1 rounded-full hover:bg-white/10 transition-colors text-secondary hover:text-primary"
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
          </button>
        </div>
        
        <div className="flex-1 overflow-y-auto p-2">
          {isLoading ? (
            <div className="p-4 text-center text-sm text-secondary">Loading users...</div>
          ) : users.length === 0 ? (
            <div className="p-4 text-center text-sm text-secondary">No other users found.</div>
          ) : (
            users.map(user => (
              <div 
                key={user.id}
                onClick={() => onSelectUser(user.id)}
                className="flex items-center gap-3 p-3 rounded-lg cursor-pointer transition-colors hover:bg-white/5"
              >
                <Avatar src={user.avatar_url!} name={user.display_name} size={40} />
                <div className="flex-1 min-w-0">
                  <div className="font-semibold text-primary truncate">{user.display_name}</div>
                  <div className="text-xs text-secondary truncate">{user.about || user.phone}</div>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}

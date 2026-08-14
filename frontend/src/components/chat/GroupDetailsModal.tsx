import React, { useState } from "react";
import { Conversation, GroupMember } from "@/types";
import Avatar from "@/components/common/Avatar";
import api from "@/lib/api";

interface GroupDetailsModalProps {
  conversation: Conversation;
  onClose: () => void;
  currentUserId: string;
}

export function GroupDetailsModal({ conversation, onClose, currentUserId }: GroupDetailsModalProps) {
  const [loading, setLoading] = useState(false);
  const isAdmin = conversation.members?.find((m: GroupMember) => m.id === currentUserId || m.user_id === currentUserId)?.role === "admin" || conversation.created_by === currentUserId;

  const handleLeave = async () => {
      if (!confirm("Are you sure you want to leave this group?")) return;
      setLoading(true);
      try {
          await api.post(`/api/groups/${conversation.id}/leave`);
          window.location.reload(); 
      } catch (e) {
          alert("Failed to leave group");
      }
      setLoading(false);
  };

  const handleRemoveMember = async (userId: string) => {
      if (!confirm("Remove this member?")) return;
      setLoading(true);
      try {
          await api.delete(`/api/groups/${conversation.id}/members/${userId}`);
          window.location.reload(); 
      } catch (e) {
          alert("Failed to remove member");
      }
      setLoading(false);
  };

  return (
    <div className="absolute inset-0 z-50 flex items-center justify-center bg-black/60 p-4 animate-fade-in backdrop-blur-sm">
       <div className="rounded-xl p-6 w-full max-w-sm shadow-xl" style={{ backgroundColor: 'var(--bg-secondary)', border: '1px solid var(--border-color)' }}>
          <div className="flex justify-between items-center mb-6">
              <h3 className="text-xl font-bold text-primary">Group Info</h3>
              <button onClick={onClose} className="p-1 rounded-full text-muted hover:text-primary hover:bg-white/5 transition-colors focus:outline-none">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
              </button>
          </div>
          
          <div className="flex flex-col items-center mb-6">
              <Avatar name={conversation.name || "Group"} src={conversation.avatar_url} size={80} />
              <h2 className="mt-4 font-semibold text-lg">{conversation.name}</h2>
              <span className="text-muted text-sm">{conversation.members?.length || 0} participants</span>
          </div>

          <div className="max-h-56 overflow-y-auto mb-6 p-2 rounded-lg" style={{ backgroundColor: 'var(--bg-primary)', border: '1px solid var(--border-color)' }}>
             <h4 className="text-[11px] font-bold mb-3 text-muted uppercase tracking-wider px-1">Members</h4>
             {conversation.members?.map((m: GroupMember) => (
                 <div key={m.id || m.user_id} className="flex justify-between items-center mb-1 p-2 hover:bg-white/5 rounded-lg transition-colors group">
                    <div className="flex items-center gap-3">
                       <Avatar name={m.display_name} src={m.avatar_url} size={24} />
                       <span className="text-sm font-medium text-primary">
                           {m.display_name} {(m.id === currentUserId || m.user_id === currentUserId) && <span className="text-muted font-normal">(You)</span>}
                       </span>
                    </div>
                    {m.role === "admin" && <span className="text-[10px] bg-[var(--bg-bubble-me)] text-[var(--accent-hover)] font-bold px-1.5 py-0.5 rounded tracking-wide uppercase shadow-sm">Admin</span>}
                    {isAdmin && m.role !== "admin" && (m.id !== currentUserId && m.user_id !== currentUserId) && (
                        <button 
                            disabled={loading}
                            onClick={() => handleRemoveMember(m.id || m.user_id)} 
                            className="text-red-400 hover:text-red-300 text-xs"
                        >
                            Remove
                        </button>
                    )}
                 </div>
             ))}
          </div>
          
          <div className="flex flex-col gap-3">
             {isAdmin && (
                 <button className="py-2.5 rounded-lg bg-transparent border hover:bg-white/5 font-semibold text-sm transition-colors text-blue-400 border-blue-400/30">
                     Add Participants (Coming soon)
                 </button>
             )}
             <button 
                 disabled={loading}
                 onClick={handleLeave}
                 className="py-2.5 rounded-lg font-semibold text-sm transition-colors disabled:opacity-50"
                 style={{ backgroundColor: 'rgba(220, 38, 38, 0.1)', color: '#ef4444' }}
              >
                 Exit Group
             </button>
          </div>
       </div>
    </div>
  );
}

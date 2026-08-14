import React, { useState } from "react";
import { User } from "@/types";
import Avatar from "@/components/common/Avatar";

interface SettingsModalProps {
  currentUser: User;
  onClose: () => void;
  onLogout: () => void;
}

export function SettingsModal({ currentUser, onClose, onLogout }: SettingsModalProps) {
  const [activeTab, setActiveTab] = useState("Profile");

  const tabs = ["Profile", "Privacy", "Notifications", "Appearance", "Calls", "Linked Devices", "About"];

  return (
    <div className="absolute inset-0 z-50 flex items-center justify-center bg-black/60 p-4 animate-fade-in backdrop-blur-sm">
      <div 
        className="rounded-xl w-full max-w-3xl h-[600px] max-h-[90vh] shadow-xl flex flex-row overflow-hidden" 
        style={{ backgroundColor: 'var(--bg-primary)', border: '1px solid var(--border-color)' }}
      >
         {/* Left Side: Tabs */}
         <div className="w-1/3 flex flex-col h-full border-r" style={{ borderColor: 'var(--border-color)', backgroundColor: 'var(--bg-secondary)' }}>
            <div className="p-4 border-b flex items-center gap-3" style={{ borderColor: 'var(--border-color)' }}>
               <Avatar name={currentUser.display_name} src={currentUser.avatar_url} size={40} />
               <div className="flex flex-col min-w-0">
                  <span className="font-semibold text-primary truncate">{currentUser.display_name}</span>
                  <span className="text-xs text-muted truncate">{currentUser.phone}</span>
               </div>
            </div>
            <div className="flex-1 overflow-y-auto p-2">
               {tabs.map(tab => (
                 <button 
                   key={tab}
                   onClick={() => setActiveTab(tab)}
                   className="w-full text-left px-4 py-2.5 mb-1 rounded-lg transition-colors text-sm font-medium"
                   style={{ 
                     backgroundColor: activeTab === tab ? 'var(--bg-tertiary)' : 'transparent',
                     color: activeTab === tab ? 'var(--text-primary)' : 'var(--text-secondary)'
                   }}
                 >
                   {tab}
                 </button>
               ))}
            </div>
            <div className="p-4 border-t" style={{ borderColor: 'var(--border-color)' }}>
                <button onClick={onLogout} className="w-full text-left px-4 py-2 text-sm font-medium text-red-500 hover:bg-white/5 rounded-lg transition-colors">
                  Log out
                </button>
            </div>
         </div>

         {/* Right Side: Content */}
         <div className="w-2/3 h-full flex flex-col">
            <div className="p-6 border-b flex justify-between items-center" style={{ borderColor: 'var(--border-color)' }}>
                <h3 className="text-xl font-bold text-primary">{activeTab}</h3>
                <button onClick={onClose} className="p-2 rounded-full text-muted hover:text-primary hover:bg-white/5 transition-colors focus:outline-none">
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
                </button>
            </div>
            
            <div className="p-6 flex-1 overflow-y-auto">
               {activeTab === "Profile" ? (
                  <div className="flex flex-col items-center max-w-sm mx-auto">
                     <Avatar name={currentUser.display_name} src={currentUser.avatar_url} size={120} />
                     <div className="mt-8 w-full">
                        <label className="text-xs uppercase text-accent font-bold mb-1 block">Your Name</label>
                        <div className="p-3 rounded-lg text-primary text-sm" style={{ backgroundColor: 'var(--bg-secondary)' }}>
                           {currentUser.display_name}
                        </div>
                        <p className="text-xs text-muted mt-2">This is not your username or pin. This name will be visible to your Scaler Chat contacts.</p>
                     </div>
                     <div className="mt-6 w-full">
                        <label className="text-xs uppercase text-accent font-bold mb-1 block">About</label>
                        <div className="p-3 rounded-lg text-primary text-sm min-h-[44px]" style={{ backgroundColor: 'var(--bg-secondary)' }}>
                           {currentUser.about || "Hey there! I am using Scaler Chat."}
                        </div>
                     </div>
                  </div>
               ) : (
                  <div className="h-full flex flex-col items-center justify-center text-center max-w-sm mx-auto opacity-70">
                     <svg className="mb-4 text-muted" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>
                     <h4 className="text-lg font-semibold text-primary mb-2">Coming Soon</h4>
                     <p className="text-sm text-secondary">
                       The {activeTab} settings panel is currently under development. Please check back later.
                     </p>
                  </div>
               )}
            </div>
         </div>
      </div>
    </div>
  );
}

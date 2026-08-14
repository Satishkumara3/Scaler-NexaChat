import React from "react";

export function EmptyChatState() {
  return (
    <div className="flex-1 h-full flex flex-col items-center justify-center p-8 text-center" style={{ backgroundColor: 'var(--bg-primary)' }}>
      <div 
        className="rounded-full flex flex-col items-center justify-center mb-8"
        style={{
          width: 280,
          height: 280,
          backgroundColor: 'var(--bg-secondary)',
          color: 'var(--text-muted)'
        }}
      >
        <svg
          width="80"
          height="80"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="1"
          strokeLinecap="round"
          strokeLinejoin="round"
          className="opacity-70 mb-4"
        >
          <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
          <path d="M11 11h.01" />
          <path d="M16 11h.01" />
          <path d="M6 11h.01" />
        </svg>
      </div>
      <h2 className="text-3xl font-light mb-4 text-primary">Scaler Chat for Web</h2>
      <p className="text-secondary max-w-md text-[15px] leading-relaxed">
        Send and receive messages without keeping your phone online. <br/>
        Use Scaler Chat on up to 4 linked devices and 1 phone at the same time.
      </p>
      <div className="mt-12 text-[13px] text-muted flex items-center justify-center gap-2">
         <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect><path d="M7 11V7a5 5 0 0 1 10 0v4"></path></svg>
         End-to-end encrypted messaging
      </div>
    </div>
  );
}

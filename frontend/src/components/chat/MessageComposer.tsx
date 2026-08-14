import React, { useRef, useState } from "react";
import { Message } from "@/types";

interface MessageComposerProps {
  onSendMessage: (content: string) => Promise<void>;
  onSendAttachment?: (file: File) => Promise<void>;
  onTyping?: (isTyping: boolean) => void;
  disabled?: boolean;
  replyTarget?: Message | null;
  onCancelReply?: () => void;
}

export function MessageComposer({
  onSendMessage, onSendAttachment, onTyping,
  disabled = false, replyTarget, onCancelReply,
}: MessageComposerProps) {
  const [text, setText] = useState("");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [filePreview, setFilePreview] = useState<string | null>(null);
  const [isSending, setIsSending] = useState(false);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const typingTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if ((!text.trim() && !selectedFile) || isSending || disabled) return;

    try {
      setIsSending(true);
      if (selectedFile && onSendAttachment) {
          await onSendAttachment(selectedFile);
          handleClearFile();
      }
      
      if (text.trim()) {
          await onSendMessage(text);
          setText("");
      }
      
      if (onTyping) onTyping(false);
    } catch (err) {
      console.error("Failed to send", err);
    } finally {
      setIsSending(false);
      // keep focus
      inputRef.current?.focus();
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
      if (e.key === 'Enter' && !e.shiftKey) {
          e.preventDefault();
          handleSubmit(e);
      }
  };

  const handleChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
      setText(e.target.value);
      if (onTyping) {
          onTyping(true);
          if (typingTimeoutRef.current) clearTimeout(typingTimeoutRef.current);
          typingTimeoutRef.current = setTimeout(() => {
              onTyping(false);
          }, 3000);
      }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (!file) return;
      if (file.size > 10 * 1024 * 1024) {
          alert("File size exceeds 10MB limit.");
          return;
      }
      setSelectedFile(file);
      if (file.type.startsWith("image/")) {
          setFilePreview(URL.createObjectURL(file));
      } else {
          setFilePreview(null);
      }
  };

  const handleClearFile = () => {
      setSelectedFile(null);
      if (filePreview) URL.revokeObjectURL(filePreview);
      setFilePreview(null);
      if (fileInputRef.current) fileInputRef.current.value = '';
  };

  return (
    <div className="flex flex-col" style={{ backgroundColor: "var(--bg-secondary)", borderTop: "1px solid var(--border-color)" }}>
      {/* Reply preview strip */}
      {replyTarget && (
        <div className="px-4 pt-3 pb-1 flex items-center gap-3">
          <div
            className="flex-1 flex flex-col px-3 py-2 rounded-lg text-xs"
            style={{ borderLeft: "3px solid var(--accent)", backgroundColor: "rgba(0,0,0,0.15)" }}
          >
            <span className="font-semibold" style={{ color: "var(--accent)" }}>
              Replying to {replyTarget.sender_id}
            </span>
            <span className="opacity-70 truncate mt-0.5">{replyTarget.content || "[attachment]"}</span>
          </div>
          <button
            type="button"
            onClick={onCancelReply}
            className="p-1.5 hover:bg-white/10 rounded-full transition-colors flex-shrink-0"
            style={{ color: "var(--text-secondary)" }}
            title="Cancel reply"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
              <line x1="18" y1="6" x2="6" y2="18" />
              <line x1="6" y1="6" x2="18" y2="18" />
            </svg>
          </button>
        </div>
      )}
      {selectedFile && (
        <div className="p-3 mx-3 mt-3 flex items-center justify-between rounded-lg" style={{ backgroundColor: 'var(--bg-primary)' }}>
           <div className="flex items-center gap-3 overflow-hidden">
               {filePreview ? (
                   <img src={filePreview} alt="Preview" className="w-12 h-12 object-cover rounded" />
               ) : (
                   <div className="w-12 h-12 flex items-center justify-center bg-black/20 rounded">
                     <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline></svg>
                   </div>
               )}
               <div className="flex flex-col min-w-0">
                  <span className="text-sm font-medium text-primary truncate max-w-[200px]">{selectedFile.name}</span>
                  <span className="text-xs text-muted">{(selectedFile.size / 1024).toFixed(1)} KB</span>
               </div>
           </div>
           <button type="button" onClick={handleClearFile} className="p-2 hover:bg-black/10 rounded-full transition-colors text-muted hover:text-white" disabled={isSending}>
             <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
           </button>
        </div>
      )}
    <form 
      onSubmit={handleSubmit}
      className="p-3 flex gap-2 items-end"
    >
      {onSendAttachment && (
        <>
          <input 
            type="file" 
            ref={fileInputRef} 
            onChange={handleFileChange} 
            className="hidden" 
            accept="image/jpeg,image/png,image/gif,image/webp,application/pdf,text/plain" 
          />
          <button 
            type="button" 
            onClick={() => fileInputRef.current?.click()}
            disabled={disabled || isSending}
            className="p-2 mb-1 text-muted hover:text-primary transition-colors flex-shrink-0"
            title="Attach file"
          >
             <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M21.44 11.05l-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48"></path></svg>
          </button>
        </>
      )}
      <div className="flex-1 relative">
        <textarea
          ref={inputRef}
          value={text}
          onChange={handleChange}
          onKeyDown={handleKeyDown}
          placeholder="Send a message..."
          disabled={disabled || isSending}
          rows={1}
          className="w-full bg-transparent px-4 py-3 outline-none resize-none overflow-y-auto"
          style={{
             backgroundColor: 'var(--bg-input)',
             borderRadius: '24px',
             color: 'var(--text-primary)',
             minHeight: '44px',
             maxHeight: '120px'
          }}
        />
      </div>
      
      <button 
        type="button"
        onClick={handleSubmit}
        disabled={(!text.trim() && !selectedFile) || isSending || disabled}
        className={`flex items-center mb-1 justify-center rounded-full transition-colors ${(!text.trim() && !selectedFile) || isSending || disabled ? 'opacity-50' : 'hover:scale-105'}`}
        style={{
          width: '44px',
          height: '44px',
          backgroundColor: text.trim() ? 'var(--accent)' : 'transparent',
          color: text.trim() ? 'var(--bg-primary)' : 'var(--text-muted)'
        }}
      >
        <svg fill="currentColor" viewBox="0 0 24 24" width="20" height="20">
          <path d="M22 2L2 8.66l9.64 2.7L14.34 21 22 2z" />
        </svg>
      </button>
    </form>
    </div>
  );
}

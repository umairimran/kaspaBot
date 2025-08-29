export default function ChatMessage({ role = 'assistant', content = '', timestamp }) {
  const isUser = role === 'user';
  return (
    <div className={`flex items-end gap-3 mb-2 ${isUser ? 'flex-row-reverse' : ''}`}>
      {/* Avatar/Icon */}
      <div className={`h-9 w-9 rounded-full shadow-md grid place-items-center font-bold text-base border-2 ${isUser ? 'bg-white text-kaspa-600 border-kaspa-400' : 'bg-gradient-to-tr from-kaspa-500 via-indigo-500 to-purple-600 text-white border-kaspa-500'}`}>
        {isUser ? <span className="material-icons">person</span> : <img src="/kaspa-logo.svg" alt="K" className="h-6 w-6" />}
      </div>
      {/* Bubble */}
      <div className={`relative max-w-[80%] px-4 py-3 rounded-2xl shadow-md ${isUser ? 'bg-white text-kaspa-700 ml-2' : 'bg-gradient-to-br from-kaspa-900/90 to-indigo-900/80 text-white mr-2'}`}
        style={{ borderTopLeftRadius: isUser ? 20 : 6, borderTopRightRadius: isUser ? 6 : 20 }}>
        <p className="whitespace-pre-wrap text-base leading-relaxed">{content}</p>
        {timestamp && (
          <div className={`text-xs mt-2 ${isUser ? 'text-right text-slate-400' : 'text-left text-slate-400'}`}>{timestamp}</div>
        )}
      </div>
    </div>
  );
}

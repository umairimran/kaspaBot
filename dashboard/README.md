# KASPA CHATBOT

A professional React application scaffold themed around Kaspa cryptocurrency, featuring a crypto-style dark UI, responsive layout, animated components, and modular architecture ready for plugging in a real knowledge base and embeddings.

## Stack
- React + Vite
- TailwindCSS
- Framer Motion

## Development

1. Install dependencies

   npm install

2. Start dev server

   npm run dev

3. Build for production

   npm run build

## Structure
```
kaspa-chatbot/
  ├─ src/
  │  ├─ components/    # Header, Sidebar, ChatWindow, ChatMessage, InfoCard, Ticker, StatusPill
  │  ├─ hooks/         # useChat (dummy messages), useKaspaStats (ticker placeholder)
  │  ├─ assets/        # logo
  │  ├─ index.css      # Tailwind setup and theme tokens
  │  ├─ main.jsx       # Entrypoint
  │  └─ App.jsx        # Layout
  ├─ index.html
  ├─ tailwind.config.js
  ├─ postcss.config.js
  ├─ vite.config.js
  └─ package.json
```

## Notes
- Sidebar collapses on mobile with smooth slide animation.
- Chat messages animate in with Framer Motion.
- Layout is card-based with subtle shadows, rounded corners, and Kaspa-like gradient accents.
- Replace the mocked hooks in `src/hooks` with real data sources and knowledge base integration.

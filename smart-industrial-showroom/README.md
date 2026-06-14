# Smart Industrial Cloud Showroom (智慧工業雲端展間)

TypeScript monorepo: **AI image tech-ify** → **360° AR panorama** → **digital twin overlays**.

## Directory structure

```
smart-industrial-showroom/
├── package.json                          # npm workspaces root
├── apps/
│   └── web/                              # React + Vite + R3F frontend
│       ├── package.json
│       ├── tsconfig.json
│       ├── vite.config.ts
│       ├── tailwind.config.js            # Industry 4.0 theme tokens
│       ├── postcss.config.js
│       ├── index.html
│       └── src/
│           ├── main.tsx
│           ├── App.tsx                   # Demo shell (upload → process → AR)
│           ├── index.css
│           ├── theme/
│           │   └── theme.config.ts       # Design system tokens
│           └── components/
│               ├── ui/
│               │   └── TechGlassPanel.tsx
│               └── ar/
│                   └── ARShowroom.tsx
└── services/
    └── image-processor/                  # Node.js AI processing API
        ├── package.json
        ├── tsconfig.json
        ├── .env.example
        └── src/
            ├── index.ts                  # Express REST API
            └── services/
                └── imageProcessor.service.ts
```

## Quick start

```bash
cd smart-industrial-showroom
npm install

# Terminal 1 — AI processor
cp services/image-processor/.env.example services/image-processor/.env
npm run dev:processor

# Terminal 2 — AR frontend
npm run dev:web
```

Open http://localhost:5173

## API

`POST /api/v1/process/url`

```json
{ "imageUrl": "https://cdn.example/factory.jpg", "provider": "mock" }
```

## Integration with Django showroom

Point `vite.config.ts` proxy to Django or call `imageProcessor.service.ts` from a future Python Celery task using the same prompt tokens in `image_enhance.py`.

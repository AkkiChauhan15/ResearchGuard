# Research Guard React interface

This Vite, React, TypeScript and Tailwind SPA uses the existing FastAPI `/api`
contract. It contains no provider credential or provider SDK. During development,
Vite proxies `/api` to `http://127.0.0.1:8000`.

From the repository root, start FastAPI first:

```sh
.venv/bin/python -m researchguard.server --port 8000
```

Then start the frontend in another terminal:

```sh
npm ci --prefix frontend
npm run dev --prefix frontend
```

Open `http://127.0.0.1:5173`. A production build is created with:

```sh
npm run typecheck --prefix frontend
npm run build --prefix frontend
```

After a build, FastAPI serves `frontend/dist` at `http://127.0.0.1:8000/`.
The preserved pre-React interface remains at `http://127.0.0.1:8000/legacy`.

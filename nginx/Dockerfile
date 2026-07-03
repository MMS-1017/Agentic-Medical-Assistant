# ── Stage 1: build Vue frontend ───────────────────────────────────────────────
FROM node:20-alpine AS frontend-builder

ARG VITE_API_URL=""
ENV VITE_API_URL=$VITE_API_URL

WORKDIR /app
COPY ../frontend/package*.json ./
RUN npm ci --silent
COPY ../frontend/ .
RUN npm run build

# ── Stage 2: Nginx serving built assets ──────────────────────────────────────
FROM nginx:1.27-alpine AS runtime

# Copy compiled Vue SPA
COPY --from=frontend-builder /app/dist /usr/share/nginx/html

EXPOSE 80 443

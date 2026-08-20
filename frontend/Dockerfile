FROM node:20-alpine AS build

WORKDIR /app

# Inlined into the client bundle by Vite at build time; pass via build arg.
ARG PUBLIC_API_BASE_URL=http://127.0.0.1:8000
ENV PUBLIC_API_BASE_URL=$PUBLIC_API_BASE_URL

COPY package.json package-lock.json ./
RUN npm ci

COPY . .
RUN npm run build

FROM node:20-alpine

WORKDIR /app

ENV HOST=0.0.0.0 \
    PORT=4173

COPY package.json package-lock.json ./
RUN npm ci --omit=dev

COPY --from=build /app/build /app/build

EXPOSE 4173

CMD ["node", "build"]

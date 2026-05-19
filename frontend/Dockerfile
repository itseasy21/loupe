FROM node:20-alpine AS build

WORKDIR /app

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

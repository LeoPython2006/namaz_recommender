# --- build stage ---
FROM node:20-bookworm AS build
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build
# --- runtime stage ---
FROM node:20-slim
WORKDIR /app
COPY --from=build /app /app
ENV PORT=3000
EXPOSE 3000
CMD ["npm","start"]

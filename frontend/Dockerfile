FROM node:20-alpine

WORKDIR /app

# Install dependencies first — separate layer for better caching
COPY package.json package-lock.json ./
RUN npm ci

# Copy source and build
COPY . .
RUN npm run build

EXPOSE 3000

ENV NODE_ENV=production

CMD ["npm", "start"]

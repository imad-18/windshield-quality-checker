# Frontend Dockerfile - Angular Application (Development)
FROM node:20-alpine

WORKDIR /app

# Copy package files
COPY package.json package-lock.json ./

# Install dependencies
RUN npm ci

# Copy source code
COPY . .

# Expose port
EXPOSE 4200

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD wget --quiet --tries=1 --spider http://localhost:4200 || exit 1

# Start the development server
CMD ["npx", "ng", "serve", "--host", "0.0.0.0", "--poll", "2000"]


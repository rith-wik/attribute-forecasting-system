# Build stage
FROM node:20-alpine AS builder

WORKDIR /web

# Build argument for API base URL
ARG VITE_API_BASE=http://localhost:8000/api/v1

# Copy package files
COPY package.json package-lock.json* /web/

# Install dependencies
RUN npm install

# Copy application code
COPY . /web

# Set environment variable for build
ENV VITE_API_BASE=${VITE_API_BASE}

# Build the application
RUN npm run build:prod

# Production stage
FROM node:20-alpine

WORKDIR /web

# Install serve to run the production build
RUN npm install -g serve

# Copy built files from builder
COPY --from=builder /web/dist /web/dist

EXPOSE 5173

# Serve the production build
CMD ["serve", "-s", "dist", "-l", "5173"]

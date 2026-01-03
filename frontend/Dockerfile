# Frontend Dockerfile for development
FROM node:20.11-alpine

# Install dependencies
RUN apk add --no-cache libc6-compat

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci

# Copy source code
COPY . .

# Expose port
EXPOSE 3000

# Set environment variables
ENV NEXT_PUBLIC_API_URL=http://api:8000
ENV NODE_ENV=development

# Start development server
CMD ["npm", "run", "dev", "--", "-H", "0.0.0.0"]

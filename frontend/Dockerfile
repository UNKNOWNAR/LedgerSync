FROM node:20-alpine

WORKDIR /app

COPY package.json package-lock.json* ./
RUN npm install

COPY . .

# Expose Vite development port
EXPOSE 5173

# Run the Vite development server
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]


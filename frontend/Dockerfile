FROM node:20

WORKDIR /app

COPY package*.json ./

RUN npm config set registry https://mirror-npm.runflare.com

RUN npm install --legacy-peer-deps

COPY . .

RUN npm run build

EXPOSE 3000
CMD ["npm", "run", "dev"]


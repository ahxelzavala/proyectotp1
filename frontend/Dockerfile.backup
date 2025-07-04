# Etapa de construcción
FROM node:18-alpine as build

WORKDIR /app

# Copia package.json y package-lock.json
COPY package*.json ./

# Instala las dependencias
RUN npm install --only=production

# Copia el resto del código
COPY . .

# Construye la aplicación
RUN npm run build

# Etapa de producción
FROM nginx:alpine

# Copia los archivos construidos desde la etapa anterior
COPY --from=build /app/build /usr/share/nginx/html

# Expone el puerto 80
EXPOSE 80

# Comando por defecto
CMD ["nginx", "-g", "daemon off;"]

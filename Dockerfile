FROM node:20-alpine

# Establecer el directorio de trabajo
WORKDIR /app

# Copiar los archivos de dependencias
COPY package.json .

# Instalar dependencias
RUN npm install

# Instalar serve para servir los archivos estáticos
RUN npm i -g serve

# Copiar el resto de los archivos del proyecto
COPY . .

# Ejecutar la construcción de la aplicación React
RUN npm run build

# Exponer el puerto en el que la aplicación se va a ejecutar
EXPOSE 3000

# Servir los archivos construidos
CMD ["serve", "-s", "build", "-l", "3000"]

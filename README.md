# AssetWatchAPI
# BackEnd
* Перейти в директорию ***backend*** с помощью комманды `cd backend`
* запустить сервер **UVICORN** с помощью команды `uvicorn src.main:app --reload`
* Также можете указать дополнительные параметры, для возможности доступа на других хостах `-h 0.0.0.0`

# FrontEnd

## Установка и запуск

### Установка Node.js и NPM

Для начала, вам нужно установить Node.js и NPM. Вы можете сделать это с помощью NVM (Node Version Manager).

```bash
# Установка nvm (Node Version Manager)
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash

# Загрузка и установка Node.js (возможно, вам потребуется перезапустить терминал)
nvm install 20

# Проверка версии Node.js
node -v 

# Проверка версии NPM
npm -v 
```

## Установка Vite

После установки Node.js и NPM, вам нужно установить Vite.

```bash
npm create vite@latest
```

## Установка зависимостей проекта

Теперь вы можете установить зависимости вашего проекта.

```bash
npm install
```

## Запуск проекта

После установки всех зависимостей, вы можете запустить ваш проект.

```bash
npm run dev
```

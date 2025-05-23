# frontend

This template should help get you started developing with Vue 3 in Vite.

## Recommended IDE Setup

[VSCode](https://code.visualstudio.com/) + [Volar](https://marketplace.visualstudio.com/items?itemName=Vue.volar) (and disable Vetur).

## Customize configuration

See [Vite Configuration Reference](https://vite.dev/config/).

## Project Setup

```sh
npm install
```

### Compile and Hot-Reload for Development

```sh
npm run dev
```

### Compile and Minify for Production

```sh
npm run build
```

### Run Unit Tests with [Vitest](https://vitest.dev/)

```sh
npm run test:unit
```

## Frontend structure

### Src Folder
- here resides a lot of logic to use the UI including the main app file (App.vue)
#### Assets
- contains basic css styles
#### Components
- contains the different vue components
#### Router 
- for navigating between different views
#### Stores
- provide functions to interact with the backend and collect the data currently
needed e.g. search results
#### Views
- builds the views for different pages of the UI e.g. home, combined search,..

### Utils Folder
- this defines a client to interact with the backend by using axios
- Client.js is the main file that can be used to configure the client
#### Commands
- these are the different commands that can be run
- all include the endpoint name and information specific for the command

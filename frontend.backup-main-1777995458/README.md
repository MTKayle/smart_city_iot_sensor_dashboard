# Smart City IoT Dashboard - Frontend

React + TypeScript + Vite frontend for the Smart City IoT Dashboard.

## Environment Variables

The frontend requires environment variables to connect to the backend API and WebSocket server. Copy `.env.example` to `.env` and update values as needed.

### VITE_API_URL

- **Description**: Backend REST API base URL
- **Default**: `http://localhost:8000`
- **Usage**: Used by axios for HTTP requests to fetch sensors, telemetry, alerts, and analytics data
- **Example**: `VITE_API_URL=http://localhost:8000`

### VITE_WS_URL

- **Description**: WebSocket server endpoint URL
- **Default**: `ws://localhost:8000/ws`
- **Usage**: Used for real-time telemetry and alert updates
- **Example**: `VITE_WS_URL=ws://localhost:8000/ws`

### REACT_APP_API_URL

- **Description**: Backend REST API base URL (Docker deployment)
- **Default**: `http://localhost:8000`
- **Usage**: Used in docker-compose.yml for containerized deployments
- **Note**: Vite uses `VITE_*` prefix at build time, so this variable needs to be mapped during Docker build
- **Example**: `REACT_APP_API_URL=http://localhost:8000`

### REACT_APP_WS_URL

- **Description**: WebSocket server endpoint URL (Docker deployment)
- **Default**: `ws://localhost:8000/ws`
- **Usage**: Used in docker-compose.yml for containerized deployments
- **Note**: Vite uses `VITE_*` prefix at build time, so this variable needs to be mapped during Docker build
- **Example**: `REACT_APP_WS_URL=ws://localhost:8000/ws`

### VITE_MAPBOX_TOKEN

- **Description**: Mapbox access token for map visualization
- **Default**: Public demo token (limited usage)
- **Usage**: Used by MapView component for rendering interactive maps
- **Note**: Get your own token at https://account.mapbox.com/access-tokens/
- **Example**: `VITE_MAPBOX_TOKEN=pk.your_token_here`

## Development Setup

This template provides a minimal setup to get React working in Vite with HMR and some ESLint rules.

Currently, two official plugins are available:

- [@vitejs/plugin-react](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react) uses [Oxc](https://oxc.rs)
- [@vitejs/plugin-react-swc](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react-swc) uses [SWC](https://swc.rs/)

## React Compiler

The React Compiler is not enabled on this template because of its impact on dev & build performances. To add it, see [this documentation](https://react.dev/learn/react-compiler/installation).

## Expanding the ESLint configuration

If you are developing a production application, we recommend updating the configuration to enable type-aware lint rules:

```js
export default defineConfig([
  globalIgnores(['dist']),
  {
    files: ['**/*.{ts,tsx}'],
    extends: [
      // Other configs...

      // Remove tseslint.configs.recommended and replace with this
      tseslint.configs.recommendedTypeChecked,
      // Alternatively, use this for stricter rules
      tseslint.configs.strictTypeChecked,
      // Optionally, add this for stylistic rules
      tseslint.configs.stylisticTypeChecked,

      // Other configs...
    ],
    languageOptions: {
      parserOptions: {
        project: ['./tsconfig.node.json', './tsconfig.app.json'],
        tsconfigRootDir: import.meta.dirname,
      },
      // other options...
    },
  },
])
```

You can also install [eslint-plugin-react-x](https://github.com/Rel1cx/eslint-react/tree/main/packages/plugins/eslint-plugin-react-x) and [eslint-plugin-react-dom](https://github.com/Rel1cx/eslint-react/tree/main/packages/plugins/eslint-plugin-react-dom) for React-specific lint rules:

```js
// eslint.config.js
import reactX from 'eslint-plugin-react-x'
import reactDom from 'eslint-plugin-react-dom'

export default defineConfig([
  globalIgnores(['dist']),
  {
    files: ['**/*.{ts,tsx}'],
    extends: [
      // Other configs...
      // Enable lint rules for React
      reactX.configs['recommended-typescript'],
      // Enable lint rules for React DOM
      reactDom.configs.recommended,
    ],
    languageOptions: {
      parserOptions: {
        project: ['./tsconfig.node.json', './tsconfig.app.json'],
        tsconfigRootDir: import.meta.dirname,
      },
      // other options...
    },
  },
])
```

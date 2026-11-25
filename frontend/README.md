# Frontend - React Application

Smart Plant Care dashboard built with React and Vite.

## Setup

### 1. Install Dependencies

```bash
npm install
```

This installs:
- React 18.2+
- Recharts (data visualization)
- Axios (HTTP client)
- Vite (build tool)
- ESLint (code linting)

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your configuration
```

**Key variables:**
- `VITE_API_URL` - Backend API base URL
- `VITE_SUPABASE_URL` - Supabase project URL
- `VITE_SUPABASE_ANON_KEY` - Supabase anonymous key

## Running the Application

### Development Mode

```bash
npm run dev
```

The application will start at `http://localhost:5173`

Vite provides hot module replacement (HMR) for instant updates during development.

### Build for Production

```bash
npm run build
```

Creates an optimized production build in the `dist/` directory.

### Preview Production Build

```bash
npm run preview
```

Locally preview the production build before deployment.

## Project Structure

```
frontend/
├── src/
│   ├── App.jsx         # Main application component
│   ├── App.css         # Application styles
│   ├── index.css       # Global styles
│   └── main.jsx        # React entry point
├── index.html          # HTML template
├── vite.config.js      # Vite configuration
├── .eslintrc.cjs       # ESLint configuration
├── package.json        # Dependencies and scripts
└── .env.example        # Configuration template
```

## Features

The foundation includes:

- ✅ React 18 with Vite
- ✅ Recharts integration for data visualization
- ✅ Environment variable configuration
- ✅ CORS-compatible API client setup
- ✅ ESLint for code quality
- ✅ CSS styling framework

## Code Quality

### Linting

```bash
npm run lint
```

Checks code for style and best practices issues.

## Implementation Status

✅ **Phase 2**: Foundation setup complete
- React application initialized with Vite
- Component structure in place
- Backend health check integration
- Configuration system
- Styling framework

⏳ **Phase 3**: Core features
- Dashboard components
- Real-time sensor data visualizations (Recharts)
- Plant monitoring interface
- Watering control interface
- User authentication (Supabase)

⏳ **Phase 4**: Enhanced features
- Historical data charts
- Alert and notification system
- User profile management
- Settings and preferences

## Browser Support

Targets modern browsers with ES2020+ support:
- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## Development Tools

- **Vite**: Ultra-fast build tool and dev server
- **React DevTools**: Browser extension for debugging React
- **Recharts**: Composable charting library
- **ESLint**: Code quality tool

## Performance

- Code splitting by default with Vite
- Dynamic imports for lazy-loaded components
- Optimized build with tree-shaking
- CSS modules for scoped styling (can be added)

## Support

See main project README for setup instructions and troubleshooting.

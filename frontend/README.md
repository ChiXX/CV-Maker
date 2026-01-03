# CV Maker Frontend

A Next.js application that provides a wizard interface for generating customized CVs and cover letters from job postings.

## Features

- **4-Step Wizard Interface**: Guided process for CV and cover letter generation
- **URL Input**: Paste job posting URLs for automatic content extraction
- **Real-time Loading States**: Visual feedback during content processing
- **Chat History Display**: Shows the generation process for transparency
- **Responsive Design**: Works on desktop and mobile devices

## Getting Started

### Prerequisites

- Node.js 20.9.0 or later
- npm or yarn
- Backend API running (see main project README)

### Installation

#### Option 1: Local Development
1. Install dependencies:
```bash
npm install
```

2. Start the development server:
```bash
npm run dev
```

3. Open [http://localhost:3000](http://localhost:3000) in your browser.

#### Option 2: Docker Development
The frontend can be run using Docker for consistent environments:

```bash
# From the project root directory
just ui-up          # Start only the frontend
just api-and-ui     # Start both API and frontend
just full-dev-up    # Start all services (API, frontend, database)
```

### Environment Variables

The environment variables are configured automatically in Docker. For local development, create a `.env.local` file:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Project Structure

```
src/
├── app/                 # Next.js app directory
├── components/          # React components
│   ├── steps/          # Individual wizard steps
│   ├── StepIndicator.tsx
│   └── Wizard.tsx
├── lib/                # Utility functions
│   └── api.ts         # API client functions
└── types/              # TypeScript type definitions
    └── index.ts
```

## Usage

1. **Step 1**: Enter a job posting URL
2. **Step 2**: Review extracted job details (company, title, description)
3. **Step 3**: View CV generation process and result
4. **Step 4**: View cover letter generation process and result

## API Integration

The frontend communicates with a FastAPI backend that provides:

- Job description extraction from URLs
- CV LaTeX generation
- Cover letter LaTeX generation
- Application data storage

## Development

### Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run start` - Start production server
- `npm run lint` - Run ESLint

### Building for Production

```bash
npm run build
npm start
```

## Technologies Used

- **Next.js 16** - React framework with App Router
- **TypeScript** - Type safety
- **Tailwind CSS** - Styling
- **React Hooks** - State management
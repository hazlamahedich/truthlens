# Unified Project Structure
```
truthlens/
├── apps/
│   ├── web/          # Next.js frontend application
│   └── api/          # Python/FastAPI backend agents (serverless functions)
├── packages/
│   ├── shared-types/ # Shared TypeScript interfaces between FE and BE
│   └── ui/           # Shared React components
├── docs/
│   ├── prd.md
│   └── architecture.md
└── package.json      # Root package.json for monorepo
```

---
*(Additional sections like API Specification, Detailed Component Breakdown, Security, etc., will be filled in as part of the ongoing design process during each epic.)*

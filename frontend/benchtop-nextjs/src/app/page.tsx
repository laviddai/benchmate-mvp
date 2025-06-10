// src/app/page.tsx
import { AnalysisWorkbench } from '@/components/analysis/AnalysisWorkbench';

export default function HomePage() {
  return (
    <main className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <AnalysisWorkbench />
    </main>
  );
}
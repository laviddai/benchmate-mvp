// src/app/page.tsx
'use client';

import React, { useState } from 'react';
import { AnalysisWorkbench } from '@/components/analysis/AnalysisWorkbench';
import { ImageAnalysisWorkbench } from '@/components/analysis/imaging/ImageAnalysisWorkbench';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';

type WorkbenchSelection = 'omics' | 'imaging' | null;

export default function HomePage() {
  const [selection, setSelection] = useState<WorkbenchSelection>(null);

  const renderSelection = () => {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen bg-slate-50">
        <Card className="w-full max-w-md">
          <CardHeader className="text-center">
            <CardTitle className="text-2xl">Welcome to BenchTop</CardTitle>
            <CardDescription>Please select an analysis workbench to begin.</CardDescription>
          </CardHeader>
          <CardContent className="flex flex-col space-y-4">
            <Button size="lg" onClick={() => setSelection('omics')}>
              Omics Analysis Workbench
            </Button>
            <Button size="lg" variant="secondary" onClick={() => setSelection('imaging')}>
              Image Analysis Workbench
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  };

  const renderWorkbench = () => {
    switch (selection) {
      case 'omics':
        return (
          <>
            <Button variant="link" onClick={() => setSelection(null)} className="absolute top-4 left-4">
              ← Back to selection
            </Button>
            <AnalysisWorkbench />
          </>
        );
      case 'imaging':
        return (
          <>
            <Button variant="link" onClick={() => setSelection(null)} className="absolute top-4 left-4">
              ← Back to selection
            </Button>
            <ImageAnalysisWorkbench />
          </>
        );
      default:
        return renderSelection();
    }
  };

  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-4 md:p-12 lg:p-24 bg-slate-50 relative">
      {renderWorkbench()}
    </main>
  );
}
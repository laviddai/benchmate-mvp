// src/app/page.tsx
"use client";

import { Button } from "@/components/ui/button";

export default function HomePage() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-24 bg-gradient-to-br from-slate-900 to-slate-700">
      <div className="text-center">
        <h1 className="text-5xl font-bold text-white mb-8 drop-shadow-lg">
          Welcome to BenchTop!
        </h1>
        <p className="text-xl text-slate-300 mb-12 drop-shadow-md">
          Your Next-Generation Research Analysis Workspace.
        </p>
        <Button
          variant="default"
          size="lg"
          onClick={() => alert("Get Started Button Clicked!")}
          className="shadow-xl hover:shadow-2xl transform hover:scale-105 transition-all duration-300 ease-in-out"
        >
          Get Started
        </Button>

        <div className="mt-16 p-6 bg-white/10 backdrop-blur-md rounded-xl shadow-2xl max-w-md">
          <h2 className="text-2xl font-semibold text-white mb-4">Next Steps:</h2>
          <ul className="list-disc list-inside text-slate-200 text-left space-y-2">
            <li>Verify Tailwind & shadcn/ui styling on this page.</li>
            <li>Set up an API client to connect to the backend.</li>
            <li>Build out Project and Dataset management UI.</li>
            <li>Integrate the Volcano Plot analysis workflow.</li>
          </ul>
        </div>
      </div>
    </main>
  );
}
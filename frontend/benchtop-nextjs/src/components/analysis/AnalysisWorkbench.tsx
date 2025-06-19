// frontend/benchtop-nextjs/src/components/analysis/AnalysisWorkbench.tsx
"use client";

import React, { useState, useRef, useEffect, useCallback } from 'react';
import dynamic from 'next/dynamic';
import { Toaster, toast } from 'sonner';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Progress } from '@/components/ui/progress';

// --- MODIFIED: Imports are now cleaner due to re-exporting from lib/api.ts ---
import { uploadAndCreateDataset, getAnalysisRunStatus, getPresignedUrl, getJsonFromS3, createProject } from '@/lib/api';
import { type AnalysisPlotData } from '@/types/analysis.types';
import { type VolcanoPlotData } from '@/types/volcano.types';
import { type PCAPlotData } from '@/types/pca.types';
import { type HeatmapData } from '@/types/heatmap.types';

// --- MODIFIED: Import the new tool-specific components ---
import { VolcanoAnalysis } from './tools/volcano/VolcanoAnalysis';
import { PcaAnalysis } from './tools/pca/PcaAnalysis';
import { HeatmapAnalysis } from './tools/heatmap/HeatmapAnalysis';

const InteractiveVolcanoPlot = dynamic(() => import('@/components/analysis/InteractiveVolcanoPlot'), { ssr: false });
const InteractivePCAPlot = dynamic(() => import('@/components/analysis/InteractivePCAPlot'), { ssr: false });
const InteractiveHeatmap = dynamic(() => import('@/components/analysis/InteractiveHeatmap'), { ssr: false });

// --- These interfaces remain the same ---
interface Dataset {
    id: string;
    name: string;
}
interface AnalysisRun {
    id:string;
    status: 'pending' | 'running' | 'completed' | 'failed';
    output_artifacts?: { results_json_s3_path?: string; [key: string]: any; };
    error_message?: string;
}

export function AnalysisWorkbench() {
    // --- State management remains the same ---
    const [projectId, setProjectId] = useState<string | null>(null);
    const [isCreatingProject, setIsCreatingProject] = useState(true);
    const [file, setFile] = useState<File | null>(null);
    const [isUploading, setIsUploading] = useState(false);
    const [createdDataset, setCreatedDataset] = useState<Dataset | null>(null);
    const [analysisRun, setAnalysisRun] = useState<AnalysisRun | null>(null);
    const [pollingIntervalId, setPollingIntervalId] = useState<NodeJS.Timeout | null>(null);
    const [plotData, setPlotData] = useState<AnalysisPlotData>(null);
    const [isLoadingResults, setIsLoadingResults] = useState(false);
    const fileInputRef = useRef<HTMLInputElement>(null);

    // --- All useEffect and helper functions remain largely the same ---
    useEffect(() => {
        const initializeProject = async () => {
            try {
                toast.info("Initializing new project workspace...");
                const newProject = await createProject(`User Session - ${new Date().toLocaleString()}`);
                setProjectId(newProject.id);
                toast.success("Project workspace ready!");
            } catch (error) {
                toast.error(`Could not initialize project: ${error instanceof Error ? error.message : "Unknown error"}`);
            } finally {
                setIsCreatingProject(false);
            }
        };
        initializeProject();
    }, []);

    const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
        if (event.target.files && event.target.files[0]) {
            setFile(event.target.files[0]);
            setCreatedDataset(null);
            setAnalysisRun(null);
            setPlotData(null);
            if (pollingIntervalId) stopPolling(pollingIntervalId);
        }
    };

    const handleUpload = async () => {
        if (!projectId || !file) return;
        setIsUploading(true);
        toast.info("Uploading dataset...");
        const formData = new FormData();
        formData.append('file', file);
        formData.append('project_id', projectId);
        formData.append('name', file.name);
        formData.append('technique_type', 'bulk_rna_seq');
        try {
            const data = await uploadAndCreateDataset(formData);
            setCreatedDataset(data);
            toast.success("Dataset uploaded successfully!");
        } catch (error) {
            toast.error(`Upload failed: ${error instanceof Error ? error.message : "Unknown error"}`);
        } finally {
            setIsUploading(false);
        }
    };

    const startPolling = (runId: string) => {
        if (pollingIntervalId) clearInterval(pollingIntervalId);
        const intervalId = setInterval(async () => {
            try {
                const updatedRun = await getAnalysisRunStatus(runId);
                setAnalysisRun(updatedRun);
                if (updatedRun.status === 'completed' || updatedRun.status === 'failed') {
                    stopPolling(intervalId);
                }
            } catch (error) {
                toast.error("Failed to poll for status. Stopping.");
                stopPolling(intervalId);
            }
        }, 5000);
        setPollingIntervalId(intervalId);
    };

    const stopPolling = (idToClear: NodeJS.Timeout | null) => {
        if (idToClear) {
            clearInterval(idToClear);
            if (idToClear === pollingIntervalId) setPollingIntervalId(null);
        }
    };

    // --- NEW: A single callback function passed to child components ---
    const handleAnalysisSubmit = (runId: string) => {
        setPlotData(null); // Clear previous results
        setAnalysisRun({ id: runId, status: 'pending' }); // Set initial run state
        toast.success("Analysis submitted! Polling for status...");
        startPolling(runId);
    };

    const fetchResults = useCallback(async () => {
        if (!analysisRun?.output_artifacts?.results_json_s3_path) return;
        setIsLoadingResults(true);
        toast.info("Fetching analysis results...");
        try {
            const s3Path = analysisRun.output_artifacts.results_json_s3_path;
            const bucketName = "benchmate-results";
            const objectKey = s3Path.substring(s3Path.indexOf(bucketName) + bucketName.length + 1);
            const urlData = await getPresignedUrl(bucketName, objectKey);
            const results = await getJsonFromS3(urlData.url);
            setPlotData(results);
            toast.success("Results loaded!");
        } catch (error) {
            toast.error(`Failed to fetch results: ${error instanceof Error ? error.message : "Unknown error"}`);
        } finally {
            setIsLoadingResults(false);
        }
    }, [analysisRun]);

    useEffect(() => {
        if (analysisRun?.status === 'completed') {
            toast.success("Analysis complete!");
            fetchResults();
        } else if (analysisRun?.status === 'failed') {
            toast.error(`Analysis failed: ${analysisRun.error_message || "Unknown error"}`);
        }
    }, [analysisRun?.status, analysisRun?.error_message, fetchResults]);

    useEffect(() => {
        return () => { if (pollingIntervalId) clearInterval(pollingIntervalId); };
    }, [pollingIntervalId]);

    const getProgress = () => {
        if (!analysisRun) return 0;
        switch (analysisRun.status) {
            case 'pending': return 25;
            case 'running': return 65;
            case 'completed': return 100;
            case 'failed': return 100;
            default: return 0;
        }
    };
    
    const isAnalysisRunning = !!analysisRun && (analysisRun.status === 'pending' || analysisRun.status === 'running');

    return (
        <div className="container mx-auto p-4 md:p-8 space-y-8">
            <Toaster richColors position="top-right" />
            <header className="text-center">
                <h1 className="text-4xl font-bold tracking-tight">BenchTop Analysis Workbench</h1>
                <p className="text-muted-foreground mt-2">Bulk RNA-Seq Analysis Workflow</p>
            </header>

            <Card>
                <CardHeader>
                    <CardTitle>Step 1: Upload Data</CardTitle>
                    <CardDescription>
                        {isCreatingProject ? "Initializing project workspace..." : "Select and upload your data file."}
                    </CardDescription>
                </CardHeader>
                <CardContent className="flex flex-col sm:flex-row items-center gap-4">
                    <div className="grid w-full max-w-sm items-center gap-1.5">
                        <Label htmlFor="file-upload">Data File</Label>
                        <Input id="file-upload" type="file" ref={fileInputRef} onChange={handleFileChange} disabled={isCreatingProject || !projectId} />
                    </div>
                    <Button onClick={handleUpload} disabled={isUploading || !file || !projectId || isCreatingProject}>
                        {isUploading ? "Uploading..." : "Upload"}
                    </Button>
                    {createdDataset && <p className="text-sm text-green-600">Uploaded: {createdDataset.name}</p>}
                </CardContent>
            </Card>

            <Card>
                <CardHeader>
                    <CardTitle>Step 2: Run Analysis</CardTitle>
                    <CardDescription>Once your data is uploaded, choose an analysis to run.</CardDescription>
                </CardHeader>
                <CardContent className="flex flex-wrap gap-4">
                    {projectId && createdDataset && (
                        <>
                            <VolcanoAnalysis
                                projectId={projectId}
                                datasetId={createdDataset.id}
                                onAnalysisSubmit={handleAnalysisSubmit}
                                isDisabled={!createdDataset || isAnalysisRunning}
                            />
                            <PcaAnalysis
                                projectId={projectId}
                                datasetId={createdDataset.id}
                                onAnalysisSubmit={handleAnalysisSubmit}
                                isDisabled={!createdDataset || isAnalysisRunning}
                            />
                            <HeatmapAnalysis
                                projectId={projectId}
                                datasetId={createdDataset.id}
                                onAnalysisSubmit={handleAnalysisSubmit}
                                isDisabled={!createdDataset || isAnalysisRunning}
                            />
                        </>
                    )}
                </CardContent>
            </Card>

            {analysisRun && (
                <Card>
                    <CardHeader><CardTitle>Step 3: Monitor & View Results</CardTitle></CardHeader>
                    <CardContent className="space-y-4">
                        <div className="flex items-center gap-4">
                            <Label>Status:</Label>
                            <span className={`font-mono px-2 py-1 rounded-md text-sm ${analysisRun.status === 'completed' ? 'bg-green-100 text-green-800' : analysisRun.status === 'failed' ? 'bg-red-100 text-red-800' : 'bg-blue-100 text-blue-800'}`}>
                                {analysisRun.status}
                            </span>
                        </div>
                        <Progress value={getProgress()} />
                        
                        {isLoadingResults && <p>Loading results...</p>}

                        {plotData?.plot_type === 'volcano' && <InteractiveVolcanoPlot plotData={plotData as VolcanoPlotData} />}
                        {plotData?.plot_type === 'pca' && <InteractivePCAPlot plotData={plotData as PCAPlotData} />}
                        {plotData?.plot_type === 'heatmap' && <InteractiveHeatmap plotData={plotData as HeatmapData} />}

                        {analysisRun.status === 'failed' && (
                            <div className="text-red-600 bg-red-50 p-4 rounded-md">
                                <h3 className="font-bold">Analysis Failed</h3>
                                <p className="text-sm break-words">{analysisRun.error_message}</p>
                            </div>
                        )}
                    </CardContent>
                </Card>
            )}
        </div>
    );
}
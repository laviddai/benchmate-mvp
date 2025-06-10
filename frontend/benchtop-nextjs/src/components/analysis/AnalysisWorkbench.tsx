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
// Import the new createProject function
import { uploadAndCreateDataset, submitVolcanoAnalysis, getAnalysisRunStatus, getPresignedUrl, getJsonFromS3, createProject } from '@/lib/api';
import { type AnalysisPlotData } from '@/types/analysis';

const InteractiveVolcanoPlot = dynamic(
  () => import('@/components/analysis/InteractiveVolcanoPlot'),
  { 
    ssr: false,
    loading: () => <div className="text-center p-4">Loading interactive plot...</div> 
  }
);

interface Dataset {
    id: string;
    name: string;
}

interface AnalysisRun {
    id: string;
    status: 'pending' | 'running' | 'completed' | 'failed';
    output_artifacts?: {
        results_json_s3_path?: string;
        [key: string]: any;
    };
    error_message?: string;
}

export function AnalysisWorkbench() {
    // --- NEW STATE to hold the dynamically created project ID ---
    const [projectId, setProjectId] = useState<string | null>(null);
    const [isCreatingProject, setIsCreatingProject] = useState(true);

    const [file, setFile] = useState<File | null>(null);
    const [isUploading, setIsUploading] = useState(false);
    const [createdDataset, setCreatedDataset] = useState<Dataset | null>(null);
    
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [analysisRun, setAnalysisRun] = useState<AnalysisRun | null>(null);
    const [pollingIntervalId, setPollingIntervalId] = useState<NodeJS.Timeout | null>(null);
    
    const [plotData, setPlotData] = useState<AnalysisPlotData>(null);
    const [isLoadingResults, setIsLoadingResults] = useState(false);

    const fileInputRef = useRef<HTMLInputElement>(null);

    // --- NEW useEffect to create a project when the component first loads ---
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
    }, []); // The empty dependency array [] ensures this runs only once on mount

    const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
        if (event.target.files && event.target.files[0]) {
            setFile(event.target.files[0]);
        }
    };

    const handleUpload = async () => {
        // --- Guard clause to ensure projectId exists before uploading ---
        if (!projectId) {
            toast.error("Project is not initialized. Please wait or refresh.");
            return;
        }
        if (!file) {
            toast.error("Please select a file first.");
            return;
        }
        setIsUploading(true);
        toast.info("Uploading dataset...");

        const formData = new FormData();
        formData.append('file', file);
        // --- USE a dynamic projectId from state, NOT a hardcoded one ---
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

    const handleRunAnalysis = async () => {
        // --- Guard clauses for both projectId and dataset ---
        if (!projectId) {
            toast.error("Project is not initialized. Please wait or refresh.");
            return;
        }
        if (!createdDataset) {
            toast.error("Please upload a dataset first.");
            return;
        }
        setIsSubmitting(true);
        setPlotData(null);
        toast.info("Submitting analysis job...");

        const submissionData = {
            // --- USE dynamic projectId ---
            project_id: projectId,
            primary_input_dataset_id: createdDataset.id,
            analysis_name: `Volcano Plot for ${createdDataset.name}`,
            gene_col: null,
            log2fc_col: null,
            pvalue_col: null,
            fold_change_threshold: 1.0,
            p_value_threshold: 0.05,
        };

        try {
            const run = await submitVolcanoAnalysis(submissionData);
            setAnalysisRun(run);
            toast.success("Analysis submitted! Polling for status...");
            startPolling(run.id);
        } catch (error) {
            toast.error(`Submission failed: ${error instanceof Error ? error.message : "Unknown error"}`);
            setIsSubmitting(false);
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
            if (idToClear === pollingIntervalId) {
                setPollingIntervalId(null);
            }
        }
    };

    // --- This is the corrected syntax you discovered for useCallback ---
    const fetchResults = useCallback(async (): Promise<void> => {
        if (!analysisRun || !analysisRun.output_artifacts?.results_json_s3_path) return;
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
        return () => {
            if (pollingIntervalId) clearInterval(pollingIntervalId);
        };
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
                        {/* --- Add UI feedback for project creation state --- */}
                        {isCreatingProject 
                            ? "Initializing project workspace, please wait..." 
                            : "Select and upload your bulk RNA-seq data file (e.g., CSV, TSV, XLSX)."
                        }
                    </CardDescription>
                </CardHeader>
                <CardContent className="flex flex-col sm:flex-row items-center gap-4">
                    <div className="grid w-full max-w-sm items-center gap-1.5">
                        <Label htmlFor="file-upload">Data File</Label>
                        <Input id="file-upload" type="file" ref={fileInputRef} onChange={handleFileChange} disabled={isCreatingProject || !projectId} />
                    </div>
                    {/* --- Disable button until project is ready --- */}
                    <Button onClick={handleUpload} disabled={isUploading || !file || !projectId || isCreatingProject}>
                        {isUploading ? "Uploading..." : "Upload"}
                    </Button>
                    {createdDataset && <p className="text-sm text-green-600">Uploaded: {createdDataset.name}</p>}
                </CardContent>
            </Card>

            <Card>
                <CardHeader>
                    <CardTitle>Step 2: Run Analysis</CardTitle>
                    <CardDescription>
                        Once your data is uploaded, you can run an analysis. For this MVP, we will run a Volcano Plot.
                    </CardDescription>
                </CardHeader>
                <CardContent>
                    {/* --- Disable button until project is ready --- */}
                    <Button onClick={handleRunAnalysis} disabled={!createdDataset || isSubmitting || (!!analysisRun && analysisRun.status !== 'completed' && analysisRun.status !== 'failed') || !projectId}>
                        Run Volcano Plot Analysis
                    </Button>
                </CardContent>
            </Card>

            {analysisRun && (
                <Card>
                    <CardHeader>
                        <CardTitle>Step 3: Monitor & View Results</CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        <div className="flex items-center gap-4">
                            <Label>Status:</Label>
                            <span className={`font-mono px-2 py-1 rounded-md text-sm ${analysisRun.status === 'completed' ? 'bg-green-100 text-green-800' : analysisRun.status === 'failed' ? 'bg-red-100 text-red-800' : 'bg-blue-100 text-blue-800'}`}>
                                {analysisRun.status}
                            </span>
                        </div>
                        <Progress value={getProgress()} />
                        
                        {isLoadingResults && <p>Loading results...</p>}

                        {plotData && plotData.plot_type === 'volcano' && (
                            <InteractiveVolcanoPlot plotData={plotData} />
                        )}
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
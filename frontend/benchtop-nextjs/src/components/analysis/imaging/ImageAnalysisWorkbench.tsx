// frontend/benchtop-nextjs/src/components/analysis/imaging/ImageAnalysisWorkbench.tsx
'use client';

import React, { useState, useRef, useEffect, useCallback } from 'react';
import { Toaster, toast } from 'sonner';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Progress } from '@/components/ui/progress';
import { Slider } from '@/components/ui/slider';
import { uploadAndCreateDataset, createProject, submitGaussianBlurAnalysis, getAnalysisRunStatus, getPresignedUrl } from '@/lib/api';

// Define interfaces for our state objects
interface AnalysisRun {
    id: string;
    status: 'pending' | 'running' | 'completed' | 'failed';
    output_artifacts?: { filtered_image_s3_path?: string; [key: string]: any; };
    error_message?: string;
}

export function ImageAnalysisWorkbench() {
    // State Management
    const [projectId, setProjectId] = useState<string | null>(null);
    const [originalImageFile, setOriginalImageFile] = useState<File | null>(null);
    const [originalImageUrl, setOriginalImageUrl] = useState<string | null>(null);
    const [filteredImageUrl, setFilteredImageUrl] = useState<string | null>(null);
    const [sigma, setSigma] = useState<number>(2.0);
    const [analysisRun, setAnalysisRun] = useState<AnalysisRun | null>(null);
    const [isLoading, setIsLoading] = useState<boolean>(false);
    const pollingRef = useRef<NodeJS.Timeout | null>(null);

    // Initialize a project on component mount
    useEffect(() => {
        const initializeProject = async () => {
            try {
                const newProject = await createProject("Default Imaging Project");
                setProjectId(newProject.id);
                toast.info(`Project "${newProject.name}" initialized.`);
            } catch (error) {
                toast.error("Failed to initialize project.");
                console.error(error);
            }
        };
        initializeProject();
    }, []);

    // Cleanup polling on component unmount
    useEffect(() => {
        return () => {
            if (pollingRef.current) {
                clearInterval(pollingRef.current);
            }
        };
    }, []);

    const stopPolling = useCallback((idToClear: NodeJS.Timeout | null) => {
        if (idToClear) {
            clearInterval(idToClear);
        }
    }, []);

    const startPolling = useCallback((runId: string) => {
        const intervalId = setInterval(async () => {
            try {
                const statusResult: AnalysisRun = await getAnalysisRunStatus(runId);
                setAnalysisRun(statusResult);

                if (statusResult.status === 'completed' || statusResult.status === 'failed') {
                    stopPolling(intervalId);
                    setIsLoading(false);
                    if (statusResult.status === 'completed') {
                        toast.success("Analysis complete!");
                        const s3Path = statusResult.output_artifacts?.filtered_image_s3_path;
                        if (s3Path) {
                            const [bucketName, ...objectKeyParts] = s3Path.replace('s3://', '').split('/');
                            const objectKey = objectKeyParts.join('/');
                            const urlData = await getPresignedUrl(bucketName, objectKey);
                            setFilteredImageUrl(urlData.url);
                        }
                    } else {
                        toast.error(`Analysis failed: ${statusResult.error_message || 'Unknown error'}`);
                    }
                }
            } catch (error) {
                console.error("Polling error:", error);
                toast.error("Failed to get analysis status.");
                stopPolling(intervalId);
                setIsLoading(false);
            }
        }, 3000);
        pollingRef.current = intervalId;
    }, [stopPolling]);

    const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
        const file = event.target.files?.[0];
        if (file) {
            setOriginalImageFile(file);
            setOriginalImageUrl(URL.createObjectURL(file));
            setFilteredImageUrl(null); // Clear previous results
            setAnalysisRun(null);
        }
    };

    const handleRunAnalysis = async () => {
        if (!originalImageFile || !projectId) {
            toast.warning("Please select an image file first.");
            return;
        }

        setIsLoading(true);
        setFilteredImageUrl(null);
        setAnalysisRun(null);
        toast.info("Uploading image and submitting analysis...");

        try {
            // 1. Upload image and create dataset record
            const formData = new FormData();
            formData.append("file", originalImageFile);
            formData.append("project_id", projectId);
            formData.append("name", originalImageFile.name);
            formData.append("metadata_json", JSON.stringify({ source: "ImageAnalysisWorkbench" }));
            
            const dataset = await uploadAndCreateDataset(formData);
            toast.success(`Dataset "${dataset.name}" created.`);

            // 2. Submit analysis job
            const submissionData = {
                projectId: projectId,
                primary_input_dataset_id: dataset.id,
                sigma: sigma,
                analysis_name: `Gaussian Blur (Sigma ${sigma}) on ${originalImageFile.name}`
            };
            const newRun: AnalysisRun = await submitGaussianBlurAnalysis(submissionData);
            setAnalysisRun(newRun);
            
            // 3. Start polling for results
            startPolling(newRun.id);

        } catch (error) {
            console.error("Analysis submission failed:", error);
            toast.error("Failed to submit analysis.");
            setIsLoading(false);
        }
    };

    const getProgress = () => {
        if (!isLoading || !analysisRun) return 0;
        switch (analysisRun.status) {
            case 'pending': return 33;
            case 'running': return 66;
            case 'completed': return 100;
            default: return 0;
        }
    };

    return (
        <>
            <Toaster position="bottom-right" />
            <Card className="w-full max-w-4xl mx-auto mt-8">
                <CardHeader>
                    <CardTitle>Image Analysis Workbench</CardTitle>
                    <CardDescription>Upload an image and apply a Gaussian Blur filter.</CardDescription>
                </CardHeader>
                <CardContent className="space-y-6">
                    {/* --- CONTROLS --- */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6 items-start">
                        <div className="space-y-2">
                            <Label htmlFor="image-upload">1. Upload Image</Label>
                            <Input id="image-upload" type="file" accept="image/png, image/tiff, image/jpeg" onChange={handleFileChange} />
                        </div>
                        <div className="space-y-2">
                            <Label htmlFor="sigma-slider">2. Set Sigma ({sigma.toFixed(1)})</Label>
                            <Slider
                                id="sigma-slider"
                                min={0.1}
                                max={10}
                                step={0.1}
                                value={[sigma]}
                                onValueChange={(value) => setSigma(value[0])}
                                disabled={isLoading || !originalImageFile}
                            />
                        </div>
                    </div>
                    <Button onClick={handleRunAnalysis} disabled={!originalImageFile || isLoading}>
                        {isLoading ? "Processing..." : "3. Run Gaussian Blur"}
                    </Button>

                    {/* --- STATUS AND PROGRESS --- */}
                    {isLoading && analysisRun && (
                        <div className="space-y-2">
                            <Label>Status: {analysisRun.status}</Label>
                            <Progress value={getProgress()} className="w-full" />
                        </div>
                    )}
                    
                    {/* --- IMAGE DISPLAY --- */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div className="space-y-2">
                            <Label>Original Image</Label>
                            <div className="aspect-square w-full bg-slate-100 rounded-md flex items-center justify-center border">
                                {originalImageUrl ? (
                                    <img src={originalImageUrl} alt="Original" className="max-w-full max-h-full object-contain" />
                                ) : (
                                    <span className="text-slate-500">Awaiting image upload...</span>
                                )}
                            </div>
                        </div>
                        <div className="space-y-2">
                            <Label>Filtered Image</Label>
                            <div className="aspect-square w-full bg-slate-100 rounded-md flex items-center justify-center border">
                                {isLoading && <span className="text-slate-500">Processing...</span>}
                                {!isLoading && filteredImageUrl && (
                                    <img src={filteredImageUrl} alt="Filtered" className="max-w-full max-h-full object-contain" />
                                )}
                                {!isLoading && !filteredImageUrl && (
                                    <span className="text-slate-500">Result will appear here.</span>
                                )}
                            </div>
                        </div>
                    </div>
                </CardContent>
            </Card>
        </>
    );
}
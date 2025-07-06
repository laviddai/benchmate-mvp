// frontend/benchtop-nextjs/src/components/analysis/InteractiveHeatmap.tsx
"use client";

import React, { useState, useMemo, useCallback, useRef } from 'react'; // Removed useEffect as it's not directly used here anymore
import dynamic from 'next/dynamic';
import { type Layout, type Data } from 'plotly.js';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Checkbox } from '@/components/ui/checkbox';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Download, RotateCcw, Info } from 'lucide-react';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";
import Plotly from 'plotly.js-dist-min'; // Import Plotly for the download function

import { type HeatmapData } from '@/types/heatmap.types';

const ClientOnlyPlot = dynamic(() => import('@/components/analysis/ClientOnlyPlot'), {
  ssr: false,
  loading: () => <div className="h-[600px] w-full flex items-center justify-center">Loading Plot...</div>,
});

interface PlotState {
    title: string;
    colorMap: string;
    showGeneLabels: boolean;
    showSampleLabels: boolean;
}

const CustomCheckbox = ({ label, checked, onCheckedChange }: { label: string, checked: boolean, onCheckedChange: (checked: boolean) => void }) => (
    <div className="flex items-center space-x-2">
        <Checkbox id={label} checked={checked} onCheckedChange={onCheckedChange} />
        <label htmlFor={label} className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70">{label}</label>
    </div>
);

const InfoTooltip = ({ content }: { content: string }) => (
    <TooltipProvider delayDuration={100}>
        <Tooltip>
            <TooltipTrigger asChild><button type="button" className="ml-1.5"><Info size={14} className="text-muted-foreground" /></button></TooltipTrigger>
            <TooltipContent><p className="max-w-xs">{content}</p></TooltipContent>
        </Tooltip>
    </TooltipProvider>
);

export default function InteractiveHeatmap({ plotData }: { plotData: HeatmapData }) {
    // --- FIX: Create a ref that can be forwarded to the ClientOnlyPlot ---
    const plotRef = useRef<HTMLDivElement>(null);
    const { plot_data, default_plot_config, summary_stats } = plotData;

    const getInitialState = useCallback((): PlotState => ({
        title: default_plot_config.title,
        colorMap: default_plot_config.color_map,
        showGeneLabels: default_plot_config.show_gene_labels,
        showSampleLabels: default_plot_config.show_sample_labels,
    }), [default_plot_config]);

    const [state, setState] = useState<PlotState>(getInitialState);

    const handleStateChange = <K extends keyof PlotState>(key: K, value: PlotState[K]) => {
        setState(prevState => ({ ...prevState, [key]: value }));
    };

    const { data, layout } = useMemo(() => {
        const allValues = plot_data.heatmap_values.flat().filter(v => isFinite(v));
        const zMin = Math.min(...allValues);
        const zMax = Math.max(...allValues);

        const trace: Data = {
            z: plot_data.heatmap_values,
            x: plot_data.sample_labels,
            y: plot_data.gene_labels,
            type: 'heatmap',
            colorscale: state.colorMap,
            showscale: true,
            hovertemplate: default_plot_config.hover_template,
            zmin: zMin,
            zmax: zMax,
        };

        const plotLayout: Partial<Layout> = {
            title: { text: `${state.title}<br><sub>${summary_stats.gene_selection_reason}</sub>`, x: 0.5, xanchor: 'center', yanchor: 'top', y: 0.95 },
            xaxis: { tickangle: -45, showticklabels: state.showSampleLabels, categoryorder: 'array', categoryarray: plot_data.sample_labels },
            yaxis: { showticklabels: state.showGeneLabels, automargin: true, categoryorder: 'array', categoryarray: plot_data.gene_labels },
            autosize: true,
            margin: { l: state.showGeneLabels ? 120 : 50, r: 30, t: 90, b: state.showSampleLabels ? 120 : 50 },
        };

        return { data: [trace], layout: plotLayout };
    }, [state, plot_data, default_plot_config, summary_stats]);
    
    // --- FIX: Re-enable download functionality ---
    const downloadPlot = useCallback(async () => {
        if (plotRef.current) {
            const dataUrl = await Plotly.toImage(plotRef.current, { format: 'png', width: 1200, height: 1000, scale: 2 });
            const link = document.createElement('a');
            link.download = `${state.title.replace(/\s+/g, '_')}.png`;
            link.href = dataUrl;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        }
    }, [state.title]);
    
    const downloadData = useCallback(() => {
        const csvData = [
            ['gene', ...plot_data.sample_labels],
            ...plot_data.gene_labels.map((gene, i) => [gene, ...plot_data.heatmap_values[i]])
        ];
        const csvContent = "data:text/csv;charset=utf-8," + csvData.map(e => e.join(",")).join("\n");
        const link = document.createElement("a");
        link.setAttribute("href", encodeURI(csvContent));
        link.setAttribute("download", "heatmap_data.csv");
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }, [plot_data]);

    const colorMaps = ['RdBu_r', 'Viridis', 'Plasma', 'Inferno', 'Magma', 'Cividis', 'Greys', 'Blues', 'Greens'];
    
    // --- FIX: Create a more accurate description ---
    const cardDescription = `${summary_stats.gene_selection_reason} (${plot_data.gene_labels.length} genes shown).`;

    return (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mt-6">
            <div className="lg:col-span-2 flex justify-center items-start">
                <div className="w-full" style={{ maxWidth: '800px' }}>
                    <Card>
                        <CardHeader>
                            <CardTitle>{state.title}</CardTitle>
                            <CardDescription>{cardDescription}</CardDescription>
                        </CardHeader>
                        <CardContent className="p-2">
                            <ClientOnlyPlot ref={plotRef} data={data} layout={layout} style={{width: '100%', height: '600px'}} />
                        </CardContent>
                    </Card>
                </div>
            </div>
            <div className="space-y-4">
                <Card>
                    <CardHeader className="flex flex-row items-center justify-between pb-2">
                        <CardTitle>Plot Controls</CardTitle>
                        <Button variant="ghost" size="sm" onClick={() => setState(getInitialState())}><RotateCcw size={14} className="mr-2"/>Reset</Button>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        <div>
                            <Label htmlFor="plot-title">Plot Title</Label>
                            <Input id="plot-title" value={state.title} onChange={(e) => handleStateChange('title', e.target.value)} />
                        </div>
                        <div>
                            <Label htmlFor="color-map-select">Color Map</Label>
                            <div className="flex items-center">
                                <Select value={state.colorMap} onValueChange={(val) => handleStateChange('colorMap', val)}>
                                    <SelectTrigger id="color-map-select"><SelectValue /></SelectTrigger>
                                    <SelectContent>
                                        {colorMaps.map(map => <SelectItem key={map} value={map}>{map}</SelectItem>)}
                                    </SelectContent>
                                </Select>
                                <InfoTooltip content="RdBu_r is ideal for z-scored data (Red=High, Blue=Low). Others are sequential." />
                            </div>
                        </div>
                        <div className="grid grid-cols-2 gap-4 pt-2">
                            <CustomCheckbox label="Show Gene Labels" checked={state.showGeneLabels} onCheckedChange={(c: boolean) => handleStateChange('showGeneLabels', c)} />
                            <CustomCheckbox label="Show Sample Labels" checked={state.showSampleLabels} onCheckedChange={(c: boolean) => handleStateChange('showSampleLabels', c)} />
                        </div>
                    </CardContent>
                </Card>
                <Card>
                    <CardHeader><CardTitle className="flex items-center gap-2"><Download size={20} /> Data & Image</CardTitle></CardHeader>
                    <CardContent className="space-y-2 pt-2">
                         <Button onClick={downloadData} variant="outline" className="w-full">Download Plotted Data</Button>
                         <Button onClick={downloadPlot} className="w-full">Download Plot as PNG</Button>
                    </CardContent>
                </Card>
            </div>
        </div>
    );
}
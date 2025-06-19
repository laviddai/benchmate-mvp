// frontend/benchtop-nextjs/src/components/analysis/InteractivePCAPlot.tsx
"use client";

import React, { useState, useMemo, useCallback, useEffect, useRef } from 'react';
import Plotly from 'plotly.js-basic-dist-min';
import { type Layout, type Data } from 'plotly.js';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Checkbox } from '@/components/ui/checkbox';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";
import { Download, Info, RotateCcw } from 'lucide-react';

import { type PCAPlotData, type PCAPoint } from '@/types/pca.types';

// A state interface to hold all user-customizable plot settings
interface PlotState {
    title: string;
    pcX: number;
    pcY: number;
    pointSize: number;
    showGridLines: boolean;
    showPlotBorder: boolean;
}

const InfoTooltip = ({ content }: { content: string }) => (
    <TooltipProvider delayDuration={100}>
        <Tooltip>
            <TooltipTrigger asChild><button type="button" className="ml-1.5"><Info size={14} className="text-muted-foreground" /></button></TooltipTrigger>
            <TooltipContent><p className="max-w-xs">{content}</p></TooltipContent>
        </Tooltip>
    </TooltipProvider>
);

const CustomCheckbox = ({ label, checked, onCheckedChange }: { label: string, checked: boolean, onCheckedChange: (checked: boolean) => void }) => (
    <div className="flex items-center space-x-2">
        <Checkbox id={label} checked={checked} onCheckedChange={onCheckedChange} />
        <label htmlFor={label} className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70">{label}</label>
    </div>
);

export default function InteractivePCAPlot({ plotData }: { plotData: PCAPlotData }) {
    const plotRef = useRef<HTMLDivElement>(null);
    const { plot_data, default_plot_config, summary_stats } = plotData;

    // Function to set the initial state from backend defaults
    const getInitialState = useCallback((): PlotState => ({
        title: default_plot_config.title,
        pcX: default_plot_config.pc_x_axis,
        pcY: default_plot_config.pc_y_axis,
        pointSize: default_plot_config.point_size,
        showGridLines: true,
        showPlotBorder: false,
    }), [default_plot_config]);

    const [state, setState] = useState<PlotState>(getInitialState);

    const handleStateChange = <K extends keyof PlotState>(key: K, value: PlotState[K]) => {
        setState(prevState => ({ ...prevState, [key]: value }));
    };

    // useMemo hook to recalculate plot data only when state or data changes
    const { traces, layout } = useMemo(() => {
        const groups = new Map<string, { x: number[], y: number[], text: string[] }>();
        const pcXKey = `PC${state.pcX}`;
        const pcYKey = `PC${state.pcY}`;

        plot_data.forEach((d: PCAPoint) => {
            const groupName = d.group || 'all_samples';
            if (!groups.has(groupName)) {
                groups.set(groupName, { x: [], y: [], text: [] });
            }
            const group = groups.get(groupName)!;
            group.x.push(d[pcXKey] as number);
            group.y.push(d[pcYKey] as number);
            group.text.push(d.sample);
        });

        const allTraces: Partial<Data>[] = Array.from(groups.entries()).map(([groupName, data]) => ({
            ...data,
            type: 'scatter',
            mode: 'markers',
            name: groupName,
            marker: { size: state.pointSize },
            hoverinfo: 'x+y+text',
            text: data.text,
        }));
        
        const getAxisLabel = (pcIndex: number): string => {
            const variance = summary_stats.explained_variance_ratio[pcIndex - 1];
            return `PC${pcIndex} (${(variance * 100).toFixed(1)}%)`;
        };

        const plotLayout: Partial<Layout> = {
            title: { text: state.title, x: 0.5, xanchor: 'center', yanchor: 'top', y: 0.95 },
            xaxis: { 
                title: { text: getAxisLabel(state.pcX) },
                automargin: true,
                gridcolor: state.showGridLines ? '#eee' : 'rgba(0,0,0,0)',
                zeroline: false,
                showline: state.showPlotBorder,
                mirror: state.showPlotBorder,
                linecolor: 'black',
                linewidth: 1,
            },
            yaxis: { 
                title: { text: getAxisLabel(state.pcY) },
                automargin: true,
                gridcolor: state.showGridLines ? '#eee' : 'rgba(0,0,0,0)',
                zeroline: false,
                showline: state.showPlotBorder,
                mirror: state.showPlotBorder,
                linecolor: 'black',
                linewidth: 1,
            },
            hovermode: 'closest',
            showlegend: true,
            autosize: true,
            margin: { l: 70, r: 30, t: 80, b: 60 },
        };

        return { traces: allTraces, layout: plotLayout };
    }, [state, plot_data, summary_stats]);

    useEffect(() => {
        if (plotRef.current) {
            Plotly.react(plotRef.current, traces as Data[], layout, { responsive: true, displaylogo: false });
        }
    }, [traces, layout]);

    const downloadPlot = useCallback(async () => {
        if (plotRef.current) {
            const dataUrl = await Plotly.toImage(plotRef.current, { format: 'png', width: 1200, height: 900, scale: 2 });
            const link = document.createElement('a');
            link.download = `${state.title.replace(/\s+/g, '_')}_PC${state.pcX}_vs_PC${state.pcY}.png`;
            link.href = dataUrl;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        }
    }, [state.title, state.pcX, state.pcY]);
    
    const downloadData = useCallback(() => {
        const headers = Object.keys(plot_data[0]).join(',');
        const csvContent = "data:text/csv;charset=utf-8," + headers + "\n" + plot_data.map(row => Object.values(row).join(',')).join("\n");
        const link = document.createElement("a");
        link.setAttribute("href", encodeURI(csvContent));
        link.setAttribute("download", "pca_coordinates.csv");
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }, [plot_data]);

    const availablePCs = summary_stats.explained_variance_ratio.map((_, i) => i + 1);
    const pcTooltipContent = "PCA creates new axes (Principal Components) to summarize data. PC1 captures the most variation, PC2 the second most, etc. Plotting different PCs reveals different aspects of your data's structure.";

    return (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mt-6">
            <div className="lg:col-span-2 flex justify-center items-start">
                <div className="w-full" style={{ maxWidth: '800px' }}>
                    <Card>
                        <CardContent className="p-2">
                            <div ref={plotRef} className="w-full" style={{ aspectRatio: '1.25 / 1' }}></div>
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
                        <div className="grid grid-cols-2 gap-4">
                            <div>
                                {/* --- NEW: Added tooltip --- */}
                                <div className="flex items-center">
                                    <Label htmlFor="pc-x-select">X-Axis</Label>
                                    <InfoTooltip content={pcTooltipContent} />
                                </div>
                                <Select value={String(state.pcX)} onValueChange={(val) => handleStateChange('pcX', parseInt(val))}>
                                    <SelectTrigger id="pc-x-select"><SelectValue /></SelectTrigger>
                                    <SelectContent>
                                        {availablePCs.map(pc => <SelectItem key={`x-${pc}`} value={String(pc)}>PC{pc}</SelectItem>)}
                                    </SelectContent>
                                </Select>
                            </div>
                            <div>
                                {/* --- NEW: Added tooltip --- */}
                                <div className="flex items-center">
                                    <Label htmlFor="pc-y-select">Y-Axis</Label>
                                    <InfoTooltip content={pcTooltipContent} />
                                </div>
                                <Select value={String(state.pcY)} onValueChange={(val) => handleStateChange('pcY', parseInt(val))}>
                                    <SelectTrigger id="pc-y-select"><SelectValue /></SelectTrigger>
                                    <SelectContent>
                                        {availablePCs.map(pc => <SelectItem key={`y-${pc}`} value={String(pc)}>PC{pc}</SelectItem>)}
                                    </SelectContent>
                                </Select>
                            </div>
                        </div>
                         <div>
                            <div className="flex items-center">
                                <Label htmlFor="point-size">Point Size</Label>
                                <InfoTooltip content="Adjust the size of the points on the scatter plot." />
                            </div>
                            <Input id="point-size" type="number" value={state.pointSize} onChange={(e) => handleStateChange('pointSize', parseInt(e.target.value) || 8)} min={1} max={30} />
                        </div>
                        <div className="grid grid-cols-2 gap-4 pt-2">
                            <CustomCheckbox label="Grid Lines" checked={state.showGridLines} onCheckedChange={(c: boolean) => handleStateChange('showGridLines', c)} />
                            <CustomCheckbox label="Plot Border" checked={state.showPlotBorder} onCheckedChange={(c: boolean) => handleStateChange('showPlotBorder', c)} />
                        </div>
                    </CardContent>
                </Card>
                <Card>
                    <CardHeader><CardTitle className="flex items-center gap-2"><Download size={20} /> Data & Image</CardTitle></CardHeader>
                    <CardContent className="space-y-2 pt-2">
                         <Button onClick={downloadData} variant="outline" className="w-full">Download PCA Coordinates</Button>
                         <Button onClick={downloadPlot} className="w-full">Download Plot as PNG</Button>
                    </CardContent>
                </Card>
            </div>
        </div>
    );
}